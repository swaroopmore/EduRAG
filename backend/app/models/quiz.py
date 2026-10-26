import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base.timestamp import TimestampMixin
from app.models.base.uuid import UUIDMixin


class Quiz(UUIDMixin, TimestampMixin, Base):
    """A single multiple-choice question."""

    __tablename__ = "quizzes"

    question: Mapped[str] = mapped_column(String, nullable=False)
    option_a: Mapped[str] = mapped_column(String, nullable=False)
    option_b: Mapped[str] = mapped_column(String, nullable=False)
    option_c: Mapped[str] = mapped_column(String, nullable=False)
    option_d: Mapped[str] = mapped_column(String, nullable=False)
    correct_answer: Mapped[str] = mapped_column(String, nullable=False)
    explanation: Mapped[str] = mapped_column(String, nullable=False)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True
    )


class QuizAttempt(UUIDMixin, TimestampMixin, Base):
    """A graded quiz submission (server-side graded)."""

    __tablename__ = "quiz_attempts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    total: Mapped[int] = mapped_column(Integer, nullable=False)
    answers: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
