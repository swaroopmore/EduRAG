from langchain_core.documents import Document
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.ai.guardrails.sanitize import clean_text
from app.ai.loaders.base import DocumentProcessingError
from app.core.logging import get_logger

logger = get_logger("loader.pdf")


class PDFLoaderService:
    def load(self, path: str) -> list[Document]:
        try:
            reader = PdfReader(path)
            if reader.is_encrypted:
                try:
                    if not reader.decrypt(""):
                        raise DocumentProcessingError(
                            "This PDF is password protected. Remove the password and upload it again."
                        )
                except DocumentProcessingError:
                    raise
                except Exception as exc:  # unsupported encryption etc.
                    raise DocumentProcessingError(
                        "This PDF is encrypted and can't be read."
                    ) from exc
            pages = reader.pages
            total = len(pages)
        except DocumentProcessingError:
            raise
        except (PdfReadError, ValueError, OSError, KeyError, TypeError) as exc:
            logger.warning("PDF could not be opened: %s", exc)
            raise DocumentProcessingError(
                "We couldn't open this PDF. It may be corrupted."
            ) from exc

        documents: list[Document] = []
        for index in range(total):
            try:
                text = clean_text(pages[index].extract_text() or "")
            except Exception as exc:  # one bad page must not fail the document
                logger.warning("Page %s could not be extracted: %s", index + 1, exc)
                continue
            if text:
                documents.append(
                    Document(
                        page_content=text,
                        metadata={"page": index, "unit": "page", "total_pages": total},
                    )
                )
        return documents
