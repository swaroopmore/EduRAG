from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FlashcardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    question: str
    answer: str
    mastered: bool = False
    subject_id: UUID
    created_at: datetime


class FlashcardUpdate(BaseModel):
    mastered: bool


class GenerateFlashcardsResponse(BaseModel):
    generated: int
