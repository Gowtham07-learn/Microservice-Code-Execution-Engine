from app.core.exceptions import RequestValidationError, UnsupportedLanguageError
from app.core.models.enums import ExecutionStatus, SecurityStatus, TestCaseStatus
from app.core.models.request import ExecutionRequest, TestCase
from app.core.models.sandbox import SandboxResult
from app.core.models.security import SecurityResult
from app.core.services.validation import RequestValidator
from app.registry.in_memory import InMemoryPluginRegistry
from tests.conftest import build_orchestrator, request_python, settings
from tests.fakes import FakePlugin, FakeScanner, ScriptedSandbox


def test_valid_request_is_accepted():
    registry = InMemoryPluginRegistry()
    registry.register(FakePlugin())
    validator = RequestValidator(registry, settings())
    validator.validate(request_python(("2", "4")))


def test_invalid_request_empty_code():
    registry = InMemoryPluginRegistry()
    registry.register(FakePlugin())
    validator = RequestValidator(registry, settings())
    try:
        validator.validate(
            ExecutionRequest(language="python", code="   ", test_cases=[TestCase(input="1", expected_output="1")])
        )
        assert False, "expected RequestValidationError"
    except RequestValidationError as exc:
        assert any("source code" in item for item in exc.details)


def test_unsupported_language():
    registry = InMemoryPluginRegistry()
    registry.register(FakePlugin(name="python"))
    validator = RequestValidator(registry, settings())
    try:
        validator.validate(
            ExecutionRequest(
                language="java",
                code="class A {}",
                test_cases=[TestCase(input="1", expected_output="1")],
            )
        )
        assert False, "expected UnsupportedLanguageError"
    except UnsupportedLanguageError as exc:
        assert exc.language == "java"


def test_source_code_size_limit():
    registry = InMemoryPluginRegistry()
    registry.register(FakePlugin())
    validator = RequestValidator(registry, settings(max_code_bytes=8))
    try:
        validator.validate(
            ExecutionRequest(
                language="python",
                code="print('too-long')",
                test_cases=[TestCase(input="1", expected_output="1")],
            )
        )
        assert False, "expected RequestValidationError"
    except RequestValidationError as exc:
        assert any("exceeds" in item for item in exc.details)


def test_too_many_test_cases():
    registry = InMemoryPluginRegistry()
    registry.register(FakePlugin())
    validator = RequestValidator(registry, settings(max_test_cases=1))
    try:
        validator.validate(request_python(("1", "1"), ("2", "2")))
        assert False, "expected RequestValidationError"
    except RequestValidationError as exc:
        assert any("test_cases exceeds" in item for item in exc.details)


def test_plugin_lookup():
    registry = InMemoryPluginRegistry()
    plugin = FakePlugin(name="c", version="gcc")
    registry.register(plugin)
    found = registry.get("C")
    assert found is plugin
    assert registry.get("rust") is None


def test_security_violation_does_not_execute():
    scanner = FakeScanner(
        SecurityResult(status=SecurityStatus.SECURITY_VIOLATION, reason="os.system")
    )
    sandbox = ScriptedSandbox([SandboxResult(exit_code=0, stdout="4")])
    orchestrator, _, _, _ = build_orchestrator(scanner=scanner, sandbox=sandbox)
    result = orchestrator.execute(request_python(("2", "4")))
    assert result.status == ExecutionStatus.SECURITY_VIOLATION
    assert result.results == []
    assert sandbox.commands == []


def test_successful_execution():
    sandbox = ScriptedSandbox([SandboxResult(exit_code=0, stdout="4\n")])
    orchestrator, _, _, _ = build_orchestrator(sandbox=sandbox)
    result = orchestrator.execute(request_python(("2", "4")))
    assert result.status == ExecutionStatus.COMPLETED
    assert result.passed_test_cases == 1
    assert result.failed_test_cases == 0
    assert result.results[0].status == TestCaseStatus.PASSED
    assert result.results[0].actual_output == "4"


