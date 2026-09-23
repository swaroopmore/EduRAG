"""Document loaders.

Each loader turns a file into LangChain ``Document`` objects.  Metadata written
here is intentionally small: ``page`` (0-based index, ``None`` when the format
has no pages) and ``unit`` ("page" / "slide").  Server file paths are never put
in metadata.

To add a format (e.g. images via OCR) implement ``load`` and register it in
``factory.LOADERS`` - the rest of the pipeline is format-agnostic.
"""

from __future__ import annotations

from typing import Protocol

from langchain_core.documents import Document


class DocumentProcessingError(Exception):
    """A document could not be read.  ``str(error)`` is safe to show to users."""


class DocumentLoader(Protocol):
    def load(self, path: str) -> list[Document]: ...
