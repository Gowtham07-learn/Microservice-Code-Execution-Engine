from pathlib import Path

from app.core.interfaces.sandbox_executor import SandboxExecutor
from app.core.models.sandbox import ExecutionConfig, SandboxResult


class StubSandboxExecutor(SandboxExecutor):
    """Placeholder until Junior 2 implements Docker isolation and limits.

    Does not execute untrusted code. Returns SYSTEM_ERROR so the API never
    runs submissions inside the FastAPI process.
    """

    def execute(
        self,
        command: list[str],
        stdin: str,
        config: ExecutionConfig,
        workspace: Path,
    ) -> SandboxResult:
        return SandboxResult(
            exit_code=-1,
            system_error=True,
            error_message="Sandbox not implemented (Junior 2: Docker sandbox + limits)",
        )
