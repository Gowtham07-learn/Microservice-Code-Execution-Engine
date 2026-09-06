from pydantic import BaseModel, Field


class TestCase(BaseModel):
    __test__ = False
    input: str
    expected_output: str


class ExecutionRequest(BaseModel):
    language: str = Field(min_length=1)
    code: str = Field(min_length=1)
    test_cases: list[TestCase] = Field(min_length=1)
