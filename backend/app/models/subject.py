from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base.timestamp import TimestampMixin
from app.models.base.uuid import UUIDMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Subject(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "subjects"

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        String(500),
        nullable=True,
    )

    user_id = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    user = relationship("User", back_populates="subjects")
    documents = relationship(
    "Document",
    back_populates="subject",
    cascade="all, delete-orphan",
)


    flashcards = relationship(
    "Flashcard",
    back_populates="subject",
    cascade="all, delete-orphan",
)