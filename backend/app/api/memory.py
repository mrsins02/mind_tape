from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import verify_api_key
from app.core.database import get_session
from app.schemas.memory import (
    ContextResponse,
    GraphResponse,
    MemoryCreate,
    MemoryResponse,
    MemorySearchResult,
)
from app.services.memory import MemoryService
from app.workers.queue import get_task_queue
from app.workers.tasks import process_memory_task


router = APIRouter(
    prefix="/memory",
    tags=[
        "memory",
    ],
)


@router.post(
    path="/add",
    response_model=MemoryResponse,
)
async def add_memory(
    data: MemoryCreate,
    session: AsyncSession = Depends(dependency=get_session),
    api_key: str = Depends(dependency=verify_api_key),
):
    service = MemoryService(session)
    existing = await service.get_by_url(data.url)

    if existing:
        updated = await service.update(
            memory_id=existing.id,
            title=data.title,
            content=data.content,
        )
        if updated is not None:
            queue = get_task_queue()
            await queue.enqueue(
                f"process_{updated.id}",
                process_memory_task,
                updated.id,
            )
        return updated

    memory = await service.create(data)
    queue = get_task_queue()
    await queue.enqueue(
        f"process_{memory.id}",
        process_memory_task,
        memory.id,
    )
    return memory


@router.get(
    path="/query",
    response_model=list[MemorySearchResult],
)
async def query_memories(
    query: str,
    limit: int = 10,
    domain: str | None = None,
    api_key: str = Depends(dependency=verify_api_key),
):
    from app.vector.search import HybridSearchEngine

    search_engine = HybridSearchEngine()
    results = search_engine.search(query, limit, domain)

    search_results = []
    for r in results:
        search_results.append(
            MemorySearchResult(
                memory=MemoryResponse(
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
                ),
                score=r["score"],
                highlights=[],
            )
        )
    return search_results


@router.get("/context", response_model=ContextResponse)
async def get_context(
    query: str, limit: int = 5, api_key: str = Depends(verify_api_key)
):
    from app.services.rag import get_rag_pipeline

    pipeline = get_rag_pipeline()
    return pipeline.run(query, limit)


@router.get("/graph", response_model=GraphResponse)
async def get_graph(threshold: float = 0.7, api_key: str = Depends(verify_api_key)):
    from app.services.graph import get_graph_service

    service = get_graph_service()
    return service.build_graph(threshold)


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: str,
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(verify_api_key),
):
    service = MemoryService(session)
    memory = await service.get_by_id(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memory


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: str,
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(verify_api_key),
):
    service = MemoryService(session)
    deleted = await service.delete(memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"status": "deleted", "id": memory_id}
