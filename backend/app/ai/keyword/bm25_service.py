from app.ai.keyword.bm25_index import BM25Index
from app.ai.keyword.bm25_registry import BM25Registry


class BM25Service:

    def __init__(self):

        self.registry = BM25Registry()

    def build(
        self,
        user_id,
        subject_id,
        documents,
    ):

        index = BM25Index()

        index.build(documents)

        self.registry.set(
            user_id=user_id,
            subject_id=subject_id,
            index=index,
        )

        print(
            f"✅ BM25 Index Built ({len(documents)} chunks)"
        )

    def search(
        self,
        query,
        user_id,
        subject_id,
        k=5,
    ):

        index = self.registry.get(
            user_id=user_id,
            subject_id=subject_id,
        )

        if index is None:

            return []

        return index.search(
            query=query,
            k=k,
        )