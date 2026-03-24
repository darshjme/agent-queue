"""Tests for the Task dataclass."""

import time
import uuid

import pytest

from agent_queue import Task


# ---------------------------------------------------------------------------
# Construction & defaults
# ---------------------------------------------------------------------------

class TestTaskDefaults:
    def test_auto_id_is_uuid4(self):
        t = Task(payload="hello")
        parsed = uuid.UUID(t.id, version=4)
        assert str(parsed) == t.id

    def test_unique_ids(self):
        ids = {Task(payload=i).id for i in range(100)}
        assert len(ids) == 100

    def test_default_priority_is_zero(self):
        t = Task(payload="x")
        assert t.priority == 0

    def test_default_attempts_is_zero(self):
        t = Task(payload="x")
        assert t.attempts == 0

    def test_created_at_is_float(self):
        t = Task(payload="x")
        assert isinstance(t.created_at, float)

    def test_created_at_is_recent(self):
        before = time.monotonic()
        t = Task(payload="x")
        after = time.monotonic()
        assert before <= t.created_at <= after

    def test_custom_id(self):
        t = Task(payload="x", id="my-custom-id")
        assert t.id == "my-custom-id"


# ---------------------------------------------------------------------------
# Ordering
# ---------------------------------------------------------------------------

class TestTaskOrdering:
    def test_higher_priority_sorts_first(self):
        low = Task(payload="low", priority=1)
        high = Task(payload="high", priority=10)
        assert high < low   # min-heap: "less" = "dequeued first"

    def test_equal_priority_fifo(self):
        first = Task(payload="first", priority=5, created_at=1.0)
        second = Task(payload="second", priority=5, created_at=2.0)
        assert first < second  # earlier = dequeued first

    def test_sort_key_consistency(self):
        tasks = [
            Task(payload="c", priority=3, created_at=1.0),
            Task(payload="a", priority=10, created_at=1.0),
            Task(payload="b", priority=3, created_at=0.5),
        ]
        sorted_tasks = sorted(tasks)
        assert sorted_tasks[0].payload == "a"   # priority 10
        assert sorted_tasks[1].payload == "b"   # priority 3, earlier
        assert sorted_tasks[2].payload == "c"   # priority 3, later

    def test_heapq_compatible(self):
        import heapq
        heap = []
        for p in [1, 5, 3, 7, 2]:
            heapq.heappush(heap, Task(payload=str(p), priority=p))
        priorities = [heapq.heappop(heap).priority for _ in range(5)]
        assert priorities == sorted([1, 5, 3, 7, 2], reverse=True)


# ---------------------------------------------------------------------------
# to_dict
# ---------------------------------------------------------------------------

class TestTaskToDict:
    def test_to_dict_keys(self):
        t = Task(payload={"key": "value"}, priority=3)
        d = t.to_dict()
        assert set(d.keys()) == {"id", "payload", "priority", "created_at", "attempts"}

    def test_to_dict_values(self):
        t = Task(payload=42, priority=7, id="abc", created_at=99.9, attempts=2)
        d = t.to_dict()
        assert d["id"] == "abc"
        assert d["payload"] == 42
        assert d["priority"] == 7
        assert d["created_at"] == 99.9
        assert d["attempts"] == 2
