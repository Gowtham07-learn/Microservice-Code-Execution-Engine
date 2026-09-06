from pydantic import BaseModel, Field

from app.core.models.enums import ExecutionStatus, TestCaseStatus


class TestCaseIn(BaseModel):
    __test__ = False
    input: str
    expected_output: str


class ExecutionRequestIn(BaseModel):
    language: str = Field(min_length=1)
    code: str = Field(min_length=1)
    test_cases: list[TestCaseIn] = Field(min_length=1)


class TestCaseResultOut(BaseModel):
    __test__ = False
    test_case: int
    status: TestCaseStatus
    actual_output: str = ""
    expected_output: str | None = None
    error_message: str | None = None


class ExecutionResponseOut(BaseModel):
    status: ExecutionStatus
    total_test_cases: int
    passed_test_cases: int
    failed_test_cases: int
    results: list[TestCaseResultOut]
    error_message: str | None = None


class LanguageOut(BaseModel):
    name: str
    version: str


class LanguagesResponseOut(BaseModel):
    languages: list[LanguageOut]


class HealthResponseOut(BaseModel):
    status: str
