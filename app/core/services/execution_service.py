from app.core.interfaces.job_queue import JobQueue
from app.core.models.request import ExecutionRequest
from app.core.models.result import ExecutionResult
from app.core.services.queue import new_job_id


class ExecutionService:
    """API-facing facade: enqueue work and wait for the worker result."""

    def __init__(self, queue: JobQueue, wait_timeout_seconds: float) -> None:
        self._queue = queue
        self._wait_timeout_seconds = wait_timeout_seconds

    async def submit(self, request: ExecutionRequest) -> ExecutionResult:
        job_id = new_job_id()
        await self._queue.enqueue(job_id, request)
        return await self._queue.wait_for_result(job_id, self._wait_timeout_seconds)
