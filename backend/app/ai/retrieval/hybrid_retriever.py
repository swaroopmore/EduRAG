from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever

from app.ai.reranker.reranker import Reranker
from app.ai.vectorstore.chroma_service import ChromaService


class HybridRetriever:

    def __init__(self):
        self.vectorstore = ChromaService()
        self.reranker = Reranker()

    def retrieve(
        self,
        question,
        user_id,
        subject_id,
        k=5,
    ):

        # ----------------------------------------
        # Dense Retrieval (Chroma)
        # ----------------------------------------

        vector_docs = self.vectorstore.search(
            query=question,
            user_id=user_id,
            subject_id=subject_id,
            k=20,
        )

        # ----------------------------------------
        # Load All Documents
        # ----------------------------------------

        all_chunks = self.vectorstore.get_all_documents(
            user_id=user_id,
            subject_id=subject_id,
        )

        documents = [
            Document(
                page_content=chunk["page_content"],
                metadata=chunk["metadata"],
            )
            for chunk in all_chunks
        ]

        print(f"Vector Docs: {len(vector_docs)}")
        print(f"All Chunks: {len(documents)}")

        # ----------------------------------------
        # If no documents exist
        # ----------------------------------------

        if len(documents) == 0:
            return vector_docs[:k]

        # ----------------------------------------
        # Sparse Retrieval (BM25)
        # ----------------------------------------

        bm25 = BM25Retriever.from_documents(documents)
        bm25.k = 20

        keyword_docs = bm25.invoke(question)

        # ----------------------------------------
        # Merge Results
        # ----------------------------------------

        merged = {}

        for doc in vector_docs:
            key = (
                doc.metadata.get("document_id"),
                doc.metadata.get("page"),
                hash(doc.page_content),
            )
            merged[key] = doc

        for doc in keyword_docs:
            key = (
                doc.metadata.get("document_id"),
                doc.metadata.get("page"),
                hash(doc.page_content),
            )
            merged[key] = doc

        merged_docs = list(merged.values())

        # ----------------------------------------
        # Nothing found
        # ----------------------------------------

        if len(merged_docs) == 0:
            return []

        # ----------------------------------------
        # Reranking
        # ----------------------------------------

        final_docs = self.reranker.rerank(
            question=question,
            documents=merged_docs,
            top_k=k,
        )

        return final_docs