from pathlib import Path
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.ai.vectorstore.chroma_service import get_vectorstore
from app.core.errors import AppError, ConflictError
from app.core.logging import get_logger, short_id
from app.models.document import Document, DocumentStatus
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.services.access import require_document, require_subject
from app.services.ingestion_service import LOST_FILE_MESSAGE, ingestion_queue
from app.services.storage_service import StorageService

logger = get_logger("documents")


class DocumentService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = DocumentRepository(db)
        self.storage = StorageService()

    async def upload(self, file: UploadFile, subject_id: UUID, user: User) -> Document:
        subject = require_subject(self.db, user.id, subject_id)  # ownership first

        stored = await self.storage.save_upload(file)
        document = Document(
            filename=stored.filename,
            original_filename=stored.original_filename,
            file_type=stored.file_type,
            file_size=stored.size,
            file_path=stored.path,
            subject_id=subject.id,
            user_id=user.id,
            status=DocumentStatus.UPLOADED,
        )
        try:
            document = self.repository.create(document)
        except Exception:
            self.db.rollback()
            Path(stored.path).unlink(missing_ok=True)
            raise

        ingestion_queue.submit(document.id)
        document.subject_name = subject.name
        logger.info(
            "upload user=%s subject=%s document=%s type=%s bytes=%d",
            short_id(user.id), short_id(subject.id), short_id(document.id), stored.file_type, stored.size,
        )
        return document

    def list_for_subject(self, user_id: UUID, subject_id: UUID) -> list[Document]:
        require_subject(self.db, user_id, subject_id)
        return self.repository.list_by_subject(subject_id, user_id)

    def list_all(self, user_id: UUID) -> list[Document]:
        return self.repository.list_all(user_id)

    def get(self, user_id: UUID, document_id: UUID) -> Document:
        document = require_document(self.db, user_id, document_id)
        document.subject_name = require_subject(self.db, user_id, document.subject_id).name
        return document

    def delete(self, user_id: UUID, document_id: UUID) -> None:
        document = require_document(self.db, user_id, document_id)
        try:
            # Remove vectors first: if this fails we keep the row so nothing is orphaned.
            get_vectorstore().delete_document(document.id)
        except Exception as exc:  # noqa: BLE001
            logger.exception("vector delete failed for document %s", short_id(document.id))
            raise AppError(
                "We couldn't remove this document right now. Please try again.", code="delete_failed"
            ) from exc
        self.storage.delete(document)
        self.repository.delete(document)
        logger.info("deleted document=%s user=%s", short_id(document_id), short_id(user_id))

    def reindex(self, user_id: UUID, document_id: UUID) -> Document:
        document = require_document(self.db, user_id, document_id)
        if document.status in (DocumentStatus.PROCESSING, DocumentStatus.INDEXING, DocumentStatus.UPLOADED):
            raise ConflictError("This document is already being processed.")
        if self.storage.resolve(document) is None:
            raise ConflictError(LOST_FILE_MESSAGE, code="file_missing")
        document.status = DocumentStatus.UPLOADED
        document.stage = None
        document.error_message = None
        self.repository.commit()
        ingestion_queue.submit(document.id)
        document.subject_name = require_subject(self.db, user_id, document.subject_id).name
        return document

    def file_path(self, user_id: UUID, document_id: UUID) -> tuple[Path, Document]:
        document = require_document(self.db, user_id, document_id)
        path = self.storage.resolve(document)
        if path is None:
            raise ConflictError(LOST_FILE_MESSAGE, code="file_missing")
        return path, document
