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
        # Load Entire Knowledge Base
        # ----------------------------------------

        

        all_chunks = self.vectorstore.get_all_documents(
            user_id=user_id,
            subject_id=subject_id,
        )

        documents = []

        for chunk in all_chunks:

            documents.append(
                Document(
                    page_content=chunk["page_content"],
                    metadata=chunk["metadata"],
                )
            )

        

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
        # Cross Encoder Reranking
        # ----------------------------------------

        final_docs = self.reranker.rerank(
            question=question,
            documents=merged_docs,
            top_k=k,
        )

        

        return final_docs