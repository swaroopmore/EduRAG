from app.ai.reranker.reranker import Reranker
from app.ai.vectorstore.chroma_service import ChromaService


class RetrieverService:

    def __init__(self):
        self.vectorstore = ChromaService()
        self.reranker = Reranker()

    def search(
        self,
        query: str,
        user_id: str,
        subject_id: str,
        k: int = 5,
    ):

        # Stage 1: Retrieve more candidate chunks
        docs = self.vectorstore.search(
            query=query,
            user_id=user_id,
            subject_id=subject_id,
            k=20,
        )

        # Stage 2: Rerank them
        docs = self.reranker.rerank(
            question=query,
            documents=docs,
            top_k=k,
        )

        return docs