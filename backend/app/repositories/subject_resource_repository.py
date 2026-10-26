"""Shared persistence logic for AI-generated, per-subject resources."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import ClassVar, Generic, TypeVar
from uuid import UUID

from sqlalchemy.orm import Session

T = TypeVar("T")


class SubjectResourceRepository(Generic[T]):
    model: ClassVar[type]
    order_by: ClassVar[tuple] = ()

    def __init__(self, db: Session):
        self.db = db

    def list_for_subject(self, user_id: UUID, subject_id: UUID) -> list[T]:
        return (
            self.db.query(self.model)
            .filter(self.model.user_id == user_id, self.model.subject_id == subject_id)
            .order_by(*self.order_by)
            .all()
        )

    def count_for_subject(self, user_id: UUID, subject_id: UUID) -> int:
        return (
            self.db.query(self.model)
            .filter(self.model.user_id == user_id, self.model.subject_id == subject_id)
            .count()
        )

    def get_owned(self, item_id: UUID, user_id: UUID) -> T | None:
        return (
            self.db.query(self.model)
            .filter(self.model.id == item_id, self.model.user_id == user_id)
            .first()
        )

    def replace_for_subject(self, user_id: UUID, subject_id: UUID, items: list[T]) -> int:
        """Atomically replace the stored resources of one subject.

        Delete + insert happen in ONE transaction: if the insert fails, the old
        resources are still there.  ``created_at`` is spread by a microsecond per
        item so ordering by creation time preserves the generated order.
        """
        base = datetime.now(timezone.utc)
        for offset, item in enumerate(items):
            item.created_at = base + timedelta(microseconds=offset)
        try:
            (
                self.db.query(self.model)
                .filter(self.model.user_id == user_id, self.model.subject_id == subject_id)
                .delete(synchronize_session=False)
            )
            self.db.add_all(items)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return len(items)

    def commit(self) -> None:
        self.db.commit()
