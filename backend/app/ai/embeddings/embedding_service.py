"""Embedding model access.

The sentence-transformers model is heavy (hundreds of MB, seconds to load), so
it is created once per process and shared.  It holds no user data, so sharing
is safe.
"""

from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("embeddings")


@lru_cache(maxsize=1)
def get_embeddings():
    # Imported lazily so importing the app (and running tests) doesn't require torch.
    from langchain_huggingface import HuggingFaceEmbeddings

    logger.info("Loading embedding model %s", settings.EMBEDDING_MODEL)
    return HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)


class EmbeddingService:
    """Compatibility wrapper around the shared embedding model."""

    def get(self):
        return get_embeddings()
