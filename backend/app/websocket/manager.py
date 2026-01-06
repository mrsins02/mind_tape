import contextlib
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket

from app.core.logging import logger


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.device_ids: dict[str, str] = {}
        self.last_sync: dict[str, datetime] = {}

    async def connect(
        self,
        websocket: WebSocket,
        device_id: str,
    ) -> None:
        await websocket.accept()
        connection_id = str(id(websocket))
        self.active_connections[connection_id] = websocket
        self.device_ids[connection_id] = device_id
        self.last_sync[device_id] = datetime.now(timezone.utc)
        logger.info(msg=f"Device {device_id} connected")

    def disconnect(
        self,
        websocket: WebSocket,
    ) -> None:
        connection_id = str(id(websocket))
        if connection_id in self.active_connections:
            device_id = self.device_ids.get(connection_id, "unknown")
            del self.active_connections[connection_id]
            if connection_id in self.device_ids:
                del self.device_ids[connection_id]
            logger.info(msg=f"Device {device_id} disconnected")

    async def send_to_device(
        self,
        device_id: str,
        message: dict[str, Any],
    ) -> None:
        for conn_id, ws in self.active_connections.items():
            if self.device_ids.get(conn_id) == device_id:
                try:
                    await ws.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to {device_id}: {e}")

    async def broadcast(
        self,
        message: dict[str, Any],
        exclude_device: str | None = None,
    ) -> None:
        for conn_id, ws in list(self.active_connections.items()):
            device_id = self.device_ids.get(conn_id)
            if exclude_device and device_id == exclude_device:
                continue
            try:
                await ws.send_json(data=message)
            except Exception as e:
                logger.error(msg=f"Broadcast error to {device_id}: {e}")

    async def handle_message(
        self,
        websocket: WebSocket,
        data: dict[str, Any],
    ) -> None:
        connection_id = str(id(websocket))
        device_id = self.device_ids.get(connection_id, "unknown")
        msg_type = data.get(
            "type",
            "",
        )

        if msg_type == "ping":
            await websocket.send_json(
                data={
                    "type": "pong",
                },
            )
        elif msg_type == "sync_request":
            last_sync_str = data.get("last_sync")
            if last_sync_str:
                with contextlib.suppress(ValueError):
                    self.last_sync[device_id] = datetime.fromisoformat(last_sync_str)
            await websocket.send_json(
                data={
                    "type": "sync_ack",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        else:
            logger.warning(msg=f"Unknown message type from {device_id}: {msg_type}")

    def get_connected_devices(self) -> set[str]:
        return set(self.device_ids.values())

    def is_device_connected(
        self,
        device_id: str,
    ) -> bool:
        return device_id in self.device_ids.values()


_connection_manager: ConnectionManager | None = None


def get_connection_manager() -> ConnectionManager:
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager
