from app.ai.vectorstore.chroma_service import ChromaService


class Retriever:

    def __init__(self):

        self.vectorstore = ChromaService()

    def retrieve(
        self,
        question,
        user_id,
        subject_id,
    ):

        return self.vectorstore.similarity_search(
            query=question,
            user_id=user_id,
            subject_id=subject_id,
            k=5,
        )