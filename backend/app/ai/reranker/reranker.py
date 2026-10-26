"""Optional cross-encoder reranking.

The model is loaded once.  If it cannot be loaded (offline, out of memory,
disabled) retrieval silently falls back to reciprocal-rank fusion.
"""

from __future__ import annotations

from functools import lru_cache

from langchain_core.documents import Document

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("reranker")


class Reranker:
    def __init__(self, model) -> None:
        self.model = model

    def score(self, question: str, documents: list[Document]) -> list[float]:
        if not documents:
            return []
        pairs = [(question, doc.page_content) for doc in documents]
        return [float(s) for s in self.model.predict(pairs)]


@lru_cache(maxsize=1)
def get_reranker() -> Reranker | None:
    if not settings.RERANKER_ENABLED:
        return None
    try:
        from sentence_transformers import CrossEncoder

        logger.info("Loading reranker %s", settings.RERANKER_MODEL)
        return Reranker(CrossEncoder(settings.RERANKER_MODEL))
    except Exception as exc:  # noqa: BLE001 - any load failure means "no reranker"
        logger.warning("Reranker unavailable, using rank fusion only: %s", exc)
        return None
