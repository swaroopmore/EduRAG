from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.core.config import settings
from app.schemas.citations import Citation


class ChatRequest(BaseModel):
    subject_id: UUID
    question: str = Field(min_length=1)
    document_id: UUID | None = None  # optionally scope the answer to one document
    regenerate: bool = False

    @field_validator("question")
    @classmethod
    def _validate_question(cls, value: str) -> str:
        value = value.replace("\x00", "").strip()
        if not value:
            raise ValueError("Please enter a question.")
        if len(value) > settings.MAX_QUESTION_CHARS:
            raise ValueError(
                f"Questions are limited to {settings.MAX_QUESTION_CHARS} characters."
            )
        return value


class ChatResponse(BaseModel):
    id: UUID | None = None
    answer: str
    citations: list[Citation] = []
    grounded: bool = True  # False when the documents did not contain the answer
    cached: bool = False


class ChatHistoryItem(BaseModel):
    id: UUID
    question: str
    answer: str
    citations: list[Citation] = []
    created_at: datetime

    model_config = {"from_attributes": True}
