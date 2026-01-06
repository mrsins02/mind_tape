from unittest.mock import AsyncMock, MagicMock

import pytest

from app.websocket.manager import ConnectionManager


@pytest.fixture
def manager():
    return ConnectionManager()


@pytest.fixture
def mock_websocket():
    ws = MagicMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    return ws


@pytest.mark.asyncio
async def test_connect(manager, mock_websocket):
    await manager.connect(mock_websocket, "device1")
    mock_websocket.accept.assert_called_once()
    assert "device1" in manager.get_connected_devices()


@pytest.mark.asyncio
async def test_disconnect(manager, mock_websocket):
    await manager.connect(mock_websocket, "device1")
    manager.disconnect(mock_websocket)
    assert "device1" not in manager.get_connected_devices()


@pytest.mark.asyncio
async def test_broadcast(manager, mock_websocket):
    await manager.connect(mock_websocket, "device1")
    message = {"type": "test", "data": "hello"}
    await manager.broadcast(message)
    mock_websocket.send_json.assert_called_once_with(message)


@pytest.mark.asyncio
async def test_handle_ping(manager, mock_websocket):
    await manager.connect(mock_websocket, "device1")
    await manager.handle_message(mock_websocket, {"type": "ping"})
    mock_websocket.send_json.assert_called_with({"type": "pong"})


def test_is_device_connected(manager):
    assert manager.is_device_connected("unknown") is False
