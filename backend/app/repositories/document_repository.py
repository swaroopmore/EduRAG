from datetime import datetime
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentStatus
from app.models.subject import Subject


class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, document: Document) -> Document:
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def get(self, document_id: UUID) -> Document | None:
        return self.db.get(Document, document_id)

    def get_owned(self, document_id: UUID, user_id: UUID) -> Document | None:
        return (
            self.db.query(Document)
            .filter(Document.id == document_id, Document.user_id == user_id)
            .first()
        )

    def _with_subject_name(self, query):
        return query.join(Subject, Subject.id == Document.subject_id).add_columns(Subject.name)

    @staticmethod
    def _attach_names(rows) -> list[Document]:
        documents = []
        for document, subject_name in rows:
            document.subject_name = subject_name  # transient attribute for the response model
            documents.append(document)
        return documents

    def list_by_subject(self, subject_id: UUID, user_id: UUID) -> list[Document]:
        rows = (
            self._with_subject_name(self.db.query(Document))
            .filter(Document.subject_id == subject_id, Document.user_id == user_id)
            .order_by(Document.created_at.desc())
            .all()
        )
        return self._attach_names(rows)

    def list_all(self, user_id: UUID, limit: int | None = None) -> list[Document]:
        query = (
            self._with_subject_name(self.db.query(Document))
            .filter(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
        )
        if limit:
            query = query.limit(limit)
        return self._attach_names(query.all())

    def list_with_status(self, *statuses: str) -> list[Document]:
        return self.db.query(Document).filter(Document.status.in_(statuses)).all()

    def status_counts(self, subject_id: UUID, user_id: UUID) -> dict[str, int]:
        rows = (
            self.db.query(Document.status, func.count())
            .filter(Document.subject_id == subject_id, Document.user_id == user_id)
            .group_by(Document.status)
            .all()
        )
        return {status: n for status, n in rows}

    def ready_ids(self, subject_id: UUID, user_id: UUID) -> list[UUID]:
        return [
            row[0]
            for row in self.db.query(Document.id)
            .filter(
                Document.subject_id == subject_id,
                Document.user_id == user_id,
                Document.status == DocumentStatus.READY,
            )
            .all()
        ]

    def last_change(self, subject_id: UUID, user_id: UUID) -> datetime | None:
        return (
            self.db.query(func.max(Document.updated_at))
            .filter(Document.subject_id == subject_id, Document.user_id == user_id)
            .scalar()
        )

    def paths_for_subject(self, subject_id: UUID, user_id: UUID) -> list[Document]:
        return (
            self.db.query(Document)
            .filter(Document.subject_id == subject_id, Document.user_id == user_id)
            .all()
        )

    def commit(self) -> None:
        self.db.commit()

    def delete(self, document: Document) -> None:
        self.db.delete(document)
        self.db.commit()
