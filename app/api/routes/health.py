from fastapi import APIRouter, Request

from app.api.schemas import HealthResponseOut

router = APIRouter()


@router.get("/health", response_model=HealthResponseOut)
async def health(request: Request) -> HealthResponseOut:
    return HealthResponseOut(status="healthy")
