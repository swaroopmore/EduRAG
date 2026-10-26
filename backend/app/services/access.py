"""Server-side ownership checks.

Ids arriving from the browser (subject_id, document_id, ...) are never trusted:
every route resolves them through these helpers, which only return objects that
belong to the authenticated user.  Unknown *and* foreign ids both produce the same
404, so ids of other users can't be probed.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import DocumentsNotReadyError, NoContentError, NotFoundError
from app.models.document import Document, DocumentStatus
from app.models.subject import Subject
from app.repositories.document_repository import DocumentRepository
from app.repositories.subject_repository import SubjectRepository


def require_subject(db: Session, user_id: UUID, subject_id: UUID) -> Subject:
    subject = SubjectRepository(db).get_owned(subject_id, user_id)
    if subject is None:
        raise NotFoundError("Subject not found.", code="subject_not_found")
    return subject


def require_document(db: Session, user_id: UUID, document_id: UUID) -> Document:
    document = DocumentRepository(db).get_owned(document_id, user_id)
    if document is None:
        raise NotFoundError("Document not found.", code="document_not_found")
    return document


def require_ready_documents(
    db: Session, user_id: UUID, subject_id: UUID, document_id: UUID | None = None
) -> list[UUID]:
    """Return the ids of READY documents to search, or raise a friendly error."""
    repo = DocumentRepository(db)

    if document_id is not None:
        document = require_document(db, user_id, document_id)
        if document.subject_id != subject_id:
            raise NotFoundError("Document not found.", code="document_not_found")
        if document.status in DocumentStatus.IN_PROGRESS:
            raise DocumentsNotReadyError()
        if document.status != DocumentStatus.READY:
            raise NoContentError(
                "This document couldn't be processed. Remove it or try re-indexing it."
            )
        return [document.id]

    counts = repo.status_counts(subject_id, user_id)
    if not counts:
        raise NoContentError("Upload a document to this subject first.")
    if counts.get(DocumentStatus.READY, 0) == 0:
        if any(counts.get(s, 0) for s in DocumentStatus.IN_PROGRESS):
            raise DocumentsNotReadyError()
        raise NoContentError(
            "None of your documents could be processed. Check the Documents page for details."
        )
    return repo.ready_ids(subject_id, user_id)
