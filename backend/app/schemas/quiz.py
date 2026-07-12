from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class QuizResponse(BaseModel):

    id: UUID

    question: str

    option_a: str

    option_b: str

    option_c: str

    option_d: str

    correct_answer: str

    explanation: str

    subject_id: UUID

    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class GenerateQuizResponse(BaseModel):

    generated: int