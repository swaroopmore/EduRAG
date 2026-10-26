from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base.timestamp import TimestampMixin
from app.models.base.uuid import UUIDMixin


class DocumentStatus:
    """Document lifecycle: UPLOADED -> PROCESSING -> INDEXING -> READY | FAILED."""

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    INDEXING = "indexing"
    READY = "ready"
    FAILED = "failed"

    IN_PROGRESS = (UPLOADED, PROCESSING, INDEXING)


class Document(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "documents"

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=DocumentStatus.UPLOADED, index=True
    )
    # Finer-grained progress inside a status: extracting | chunking | embedding | storing
    stage: Mapped[str | None] = mapped_column(String(30), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user_id = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject_id = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    subject = relationship("Subject", back_populates="documents")
