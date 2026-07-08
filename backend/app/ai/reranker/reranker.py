from sentence_transformers import CrossEncoder


class Reranker:

    def __init__(self):

        print("=" * 60)
        print("Loading Cross Encoder...")
        print("=" * 60)

        self.model = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2"
        )

        print("✅ Cross Encoder Loaded Successfully")
        print("=" * 60)

    def rerank(
        self,
        question,
        documents,
        top_k=5,
    ):

        if not documents:
            print("⚠️ No documents received for reranking.")
            return []

        print("\n" + "=" * 60)
        print("RERANKER STARTED")
        print("=" * 60)

        print(f"Question: {question}")
        print(f"Candidate Chunks Retrieved: {len(documents)}")

        # Create Question-Chunk pairs
        pairs = [
            (question, doc.page_content)
            for doc in documents
        ]

        # Predict relevance scores
        scores = self.model.predict(pairs)

        print("\nScores Before Sorting\n")

        for index, (doc, score) in enumerate(zip(documents, scores), start=1):

            print("-" * 60)
            print(f"Chunk {index}")
            print(f"Score : {score:.4f}")

            filename = doc.metadata.get("filename", "Unknown")
            page = doc.metadata.get("page", 0) + 1

            print(f"Document : {filename}")
            print(f"Page     : {page}")

            preview = doc.page_content.replace("\n", " ")
            print("Preview  :", preview[:200])

        # Sort documents by score
        ranked = sorted(
            zip(documents, scores),
            key=lambda x: x[1],
            reverse=True,
        )

        print("\n" + "=" * 60)
        print("TOP CHUNKS AFTER RERANKING")
        print("=" * 60)

        top_documents = []

        for rank, (doc, score) in enumerate(ranked[:top_k], start=1):

            print("-" * 60)
            print(f"Rank : {rank}")
            print(f"Score: {score:.4f}")

            filename = doc.metadata.get("filename", "Unknown")
            page = doc.metadata.get("page", 0) + 1

            print(f"Document : {filename}")
            print(f"Page     : {page}")

            preview = doc.page_content.replace("\n", " ")
            print("Preview  :", preview[:200])

            top_documents.append(doc)

        print("=" * 60)
        print("RERANKER FINISHED")
        print("=" * 60 + "\n")

        return top_documents