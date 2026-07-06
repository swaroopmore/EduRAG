from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base.timestamp import TimestampMixin
from app.models.base.uuid import UUIDMixin


class ChatHistory(UUIDMixin, TimestampMixin, Base):

    __tablename__ = "chat_history"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    subject_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id"),
        nullable=False,
        index=True,
    )

    question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    normalized_question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        index=True,
    )

    answer: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    citations: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )