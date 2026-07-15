from pydantic import BaseModel


class DashboardResponse(BaseModel):

    subjects: int

    documents: int

    flashcards: int

    quizzes: int

    notes: int

    study_plans: int

    storage_used: float