from pydantic import BaseModel, Field


class ExecutionConfig(BaseModel):
    timeout_seconds: float = 2.0
    memory_limit_mb: int = 128
    cpu_limit: float = 0.5
    max_output_bytes: int = 1_048_576
    max_processes: int = 32
    network_disabled: bool = True


class SandboxResult(BaseModel):
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    output_truncated: bool = False
    system_error: bool = False
    error_message: str | None = None
    metadata: dict = Field(default_factory=dict)
