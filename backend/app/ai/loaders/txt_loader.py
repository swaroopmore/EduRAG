from langchain_core.documents import Document

from app.ai.guardrails.sanitize import clean_text
from app.ai.loaders.base import DocumentProcessingError


class TextLoaderService:
    def load(self, path: str) -> list[Document]:
        with open(path, "rb") as handle:
            raw = handle.read()
        for encoding in ("utf-8-sig", "utf-16", "latin-1"):
            try:
                text = raw.decode(encoding)
                break
            except UnicodeError:
                continue
        else:  # pragma: no cover - latin-1 never fails
            raise DocumentProcessingError("This text file uses an unsupported encoding.")
        text = clean_text(text)
        if not text:
            return []
        return [Document(page_content=text, metadata={"unit": "page"})]
