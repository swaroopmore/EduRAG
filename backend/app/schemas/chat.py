from pydantic import BaseModel
from uuid import UUID


class ChatRequest(BaseModel):
    subject_id: UUID
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]