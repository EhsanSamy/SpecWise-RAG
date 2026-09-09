from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Human-readable project name.")
    description: str | None = Field(default=None, description="Optional short description.")


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    created_at: datetime
    document_count: int = 0
