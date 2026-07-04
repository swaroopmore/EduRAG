from langchain_chroma import Chroma

from app.ai.embeddings.embedding_service import EmbeddingService


class ChromaService:

    def __init__(self):

        self.db = Chroma(
            collection_name="edurag",
            persist_directory="vector_db",
            embedding_function=EmbeddingService().get(),
        )

    def add_documents(self, documents):

        self.db.add_documents(documents)

    def similarity_search(
    self,
    query,
    user_id,
    subject_id,
    k=5,
):

        return self.db.similarity_search(
        query=query,
        k=k,
        filter={
            "user_id": str(user_id),
            "subject_id": str(subject_id),
        },
    )