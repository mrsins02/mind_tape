import pytest
from httpx import ASGITransport, AsyncClient


try:
    from main import app

    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    app = None

pytestmark = pytest.mark.skipif(
    condition=not DEPENDENCIES_AVAILABLE,
    reason="Heavy dependencies not installed",
)


@pytest.fixture
def api_key():
    return "dev-api-key-change-in-production"


@pytest.fixture
def headers(api_key):
    return {
        "X-API-Key": api_key,
    }


@pytest.fixture
async def client():
    if not DEPENDENCIES_AVAILABLE:
        pytest.skip(reason="Dependencies not available")
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check(client, headers):
    response = await client.get(
        url="/health",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "components" in data


@pytest.mark.asyncio
async def test_root(client):
    response = await client.get(url="/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "MindTape API"


@pytest.mark.asyncio
async def test_add_memory(
    client,
    headers,
):
    memory_data = {
        "url": "https://example.com/test",
        "title": "Test Page",
        "content": "This is test content for the memory.",
        "device_id": "test_device",
    }
    response = await client.post(
        "/memory/add",
        json=memory_data,
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["url"] == memory_data["url"]
    assert data["title"] == memory_data["title"]
    assert data["device_id"] == memory_data["device_id"]


@pytest.mark.asyncio
async def test_add_memory_unauthorized(client):
    memory_data = {
        "url": "https://example.com/test",
        "title": "Test Page",
        "content": "Content",
        "device_id": "test",
    }
    response = await client.post(
        url="/memory/add",
        json=memory_data,
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_query_memories(client, headers):
    response = await client.get(
        url="/memory/query?query=test&limit=5",
        headers=headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_context(client, headers):
    response = await client.get(
        url="/memory/context?query=test",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "context" in data
    assert "sources" in data


@pytest.mark.asyncio
async def test_get_graph(client, headers):
    response = await client.get(
        url="/memory/graph",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
