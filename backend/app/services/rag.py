from typing import Any

from app.schemas.memory import ContextResponse, MemoryResponse
from app.services.llm import get_llm_service


class RAGPipeline:
    def __init__(self):
        from app.vector.search import HybridSearchEngine

        self.search_engine = HybridSearchEngine()
        self.llm = get_llm_service()
        self.max_context_tokens = 2000

    def retrieve(
        self,
        query: str,
        n_results: int = 5,
        domain: str | None = None,
    ) -> list[dict[str, Any]]:
        return self.search_engine.search(
            query=query,
            n_results=n_results,
            domain_filter=domain,
        )

    def rerank(
        self,
        query: str,
        results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        query_terms = set(query.lower().split())
        for result in results:
            doc_terms = set(result["document"].lower().split())
            overlap = len(query_terms & doc_terms)
            result["relevance_boost"] = overlap * 0.05
            result["final_score"] = result["score"] + result["relevance_boost"]
        results.sort(key=lambda x: x["final_score"], reverse=True)
        return results

    def build_context(
        self,
        results: list[dict[str, Any]],
    ) -> str:
        context_parts = []
        total_length = 0

        for result in results:
            doc = result["document"]
            metadata = result["metadata"]
            source = f"[{metadata.get('title', 'Unknown')}]"
            part = f"{source}\n{doc}\n"

            if total_length + len(part) > self.max_context_tokens * 4:
                break
            context_parts.append(part)
            total_length += len(part)

        return "\n---\n".join(context_parts)

    def generate_answer(self, query: str, context: str) -> str:
        return self.llm.generate_answer(query, context)

    def run(
        self,
        query: str,
        n_results: int = 5,
        domain: str | None = None,
    ) -> ContextResponse:
        results = self.retrieve(
            query=query,
            n_results=n_results * 2,
            domain=domain,
        )
        if not results:
            return ContextResponse(
                query=query,
                context="",
                sources=[],
                answer="No relevant memories found.",
            )

        reranked = self.rerank(query, results)[:n_results]
        context = self.build_context(reranked)
        answer = self.generate_answer(query, context)

        sources = []
        for r in reranked:
            sources.append(
                MemoryResponse(
                    id=r["id"],
                    url=r["metadata"].get("url", ""),
                    title=r["metadata"].get("title", ""),
                    content=r["document"],
                    summary=None,
                    domain=r["metadata"].get("domain", ""),
                    device_id=r["metadata"].get("device_id", ""),
                    version=1,
                    created_at=r["metadata"].get("updated_at", ""),
                    updated_at=r["metadata"].get("updated_at", ""),
                    processed=True,
                )
            )

        return ContextResponse(
            query=query,
            context=context,
            sources=sources,
            answer=answer,
        )


_rag_pipeline = None


def get_rag_pipeline() -> RAGPipeline:
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline
