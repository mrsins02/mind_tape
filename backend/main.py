from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import extension, health, memory
from app.core.config import get_settings
from app.core.database import init_db
from app.core.logging import LoggingMiddleware
from app.websocket.routes import router as ws_router
from app.workers.queue import get_task_queue


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    queue = get_task_queue()
    await queue.start()
    yield
    await queue.stop()


app = FastAPI(
    title=settings.app_name,
    description="Realtime memory-synced browser assistant",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    middleware_class=CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(middleware_class=LoggingMiddleware)

app.include_router(memory.router)
app.include_router(extension.router)
app.include_router(health.router)
app.include_router(router=ws_router)


@app.get(path="/")
async def root():
    return {
        "message": "MindTape API",
        "version": "1.0.0",
    }
