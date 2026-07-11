from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class FlashcardResponse(BaseModel):
    id: UUID
    question: str
    answer: str
    subject_id: UUID
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class GenerateFlashcardsResponse(BaseModel):
    generated: int