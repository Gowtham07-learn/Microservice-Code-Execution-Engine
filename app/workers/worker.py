import asyncio
import logging

from app.core.engine.orchestrator import ExecutionOrchestrator
from app.core.interfaces.job_queue import JobQueue
from app.core.models.enums import ExecutionStatus
from app.core.models.result import ExecutionResult

logger = logging.getLogger(__name__)


async def run_worker_loop(queue: JobQueue, orchestrator: ExecutionOrchestrator) -> None:
    """Consume queued execution jobs until cancelled."""
    while True:
        job_id, request = await queue.dequeue()
        try:
            result = await asyncio.to_thread(orchestrator.execute, request)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Worker failed job %s", job_id)
            result = ExecutionResult(
                status=ExecutionStatus.SYSTEM_ERROR,
                total_test_cases=len(request.test_cases),
                error_message=f"Worker error: {exc}",
            )
        await queue.store_result(job_id, result)


def main() -> None:
    """Entry point: python -m app.workers.worker"""
    logging.basicConfig(level=logging.INFO)
    from app.main import build_container

    container = build_container()
    asyncio.run(run_worker_loop(container["queue"], container["orchestrator"]))


if __name__ == "__main__":
    main()
