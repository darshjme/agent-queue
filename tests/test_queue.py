"""Tests for TaskQueue."""

import threading
import time

import pytest

from agent_queue import Task, TaskQueue, QueueFullError, QueueEmptyError


# ---------------------------------------------------------------------------
# Basic put / get
# ---------------------------------------------------------------------------

class TestTaskQueueBasic:
    def test_put_and_get(self):
        q = TaskQueue(max_size=10)
        t = Task(payload="hello")
        q.put(t)
        got = q.get()
        assert got.payload == "hello"

    def test_size_after_put(self):
        q = TaskQueue(max_size=10)
        assert q.size == 0
        q.put(Task(payload="a"))
        assert q.size == 1
        q.put(Task(payload="b"))
        assert q.size == 2

    def test_size_after_get(self):
        q = TaskQueue(max_size=10)
        q.put(Task(payload="a"))
        q.get()
        assert q.size == 0

    def test_is_empty_initially(self):
        q = TaskQueue()
        assert q.is_empty is True

    def test_not_empty_after_put(self):
        q = TaskQueue()
        q.put(Task(payload="x"))
        assert q.is_empty is False

    def test_is_full(self):
        q = TaskQueue(max_size=2)
        assert q.is_full is False
        q.put(Task(payload="a"))
        q.put(Task(payload="b"))
        assert q.is_full is True

    def test_put_nowait_full_raises(self):
        q = TaskQueue(max_size=1)
        q.put_nowait(Task(payload="a"))
        with pytest.raises(QueueFullError):
            q.put_nowait(Task(payload="b"))

    def test_get_nowait_empty_raises(self):
        q = TaskQueue(max_size=10)
        with pytest.raises(QueueEmptyError):
            q.get_nowait()

    def test_get_with_timeout_raises(self):
        q = TaskQueue(max_size=10)
        with pytest.raises(QueueEmptyError):
            q.get(block=True, timeout=0.05)

    def test_put_with_timeout_raises_when_full(self):
        q = TaskQueue(max_size=1)
        q.put(Task(payload="filler"))
        with pytest.raises(QueueFullError):
            q.put(Task(payload="overflow"), block=True, timeout=0.05)

    def test_invalid_max_size(self):
        with pytest.raises(ValueError):
            TaskQueue(max_size=0)


# ---------------------------------------------------------------------------
# Priority ordering
# ---------------------------------------------------------------------------

class TestTaskQueuePriority:
    def test_priority_ordering(self):
        q = TaskQueue(max_size=10)
        for p in [1, 5, 3]:
            q.put(Task(payload=str(p), priority=p))
        priorities = [q.get().priority for _ in range(3)]
        assert priorities == [5, 3, 1]

    def test_fifo_same_priority(self):
        q = TaskQueue(max_size=10)
        t1 = Task(payload="first", priority=1, created_at=1.0)
        t2 = Task(payload="second", priority=1, created_at=2.0)
        q.put(t2)
        q.put(t1)
        assert q.get().payload == "first"
        assert q.get().payload == "second"


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

class TestTaskQueueStats:
    def test_stats_initial(self):
        q = TaskQueue()
        s = q.stats()
        assert s["enqueued"] == 0
        assert s["dequeued"] == 0
        assert s["dropped"] == 0
        assert s["current_size"] == 0

    def test_stats_after_operations(self):
        q = TaskQueue(max_size=2)
        q.put(Task(payload="a"))
        q.put(Task(payload="b"))
        # Queue is now full (size=2); try to overflow — should increment dropped
        try:
            q.put_nowait(Task(payload="overflow"))
        except QueueFullError:
            pass
        q.get()  # dequeue one
        s = q.stats()
        assert s["enqueued"] == 2
        assert s["dequeued"] == 1
        assert s["dropped"] == 1
        assert s["current_size"] == 1


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------

class TestTaskQueueThreadSafety:
    def test_concurrent_producers(self):
        q = TaskQueue(max_size=500)
        errors = []

        def producer(n):
            try:
                for i in range(50):
                    q.put(Task(payload=f"{n}-{i}"))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=producer, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert q.size == 250

    def test_concurrent_consumers(self):
        q = TaskQueue(max_size=100)
        for i in range(100):
            q.put(Task(payload=i))

        results = []
        lock = threading.Lock()

        def consumer():
            try:
                while True:
                    task = q.get_nowait()
                    with lock:
                        results.append(task.payload)
            except QueueEmptyError:
                pass

        threads = [threading.Thread(target=consumer) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 100
        assert sorted(results) == list(range(100))
