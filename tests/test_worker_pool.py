"""Tests for WorkerPool."""

import threading
import time

import pytest

from agent_queue import Task, TaskQueue, WorkerPool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_pool(num_workers: int = 2, max_size: int = 100):
    results = []
    lock = threading.Lock()

    def handler(task: Task):
        with lock:
            results.append(task.payload)

    q = TaskQueue(max_size=max_size)
    pool = WorkerPool(q, handler, num_workers=num_workers)
    return q, pool, results


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

class TestWorkerPoolLifecycle:
    def test_start_and_stop(self):
        q, pool, _ = make_pool()
        pool.start()
        assert pool.is_running is True
        pool.stop()
        assert pool.is_running is False

    def test_cannot_start_twice(self):
        q, pool, _ = make_pool()
        pool.start()
        with pytest.raises(RuntimeError):
            pool.start()
        pool.stop()

    def test_invalid_num_workers(self):
        q = TaskQueue()
        with pytest.raises(ValueError):
            WorkerPool(q, lambda t: None, num_workers=0)

    def test_stop_no_wait(self):
        q, pool, _ = make_pool()
        pool.start()
        pool.stop(wait=False)
        # After stop(wait=False) threads are still tracked but stopping.
        # Give them a moment to finish.
        time.sleep(0.2)
        assert pool.is_running is False


# ---------------------------------------------------------------------------
# Task processing
# ---------------------------------------------------------------------------

class TestWorkerPoolProcessing:
    def test_processes_all_tasks(self):
        q, pool, results = make_pool(num_workers=4)
        pool.start()
        for i in range(20):
            q.put(Task(payload=i))
        # Wait for all tasks to be consumed
        deadline = time.monotonic() + 5.0
        while q.size > 0 and time.monotonic() < deadline:
            time.sleep(0.01)
        time.sleep(0.1)  # let workers finish last task
        pool.stop()
        assert sorted(results) == list(range(20))

    def test_stats_tasks_processed(self):
        q, pool, results = make_pool(num_workers=2)
        pool.start()
        for i in range(10):
            q.put(Task(payload=i))
        deadline = time.monotonic() + 5.0
        while q.size > 0 and time.monotonic() < deadline:
            time.sleep(0.01)
        time.sleep(0.1)
        pool.stop()
        s = pool.stats()
        assert s["tasks_processed"] == 10
        assert s["tasks_failed"] == 0

    def test_failed_tasks_counted(self):
        """Worker errors should increment tasks_failed without killing the worker."""
        q = TaskQueue(max_size=20)

        def bad_handler(task: Task):
            raise ValueError("intentional failure")

        pool = WorkerPool(q, bad_handler, num_workers=2)
        pool.start()
        for i in range(5):
            q.put(Task(payload=i))
        deadline = time.monotonic() + 5.0
        while q.size > 0 and time.monotonic() < deadline:
            time.sleep(0.01)
        time.sleep(0.1)
        pool.stop()
        s = pool.stats()
        assert s["tasks_failed"] == 5
        assert s["tasks_processed"] == 0

    def test_uptime_seconds_positive(self):
        q, pool, _ = make_pool()
        pool.start()
        time.sleep(0.1)
        pool.stop()
        s = pool.stats()
        assert s["uptime_seconds"] >= 0.05

    def test_workers_active_when_running(self):
        q, pool, _ = make_pool(num_workers=3)
        pool.start()
        s = pool.stats()
        assert s["workers_active"] == 3
        pool.stop()
