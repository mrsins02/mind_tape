from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import verify_api_key
from app.core.database import get_session
from app.schemas.memory import MemoryResponse, SyncRequest, SyncResponse
from app.services.memory import MemoryService
from app.workers.queue import get_task_queue
from app.workers.tasks import process_memory_task


router = APIRouter(
    prefix="/extension",
    tags=[
        "extension",
    ],
)


@router.post(
    path="/sync",
    response_model=SyncResponse,
)
async def sync_extension(
    data: SyncRequest,
    session: AsyncSession = Depends(dependency=get_session),
    api_key: str = Depends(dependency=verify_api_key),
):
    service = MemoryService(session)
    queue = get_task_queue()

    for mem_data in data.memories:
        mem_data_dict = mem_data.model_dump()
        mem_data_dict["device_id"] = data.device_id
        from app.schemas.memory import MemoryCreate

        memory = await service.create(data=MemoryCreate(**mem_data_dict))
        await queue.enqueue(
            f"process_{memory.id}",
            process_memory_task,
            memory.id,
        )

    if data.last_sync:
        updated_memories = await service.get_since(since=data.last_sync)
    else:
        updated_memories = await service.get_all(limit=50)

    return SyncResponse(
        memories=[MemoryResponse.model_validate(obj=m) for m in updated_memories],
        sync_timestamp=datetime.now(tz=timezone.utc),
    )
