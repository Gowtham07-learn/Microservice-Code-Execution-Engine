from fastapi import APIRouter, Request

from app.api.schemas import ExecutionRequestIn, ExecutionResponseOut
from app.core.models.request import ExecutionRequest, TestCase

router = APIRouter()


@router.post("/api/v1/executions", response_model=ExecutionResponseOut)
async def create_execution(payload: ExecutionRequestIn, request: Request) -> ExecutionResponseOut:
    domain_request = ExecutionRequest(
        language=payload.language.strip().lower(),
        code=payload.code,
        test_cases=[
            TestCase(input=case.input, expected_output=case.expected_output)
            for case in payload.test_cases
        ],
    )
    request.app.state.request_validator.validate(domain_request)
    result = await request.app.state.execution_service.submit(domain_request)
    return ExecutionResponseOut.model_validate(result.model_dump())
