"""ChromaDB access with mandatory tenant filtering.

Every read is filtered by ``user_id`` AND ``subject_id`` (and optionally a set of
``document_id``).  There is deliberately no method that searches without those
filters, so a caller cannot accidentally retrieve another user's chunks.
"""

from __future__ import annotations

import threading
from functools import lru_cache
from typing import Iterable, Sequence

from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.ai.embeddings.embedding_service import get_embeddings
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("vectorstore")

_write_lock = threading.RLock()
_BATCH_SIZE = 64


def build_where(user_id, subject_id, document_ids: Iterable | None = None) -> dict:
    """Build the mandatory tenant filter.  Raises if an id is missing."""
    if not user_id or not subject_id:
        raise ValueError("user_id and subject_id are required for vector queries")

    clauses: list[dict] = [
        {"user_id": str(user_id)},
        {"subject_id": str(subject_id)},
    ]
    if document_ids:
        ids = sorted({str(d) for d in document_ids})
        clauses.append({"document_id": ids[0]} if len(ids) == 1 else {"document_id": {"$in": ids}})
    return {"$and": clauses}


class ChromaService:
    def __init__(
        self,
        embedding_function=None,
        persist_directory: str | None = None,
        collection_name: str | None = None,
    ):
        import chromadb

        self.db = Chroma(
            collection_name=collection_name or settings.CHROMA_COLLECTION,
            persist_directory=persist_directory or settings.VECTOR_DB_PATH,
            embedding_function=embedding_function or get_embeddings(),
            client_settings=chromadb.config.Settings(
                anonymized_telemetry=False, is_persistent=True
            ),
        )
        logger.info(
            "Chroma ready (collection=%s, path=%s, vectors=%s)",
            self.db._collection.name,
            persist_directory or settings.VECTOR_DB_PATH,
            self.count(),
        )

    @property
    def _collection(self):
        return self.db._collection

    # ------------------------------------------------------------------ write
    def add_chunks(self, chunks: Sequence[Document], ids: Sequence[str]) -> None:
        """Embed and store chunks (idempotent: same ids overwrite)."""
        with _write_lock:
            for start in range(0, len(chunks), _BATCH_SIZE):
                self.db.add_documents(
                    list(chunks[start : start + _BATCH_SIZE]),
                    ids=list(ids[start : start + _BATCH_SIZE]),
                )

    def delete_document(self, document_id) -> None:
        with _write_lock:
            self._collection.delete(where={"document_id": str(document_id)})

    def delete_subject(self, user_id, subject_id) -> None:
        with _write_lock:
            self._collection.delete(where=build_where(user_id, subject_id))

    # ------------------------------------------------------------------- read
    def similarity_search(
        self,
        query: str,
        user_id,
        subject_id,
        k: int = 20,
        document_ids: Iterable | None = None,
    ) -> list[tuple[Document, float]]:
        """Return ``(chunk, cosine_similarity)`` pairs, best first.

        Chroma returns squared-L2 distances; with unit-length embeddings
        ``similarity = 1 - distance / 2``.
        """
        where = build_where(user_id, subject_id, document_ids)
        results = self.db.similarity_search_with_score(query=query, k=k, filter=where)
        return [(doc, max(-1.0, min(1.0, 1.0 - dist / 2.0))) for doc, dist in results]

    def get_chunk_ids(self, user_id, subject_id, document_ids: Iterable | None = None) -> list[str]:
        where = build_where(user_id, subject_id, document_ids)
        return list(self._collection.get(where=where, include=[])["ids"])

    def get_chunks(self, user_id, subject_id, document_ids: Iterable | None = None) -> list[Document]:
        """All chunks of a subject in reading order (document, page, chunk)."""
        where = build_where(user_id, subject_id, document_ids)
        result = self._collection.get(where=where, include=["documents", "metadatas"])
        chunks = [
            Document(page_content=content or "", metadata=dict(meta or {}), id=chunk_id)
            for chunk_id, content, meta in zip(
                result["ids"], result["documents"], result["metadatas"]
            )
        ]
        chunks.sort(key=chunk_sort_key)
        return chunks

    def document_chunk_count(self, document_id) -> int:
        return len(self._collection.get(where={"document_id": str(document_id)}, include=[])["ids"])

    def count(self) -> int:
        try:
            return self._collection.count()
        except Exception:  # pragma: no cover - defensive
            return -1


def chunk_sort_key(doc: Document) -> tuple:
    meta = doc.metadata or {}
    return (
        str(meta.get("document_id", "")),
        meta.get("page") if isinstance(meta.get("page"), int) else -1,
        meta.get("chunk_index") if isinstance(meta.get("chunk_index"), int) else 0,
    )


@lru_cache(maxsize=1)
def get_vectorstore() -> ChromaService:
    return ChromaService()


def reset_vectorstore() -> None:
    """Drop the cached client (used by tests and after configuration changes)."""
    get_vectorstore.cache_clear()
