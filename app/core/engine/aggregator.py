from app.core.models.enums import ExecutionStatus, TestCaseStatus
from app.core.models.result import ExecutionResult, TestCaseResult


def aggregate(
    test_results: list[TestCaseResult],
    total_test_cases: int,
    overall_status: ExecutionStatus = ExecutionStatus.COMPLETED,
    error_message: str | None = None,
) -> ExecutionResult:
    passed = sum(1 for item in test_results if item.status == TestCaseStatus.PASSED)
    failed = sum(1 for item in test_results if item.status != TestCaseStatus.PASSED)
    return ExecutionResult(
        status=overall_status,
        total_test_cases=total_test_cases,
        passed_test_cases=passed,
        failed_test_cases=failed,
        results=test_results,
        error_message=error_message,
    )
