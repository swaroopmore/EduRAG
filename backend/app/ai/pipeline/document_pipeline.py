from app.ai.chunking.chunker import ChunkingService
from app.ai.loaders.factory import DocumentLoaderFactory
from app.ai.vectorstore.chroma_service import ChromaService


class DocumentPipeline:

    def __init__(self):
        self.chunker = ChunkingService()
        self.vectorstore = ChromaService()

    def process(
        self,
        path,
        file_type,
        document,
        user,
    ):

        loader = DocumentLoaderFactory.get_loader(file_type)

        pages = loader.load(path)

        chunks = self.chunker.split(pages)

        for chunk in chunks:
            chunk.metadata["user_id"] = str(user.id)
            chunk.metadata["subject_id"] = str(document.subject_id)
            chunk.metadata["document_id"] = str(document.id)
            chunk.metadata["filename"] = document.original_filename

        self.vectorstore.add_documents(chunks)

        return len(chunks)