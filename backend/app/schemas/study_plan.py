from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class StudyPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    day: int
    time: str
    title: str
    description: str
    duration: str
    quote: str | None = None
    completed: bool = False
    subject_id: UUID
    created_at: datetime


class StudyPlanUpdate(BaseModel):
    completed: bool


class GenerateStudyPlanResponse(BaseModel):
    generated: int
