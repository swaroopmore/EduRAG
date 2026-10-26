from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base.timestamp import TimestampMixin
from app.models.base.uuid import UUIDMixin


class Note(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "notes"

    title: Mapped[str] = mapped_column(String, nullable=False)
    # Markdown-lite (headings, lists, **bold**, `code`, fenced code); rendered
    # client-side through an escaping renderer, never as raw HTML.
    content: Mapped[str] = mapped_column(Text, nullable=False)
    keywords: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    user_id = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_id = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True
    )
