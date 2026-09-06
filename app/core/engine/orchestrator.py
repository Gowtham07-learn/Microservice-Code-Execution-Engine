from pathlib import Path
import tempfile

from app.core.engine.aggregator import aggregate
from app.core.engine.evaluator import normalize_output
from app.core.exceptions import PluginValidationError, UnsupportedLanguageError
from app.core.interfaces.plugin_registry import PluginRegistry
from app.core.interfaces.sandbox_executor import SandboxExecutor
from app.core.interfaces.security_scanner import SecurityScanner
from app.core.models.enums import ExecutionStatus, SecurityStatus, TestCaseStatus
from app.core.models.request import ExecutionRequest, TestCase
from app.core.models.result import ExecutionResult, TestCaseResult
from app.core.models.sandbox import ExecutionConfig, SandboxResult


class ExecutionOrchestrator:
    """Language-agnostic execution lifecycle. Depends only on abstractions."""

    def __init__(
        self,
        plugin_registry: PluginRegistry,
        security_scanner: SecurityScanner,
        sandbox_executor: SandboxExecutor,
        execution_config: ExecutionConfig,
    ) -> None:
        self._registry = plugin_registry
        self._scanner = security_scanner
        self._sandbox = sandbox_executor
        self._config = execution_config

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        total = len(request.test_cases)
        plugin = self._registry.get(request.language)
        if plugin is None:
            raise UnsupportedLanguageError(request.language)

        security = self._scanner.scan(request.code, request.language)
        if security.status == SecurityStatus.SECURITY_VIOLATION:
            return ExecutionResult(
                status=ExecutionStatus.SECURITY_VIOLATION,
                total_test_cases=total,
                error_message=security.reason or "Dangerous code detected",
            )

        try:
            plugin.validate(request.code)
        except PluginValidationError as exc:
            return ExecutionResult(
                status=ExecutionStatus.COMPILATION_ERROR,
                total_test_cases=total,
                error_message=str(exc),
            )

        workspace_root = Path(tempfile.mkdtemp(prefix="code-engine-"))
        try:
            prepared = plugin.prepare(request.code, workspace_root)
            compile_cmd = plugin.compile_command(prepared)
            if compile_cmd:
                compiled = self._sandbox.execute(
                    compile_cmd, "", self._config, prepared.workspace
                )
                compile_failure = self._compilation_failure(compiled, total)
                if compile_failure is not None:
                    return compile_failure

            run_cmd = plugin.run_command(prepared)
            results: list[TestCaseResult] = []
            for index, test_case in enumerate(request.test_cases, start=1):
                sandbox_result = self._sandbox.execute(
                    run_cmd, test_case.input, self._config, prepared.workspace
                )
                results.append(self._evaluate_test_case(index, test_case, sandbox_result))
            return aggregate(results, total)
        except Exception as exc:  # noqa: BLE001 - convert unexpected failures
            return ExecutionResult(
                status=ExecutionStatus.SYSTEM_ERROR,
                total_test_cases=total,
                error_message=f"Execution infrastructure error: {exc}",
            )
        finally:
            self._cleanup_workspace(workspace_root)

    def _compilation_failure(
        self, compiled: SandboxResult, total: int
    ) -> ExecutionResult | None:
        if compiled.system_error:
            return ExecutionResult(
                status=ExecutionStatus.SYSTEM_ERROR,
                total_test_cases=total,
                error_message=compiled.error_message or "Sandbox failed during compilation",
            )
        if compiled.timed_out:
            return ExecutionResult(
                status=ExecutionStatus.TIME_LIMIT_EXCEEDED,
                total_test_cases=total,
                error_message="Compilation exceeded the time limit",
            )
        if compiled.exit_code not in (0, None):
            message = compiled.stderr.strip() or compiled.error_message or "Compilation failed"
            return ExecutionResult(
                status=ExecutionStatus.COMPILATION_ERROR,
                total_test_cases=total,
                error_message=message,
            )
        return None

    def _evaluate_test_case(
        self, index: int, test_case: TestCase, sandbox_result: SandboxResult
    ) -> TestCaseResult:
        expected = normalize_output(test_case.expected_output)
        actual = normalize_output(sandbox_result.stdout)

        if sandbox_result.system_error:
            return TestCaseResult(
                test_case=index,
                status=TestCaseStatus.SYSTEM_ERROR,
                actual_output=actual,
                expected_output=expected,
                error_message=sandbox_result.error_message or "Sandbox error",
            )
        if sandbox_result.timed_out:
            return TestCaseResult(
                test_case=index,
                status=TestCaseStatus.TIME_LIMIT_EXCEEDED,
                actual_output=actual,
                expected_output=expected,
                error_message="Execution exceeded the time limit",
            )
        if sandbox_result.exit_code not in (0, None):
            message = sandbox_result.stderr.strip() or sandbox_result.error_message
            return TestCaseResult(
                test_case=index,
                status=TestCaseStatus.RUNTIME_ERROR,
                actual_output=actual,
                expected_output=expected,
                error_message=message or "Program terminated with a non-zero exit code",
            )

        passed = actual == expected
        return TestCaseResult(
            test_case=index,
            status=TestCaseStatus.PASSED if passed else TestCaseStatus.FAILED,
            actual_output=actual,
            expected_output=expected,
        )

    def _cleanup_workspace(self, workspace: Path) -> None:
        import shutil

        shutil.rmtree(workspace, ignore_errors=True)
