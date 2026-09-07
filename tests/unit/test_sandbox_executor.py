from pathlib import Path
from unittest.mock import patch

from app.core.models.sandbox import ExecutionConfig
from sandbox.executor import DockerSandboxExecutor


def test_output_under_limit_is_not_truncated():
    output, truncated = DockerSandboxExecutor._limit_output(
        "hello",
        100,
    )

    assert output == "hello"
    assert truncated is False


def test_output_over_limit_is_truncated():
    output, truncated = DockerSandboxExecutor._limit_output(
        "A" * 100,
        10,
    )

    assert len(output.encode("utf-8")) <= 10
    assert truncated is True


def test_docker_command_contains_security_limits(tmp_path):
    executor = DockerSandboxExecutor()

    config = ExecutionConfig(
        timeout_seconds=2,
        memory_limit_mb=128,
        cpu_limit=0.5,
        max_output_bytes=1024,
        max_processes=32,
        network_disabled=True,
    )

    captured_command = []

    def fake_popen(command, **kwargs):
        captured_command.extend(command)

        class FakeProcess:
            returncode = 0

            def communicate(self, input=None, timeout=None):
                return "", ""

        return FakeProcess()

    with patch("sandbox.executor.subprocess.Popen", side_effect=fake_popen):
        executor.execute(
            ["python", "main.py"],
            "",
            config,
            tmp_path,
        )

    assert "--network" in captured_command
    assert "none" in captured_command

    assert "--cap-drop" in captured_command
    assert "ALL" in captured_command

    assert "--cpus" in captured_command
    assert "0.5" in captured_command

    assert "--memory" in captured_command
    assert "128m" in captured_command

    assert "--pids-limit" in captured_command
    assert "32" in captured_command

    assert "--read-only" in captured_command
    assert "--user" in captured_command
    assert "65534:65534" in captured_command


def test_empty_command_returns_system_error(tmp_path):
    executor = DockerSandboxExecutor()

    result = executor.execute(
        [],
        "",
        ExecutionConfig(),
        tmp_path,
    )

    assert result.system_error is True
    assert result.error_message == "No command provided"
    