"""Process-wide retriever accessor (models and indexes are shared, data is not)."""

from __future__ import annotations

from functools import lru_cache

from app.ai.retrieval.hybrid_retriever import HybridRetriever, RetrievalResult

__all__ = ["Retriever", "get_retriever", "reset_retriever", "RetrievalResult"]

# ``Retriever`` was the public name in the original code base.
Retriever = HybridRetriever


@lru_cache(maxsize=1)
def get_retriever() -> HybridRetriever:
    return HybridRetriever()


def reset_retriever() -> None:
    get_retriever.cache_clear()
