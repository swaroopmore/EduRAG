from app.ai.chunking.chunker import ChunkingService
from app.ai.loaders.factory import DocumentLoaderFactory
from app.ai.vectorstore.chroma_service import ChromaService
from app.ai.keyword.bm25_service import BM25Service


class DocumentPipeline:

    def __init__(self):
        self.chunker = ChunkingService()
        self.vectorstore = ChromaService()
        self.keyword = BM25Service()

    def process(
        self,
        path,
        file_type,
        document,
        user,
    ):

        print("\n========== DOCUMENT PIPELINE ==========")

        loader = DocumentLoaderFactory.get_loader(file_type)

        pages = loader.load(path)

        print(f"Pages Loaded: {len(pages)}")

        chunks = self.chunker.split(pages)

        print(f"Chunks Created: {len(chunks)}")

        for chunk in chunks:
            chunk.metadata["user_id"] = str(user.id)
            chunk.metadata["subject_id"] = str(document.subject_id)
            chunk.metadata["document_id"] = str(document.id)
            chunk.metadata["filename"] = document.original_filename

        if chunks:
            print("First Chunk Metadata:")
            print(chunks[0].metadata)

        self.vectorstore.add_documents(chunks)

        self.keyword.build(
            user_id=str(user.id),
            subject_id=str(document.subject_id),
            documents=chunks,
        )

        print("Documents stored successfully.")
        print("=======================================\n")

        return len(chunks)