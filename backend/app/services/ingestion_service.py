"""Background document processing with a visible lifecycle.

UPLOADED -> PROCESSING(extracting, chunking) -> INDEXING(embedding) -> READY | FAILED

Jobs run on a small thread pool so uploads return immediately and embedding a big
PDF can't starve the API.  ``recover_documents`` runs at start-up to make restarts
predictable: interrupted jobs are re-queued and documents whose vectors vanished
(ephemeral disk) are re-indexed from the stored file or marked FAILED with an
explanation - never silently lost.
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from uuid import UUID

from app.ai.loaders.base import DocumentProcessingError
from app.ai.pipeline.document_pipeline import DocumentPipeline
from app.ai.vectorstore.chroma_service import get_vectorstore
from app.core.config import settings
from app.core.logging import get_logger, short_id, timed
from app.database.session import session_scope
from app.models.document import Document, DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.services.storage_service import StorageService

logger = get_logger("ingestion")

LOST_FILE_MESSAGE = (
    "The original file is no longer available on the server, so this document can't be "
    "re-indexed. Please upload it again."
)


class IngestionQueue:
    def __init__(self) -> None:
        self._executor: ThreadPoolExecutor | None = None
        self._lock = threading.Lock()

    def submit(self, document_id: UUID) -> None:
        with self._lock:
            if self._executor is None:
                self._executor = ThreadPoolExecutor(
                    max_workers=max(1, settings.INGESTION_WORKERS),
                    thread_name_prefix="ingest",
                )
            self._executor.submit(process_document, document_id)

    def shutdown(self) -> None:
        with self._lock:
            if self._executor is not None:
                self._executor.shutdown(wait=False, cancel_futures=True)
                self._executor = None


ingestion_queue = IngestionQueue()


def _set_state(repo: DocumentRepository, document: Document, status: str, stage: str | None) -> None:
    document.status = status
    document.stage = stage
    repo.commit()


def process_document(document_id: UUID, pipeline: DocumentPipeline | None = None) -> None:
    """Extract, chunk, embed and index one document, tracking status as it goes."""
    pipeline = pipeline or DocumentPipeline()
    storage = StorageService()

    with session_scope() as db:
        repo = DocumentRepository(db)
        document = repo.get(document_id)
        if document is None:
            logger.warning("document %s vanished before processing", short_id(document_id))
            return

        user_id, subject_id = document.user_id, document.subject_id
        with timed() as t:
            try:
                path = storage.resolve(document)
                if path is None:
                    raise DocumentProcessingError(LOST_FILE_MESSAGE)

                document.error_message = None
                _set_state(repo, document, DocumentStatus.PROCESSING, "extracting")
                pages = pipeline.extract(str(path), document.file_type)
                document.page_count = len(pages) if document.file_type in ("pdf", "pptx") else None

                _set_state(repo, document, DocumentStatus.PROCESSING, "chunking")
                chunks, ids = pipeline.build_chunks(pages, document)

                _set_state(repo, document, DocumentStatus.INDEXING, "embedding")
                pipeline.index(chunks, ids, document.id)

                document.chunk_count = len(chunks)
                document.processed_at = datetime.now(timezone.utc)
                _set_state(repo, document, DocumentStatus.READY, None)
                outcome = f"ready chunks={len(chunks)}"
            except DocumentProcessingError as exc:
                _fail(repo, document, str(exc), pipeline)
                outcome = "failed (user-facing)"
            except Exception:  # noqa: BLE001 - never let a worker thread die silently
                logger.exception("document processing crashed (document=%s)", short_id(document_id))
                _fail(
                    repo,
                    document,
                    "Something went wrong while processing this document. Try re-indexing it, "
                    "or upload it again.",
                    pipeline,
                )
                outcome = "failed (unexpected)"

        logger.info(
            "ingest document=%s user=%s subject=%s type=%s %s ms=%s",
            short_id(document_id), short_id(user_id), short_id(subject_id),
            document.file_type, outcome, t["ms"],
        )


def _fail(repo: DocumentRepository, document: Document, message: str, pipeline: DocumentPipeline) -> None:
    try:
        pipeline.vectorstore.delete_document(document.id)  # don't leave partial chunks behind
    except Exception:  # noqa: BLE001
        logger.warning("could not clean partial vectors for %s", short_id(document.id))
    document.error_message = message
    document.chunk_count = None
    _set_state(repo, document, DocumentStatus.FAILED, None)


def recover_documents() -> dict[str, int]:
    """Reconcile the database with the vector store after a (re)start."""
    stats = {"requeued": 0, "reindexed": 0, "failed": 0}
    storage = StorageService()
    try:
        vectorstore = get_vectorstore()
    except Exception:  # noqa: BLE001
        logger.exception("vector store unavailable - skipping recovery")
        return stats

    with session_scope() as db:
        repo = DocumentRepository(db)

        for document in repo.list_with_status(*DocumentStatus.IN_PROGRESS):
            if storage.resolve(document):
                _set_state(repo, document, DocumentStatus.UPLOADED, None)
                ingestion_queue.submit(document.id)
                stats["requeued"] += 1
            else:
                document.error_message = "Processing was interrupted by a restart. " + LOST_FILE_MESSAGE
                _set_state(repo, document, DocumentStatus.FAILED, None)
                stats["failed"] += 1

        for document in repo.list_with_status(DocumentStatus.READY):
            try:
                present = vectorstore.document_chunk_count(document.id) > 0
            except Exception:  # noqa: BLE001
                logger.exception("could not verify index for %s", short_id(document.id))
                continue
            if present:
                continue
            if storage.resolve(document):
                logger.warning("index for document %s was lost - re-indexing", short_id(document.id))
                _set_state(repo, document, DocumentStatus.UPLOADED, None)
                ingestion_queue.submit(document.id)
                stats["reindexed"] += 1
            else:
                logger.warning("index AND file lost for document %s", short_id(document.id))
                document.error_message = (
                    "This document's search index was lost when the server restarted. " + LOST_FILE_MESSAGE
                )
                document.chunk_count = None
                _set_state(repo, document, DocumentStatus.FAILED, None)
                stats["failed"] += 1

    logger.info("recovery finished: %s", stats)
    return stats
