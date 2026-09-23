from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class NoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    content: str
    keywords: list[str] = []
    subject_id: UUID
    created_at: datetime

    @field_validator("keywords", mode="before")
    @classmethod
    def _none_to_list(cls, value):
        return value or []


class GenerateNotesResponse(BaseModel):
    generated: int
