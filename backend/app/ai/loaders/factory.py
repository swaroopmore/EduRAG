from app.ai.loaders.pdf_loader import PDFLoaderService
from app.ai.loaders.docx_loader import DOCXLoaderService
from app.ai.loaders.ppt_loader import PPTLoaderService


class DocumentLoaderFactory:

    @staticmethod
    def get_loader(file_type: str):

        file_type = file_type.lower()

        if file_type == "pdf":
            return PDFLoaderService()

        if file_type == "docx":
            return DOCXLoaderService()

        if file_type == "pptx":
            return PPTLoaderService()

        raise ValueError("Unsupported file type")