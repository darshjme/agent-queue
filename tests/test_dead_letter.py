"""Tests for DeadLetterQueue."""

import pytest
from agent_queue import Task, DeadLetterQueue


def _task(tid="t1") -> Task:
    t = Task(tid, {"x": 1})
    t.retries = 3
    t.status = "failed"
    t.error = "boom"
    return t


def test_add_and_count():
    dlq = DeadLetterQueue()
    assert dlq.count == 0
    dlq.add(_task("t1"), "handler raised ValueError")
    assert dlq.count == 1


def test_list_returns_copies():
    dlq = DeadLetterQueue()
    t = _task("t1")
    dlq.add(t, "reason A")
    entries = dlq.list()
    assert len(entries) == 1
    assert entries[0]["reason"] == "reason A"
    assert "task" in entries[0]
    assert "failed_at" in entries[0]


def test_add_sets_task_status_dead():
    dlq = DeadLetterQueue()
    t = _task("t1")
    dlq.add(t, "permanent failure")
    assert t.status == "dead"


def test_clear():
    dlq = DeadLetterQueue()
    dlq.add(_task("t1"), "r1")
    dlq.add(_task("t2"), "r2")
    assert dlq.count == 2
    dlq.clear()
    assert dlq.count == 0
    assert dlq.list() == []


def test_maxsize_evicts_oldest():
    dlq = DeadLetterQueue(maxsize=3)
    for i in range(3):
        dlq.add(_task(f"t{i}"), f"reason {i}")
    assert dlq.count == 3

    dlq.add(_task("t_new"), "overflow")
    assert dlq.count == 3  # still 3
    ids = [e["task"]["id"] for e in dlq.list()]
    assert "t0" not in ids       # oldest evicted
    assert "t_new" in ids        # newest present


def test_list_is_independent_copy():
    dlq = DeadLetterQueue()
    dlq.add(_task("t1"), "r")
    entries = dlq.list()
    entries.clear()  # mutating result should not affect dlq
    assert dlq.count == 1


def test_multiple_entries_same_task_id():
    """DLQ does not deduplicate — same task can appear multiple times."""
    dlq = DeadLetterQueue()
    dlq.add(_task("same"), "first")
    dlq.add(_task("same"), "second")
    assert dlq.count == 2
