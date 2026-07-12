from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base.timestamp import TimestampMixin
from app.models.base.uuid import UUIDMixin


class Note(
    Base,
    UUIDMixin,
    TimestampMixin,
):
    __tablename__ = "notes"

    title: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    user_id = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    subject_id = mapped_column(
        ForeignKey("subjects.id"),
        nullable=False,
    )