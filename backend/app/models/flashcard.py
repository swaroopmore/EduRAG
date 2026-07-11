from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base.timestamp import TimestampMixin
from app.models.base.uuid import UUIDMixin


class Flashcard(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "flashcards"

    question: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    answer: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    user_id = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    subject_id = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="flashcards",
    )

    subject = relationship(
        "Subject",
        back_populates="flashcards",
    )