import asyncio
import json
import uuid

from app.core.interfaces.job_queue import JobQueue
from app.core.models.request import ExecutionRequest
from app.core.models.result import ExecutionResult
from app.core.models.enums import ExecutionStatus


class InMemoryJobQueue(JobQueue):
    """Process-local queue used for tests and single-process local runs."""

    def __init__(self) -> None:
        self._jobs: asyncio.Queue[tuple[str, ExecutionRequest]] = asyncio.Queue()
        self._results: dict[str, ExecutionResult] = {}
        self._events: dict[str, asyncio.Event] = {}

    def _event(self, job_id: str) -> asyncio.Event:
        if job_id not in self._events:
            self._events[job_id] = asyncio.Event()
        return self._events[job_id]

    async def enqueue(self, job_id: str, request: ExecutionRequest) -> None:
        self._event(job_id)
        await self._jobs.put((job_id, request))

    async def dequeue(self) -> tuple[str, ExecutionRequest]:
        return await self._jobs.get()

    async def store_result(self, job_id: str, result: ExecutionResult) -> None:
        self._results[job_id] = result
        self._event(job_id).set()

    async def wait_for_result(self, job_id: str, timeout_seconds: float) -> ExecutionResult:
        event = self._event(job_id)
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout_seconds)
        except TimeoutError:
            return ExecutionResult(
                status=ExecutionStatus.SYSTEM_ERROR,
                error_message="Timed out waiting for an execution worker",
            )
        return self._results[job_id]


class RedisJobQueue(JobQueue):
    """Shared queue for API + worker processes (docker compose / scale-out)."""

    JOBS_KEY = "execution:jobs"

    def __init__(self, redis_client, result_ttl_seconds: int = 300) -> None:
        self._redis = redis_client
        self._ttl = result_ttl_seconds

    def _result_key(self, job_id: str) -> str:
        return f"execution:result:{job_id}"

    async def enqueue(self, job_id: str, request: ExecutionRequest) -> None:
        payload = json.dumps({"job_id": job_id, "request": request.model_dump()})
        await self._redis.lpush(self.JOBS_KEY, payload)

    async def dequeue(self) -> tuple[str, ExecutionRequest]:
        while True:
            item = await self._redis.brpop(self.JOBS_KEY, timeout=5)
            if item is None:
                continue
            _key, raw = item
            data = json.loads(raw)
            return data["job_id"], ExecutionRequest.model_validate(data["request"])

    async def store_result(self, job_id: str, result: ExecutionResult) -> None:
        await self._redis.setex(
            self._result_key(job_id),
            self._ttl,
            result.model_dump_json(),
        )

    async def wait_for_result(self, job_id: str, timeout_seconds: float) -> ExecutionResult:
        deadline = asyncio.get_event_loop().time() + timeout_seconds
        key = self._result_key(job_id)
        while asyncio.get_event_loop().time() < deadline:
            raw = await self._redis.get(key)
            if raw:
                return ExecutionResult.model_validate_json(raw)
            await asyncio.sleep(0.05)
        return ExecutionResult(
            status=ExecutionStatus.SYSTEM_ERROR,
            error_message="Timed out waiting for an execution worker",
        )


def new_job_id() -> str:
    return str(uuid.uuid4())
