"""A small, dependency-free BM25 (Okapi) index.

Why not ``rank_bm25``?  Its IDF becomes zero/negative when a term occurs in half or
more of the documents, which silently disables keyword search for small subjects
(one or two chunks).  This index uses the non-negative Lucene IDF
``ln(1 + (N - n + 0.5) / (n + 0.5))`` and an inverted index, so only chunks that
actually contain a query term are scored.
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict

from langchain_core.documents import Document

# Small English stop-word list.  Without it, "what is the ..." matches every
# chunk and BM25 stops being a useful relevance signal.
STOPWORDS = frozenset(
    """a an and are as at be but by for from has have how i if in into is it its of on or
    that the their then there these they this to was were what when where which who whom why
    will with you your can could should would do does did about explain tell me give show
    please between over under than so such not no yes""".split()
)

_TOKEN = re.compile(r"\w+", re.UNICODE)

K1 = 1.5
B = 0.75


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text.lower()) if t not in STOPWORDS]


class BM25Index:
    def __init__(self) -> None:
        self.documents: list[Document] = []
        self._postings: dict[str, list[tuple[int, int]]] = {}
        self._doc_len: list[int] = []
        self._avg_len = 0.0

    def build(self, documents: list[Document]) -> None:
        self.documents = documents
        postings: dict[str, list[tuple[int, int]]] = defaultdict(list)
        self._doc_len = []
        for index, doc in enumerate(documents):
            tokens = tokenize(doc.page_content)
            self._doc_len.append(len(tokens))
            for term, freq in Counter(tokens).items():
                postings[term].append((index, freq))
        self._postings = dict(postings)
        self._avg_len = (sum(self._doc_len) / len(self._doc_len)) if self._doc_len else 0.0

    def search(self, query: str, k: int = 20) -> list[tuple[Document, float]]:
        """Return ``(chunk, score)`` for chunks sharing at least one term, best first."""
        if not self.documents:
            return []
        n_docs = len(self.documents)
        scores: dict[int, float] = defaultdict(float)
        for term in set(tokenize(query)):
            postings = self._postings.get(term)
            if not postings:
                continue
            idf = math.log(1 + (n_docs - len(postings) + 0.5) / (len(postings) + 0.5))
            for doc_index, freq in postings:
                length_norm = 1 - B + B * (self._doc_len[doc_index] / (self._avg_len or 1.0))
                scores[doc_index] += idf * (freq * (K1 + 1)) / (freq + K1 * length_norm)
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:k]
        return [(self.documents[i], score) for i, score in ranked]
