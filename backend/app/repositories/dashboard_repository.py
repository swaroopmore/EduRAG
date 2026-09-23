"""Aggregate queries for the dashboard.

Everything is scoped by ``user_id`` and uses grouped queries, so the number of
round trips is constant regardless of how many subjects/documents a user has.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Float, case, cast, func
from sqlalchemy.orm import Session

from app.models.chat_history import ChatHistory
from app.models.document import Document, DocumentStatus
from app.models.flashcard import Flashcard
from app.models.note import Note
from app.models.quiz import Quiz, QuizAttempt
from app.models.study_plan import StudyPlan
from app.models.subject import Subject


class DashboardRepository:
    def __init__(self, db: Session):
        self.db = db

    # ---------------------------------------------------------------- totals
    def _count(self, model, *filters) -> int:
        return self.db.query(func.count()).select_from(model).filter(*filters).scalar() or 0

    def count_subjects(self, user_id: UUID) -> int:
        return self._count(Subject, Subject.user_id == user_id)

    def count_documents(self, user_id: UUID) -> int:
        return self._count(Document, Document.user_id == user_id)

    def document_status_counts(self, user_id: UUID) -> dict[str, int]:
        rows = (
            self.db.query(Document.status, func.count())
            .filter(Document.user_id == user_id)
            .group_by(Document.status)
            .all()
        )
        return {status: n for status, n in rows}

    def count_flashcards(self, user_id: UUID) -> int:
        return self._count(Flashcard, Flashcard.user_id == user_id)

    def count_mastered_flashcards(self, user_id: UUID) -> int:
        return self._count(Flashcard, Flashcard.user_id == user_id, Flashcard.mastered.is_(True))

    def count_quizzes(self, user_id: UUID) -> int:
        return self._count(Quiz, Quiz.user_id == user_id)

    def count_notes(self, user_id: UUID) -> int:
        return self._count(Note, Note.user_id == user_id)

    def count_study_plans(self, user_id: UUID) -> int:
        return self._count(StudyPlan, StudyPlan.user_id == user_id)

    def count_completed_sessions(self, user_id: UUID) -> int:
        return self._count(StudyPlan, StudyPlan.user_id == user_id, StudyPlan.completed.is_(True))

    def count_chat_messages(self, user_id: UUID) -> int:
        return self._count(ChatHistory, ChatHistory.user_id == user_id)

    def quiz_attempt_stats(self, user_id: UUID) -> tuple[int, int | None]:
        """(number of attempts, average accuracy in %)"""
        count, avg = (
            self.db.query(
                func.count(),
                func.avg(cast(QuizAttempt.score, Float) / func.nullif(QuizAttempt.total, 0)),
            )
            .filter(QuizAttempt.user_id == user_id)
            .one()
        )
        return count or 0, (round(avg * 100) if avg is not None else None)

    def storage_used(self, user_id: UUID) -> float:
        total = (
            self.db.query(func.sum(Document.file_size))
            .filter(Document.user_id == user_id)
            .scalar()
        )
        return round((total or 0) / (1024 * 1024), 2)

    # ------------------------------------------------------- per-subject data
    def _grouped(self, query) -> dict[UUID, int]:
        return {subject_id: n for subject_id, n in query.all()}

    def mastered_by_subject(self, user_id: UUID) -> dict[UUID, int]:
        return self._grouped(
            self.db.query(Flashcard.subject_id, func.count())
            .filter(Flashcard.user_id == user_id, Flashcard.mastered.is_(True))
            .group_by(Flashcard.subject_id)
        )

    def completed_sessions_by_subject(self, user_id: UUID) -> dict[UUID, int]:
        return self._grouped(
            self.db.query(StudyPlan.subject_id, func.count())
            .filter(StudyPlan.user_id == user_id, StudyPlan.completed.is_(True))
            .group_by(StudyPlan.subject_id)
        )

    def attempts_by_subject(self, user_id: UUID) -> dict[UUID, tuple[int, int]]:
        """subject -> (attempt count, best accuracy %)"""
        rows = (
            self.db.query(
                QuizAttempt.subject_id,
                func.count(),
                func.max(cast(QuizAttempt.score, Float) / func.nullif(QuizAttempt.total, 0)),
            )
            .filter(QuizAttempt.user_id == user_id)
            .group_by(QuizAttempt.subject_id)
            .all()
        )
        return {sid: (n, round((best or 0) * 100)) for sid, n, best in rows}

    def latest_by_subject(self, user_id: UUID) -> dict[UUID, datetime]:
        """Most recent activity timestamp per subject across all resources."""
        latest: dict[UUID, datetime] = {}
        for model in (Document, ChatHistory, QuizAttempt, Note, Flashcard, Quiz, StudyPlan):
            rows = (
                self.db.query(model.subject_id, func.max(model.created_at))
                .filter(model.user_id == user_id)
                .group_by(model.subject_id)
                .all()
            )
            for subject_id, at in rows:
                if at and (subject_id not in latest or at > latest[subject_id]):
                    latest[subject_id] = at
        return latest

    # -------------------------------------------------------------- activity
    def recent_documents(self, user_id: UUID, limit: int = 5):
        return (
            self.db.query(Document, Subject.name)
            .join(Subject, Subject.id == Document.subject_id)
            .filter(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
            .limit(limit)
            .all()
        )

    def recent_chats(self, user_id: UUID, limit: int = 5):
        return (
            self.db.query(ChatHistory.question, ChatHistory.subject_id, ChatHistory.created_at, Subject.name)
            .join(Subject, Subject.id == ChatHistory.subject_id)
            .filter(ChatHistory.user_id == user_id)
            .order_by(ChatHistory.created_at.desc())
            .limit(limit)
            .all()
        )

    def recent_attempts(self, user_id: UUID, limit: int = 5):
        return (
            self.db.query(
                QuizAttempt.score, QuizAttempt.total, QuizAttempt.subject_id, QuizAttempt.created_at, Subject.name
            )
            .join(Subject, Subject.id == QuizAttempt.subject_id)
            .filter(QuizAttempt.user_id == user_id)
            .order_by(QuizAttempt.created_at.desc())
            .limit(limit)
            .all()
        )

    def generated_resources(self, user_id: UUID):
        """(kind, subject_id, subject_name, count, latest_created_at) per subject/resource."""
        out = []
        for kind, model in (
            ("notes", Note),
            ("flashcards", Flashcard),
            ("quiz_generated", Quiz),
            ("plan", StudyPlan),
        ):
            rows = (
                self.db.query(model.subject_id, Subject.name, func.count(), func.max(model.created_at))
                .join(Subject, Subject.id == model.subject_id)
                .filter(model.user_id == user_id)
                .group_by(model.subject_id, Subject.name)
                .all()
            )
            out.extend((kind, sid, name, n, at) for sid, name, n, at in rows)
        return out
