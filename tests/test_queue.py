"""Tests for TaskQueue."""

import pytest
from agent_queue import Task, TaskQueue
from agent_queue.queue import QueueFullError


# ── Basic push/pop ────────────────────────────────────────────────────────────

def test_empty_queue():
    q = TaskQueue()
    assert q.empty is True
    assert q.size == 0
    assert q.pop() is None
    assert q.peek() is None


def test_push_single_and_pop():
    q = TaskQueue()
    t = Task("t1", {"a": 1})
    q.push(t)
    assert q.size == 1
    assert q.empty is False
    out = q.pop()
    assert out is t
    assert q.empty is True


def test_priority_ordering():
    """Higher priority tasks should be popped first."""
    q = TaskQueue()
    low = Task("low", {}, priority=0)
    normal = Task("normal", {}, priority=5)
    high = Task("high", {}, priority=10)
    critical = Task("critical", {}, priority=100)

    q.push(low)
    q.push(normal)
    q.push(high)
    q.push(critical)

    assert q.pop().id == "critical"
    assert q.pop().id == "high"
    assert q.pop().id == "normal"
    assert q.pop().id == "low"


def test_fifo_on_equal_priority():
    """Equal-priority tasks must come out in insertion order (FIFO)."""
    import time
    q = TaskQueue()
    t1 = Task("first", {}, priority=5)
    time.sleep(0.001)
    t2 = Task("second", {}, priority=5)
    time.sleep(0.001)
    t3 = Task("third", {}, priority=5)

    q.push(t1)
    q.push(t2)
    q.push(t3)

    assert q.pop().id == "first"
    assert q.pop().id == "second"
    assert q.pop().id == "third"


def test_peek_does_not_remove():
    q = TaskQueue()
    t = Task("t1", {}, priority=5)
    q.push(t)
    assert q.peek() is t
    assert q.size == 1
    assert q.peek() is t  # idempotent


def test_peek_priority_order():
    q = TaskQueue()
    q.push(Task("low", {}, priority=1))
    q.push(Task("high", {}, priority=99))
    assert q.peek().id == "high"


# ── contains / id tracking ────────────────────────────────────────────────────

def test_contains_after_push():
    q = TaskQueue()
    q.push(Task("abc", {}))
    assert q.contains("abc") is True
    assert q.contains("xyz") is False


def test_contains_false_after_pop():
    q = TaskQueue()
    q.push(Task("abc", {}))
    q.pop()
    assert q.contains("abc") is False


# ── maxsize / bounded queue ───────────────────────────────────────────────────

def test_maxsize_respected():
    q = TaskQueue(maxsize=2)
    q.push(Task("t1", {}))
    q.push(Task("t2", {}))
    with pytest.raises(QueueFullError):
        q.push(Task("t3", {}))


def test_maxsize_zero_is_unlimited():
    q = TaskQueue(maxsize=0)
    for i in range(500):
        q.push(Task(f"t{i}", {}))
    assert q.size == 500


def test_push_after_pop_on_bounded_queue():
    q = TaskQueue(maxsize=1)
    q.push(Task("t1", {}))
    q.pop()
    q.push(Task("t2", {}))  # should not raise
    assert q.size == 1


# ── __len__ ───────────────────────────────────────────────────────────────────

def test_len_alias():
    q = TaskQueue()
    assert len(q) == 0
    q.push(Task("t1", {}))
    assert len(q) == 1
