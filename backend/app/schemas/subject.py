from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SubjectCreate(BaseModel):
    name: str
    description: str | None = None


class SubjectUpdate(BaseModel):
    name: str
    description: str | None = None


class SubjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime