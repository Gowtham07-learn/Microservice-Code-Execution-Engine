from pydantic import BaseModel

from app.core.models.enums import SecurityStatus


class SecurityResult(BaseModel):
    status: SecurityStatus
    reason: str | None = None
