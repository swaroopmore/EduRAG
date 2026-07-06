from app.ai.retrieval.retriever_service import RetrieverService


class Retriever:

    def __init__(self):

        self.service = RetrieverService()

    def retrieve(
        self,
        question,
        user_id,
        subject_id,
    ):

        return self.service.search(
            query=question,
            user_id=user_id,
            subject_id=subject_id,
        )