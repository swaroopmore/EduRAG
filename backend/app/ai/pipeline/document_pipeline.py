"""Document -> chunks -> vectors.

The pipeline is a pure transformation (no database access); status tracking is
handled by ``IngestionService`` which calls the three stages in order.
"""

from __future__ import annotations

from langchain_core.documents import Document

from app.ai.chunking.chunker import ChunkingService
from app.ai.loaders.base import DocumentProcessingError
from app.ai.loaders.factory import DocumentLoaderFactory
from app.ai.vectorstore.chroma_service import ChromaService, get_vectorstore
from app.core.logging import get_logger

logger = get_logger("pipeline")

MIN_TOTAL_CHARS = 20


class DocumentPipeline:
    def __init__(self, vectorstore: ChromaService | None = None, chunker: ChunkingService | None = None):
        self._vectorstore = vectorstore
        self.chunker = chunker or ChunkingService()

    @property
    def vectorstore(self) -> ChromaService:
        return self._vectorstore or get_vectorstore()

    # ------------------------------------------------------------ stage 1
    def extract(self, path: str, file_type: str) -> list[Document]:
        pages = DocumentLoaderFactory.get_loader(file_type).load(path)
        if sum(len(p.page_content.strip()) for p in pages) < MIN_TOTAL_CHARS:
            raise DocumentProcessingError(
                "No readable text was found in this file. If it is a scanned document, "
                "run OCR on it first and upload the searchable version."
            )
        return pages

    # ------------------------------------------------------------ stage 2
    def build_chunks(self, pages: list[Document], document) -> tuple[list[Document], list[str]]:
        """Chunk pages and attach tenant metadata + deterministic ids."""
        raw_chunks = self.chunker.split(pages)
        if not raw_chunks:
            raise DocumentProcessingError("This document didn't contain enough text to index.")

        chunks: list[Document] = []
        ids: list[str] = []
        for index, chunk in enumerate(raw_chunks):
            source_meta = chunk.metadata or {}
            metadata = {
                "user_id": str(document.user_id),
                "subject_id": str(document.subject_id),
                "document_id": str(document.id),
                "filename": document.original_filename,
                "source": document.original_filename,  # never the server path
                "file_type": document.file_type,
                "chunk_index": index,
                "unit": source_meta.get("unit", "page"),
            }
            if isinstance(source_meta.get("page"), int):
                metadata["page"] = source_meta["page"]
            chunks.append(Document(page_content=chunk.page_content, metadata=metadata))
            ids.append(f"{document.id}:{index}")
        return chunks, ids

    # ------------------------------------------------------------ stage 3
    def index(self, chunks: list[Document], ids: list[str], document_id) -> None:
        # Remove stale chunks first so re-indexing never duplicates content.
        self.vectorstore.delete_document(document_id)
        self.vectorstore.add_chunks(chunks, ids)
