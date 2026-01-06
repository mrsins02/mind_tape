import asyncio

import pytest

from app.workers.queue import TaskQueue


@pytest.fixture
def task_queue():
    return TaskQueue(max_workers=2)


async def sample_task(value):
    await asyncio.sleep(0.1)
    return value * 2


@pytest.mark.asyncio
async def test_enqueue_task(task_queue):
    await task_queue.enqueue("task1", sample_task, 5)
    assert task_queue.pending_count() == 1


@pytest.mark.asyncio
async def test_start_stop_queue(task_queue):
    await task_queue.start()
    assert task_queue.running is True
    assert len(task_queue.workers) == 2
    await task_queue.stop()
    assert task_queue.running is False


@pytest.mark.asyncio
async def test_process_tasks(task_queue):
    results = []

    async def track_task(value):
        results.append(value)

    await task_queue.enqueue("t1", track_task, 1)
    await task_queue.enqueue("t2", track_task, 2)

    await task_queue.start()
    await asyncio.sleep(0.5)
    await task_queue.stop()

    assert 1 in results
    assert 2 in results
