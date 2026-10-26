from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings


class ChunkingService:
    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        min_chars: int | None = None,
    ):
        self.min_chars = settings.MIN_CHUNK_CHARS if min_chars is None else min_chars
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size or settings.CHUNK_SIZE,
            chunk_overlap=chunk_overlap if chunk_overlap is not None else settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""],
        )

    def split(self, documents: list[Document]) -> list[Document]:
        """Split pages into overlapping chunks, dropping near-empty fragments."""
        chunks = self.splitter.split_documents(documents)
        return [c for c in chunks if len(c.page_content.strip()) >= self.min_chars]
