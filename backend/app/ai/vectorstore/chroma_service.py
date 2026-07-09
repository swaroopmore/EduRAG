from langchain_chroma import Chroma

from app.ai.embeddings.embedding_service import EmbeddingService


class ChromaService:

    def __init__(self):

        self.db = Chroma(
            collection_name="edurag",
            persist_directory="vector_db",
            embedding_function=EmbeddingService().get(),
        )

    def add_documents(
        self,
        documents,
    ):

        self.db.add_documents(documents)

    def search(
        self,
        query,
        user_id,
        subject_id,
        k=20,
    ):

        return self.db.similarity_search(
            query=query,
            k=k,
            filter={
                "$and": [
                    {"user_id": str(user_id)},
                    {"subject_id": str(subject_id)},
                ]
            },
        )

    def get_all_documents(
        self,
        user_id,
        subject_id,
    ):

        result = self.db.get(
            where={
                "$and": [
                    {"user_id": str(user_id)},
                    {"subject_id": str(subject_id)},
                ]
            },
            include=["metadatas", "documents"],
        )

        documents = []

        for content, metadata in zip(
            result["documents"],
            result["metadatas"],
        ):

            metadata = metadata or {}

            documents.append(
                {
                    "page_content": content,
                    "metadata": metadata,
                }
            )

        return documents