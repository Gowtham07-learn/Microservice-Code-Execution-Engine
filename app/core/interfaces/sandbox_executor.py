from abc import ABC, abstractmethod
from pathlib import Path

from app.core.models.sandbox import ExecutionConfig, SandboxResult


class SandboxExecutor(ABC):
    """Contract for isolated command execution. Implemented by Junior 2.

    The core never issues Docker commands. It only passes argv, stdin, and limits.
    """

    @abstractmethod
    def execute(
        self,
        command: list[str],
        stdin: str,
        config: ExecutionConfig,
        workspace: Path,
    ) -> SandboxResult:
        """Run command with stdin under resource limits. Always clean up containers."""
