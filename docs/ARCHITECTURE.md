# MindTape Architecture

## System Overview

MindTape is a realtime memory-synced browser assistant that captures, stores, and retrieves web browsing context using vector embeddings and semantic search.

## Components

### 1. Browser Extension (Chrome MV3)
- Extracts page content (text, URL, title)
- Sends data to backend API
- Displays summaries, related memories, and RAG answers
- Maintains WebSocket connection for realtime sync

### 2. FastAPI Backend
- REST API for memory operations
- WebSocket server for realtime sync
- Background workers for async processing
- Authentication via API key

### 3. Vector Database (ChromaDB)
- Stores embeddings with metadata
- Enables similarity search
- Supports hybrid search (vector + keyword)

### 4. RAG Pipeline
- Retrieves relevant context
- Reranks results
- Generates answers using LLM

## Data Flow

```
┌─────────────────┐
│ Browser Extension│
└────────┬────────┘
         │ POST /memory/add
         ▼
┌─────────────────┐
│   FastAPI App   │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌──────────┐
│ Queue │ │ ChromaDB │
└───┬───┘ └──────────┘
    │
    ▼
┌───────────────┐
│ Background    │
│ Workers       │
│ - Summarize   │
│ - Embed       │
└───────────────┘
```

## Event Flow

1. User visits webpage → Extension captures content
2. Content sent to `/memory/add` endpoint
3. Backend queues processing job
4. Worker summarizes content (LLM)
5. Worker generates embeddings
6. Embeddings stored in ChromaDB
7. WebSocket broadcasts update to all devices
8. Extension receives update and refreshes UI

## RAG Pipeline Steps

1. **Chunk**: Split text into overlapping chunks
2. **Summarize**: Generate summary using LLM
3. **Embed**: Create vector embeddings
4. **Store**: Save to ChromaDB with metadata
5. **Search**: Query with hybrid search
6. **Rerank**: Score and reorder results
7. **Build Context**: Assemble context window
8. **Generate**: Pass to LLM for answer

## Sync Algorithm

1. Each device has unique device_id
2. Each memory has version timestamp
3. On connection, client sends last_sync timestamp
4. Server returns all memories updated since last_sync
5. Client applies updates, stores new last_sync
6. Conflict resolution: latest timestamp wins

## Storage Model

### Memory Entry
```json
{
  "id": "uuid",
  "url": "string",
  "title": "string",
  "content": "string",
  "summary": "string",
  "domain": "string",
  "embedding": "vector",
  "created_at": "datetime",
  "updated_at": "datetime",
  "version": "int",
  "device_id": "string"
}
```

## API Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| /memory/add | POST | Add new memory |
| /memory/query | GET | Search memories |
| /memory/context | GET | Get RAG context |
| /memory/graph | GET | Get graph data |
| /extension/sync | POST | Sync from extension |
| /sync/realtime | WS | WebSocket sync |
| /health | GET | Health check |

## Security Model

- API Key authentication via X-API-Key header
- Keys stored hashed in database
- Rate limiting on all endpoints
- CORS configured for extension origin
- WebSocket auth via query param token

## Hybrid Search Engine

1. **Vector Search**: Cosine similarity on embeddings
2. **Keyword Search**: BM25 on text content
3. **Recency Boost**: Decay function on timestamp
4. **Domain Similarity**: Bonus for same domain
5. **Final Score**: Weighted combination
