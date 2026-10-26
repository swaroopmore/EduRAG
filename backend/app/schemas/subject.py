from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class _SubjectFields(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)

    @field_validator("name")
    @classmethod
    def _clean_name(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("Subject name cannot be empty.")
        return value

    @field_validator("description")
    @classmethod
    def _clean_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class SubjectCreate(_SubjectFields):
    pass


class SubjectUpdate(_SubjectFields):
    pass


class SubjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    # Real counts, filled by the repository (defaults keep create/update simple).
    document_count: int = 0
    ready_document_count: int = 0
    note_count: int = 0
    flashcard_count: int = 0
    quiz_question_count: int = 0
    study_session_count: int = 0
