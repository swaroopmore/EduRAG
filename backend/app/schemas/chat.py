from uuid import UUID

from pydantic import BaseModel

from app.schemas.citations import Citation


class ChatRequest(BaseModel):
    subject_id: UUID
    question: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]