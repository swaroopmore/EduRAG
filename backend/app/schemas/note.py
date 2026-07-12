from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class NoteResponse(BaseModel):

    id: UUID

    title: str

    content: str

    subject_id: UUID

    created_at: datetime

    class Config:

        from_attributes = True


class GenerateNotesResponse(BaseModel):

    generated: int