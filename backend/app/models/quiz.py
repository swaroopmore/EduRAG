from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base.timestamp import TimestampMixin
from app.models.base.uuid import UUIDMixin


class Quiz(
    Base,
    UUIDMixin,
    TimestampMixin,
):
    __tablename__ = "quizzes"

    question: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    option_a: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    option_b: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    option_c: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    option_d: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    correct_answer: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    explanation: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    subject_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "subjects.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )