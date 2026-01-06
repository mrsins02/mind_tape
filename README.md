# MindTape

A realtime memory-synced browser assistant with local vector database, FastAPI backend, browser extension, RAG pipeline, and hybrid search engine.

## Features

- **Browser Extension**: Automatically captures and stores webpage content
- **Semantic Search**: Find memories using natural language queries
- **RAG-based Q&A**: Ask questions about your browsing history
- **Memory Graph**: Visualize connections between memories
- **Realtime Sync**: WebSocket-based sync across devices
- **Hybrid Search**: Combines vector, keyword, and recency scoring

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│ Browser Extension│────▶│   FastAPI API   │
└─────────────────┘     └────────┬────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                        ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│   ChromaDB    │     │   SQLite DB   │     │  WebSocket    │
│ (Embeddings)  │     │  (Memories)   │     │   (Sync)      │
└───────────────┘     └───────────────┘     └───────────────┘
```

## Quick Start

### Using Docker

```bash
# Clone the repository
git clone https://github.com/yourusername/mind_tape.git
cd mind_tape

# Set environment variables
cd backend
cp .env.example .env

# Start services
docker-compose up -d
```

### Manual Setup

```bash
# Backend
cd backend
poetry env use 3.12
poetry install
poetry run uvicorn main:app --reload

# Frontend
# Serve the frontend directory with any static file server
npx serve frontend -p 3000
```

### Browser Extension

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `extension` folder
5. Click the MindTape icon and configure your API key

## API Endpoints

| Endpoint            | Method | Description                  |
| ------------------- | ------ | ---------------------------- |
| `/memory/add`     | POST   | Add new memory               |
| `/memory/query`   | GET    | Search memories              |
| `/memory/context` | GET    | Get RAG context & answer     |
| `/memory/graph`   | GET    | Get graph visualization data |
| `/extension/sync` | POST   | Sync from extension          |
| `/sync/realtime`  | WS     | WebSocket realtime sync      |
| `/health`         | GET    | Health check                 |

## Configuration

Environment variables:

| Variable               | Description                | Default                               |
| ---------------------- | -------------------------- | ------------------------------------- |
| `MINDTAPE_API_KEY`   | API authentication key     | `dev-api-key...`                    |
| `OPENAI_API_KEY`     | OpenAI API key for LLM     | Empty (uses fallback)                 |
| `DATABASE_URL`       | SQLite database URL        | `sqlite+aiosqlite:///./mindtape.db` |
| `CHROMA_PERSIST_DIR` | ChromaDB storage path      | `./chroma_data`                     |
| `EMBEDDING_MODEL`    | Sentence transformer model | `all-MiniLM-L6-v2`                  |

## Project Structure

```
mind_tape/
├── backend/
│   ├── app/
│   │   ├── api/           # API routes
│   │   ├── core/          # Config, auth, logging
│   │   ├── models/        # SQLModel database models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   ├── vector/        # Vector store & search
│   │   ├── websocket/     # WebSocket handling
│   │   └── workers/       # Background tasks
│   ├── tests/             # Pytest tests
│   ├── main.py            # FastAPI app
│   ├── requirements.txt
│   └── Dockerfile
├── extension/
│   ├── manifest.json      # Chrome MV3 manifest
│   ├── background.js      # Service worker
│   ├── content.js         # Content script
│   ├── popup.html/js/css  # Extension popup
│   └── icons/             # Extension icons
├── frontend/
│   ├── index.html         # Graph visualization UI
│   ├── graph.js           # D3.js force graph
│   ├── api.js             # API client
│   └── styles.css
├── docs/
│   └── ARCHITECTURE.md    # Technical architecture
└── docker-compose.yml
```

## Testing

```bash
cd backend
poetry add pytest pytest-asyncio httpx
poetry run pytest
```

## Development

### Adding Custom Embeddings

The embedding model can be changed via `EMBEDDING_MODEL` environment variable. Any model supported by `sentence-transformers` will work.

### Customizing Search Weights

Edit `backend/app/vector/search.py` to adjust:

- `vector_weight`: Weight for semantic similarity (default: 0.6)
- `keyword_weight`: Weight for BM25 keyword match (default: 0.3)
- `recency_weight`: Weight for recency boost (default: 0.1)

## License

MIT
