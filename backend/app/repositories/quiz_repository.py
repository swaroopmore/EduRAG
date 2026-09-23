from uuid import UUID

from app.models.quiz import Quiz, QuizAttempt
from app.repositories.subject_resource_repository import SubjectResourceRepository


class QuizRepository(SubjectResourceRepository[Quiz]):
    model = Quiz
    order_by = (Quiz.created_at.asc(),)

    def create_attempt(self, attempt: QuizAttempt) -> QuizAttempt:
        self.db.add(attempt)
        self.db.commit()
        self.db.refresh(attempt)
        return attempt

    def list_attempts(self, user_id: UUID, subject_id: UUID, limit: int = 10) -> list[QuizAttempt]:
        return (
            self.db.query(QuizAttempt)
            .filter(QuizAttempt.user_id == user_id, QuizAttempt.subject_id == subject_id)
            .order_by(QuizAttempt.created_at.desc())
            .limit(limit)
            .all()
        )