def test_wrong_output():
    sandbox = ScriptedSandbox([SandboxResult(exit_code=0, stdout="14")])
    orchestrator, _, _, _ = build_orchestrator(sandbox=sandbox)
    result = orchestrator.execute(request_python(("7", "20")))
    assert result.status == ExecutionStatus.COMPLETED
    assert result.results[0].status == TestCaseStatus.FAILED
    assert result.results[0].actual_output == "14"
    assert result.results[0].expected_output == "20"


def test_multiple_test_cases_aggregation():
    sandbox = ScriptedSandbox(
        [
            SandboxResult(exit_code=0, stdout="4"),
            SandboxResult(exit_code=0, stdout="10"),
            SandboxResult(exit_code=0, stdout="14"),
        ]
    )
    orchestrator, _, plugin, _ = build_orchestrator(sandbox=sandbox)
    result = orchestrator.execute(
        request_python(("2", "4"), ("5", "10"), ("7", "20"))
    )
    assert result.total_test_cases == 3
    assert result.passed_test_cases == 2
    assert result.failed_test_cases == 1
    assert [item.status for item in result.results] == [
        TestCaseStatus.PASSED,
        TestCaseStatus.PASSED,
        TestCaseStatus.FAILED,
    ]
    assert plugin.prepare_calls == 1
    assert sandbox.stdins == ["2", "5", "7"]


def test_compilation_error_compiles_once():
    sandbox = ScriptedSandbox(
        [SandboxResult(exit_code=1, stderr="error: expected ';'")]
    )
    orchestrator, _, plugin, _ = build_orchestrator(
        sandbox=sandbox, compile_argv=["gcc", "main.c"]
    )
    result = orchestrator.execute(
        ExecutionRequest(
            language="python",
            code="int main() {",
            test_cases=[
                TestCase(input="1", expected_output="1"),
                TestCase(input="2", expected_output="2"),
            ],
        )
    )
    assert result.status == ExecutionStatus.COMPILATION_ERROR
    assert result.results == []
    assert sandbox.commands == [["gcc", "main.c"]]
    assert plugin.compile_calls == 1


def test_runtime_error():
    sandbox = ScriptedSandbox(
        [SandboxResult(exit_code=1, stderr="ZeroDivisionError")]
    )
    orchestrator, _, _, _ = build_orchestrator(sandbox=sandbox)
    result = orchestrator.execute(request_python(("1", "1")))
    assert result.results[0].status == TestCaseStatus.RUNTIME_ERROR


def test_timeout():
    sandbox = ScriptedSandbox([SandboxResult(timed_out=True, stdout="")])
    orchestrator, _, _, _ = build_orchestrator(sandbox=sandbox)
    result = orchestrator.execute(request_python(("1", "1")))
    assert result.results[0].status == TestCaseStatus.TIME_LIMIT_EXCEEDED


def test_c_compile_once_then_run_each_test():
    sandbox = ScriptedSandbox(
        [
            SandboxResult(exit_code=0),
            SandboxResult(exit_code=0, stdout="4"),
            SandboxResult(exit_code=0, stdout="10"),
        ]
    )
    plugin = FakePlugin(name="c", version="gcc", compile_argv=["gcc", "-o", "a.out", "main.c"])
    orchestrator, _, plugin, _ = build_orchestrator(plugin=plugin, sandbox=sandbox)
    result = orchestrator.execute(
        ExecutionRequest(
            language="c",
            code="int main(){}",
            test_cases=[
                TestCase(input="2", expected_output="4"),
                TestCase(input="5", expected_output="10"),
            ],
        )
    )
    assert result.passed_test_cases == 2
    assert sandbox.commands[0] == ["gcc", "-o", "a.out", "main.c"]
    assert sandbox.commands[1:] == [["run"], ["run"]]
    assert plugin.compile_calls == 1
