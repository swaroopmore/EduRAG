"""Hybrid retrieval: dense vectors + BM25, fused with reciprocal-rank fusion.

Pipeline
    1. Chroma similarity search  (filtered by user_id + subject_id [+ documents])
    2. BM25 keyword search       (same tenant scope, cached per subject)
    3. Reciprocal-rank fusion    (robust to the two score scales differing)
    4. Optional cross-encoder rerank + relevance threshold
    5. De-duplication, top-k

Both retrievers are hard-scoped to the caller's user and subject, so a query can
never surface another user's chunks.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from langchain_core.documents import Document

from app.ai.keyword.bm25_service import BM25Service
from app.ai.reranker.reranker import get_reranker
from app.ai.vectorstore.chroma_service import ChromaService, get_vectorstore
from app.core.config import settings
from app.core.logging import get_logger, short_id, timed

logger = get_logger("retrieval")

RRF_K = 60


@dataclass
class RetrievalResult:
    documents: list[Document] = field(default_factory=list)
    method: str = "none"
    best_similarity: float | None = None
    keyword_hits: int = 0
    candidates: int = 0
    relevant: bool = False
    empty_index: bool = False


def _chunk_key(doc: Document) -> str:
    meta = doc.metadata or {}
    if doc.id:
        return str(doc.id)
    return f"{meta.get('document_id')}:{meta.get('page')}:{hash(doc.page_content)}"


def _dedupe_signature(doc: Document) -> str:
    return " ".join(doc.page_content.lower().split())[:160]


class HybridRetriever:
    def __init__(self, vectorstore: ChromaService | None = None):
        self.vectorstore = vectorstore or get_vectorstore()
        self.bm25 = BM25Service(self.vectorstore)

    def search(
        self,
        question: str,
        user_id,
        subject_id,
        k: int | None = None,
        document_ids=None,
    ) -> RetrievalResult:
        k = k or settings.RETRIEVAL_TOP_K
        pool = settings.RETRIEVAL_CANDIDATES

        with timed() as t:
            vector_hits = self.vectorstore.similarity_search(
                question, user_id, subject_id, k=pool, document_ids=document_ids
            )
            keyword_hits = self.bm25.search(
                question, user_id, subject_id, k=pool, document_ids=document_ids
            )

            result = RetrievalResult(
                keyword_hits=len(keyword_hits),
                best_similarity=vector_hits[0][1] if vector_hits else None,
            )

            if not vector_hits and not keyword_hits:
                result.empty_index = (
                    not self.vectorstore.get_chunk_ids(user_id, subject_id, document_ids)
                )
                self._log(user_id, subject_id, result, t["ms"])
                return result

            # -------- reciprocal rank fusion
            fused: dict[str, float] = {}
            by_key: dict[str, Document] = {}
            for rank, (doc, _sim) in enumerate(vector_hits, start=1):
                key = _chunk_key(doc)
                by_key[key] = doc
                fused[key] = fused.get(key, 0.0) + 1.0 / (RRF_K + rank)
            for rank, (doc, _score) in enumerate(keyword_hits, start=1):
                key = _chunk_key(doc)
                by_key.setdefault(key, doc)
                fused[key] = fused.get(key, 0.0) + 1.0 / (RRF_K + rank)

            ordered = [by_key[key] for key, _ in sorted(fused.items(), key=lambda kv: kv[1], reverse=True)]
            result.candidates = len(ordered)
            result.method = "hybrid" if vector_hits and keyword_hits else ("vector" if vector_hits else "keyword")

            # -------- optional cross-encoder rerank + relevance threshold
            reranker = get_reranker()
            if reranker is not None and ordered:
                scores = reranker.score(question, ordered)
                ranked = sorted(zip(ordered, scores), key=lambda x: x[1], reverse=True)
                kept = [doc for doc, score in ranked if score >= settings.RERANK_MIN_SCORE]
                result.relevant = bool(kept)
                ordered = kept
                result.method += "+rerank"
            else:
                result.relevant = bool(
                    keyword_hits
                    or (result.best_similarity or 0.0) >= settings.MIN_VECTOR_SIMILARITY
                )

            # -------- de-duplicate overlapping chunks, take top-k
            seen: set[str] = set()
            final: list[Document] = []
            for doc in ordered:
                signature = _dedupe_signature(doc)
                if signature in seen:
                    continue
                seen.add(signature)
                final.append(doc)
                if len(final) >= k:
                    break
            result.documents = final if result.relevant else []

        self._log(user_id, subject_id, result, t["ms"])
        return result

    def retrieve(self, question, user_id, subject_id, k: int | None = None, document_ids=None) -> list[Document]:
        """Convenience wrapper returning only the chunks."""
        return self.search(question, user_id, subject_id, k, document_ids).documents

    @staticmethod
    def _log(user_id, subject_id, result: RetrievalResult, ms: float) -> None:
        logger.info(
            "retrieve user=%s subject=%s method=%s returned=%d candidates=%d keyword_hits=%d best_sim=%s relevant=%s ms=%s",
            short_id(user_id),
            short_id(subject_id),
            result.method,
            len(result.documents),
            result.candidates,
            result.keyword_hits,
            None if result.best_similarity is None else round(result.best_similarity, 3),
            result.relevant,
            ms,
        )
