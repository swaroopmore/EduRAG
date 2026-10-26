"""Per-subject BM25 indexes, cached in memory.

The cache key is ``(user_id, subject_id)`` and the cached value carries a
fingerprint of the chunk ids currently stored in Chroma, so the index is rebuilt
automatically when documents are added or removed (even by another process).
"""

from __future__ import annotations

import hashlib
import threading
from collections import OrderedDict

from langchain_core.documents import Document

from app.ai.keyword.bm25_index import BM25Index
from app.ai.vectorstore.chroma_service import ChromaService

_MAX_CACHED_INDEXES = 64


def _fingerprint(ids: list[str]) -> str:
    digest = hashlib.sha1("\n".join(sorted(ids)).encode()).hexdigest()
    return f"{len(ids)}:{digest}"


class BM25Service:
    def __init__(self, vectorstore: ChromaService):
        self.vectorstore = vectorstore
        self._cache: OrderedDict[tuple[str, str], tuple[str, BM25Index]] = OrderedDict()
        self._lock = threading.Lock()

    def _get_index(self, user_id, subject_id) -> BM25Index | None:
        key = (str(user_id), str(subject_id))
        ids = self.vectorstore.get_chunk_ids(user_id, subject_id)
        if not ids:
            with self._lock:
                self._cache.pop(key, None)
            return None

        fingerprint = _fingerprint(ids)
        with self._lock:
            cached = self._cache.get(key)
            if cached and cached[0] == fingerprint:
                self._cache.move_to_end(key)
                return cached[1]

        chunks = self.vectorstore.get_chunks(user_id, subject_id)
        index = BM25Index()
        index.build(chunks)
        with self._lock:
            self._cache[key] = (fingerprint, index)
            self._cache.move_to_end(key)
            while len(self._cache) > _MAX_CACHED_INDEXES:
                self._cache.popitem(last=False)
        return index

    def search(
        self,
        query: str,
        user_id,
        subject_id,
        k: int = 20,
        document_ids=None,
    ) -> list[tuple[Document, float]]:
        index = self._get_index(user_id, subject_id)
        if index is None:
            return []
        wanted = {str(d) for d in document_ids} if document_ids else None
        # Over-fetch when filtering by document so we still return k results.
        hits = index.search(query, k=k * 3 if wanted else k)
        if wanted:
            hits = [h for h in hits if h[0].metadata.get("document_id") in wanted]
        return hits[:k]

    def invalidate(self, user_id=None, subject_id=None) -> None:
        with self._lock:
            if user_id is None:
                self._cache.clear()
            else:
                self._cache.pop((str(user_id), str(subject_id)), None)
