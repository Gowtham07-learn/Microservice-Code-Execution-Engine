from pathlib import Path

from app.core.interfaces.sandbox_executor import SandboxExecutor
from app.core.models.sandbox import ExecutionConfig, SandboxResult

SANDBOX_READY = False


class DockerSandboxExecutor(SandboxExecutor):
    """Junior 2: isolate argv with Docker. Enforce timeout and resource limits.

    Core must not know Docker commands. Set SANDBOX_READY = True when complete.
    """

    def execute(
        self,
        command: list[str],
        stdin: str,
        config: ExecutionConfig,
        workspace: Path,
    ) -> SandboxResult:
        raise NotImplementedError(
            "Junior 2: implement DockerSandboxExecutor.execute"
        )
