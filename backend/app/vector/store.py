from typing import Any

from app.core.config import get_settings


settings = get_settings()


class EmbeddingService:
    def __init__(self):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name_or_path=settings.embedding_model)

    def embed(
        self,
        text: str,
    ) -> list[float]:
        embedding = self.model.encode(
            sentences=text,
            convert_to_numpy=True,
        )
        return embedding.tolist()

    def embed_batch(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        embeddings = self.model.encode(
            sentences=texts,
            convert_to_numpy=True,
        )
        return embeddings.tolist()


class VectorStore:
    def __init__(self):
        import chromadb
        from chromadb.config import Settings as ChromaSettings

        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(
                anonymized_telemetry=False,
            ),
        )
        self.collection = self.client.get_or_create_collection(
            name="memories",
            metadata={
                "hnsw:space": "cosine",
            },
        )
        self.embedding_service = EmbeddingService()

    def add(
        self,
        id: str,
        text: str,
        metadata: dict[str, Any],
        embedding: list[float] | None = None,
    ) -> None:
        if embedding is None:
            embedding = self.embedding_service.embed(text)
        self.collection.add(
            ids=[id],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[text],
        )

    def update(
        self,
        id: str,
        text: str,
        metadata: dict[str, Any],
        embedding: list[float] | None = None,
    ) -> None:
        if embedding is None:
            embedding = self.embedding_service.embed(text)
        self.collection.update(
            ids=[id],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[text],
        )

    def delete(self, id: str) -> None:
        self.collection.delete(ids=[id])

    def query(
        self,
        query_text: str,
        n_results: int = 10,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        query_embedding = self.embedding_service.embed(query_text)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=[
                "documents",
                "metadatas",
                "distances",
            ],
        )
        return results

    def get_by_id(
        self,
        id: str,
    ) -> dict[str, Any] | None:
        result = self.collection.get(
            ids=[id],
            include=[
                "documents",
                "metadatas",
            ],
        )
        if result["ids"]:
            return {
                "id": result["ids"][0],
                "document": result["documents"][0] if result["documents"] else None,
                "metadata": result["metadatas"][0] if result["metadatas"] else None,
            }
        return None

    def get_all(self) -> dict[str, Any]:
        return self.collection.get(
            include=[
                "documents",
                "metadatas",
            ],
        )

    def count(self) -> int:
        return self.collection.count()


_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
