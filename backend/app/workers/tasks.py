from app.core.database import async_session
from app.core.logging import logger
from app.services.memory import MemoryService
from app.websocket.manager import get_connection_manager


async def process_memory_task(memory_id: str) -> None:
    async with async_session() as session:
        service = MemoryService(session)
        memory = await service.process_memory(memory_id)
        if memory:
            manager = get_connection_manager()
            await manager.broadcast(
                {
                    "type": "memory_updated",
                    "memory_id": memory.id,
                    "device_id": memory.device_id,
                }
            )
            logger.info(msg=f"Memory {memory_id} processed and broadcast")
