from pathlib import Path

import pytest

from app.core.exceptions import PluginValidationError
from app.core.models.enums import ExecutionStatus, TestCaseStatus
from app.core.models.request import ExecutionRequest, TestCase
from app.core.models.sandbox import SandboxResult
from plugins.c.plugin import CPlugin
from plugins.python.plugin import PythonPlugin
from tests.conftest import build_orchestrator
from tests.fakes import ScriptedSandbox


def execution_request(language: str, code: str, *cases: tuple[str, str]) -> ExecutionRequest:
    return ExecutionRequest(
        language=language,
        code=code,
        test_cases=[
            TestCase(input=stdin, expected_output=expected)
            for stdin, expected in cases
        ],
    )


def test_python_prepare_and_run_command(tmp_path: Path):
    plugin = PythonPlugin()
    prepared = plugin.prepare("print('hello')", tmp_path)

    assert prepared.source_path == tmp_path / "main.py"
    assert prepared.source_path.read_text(encoding="utf-8") == "print('hello')"
    assert plugin.compile_command(prepared) is None
    assert plugin.run_command(prepared) == ["python", "main.py"]


def test_python_program_with_input_and_stdout_capture():
    sandbox = ScriptedSandbox([SandboxResult(exit_code=0, stdout="10\n")])
    orchestrator, _, _, _ = build_orchestrator(plugin=PythonPlugin(), sandbox=sandbox)

    result = orchestrator.execute(
        execution_request("python", "n = int(input())\nprint(n * 2)", ("5", "10"))
    )

    assert result.status == ExecutionStatus.COMPLETED
    assert result.results[0].status == TestCaseStatus.PASSED
    assert result.results[0].actual_output == "10"
    assert sandbox.commands == [["python", "main.py"]]
    assert sandbox.stdins == ["5"]


def test_python_syntax_error():
    plugin = PythonPlugin()

    with pytest.raises(PluginValidationError, match="Python syntax error"):
        plugin.validate("def broken(:\n    pass")


def test_python_runtime_error_uses_stderr():
    sandbox = ScriptedSandbox([SandboxResult(exit_code=1, stderr="ZeroDivisionError")])
    orchestrator, _, _, _ = build_orchestrator(plugin=PythonPlugin(), sandbox=sandbox)

    result = orchestrator.execute(
        execution_request("python", "print(1 / 0)", ("", ""))
    )

    assert result.results[0].status == TestCaseStatus.RUNTIME_ERROR
    assert result.results[0].error_message == "ZeroDivisionError"


def test_python_stderr_capture_on_nonzero_exit():
    sandbox = ScriptedSandbox([SandboxResult(exit_code=2, stderr="custom stderr")])
    orchestrator, _, _, _ = build_orchestrator(plugin=PythonPlugin(), sandbox=sandbox)

    result = orchestrator.execute(
        execution_request("python", "import sys\nprint('x', file=sys.stderr)\nsys.exit(2)", ("", ""))
    )

    assert result.results[0].status == TestCaseStatus.RUNTIME_ERROR
    assert result.results[0].error_message == "custom stderr"


def test_python_multiple_executions():
    sandbox = ScriptedSandbox(
        [
            SandboxResult(exit_code=0, stdout="2"),
            SandboxResult(exit_code=0, stdout="4"),
        ]
    )
    orchestrator, _, _, _ = build_orchestrator(plugin=PythonPlugin(), sandbox=sandbox)

    result = orchestrator.execute(
        execution_request("python", "print(int(input()) * 2)", ("1", "2"), ("2", "4"))
    )

    assert result.passed_test_cases == 2
    assert sandbox.commands == [["python", "main.py"], ["python", "main.py"]]
    assert sandbox.stdins == ["1", "2"]


def test_c_prepare_compile_and_run_commands(tmp_path: Path):
    plugin = CPlugin()
    prepared = plugin.prepare("int main(void) { return 0; }", tmp_path)

    assert prepared.source_path == tmp_path / "main.c"
    assert prepared.artifact_path == tmp_path / "main"
    assert prepared.source_path.read_text(encoding="utf-8") == "int main(void) { return 0; }"
    assert plugin.compile_command(prepared) == [
        "gcc",
        "main.c",
        "-O2",
        "-std=c11",
        "-Wall",
        "-Wextra",
        "-o",
        "main",
    ]
    assert plugin.run_command(prepared) == ["./main"]


