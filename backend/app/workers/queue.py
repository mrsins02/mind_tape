import asyncio
from collections import deque
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.core.logging import logger


@dataclass
class Task:
    id: str
    func: Callable[..., Coroutine[Any, Any, Any]]
    args: tuple
    kwargs: dict
    created_at: datetime
    retries: int = 0
    max_retries: int = 3


class TaskQueue:
    def __init__(
        self,
        max_workers: int = 3,
    ):
        self.queue: deque[Task] = deque()
        self.max_workers = max_workers
        self.workers: list[asyncio.Task] = []
        self.running = False
        self._lock = asyncio.Lock()

    async def enqueue(
        self,
        task_id: str,
        func: Callable[..., Coroutine[Any, Any, Any]],
        *args,
        **kwargs,
    ) -> None:
        task = Task(
            id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            created_at=datetime.now(tz=timezone.utc),
        )
        async with self._lock:
            self.queue.append(task)
        logger.info(msg=f"Task {task_id} enqueued")

    async def process_task(
        self,
        task: Task,
    ) -> bool:
        try:
            await task.func(*task.args, **task.kwargs)
            logger.info(msg=f"Task {task.id} completed")
            return True
        except Exception as e:
            logger.error(msg=f"Task {task.id} failed: {e}")
            if task.retries < task.max_retries:
                task.retries += 1
                async with self._lock:
                    self.queue.append(task)
                logger.info(msg=f"Task {task.id} requeued, retry {task.retries}")
            return False

    async def worker(
        self,
        worker_id: int,
    ) -> None:
        logger.info(msg=f"Worker {worker_id} started")
        while self.running:
            task = None
            async with self._lock:
                if self.queue:
                    task = self.queue.popleft()

            if task:
                await self.process_task(task)
            else:
                await asyncio.sleep(0.5)

    async def start(self) -> None:
        if self.running:
            return
        self.running = True
        for i in range(self.max_workers):
            worker_task = asyncio.create_task(
                coro=self.worker(
                    worker_id=i,
                ),
            )
            self.workers.append(worker_task)
        logger.info(msg=f"Task queue started with {self.max_workers} workers")

    async def stop(self) -> None:
        self.running = False
        for worker in self.workers:
            worker.cancel()
        self.workers.clear()
        logger.info(msg="Task queue stopped")

    def pending_count(self) -> int:
        return len(self.queue)


_task_queue: TaskQueue | None = None


def get_task_queue() -> TaskQueue:
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueue()
    return _task_queue
