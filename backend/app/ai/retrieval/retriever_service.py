from app.ai.vectorstore.chroma_service import ChromaService


class RetrieverService:

    def __init__(self):
        self.vectorstore = ChromaService()

    def search(
        self,
        query: str,
        user_id: str,
        subject_id: str,
        k: int = 5,
    ):

        return self.vectorstore.search(
            query=query,
            user_id=user_id,
            subject_id=subject_id,
            k=k,
        )