def test_c_program_with_input_and_stdout_capture():
    sandbox = ScriptedSandbox(
        [
            SandboxResult(exit_code=0),
            SandboxResult(exit_code=0, stdout="10\n"),
        ]
    )
    orchestrator, _, _, _ = build_orchestrator(plugin=CPlugin(), sandbox=sandbox)

    result = orchestrator.execute(
        execution_request(
            "c",
            '#include <stdio.h>\nint main(void){int n; scanf("%d", &n); printf("%d\\n", n*2);}',
            ("5", "10"),
        )
    )

    assert result.results[0].status == TestCaseStatus.PASSED
    assert sandbox.commands == [
        ["gcc", "main.c", "-O2", "-std=c11", "-Wall", "-Wextra", "-o", "main"],
        ["./main"],
    ]
    assert sandbox.stdins == ["", "5"]


def test_c_wrong_program_output():
    sandbox = ScriptedSandbox(
        [
            SandboxResult(exit_code=0),
            SandboxResult(exit_code=0, stdout="14"),
        ]
    )
    orchestrator, _, _, _ = build_orchestrator(plugin=CPlugin(), sandbox=sandbox)

    result = orchestrator.execute(
        execution_request("c", "int main(void) { return 0; }", ("7", "20"))
    )

    assert result.status == ExecutionStatus.COMPLETED
    assert result.results[0].status == TestCaseStatus.FAILED
    assert result.results[0].actual_output == "14"


def test_c_compilation_error_stops_before_run():
    sandbox = ScriptedSandbox([SandboxResult(exit_code=1, stderr="expected ';'")])
    orchestrator, _, _, _ = build_orchestrator(plugin=CPlugin(), sandbox=sandbox)

    result = orchestrator.execute(
        execution_request("c", "int main(void) {", ("", ""))
    )

    assert result.status == ExecutionStatus.COMPILATION_ERROR
    assert result.results == []
    assert result.error_message == "expected ';'"
    assert len(sandbox.commands) == 1


def test_c_runtime_error_uses_stderr():
    sandbox = ScriptedSandbox(
        [
            SandboxResult(exit_code=0),
            SandboxResult(exit_code=136, stderr="Floating point exception"),
        ]
    )
    orchestrator, _, _, _ = build_orchestrator(plugin=CPlugin(), sandbox=sandbox)

    result = orchestrator.execute(
        execution_request("c", "int main(void) { return 136; }", ("", ""))
    )

    assert result.results[0].status == TestCaseStatus.RUNTIME_ERROR
    assert result.results[0].error_message == "Floating point exception"


def test_c_stderr_capture_on_nonzero_exit():
    sandbox = ScriptedSandbox(
        [
            SandboxResult(exit_code=0),
            SandboxResult(exit_code=1, stderr="c stderr"),
        ]
    )
    orchestrator, _, _, _ = build_orchestrator(plugin=CPlugin(), sandbox=sandbox)

    result = orchestrator.execute(
        execution_request("c", "int main(void) { return 1; }", ("", ""))
    )

    assert result.results[0].status == TestCaseStatus.RUNTIME_ERROR
    assert result.results[0].error_message == "c stderr"


def test_c_timeout_is_propagated():
    sandbox = ScriptedSandbox(
        [
            SandboxResult(exit_code=0),
            SandboxResult(timed_out=True),
        ]
    )
    orchestrator, _, _, _ = build_orchestrator(plugin=CPlugin(), sandbox=sandbox)

    result = orchestrator.execute(
        execution_request("c", "int main(void) { for(;;){} }", ("", ""))
    )

    assert result.results[0].status == TestCaseStatus.TIME_LIMIT_EXCEEDED


def test_c_multiple_executions_compile_once():
    sandbox = ScriptedSandbox(
        [
            SandboxResult(exit_code=0),
            SandboxResult(exit_code=0, stdout="4"),
            SandboxResult(exit_code=0, stdout="10"),
        ]
    )
    orchestrator, _, _, _ = build_orchestrator(plugin=CPlugin(), sandbox=sandbox)

    result = orchestrator.execute(
        execution_request("c", "int main(void) { return 0; }", ("2", "4"), ("5", "10"))
    )

    assert result.passed_test_cases == 2
    assert sandbox.commands == [
        ["gcc", "main.c", "-O2", "-std=c11", "-Wall", "-Wextra", "-o", "main"],
        ["./main"],
        ["./main"],
    ]
