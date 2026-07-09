import re

from rank_bm25 import BM25Okapi


class BM25Index:

    def __init__(self):

        self.bm25 = None
        self.documents = []

    def build(self, documents):

        self.documents = documents

        tokenized = [
            self.tokenize(doc.page_content)
            for doc in documents
        ]

        self.bm25 = BM25Okapi(tokenized)

    def search(
        self,
        query,
        k=5,
    ):

        if self.bm25 is None:
            return []

        query_tokens = self.tokenize(query)

        scores = self.bm25.get_scores(query_tokens)

        ranked = sorted(
            zip(self.documents, scores),
            key=lambda x: x[1],
            reverse=True,
        )

        return [
            doc
            for doc, score in ranked[:k]
        ]

    @staticmethod
    def tokenize(text):

        text = text.lower()

        return re.findall(
            r"\w+",
            text,
        )