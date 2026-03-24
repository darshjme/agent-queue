"""Tests for DeduplicatingQueue."""

import threading

import pytest

from agent_queue import Task, QueueFullError, QueueEmptyError
from agent_queue import DeduplicatingQueue


class TestDeduplicatingQueue:
    def test_basic_put_get(self):
        q = DeduplicatingQueue(max_size=10)
        t = Task(payload="hello", id="t1")
        q.put(t)
        got = q.get()
        assert got.id == "t1"

    def test_duplicate_is_dropped(self):
        q = DeduplicatingQueue(max_size=10)
        t1 = Task(payload="first", id="same-id")
        t2 = Task(payload="second", id="same-id")
        q.put(t1)
        q.put(t2)  # should be silently dropped
        assert q.size == 1

    def test_dedup_hits_counter(self):
        q = DeduplicatingQueue(max_size=10)
        t = Task(payload="x", id="dup")
        q.put(t)
        q.put(Task(payload="y", id="dup"))
        q.put(Task(payload="z", id="dup"))
        assert q.dedup_hits == 2

    def test_is_duplicate_true(self):
        q = DeduplicatingQueue(max_size=10)
        t = Task(payload="x", id="exists")
        q.put(t)
        assert q.is_duplicate("exists") is True

    def test_is_duplicate_false(self):
        q = DeduplicatingQueue(max_size=10)
        assert q.is_duplicate("nonexistent") is False

    def test_id_reusable_after_get(self):
        q = DeduplicatingQueue(max_size=10)
        t1 = Task(payload="first", id="reuse-me")
        q.put(t1)
        q.get()  # removes "reuse-me" from tracking set
        t2 = Task(payload="second", id="reuse-me")
        q.put(t2)  # should succeed now
        assert q.size == 1
        assert q.dedup_hits == 0

    def test_different_ids_all_accepted(self):
        q = DeduplicatingQueue(max_size=20)
        for i in range(10):
            q.put(Task(payload=i, id=str(i)))
        assert q.size == 10

    def test_stats_includes_dedup_hits(self):
        q = DeduplicatingQueue(max_size=10)
        q.put(Task(payload="a", id="x"))
        q.put(Task(payload="b", id="x"))
        s = q.stats()
        assert "dedup_hits" in s
        assert s["dedup_hits"] == 1

    def test_full_queue_does_not_mark_duplicate(self):
        """If a put fails because queue is full, the ID should not be retained."""
        q = DeduplicatingQueue(max_size=1)
        q.put(Task(payload="filler", id="filler"))
        new_task = Task(payload="new", id="new-id")
        with pytest.raises(QueueFullError):
            q.put_nowait(new_task)
        # Now consume filler and retry — should succeed
        q.get()
        q.put(new_task)
        assert q.size == 1

    def test_thread_safe_deduplication(self):
        """Many threads concurrently putting the same ID — only one should land."""
        q = DeduplicatingQueue(max_size=200)
        shared_id = "shared"

        def spammer():
            for _ in range(20):
                q.put(Task(payload="x", id=shared_id))

        threads = [threading.Thread(target=spammer) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert q.size == 1
        total = q.dedup_hits + 1  # one succeeded
        assert total == 200  # 10 threads × 20 puts each
