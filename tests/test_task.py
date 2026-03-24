"""Tests for Task."""

import time
import pytest
from agent_queue import Task


# ── Construction ──────────────────────────────────────────────────────────────

def test_task_defaults():
    t = Task("t1", {"action": "ping"})
    assert t.id == "t1"
    assert t.payload == {"action": "ping"}
    assert t.priority == 0
    assert t.max_retries == 3
    assert t.retries == 0
    assert t.status == "pending"
    assert t.error is None
    assert isinstance(t.created_at, float)


def test_task_custom_priority_and_retries():
    t = Task("t2", {}, priority=10, max_retries=5)
    assert t.priority == 10
    assert t.max_retries == 5


# ── is_retriable ──────────────────────────────────────────────────────────────

def test_is_retriable_initially_true():
    t = Task("t3", {}, max_retries=3)
    assert t.is_retriable is True


def test_is_retriable_false_when_exhausted():
    t = Task("t4", {}, max_retries=2)
    t.retries = 2
    assert t.is_retriable is False


def test_is_retriable_boundary():
    t = Task("t5", {}, max_retries=1)
    t.retries = 0
    assert t.is_retriable is True
    t.retries = 1
    assert t.is_retriable is False


# ── Serialization ─────────────────────────────────────────────────────────────

def test_to_dict_round_trip():
    t = Task("t6", {"key": "value"}, priority=5, max_retries=2)
    t.retries = 1
    t.status = "running"
    t.error = "oops"

    d = t.to_dict()
    assert d["id"] == "t6"
    assert d["payload"] == {"key": "value"}
    assert d["priority"] == 5
    assert d["max_retries"] == 2
    assert d["retries"] == 1
    assert d["status"] == "running"
    assert d["error"] == "oops"
    assert isinstance(d["created_at"], float)


def test_from_dict_restores_all_fields():
    original = Task("t7", {"x": 1}, priority=3, max_retries=4)
    original.retries = 2
    original.status = "failed"
    original.error = "bad"

    restored = Task.from_dict(original.to_dict())
    assert restored.id == original.id
    assert restored.payload == original.payload
    assert restored.priority == original.priority
    assert restored.max_retries == original.max_retries
    assert restored.retries == original.retries
    assert restored.status == original.status
    assert restored.error == original.error
    assert restored.created_at == pytest.approx(original.created_at)


def test_from_dict_defaults():
    d = {"id": "t8", "payload": {}}
    t = Task.from_dict(d)
    assert t.priority == 0
    assert t.max_retries == 3
    assert t.retries == 0
    assert t.status == "pending"
    assert t.error is None


# ── Comparison ────────────────────────────────────────────────────────────────

def test_higher_priority_less_than():
    """Higher priority task should come first in heapq (lt returns True)."""
    low = Task("low", {}, priority=0)
    high = Task("high", {}, priority=10)
    # high < low in heap terms means high comes out first
    assert high < low


def test_equal_priority_fifo_order():
    t1 = Task("t1", {}, priority=5)
    time.sleep(0.001)
    t2 = Task("t2", {}, priority=5)
    # t1 created first → should come first
    assert t1 < t2


def test_task_equality_by_id():
    t1 = Task("same-id", {}, priority=5)
    t2 = Task("same-id", {}, priority=99)
    assert t1 == t2


def test_task_inequality():
    t1 = Task("id-a", {})
    t2 = Task("id-b", {})
    assert t1 != t2
