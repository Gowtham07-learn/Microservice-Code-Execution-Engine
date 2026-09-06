from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "code-execution-engine"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    queue_backend: str = "memory"
    redis_url: str = "redis://localhost:6379/0"
    job_result_ttl_seconds: int = 300
    job_wait_timeout_seconds: float = 30.0

    max_code_bytes: int = 64_000
    max_test_cases: int = 20
    max_test_case_bytes: int = 8_192

    timeout_seconds: float = 2.0
    memory_limit_mb: int = 128
    cpu_limit: float = 0.5
    max_output_bytes: int = 1_048_576
    max_processes: int = 32

    def execution_config(self):
        from app.core.models.sandbox import ExecutionConfig

        return ExecutionConfig(
            timeout_seconds=self.timeout_seconds,
            memory_limit_mb=self.memory_limit_mb,
            cpu_limit=self.cpu_limit,
            max_output_bytes=self.max_output_bytes,
            max_processes=self.max_processes,
            network_disabled=True,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
