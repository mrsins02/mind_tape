from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.core.config import get_settings


settings = get_settings()

async_engine = create_async_engine(
    url=settings.database_url,
    echo=settings.debug,
    future=True,
)

async_session = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session():
    async with async_session() as session:
        yield session


async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(fn=SQLModel.metadata.create_all)
