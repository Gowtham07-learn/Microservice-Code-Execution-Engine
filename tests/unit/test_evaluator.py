from app.core.engine.evaluator import normalize_output
from app.core.engine.aggregator import aggregate
from app.core.models.enums import ExecutionStatus, TestCaseStatus
from app.core.models.result import TestCaseResult


def test_normalize_trailing_newlines():
    assert normalize_output("4\n") == "4"
    assert normalize_output("4\r\n") == "4"
    assert normalize_output("hello\nworld\n") == "hello\nworld"


def test_result_aggregation_counts():
    results = [
        TestCaseResult(test_case=1, status=TestCaseStatus.PASSED, actual_output="1"),
        TestCaseResult(test_case=2, status=TestCaseStatus.FAILED, actual_output="2"),
        TestCaseResult(test_case=3, status=TestCaseStatus.RUNTIME_ERROR, actual_output=""),
    ]
    summary = aggregate(results, total_test_cases=3)
    assert summary.status == ExecutionStatus.COMPLETED
    assert summary.passed_test_cases == 1
    assert summary.failed_test_cases == 2
