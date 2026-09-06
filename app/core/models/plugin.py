from pathlib import Path

from pydantic import BaseModel, Field


class PreparedProgram(BaseModel):
    """Language-independent artifact produced by a plugin before sandbox runs."""

    model_config = {"arbitrary_types_allowed": True}

    workspace: Path
    source_path: Path
    artifact_path: Path | None = None
    metadata: dict = Field(default_factory=dict)
