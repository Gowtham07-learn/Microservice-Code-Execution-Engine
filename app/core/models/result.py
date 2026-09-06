from pydantic import BaseModel, Field

from app.core.models.enums import ExecutionStatus, TestCaseStatus


class TestCaseResult(BaseModel):
    __test__ = False
    test_case: int
    status: TestCaseStatus
    actual_output: str = ""
    expected_output: str | None = None
    error_message: str | None = None


class ExecutionResult(BaseModel):
    status: ExecutionStatus
    total_test_cases: int = 0
    passed_test_cases: int = 0
    failed_test_cases: int = 0
    results: list[TestCaseResult] = Field(default_factory=list)
    error_message: str | None = None
