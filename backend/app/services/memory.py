from datetime import datetime, timezone
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.memory import Memory
from app.schemas.memory import MemoryCreate
from app.services.llm import get_llm_service


class MemoryService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._vector_store = None
        self.llm = get_llm_service()

    @property
    def vector_store(self):
        if self._vector_store is None:
            from app.vector.store import get_vector_store

            self._vector_store = get_vector_store()
        return self._vector_store

    async def create(self, data: MemoryCreate) -> Memory:
        domain = urlparse(data.url).netloc
        memory = Memory(
            url=data.url,
            title=data.title,
            content=data.content,
            domain=domain,
            device_id=data.device_id,
        )
        self.session.add(memory)
        await self.session.commit()
        await self.session.refresh(memory)
        return memory

    async def get_by_id(self, memory_id: str) -> Memory | None:
        result = await self.session.execute(
            select(Memory).where(Memory.id == memory_id)
        )
        return result.scalar_one_or_none()

    async def get_by_url(self, url: str) -> Memory | None:
        result = await self.session.execute(select(Memory).where(Memory.url == url))
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 100, offset: int = 0) -> list[Memory]:
        result = await self.session.execute(
            select(Memory)
            .offset(offset)
            .limit(limit)
            .order_by(Memory.updated_at.desc())
        )
        return list(result.scalars().all())

    async def get_since(self, since: datetime) -> list[Memory]:
        result = await self.session.execute(
            select(Memory).where(Memory.updated_at > since)
        )
        return list(result.scalars().all())

    async def update(self, memory_id: str, **kwargs) -> Memory | None:
        memory = await self.get_by_id(memory_id)
        if not memory:
            return None
        for key, value in kwargs.items():
            if hasattr(memory, key) and value is not None:
                setattr(memory, key, value)
        memory.updated_at = datetime.now(timezone.utc)
        memory.version += 1
        await self.session.commit()
        await self.session.refresh(memory)
        return memory

    async def delete(self, memory_id: str) -> bool:
        memory = await self.get_by_id(memory_id)
        if not memory:
            return False
        await self.session.delete(memory)
        await self.session.commit()
        self.vector_store.delete(memory_id)
        return True

    async def process_memory(self, memory_id: str) -> Memory | None:
        memory = await self.get_by_id(memory_id)
        if not memory:
            return None

        summary = self.llm.summarize(memory.content)
        memory.summary = summary
        memory.processed = True
        memory.updated_at = datetime.now(timezone.utc)

        self.vector_store.add(
            id=memory.id,
            text=f"{memory.title}\n{memory.summary}\n{memory.content[:1000]}",
            metadata={
                "url": memory.url,
                "title": memory.title,
                "domain": memory.domain,
                "device_id": memory.device_id,
                "updated_at": memory.updated_at.isoformat(),
            },
        )

        await self.session.commit()
        await self.session.refresh(memory)
        return memory
