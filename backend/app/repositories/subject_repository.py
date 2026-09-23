from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentStatus
from app.models.flashcard import Flashcard
from app.models.note import Note
from app.models.quiz import Quiz
from app.models.study_plan import StudyPlan
from app.models.subject import Subject
from app.repositories.base_repository import BaseRepository


class SubjectRepository(BaseRepository[Subject]):
    def __init__(self, db: Session):
        super().__init__(Subject, db)

    def get_owned(self, subject_id: UUID, user_id: UUID) -> Subject | None:
        return (
            self.db.query(Subject)
            .filter(Subject.id == subject_id, Subject.user_id == user_id)
            .first()
        )

    def get_by_user(self, user_id: UUID) -> list[Subject]:
        return (
            self.db.query(Subject)
            .filter(Subject.user_id == user_id)
            .order_by(Subject.created_at.desc())
            .all()
        )

    def name_exists(self, user_id: UUID, name: str, exclude_id: UUID | None = None) -> bool:
        query = self.db.query(Subject.id).filter(
            Subject.user_id == user_id, func.lower(Subject.name) == name.lower()
        )
        if exclude_id:
            query = query.filter(Subject.id != exclude_id)
        return query.first() is not None

    def counts_by_subject(self, user_id: UUID) -> dict[UUID, dict[str, int]]:
        """Resource counts for every subject of a user in 5 grouped queries."""
        counts: dict[UUID, dict[str, int]] = {}

        def add(model, key: str, *filters) -> None:
            rows = (
                self.db.query(model.subject_id, func.count())
                .filter(model.user_id == user_id, *filters)
                .group_by(model.subject_id)
                .all()
            )
            for subject_id, n in rows:
                counts.setdefault(subject_id, {})[key] = n

        add(Document, "documents")
        add(Document, "documents_ready", Document.status == DocumentStatus.READY)
        add(Note, "notes")
        add(Flashcard, "flashcards")
        add(Quiz, "quiz_questions")
        add(StudyPlan, "study_sessions")
        return counts
