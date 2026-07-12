from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class StudyPlanResponse(BaseModel):

    id: UUID

    day: int

    time: str

    title: str

    description: str

    duration: str

    subject_id: UUID

    created_at: datetime

    class Config:

        from_attributes = True


class GenerateStudyPlanResponse(BaseModel):

    generated: int