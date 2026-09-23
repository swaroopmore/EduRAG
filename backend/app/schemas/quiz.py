from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class QuizQuestionResponse(BaseModel):
    """Question as shown while taking the quiz - the answer is NOT included."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    question: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    subject_id: UUID
    created_at: datetime


class GenerateQuizResponse(BaseModel):
    generated: int


class QuizSubmission(BaseModel):
    # question id -> "A" | "B" | "C" | "D"
    answers: dict[UUID, Literal["A", "B", "C", "D"]] = Field(default_factory=dict)


class QuizQuestionResult(BaseModel):
    quiz_id: UUID
    question: str
    selected: str | None
    correct_answer: str
    is_correct: bool
    explanation: str
    options: dict[str, str]


class QuizAttemptResponse(BaseModel):
    id: UUID
    score: int
    total: int
    accuracy: int
    created_at: datetime
    results: list[QuizQuestionResult] = []


class QuizAttemptSummary(BaseModel):
    id: UUID
    score: int
    total: int
    accuracy: int
    created_at: datetime
