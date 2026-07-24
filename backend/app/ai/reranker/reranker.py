from sentence_transformers import CrossEncoder


class Reranker:

    def __init__(self):

       

        self.model = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2"
        )

    def rerank(
        self,
        question,
        documents,
        top_k=5,
    ):

        if not documents:
            
            return []

        

        # Create Question-Chunk pairs
        pairs = [
            (question, doc.page_content)
            for doc in documents
        ]

        # Predict relevance scores
        scores = self.model.predict(pairs)

        

        for index, (doc, score) in enumerate(zip(documents, scores), start=1):

            

            filename = doc.metadata.get("filename", "Unknown")
            page = doc.metadata.get("page", 0) + 1

          

            preview = doc.page_content.replace("\n", " ")

        # Sort documents by score
        ranked = sorted(
            zip(documents, scores),
            key=lambda x: x[1],
            reverse=True,
        )

        

        top_documents = []

        for rank, (doc, score) in enumerate(ranked[:top_k], start=1):

            

            filename = doc.metadata.get("filename", "Unknown")
            page = doc.metadata.get("page", 0) + 1

            

            preview = doc.page_content.replace("\n", " ")
            

            top_documents.append(doc)

     

        return top_documents