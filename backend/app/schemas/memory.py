from datetime import datetime

from pydantic import BaseModel, Field


class MemoryCreate(BaseModel):
    url: str
    title: str
    content: str
    device_id: str


class MemoryUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    summary: str | None = None


class MemoryResponse(BaseModel):
    id: str
    url: str
    title: str
    content: str
    summary: str | None
    domain: str
    device_id: str
    version: int
    created_at: datetime
    updated_at: datetime
    processed: bool

    class Config:
        from_attributes = True


class MemorySearchResult(BaseModel):
    memory: MemoryResponse
    score: float
    highlights: list[str] = []


class QueryRequest(BaseModel):
    query: str
    limit: int = Field(
        le=100,
        default=10,
    )
    domain_filter: str | None = None


class ContextRequest(BaseModel):
    query: str
    limit: int = Field(
        le=20,
        default=5,
    )


class ContextResponse(BaseModel):
    query: str
    context: str
    sources: list[MemoryResponse]
    answer: str | None = None


class GraphNode(BaseModel):
    id: str
    title: str
    domain: str
    size: float = 1.0


class GraphEdge(BaseModel):
    source: str
    target: str
    weight: float


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class SyncRequest(BaseModel):
    device_id: str
    last_sync: datetime | None = None
    memories: list[MemoryCreate] = []


class SyncResponse(BaseModel):
    memories: list[MemoryResponse]
    sync_timestamp: datetime


class NoteCreate(BaseModel):
    memory_id: str
    content: str


class NoteResponse(BaseModel):
    id: str
    memory_id: str
    content: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
