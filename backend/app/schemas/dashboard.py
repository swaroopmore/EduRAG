from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.document import DocumentResponse


class SubjectProgress(BaseModel):
    id: UUID
    name: str
    documents: int
    documents_ready: int
    notes: int
    flashcards: int
    flashcards_mastered: int
    quiz_questions: int
    quiz_attempts: int
    best_quiz_accuracy: int | None
    study_sessions: int
    study_sessions_completed: int
    # None until the learner has done something measurable in the subject.
    progress: int | None
    last_activity: datetime | None


class ActivityItem(BaseModel):
    type: str  # document | chat | quiz | notes | flashcards | quiz_generated | plan
    title: str
    subject_id: UUID
    subject_name: str
    at: datetime


class DashboardResponse(BaseModel):
    # Original fields (kept for backwards compatibility)
    subjects: int
    documents: int
    flashcards: int
    quizzes: int
    notes: int
    study_plans: int
    storage_used: float
    # Extended fields
    documents_ready: int = 0
    documents_in_progress: int = 0
    documents_failed: int = 0
    chat_messages: int = 0
    quiz_attempts: int = 0
    average_quiz_accuracy: int | None = None
    flashcards_mastered: int = 0
    study_sessions_completed: int = 0
    subject_progress: list[SubjectProgress] = []
    recent_documents: list[DocumentResponse] = []
    recent_activity: list[ActivityItem] = []
