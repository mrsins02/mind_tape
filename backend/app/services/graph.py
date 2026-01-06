from collections import defaultdict

from app.schemas.memory import GraphEdge, GraphNode, GraphResponse


class GraphService:
    def __init__(self):
        from app.vector.store import get_vector_store

        self.vector_store = get_vector_store()

    def build_graph(
        self,
        similarity_threshold: float = 0.7,
    ) -> GraphResponse:
        data = self.vector_store.get_all()

        if not data["ids"]:
            return GraphResponse(nodes=[], edges=[])

        nodes = []
        domain_counts = defaultdict(int)

        for i, doc_id in enumerate(data["ids"]):
            metadata = data["metadatas"][i] if data["metadatas"] else {}
            domain = metadata.get("domain", "unknown")
            domain_counts[domain] += 1
            nodes.append(
                GraphNode(
                    id=doc_id,
                    title=metadata.get("title", "Untitled"),
                    domain=domain,
                    size=1.0,
                )
            )

        for node in nodes:
            node.size = min(3.0, 1.0 + domain_counts[node.domain] * 0.2)

        edges = []
        ids = data["ids"]

        for i, doc_id in enumerate(ids):
            if data["documents"] and data["documents"][i]:
                similar = self.vector_store.query(
                    query_text=data["documents"][i], n_results=5
                )
                if similar["ids"] and similar["ids"][0]:
                    for j, similar_id in enumerate(similar["ids"][0]):
                        if similar_id != doc_id:
                            distance = (
                                similar["distances"][0][j]
                                if similar["distances"]
                                else 1.0
                            )
                            similarity = 1 - distance
                            if similarity >= similarity_threshold:
                                edges.append(
                                    GraphEdge(
                                        source=doc_id,
                                        target=similar_id,
                                        weight=similarity,
                                    )
                                )

        seen_edges = set()
        unique_edges = []
        for edge in edges:
            key = tuple(sorted([edge.source, edge.target]))
            if key not in seen_edges:
                seen_edges.add(key)
                unique_edges.append(edge)

        return GraphResponse(nodes=nodes, edges=unique_edges)


_graph_service = None


def get_graph_service() -> GraphService:
    global _graph_service
    if _graph_service is None:
        _graph_service = GraphService()
    return _graph_service
