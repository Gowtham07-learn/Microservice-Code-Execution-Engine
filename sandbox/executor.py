import subprocess
import time
from pathlib import Path

from app.core.interfaces.sandbox_executor import SandboxExecutor
from app.core.models.sandbox import ExecutionConfig, SandboxResult


SANDBOX_READY = True


class DockerSandboxExecutor(SandboxExecutor):
    """Execute untrusted programs inside a restricted Docker container."""

    IMAGE = "microservice-code-execution-engine:latest"

    def execute(
        self,
        command: list[str],
        stdin: str,
        config: ExecutionConfig,
        workspace: Path,
    ) -> SandboxResult:

        if not command:
            return SandboxResult(
                system_error=True,
                error_message="No command provided",
            )

        container_name = (
            f"code-sandbox-{int(time.time() * 1_000_000)}"
        )

        docker_command = [
            "docker",
            "run",
            "--rm",
            "--name",
            container_name,

            # Network isolation
            "--network",
            "none",

            # Drop Linux capabilities
            "--cap-drop",
            "ALL",

            # Prevent privilege escalation
            "--security-opt",
            "no-new-privileges",

            # CPU limit
            "--cpus",
            str(config.cpu_limit),

            # Memory limit
            "--memory",
            f"{config.memory_limit_mb}m",

            # Process limit
            "--pids-limit",
            str(config.max_processes),

            # Read-only root filesystem
            "--read-only",

            # Temporary writable /tmp
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=64m",

            # Only workspace is mounted
            "--mount",
            f"type=bind,src={workspace.resolve()},dst=/workspace,rw",

            "--workdir",
            "/workspace",

            # Run as nobody instead of root
            "--user",
            "65534:65534",

            self.IMAGE,
        ]

        docker_command.extend(command)

        start_time = time.monotonic()

        try:
            process = subprocess.Popen(
                docker_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            try:
                stdout, stderr = process.communicate(
                    input=stdin,
                    timeout=config.timeout_seconds,
                )

            except subprocess.TimeoutExpired:
                process.kill()

                stdout, stderr = process.communicate()

                # Extra cleanup in case the container still exists.
                self._remove_container(container_name)

                return SandboxResult(
                    exit_code=process.returncode,
                    stdout=self._limit_output(
                        stdout,
                        config.max_output_bytes,
                    )[0],
                    stderr=self._limit_output(
                        stderr,
                        config.max_output_bytes,
                    )[0],
                    timed_out=True,
                    error_message="Execution exceeded the time limit",
                    metadata={
                        "execution_time": time.monotonic() - start_time,
                    },
                )

            stdout, stdout_truncated = self._limit_output(
                stdout,
                config.max_output_bytes,
            )

            stderr, stderr_truncated = self._limit_output(
                stderr,
                config.max_output_bytes,
            )

            return SandboxResult(
                exit_code=process.returncode,
                stdout=stdout,
                stderr=stderr,
                output_truncated=(
                    stdout_truncated or stderr_truncated
                ),
                metadata={
                    "execution_time": time.monotonic() - start_time,
                },
            )

        except FileNotFoundError:
            return SandboxResult(
                system_error=True,
                error_message="Docker executable was not found",
            )

        except Exception as exc:
            return SandboxResult(
                system_error=True,
                error_message=f"Sandbox execution failed: {exc}",
            )

        finally:
            self._remove_container(container_name)

    @staticmethod
    def _limit_output(
        output: str,
        max_bytes: int,
    ) -> tuple[str, bool]:

        output_bytes = output.encode("utf-8")

        if len(output_bytes) <= max_bytes:
            return output, False

        truncated = output_bytes[:max_bytes].decode(
            "utf-8",
            errors="replace",
        )

        return truncated, True

    @staticmethod
    def _remove_container(container_name: str) -> None:
        """Best-effort container cleanup."""

        try:
            subprocess.run(
                [
                    "docker",
                    "rm",
                    "-f",
                    container_name,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=5,
            )
        except Exception:
            # Cleanup must never mask the original execution result.
            pass       