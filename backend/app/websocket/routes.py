from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.config import get_settings
from app.core.logging import logger
from app.websocket.manager import get_connection_manager


router = APIRouter()
settings = get_settings()


@router.websocket(path="/sync/realtime")
async def websocket_endpoint(
    websocket: WebSocket,
    device_id: str = Query(default=...),
    token: str = Query(default=None),
):
    if token and token != settings.api_key:
        await websocket.close(code=4001)
        return

    manager = get_connection_manager()
    await manager.connect(websocket, device_id)

    try:
        while True:
            data = await websocket.receive_json()
            await manager.handle_message(websocket, data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(msg=f"WebSocket error: {e}")
        manager.disconnect(websocket)
