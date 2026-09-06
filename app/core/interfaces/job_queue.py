from abc import ABC, abstractmethod

from app.core.models.request import ExecutionRequest
from app.core.models.result import ExecutionResult


class JobQueue(ABC):
    """Decouples the API process from CPU-bound sandbox work."""

    @abstractmethod
    async def enqueue(self, job_id: str, request: ExecutionRequest) -> None:
        """Accept a job for a worker."""

    @abstractmethod
    async def dequeue(self) -> tuple[str, ExecutionRequest]:
        """Block until a job is available. Returns (job_id, request)."""

    @abstractmethod
    async def store_result(self, job_id: str, result: ExecutionResult) -> None:
        """Publish a finished execution result."""

    @abstractmethod
    async def wait_for_result(self, job_id: str, timeout_seconds: float) -> ExecutionResult:
        """Block until the result is stored or the wait times out."""
