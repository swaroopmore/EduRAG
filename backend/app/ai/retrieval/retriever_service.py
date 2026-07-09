from app.ai.retrieval.hybrid_retriever import HybridRetriever


class RetrieverService:

    def __init__(self):

        self.retriever = HybridRetriever()

    def search(
        self,
        query: str,
        user_id: str,
        subject_id: str,
        k: int = 5,
    ):

        return self.retriever.retrieve(
            question=query,
            user_id=user_id,
            subject_id=subject_id,
            k=k,
        )