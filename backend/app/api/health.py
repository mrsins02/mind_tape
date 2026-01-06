from datetime import datetime, timezone

from fastapi import APIRouter

from app.websocket.manager import get_connection_manager
from app.workers.queue import get_task_queue


router = APIRouter(tags=["health"])


@router.get(path="/health")
async def health_check():
    from app.vector.store import get_vector_store

    vector_store = get_vector_store()
    queue = get_task_queue()
    manager = get_connection_manager()

    return {
        "status": "healthy",
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "components": {
            "vector_store": {
                "status": "ok",
                "count": vector_store.count(),
            },
            "task_queue": {
                "status": "ok",
                "pending": queue.pending_count(),
            },
            "websocket": {
                "status": "ok",
                "connected_devices": len(manager.get_connected_devices()),
            },
        },
    }
