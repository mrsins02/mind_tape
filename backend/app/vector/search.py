import math
from datetime import datetime, timezone
from typing import Any

from rank_bm25 import BM25Okapi

from app.core.config import get_settings


settings = get_settings()


class HybridSearchEngine:
    def __init__(self):
        from app.vector.store import get_vector_store

        self.vector_store = get_vector_store()
        self.vector_weight = 0.6
        self.keyword_weight = 0.3
        self.recency_weight = 0.1

    def search(
        self,
        query: str,
        n_results: int = 10,
        domain_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        where = {"domain": domain_filter} if domain_filter else None
        vector_results = self.vector_store.query(
            query_text=query,
            n_results=n_results * 2,
            where=where,
        )

        if not vector_results["ids"][0]:
            return []

        documents = vector_results["documents"][0]
        ids = vector_results["ids"][0]
        metadatas = vector_results["metadatas"][0]
        distances = vector_results["distances"][0]

        tokenized_docs = [doc.lower().split() for doc in documents]
        bm25 = BM25Okapi(corpus=tokenized_docs)
        tokenized_query = query.lower().split()
        keyword_scores = bm25.get_scores(query=tokenized_query)

        max_keyword = max(keyword_scores) if max(keyword_scores) > 0 else 1
        keyword_scores_normalized = [s / max_keyword for s in keyword_scores]

        now = datetime.now(tz=timezone.utc)
        results = []

        for i, doc_id in enumerate(ids):
            vector_score = 1 - distances[i]
            keyword_score = keyword_scores_normalized[i]

            updated_at_str = metadatas[i].get("updated_at", "")
            try:
                updated_at = datetime.fromisoformat(updated_at_str)
                days_old = (now - updated_at).days
                recency_score = math.exp(-days_old / 30)
            except (ValueError, TypeError):
                recency_score = 0.5

            domain_bonus = 0
            if domain_filter and metadatas[i].get("domain") == domain_filter:
                domain_bonus = 0.1

            final_score = (
                self.vector_weight * vector_score
                + self.keyword_weight * keyword_score
                + self.recency_weight * recency_score
                + domain_bonus
            )

            results.append(
                {
                    "id": doc_id,
                    "document": documents[i],
                    "metadata": metadatas[i],
                    "score": final_score,
                    "vector_score": vector_score,
                    "keyword_score": keyword_score,
                    "recency_score": recency_score,
                }
            )

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:n_results]

    def get_similar(
        self,
        memory_id: str,
        n_results: int = 5,
    ) -> list[dict[str, Any]]:
        memory = self.vector_store.get_by_id(id=memory_id)
        if not memory or not memory.get("document"):
            return []
        return self.search(
            query=memory["document"],
            n_results=n_results + 1,
        )[1:]
