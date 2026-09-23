from app.ai.loaders.base import DocumentLoader
from app.ai.loaders.docx_loader import DOCXLoaderService
from app.ai.loaders.pdf_loader import PDFLoaderService
from app.ai.loaders.ppt_loader import PPTLoaderService
from app.ai.loaders.txt_loader import TextLoaderService

# extension -> loader class.  Add "png"/"jpg" here once an OCR loader exists.
LOADERS: dict[str, type] = {
    "pdf": PDFLoaderService,
    "txt": TextLoaderService,
    "docx": DOCXLoaderService,
    "pptx": PPTLoaderService,
}


class DocumentLoaderFactory:
    @staticmethod
    def supported_types() -> set[str]:
        return set(LOADERS)

    @staticmethod
    def get_loader(file_type: str) -> DocumentLoader:
        loader = LOADERS.get(file_type.lower().lstrip("."))
        if loader is None:
            raise ValueError(f"Unsupported file type: {file_type}")
        return loader()
