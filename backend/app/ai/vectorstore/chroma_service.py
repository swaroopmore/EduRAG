from langchain_chroma import Chroma

from app.ai.embeddings.embedding_service import EmbeddingService


class ChromaService:

    def __init__(self):

        self.db = Chroma(
            collection_name="edurag",
            persist_directory="vector_db",
            embedding_function=EmbeddingService().get(),
        )

        try:
            print(f"✅ Chroma Collection Count: {self.db._collection.count()}")
        except Exception as e:
            print(f"Chroma Count Error: {e}")

    # ------------------------------------
    # Add Documents
    # ------------------------------------

    def add_documents(
        self,
        documents,
    ):

        print(f"Adding {len(documents)} documents to Chroma...")

        self.db.add_documents(documents)

        try:
            print(f"Collection Count After Insert: {self.db._collection.count()}")
        except Exception as e:
            print(e)

    # ------------------------------------
    # Similarity Search
    # ------------------------------------

    def search(
        self,
        query,
        user_id,
        subject_id,
        k=20,
    ):

        print("\n========== CHROMA SEARCH ==========")
        print("Query:", query)
        print("User:", user_id)
        print("Subject:", subject_id)

        results = self.db.similarity_search(
            query=query,
            k=k,
            filter={
                "$and": [
                    {"user_id": str(user_id)},
                    {"subject_id": str(subject_id)},
                ]
            },
        )

        print(f"Retrieved {len(results)} chunks")

        return results

    # ------------------------------------
    # Load All Documents
    # ------------------------------------

    def get_all_documents(
        self,
        user_id,
        subject_id,
    ):

        result = self.db.get(
            where={
                "$and": [
                    {"user_id": str(user_id)},
                    {"subject_id": str(subject_id)},
                ]
            },
            include=["documents", "metadatas"],
        )

        documents = []

        docs = result.get("documents", [])
        metas = result.get("metadatas", [])

        print(f"Loaded {len(docs)} chunks from Chroma")

        for content, metadata in zip(docs, metas):

            metadata = metadata or {}

            documents.append(
                {
                    "page_content": content,
                    "metadata": metadata,
                }
            )

        return documents