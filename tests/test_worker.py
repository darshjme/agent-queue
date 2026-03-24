"""Tests for QueueWorker."""

import pytest
from agent_queue import Task, TaskQueue, DeadLetterQueue, QueueWorker


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_queue(*tasks: Task) -> TaskQueue:
    q = TaskQueue()
    for t in tasks:
        q.push(t)
    return q


def ok_handler(task: Task) -> None:
    """Always succeeds."""
    task.payload["processed"] = True


def fail_handler(task: Task) -> None:
    """Always raises."""
    raise ValueError("handler error")


# ── process_one ───────────────────────────────────────────────────────────────

def test_process_one_returns_false_on_empty():
    q = TaskQueue()
    worker = QueueWorker(q, ok_handler)
    assert worker.process_one() is False


def test_process_one_returns_true_on_success():
    q = make_queue(Task("t1", {}))
    worker = QueueWorker(q, ok_handler)
    assert worker.process_one() is True
    assert q.empty


def test_process_one_sets_done_status():
    task = Task("t1", {})
    q = make_queue(task)
    worker = QueueWorker(q, ok_handler)
    worker.process_one()
    assert task.status == "done"


def test_process_one_handler_runs():
    task = Task("t1", {})
    q = make_queue(task)
    worker = QueueWorker(q, ok_handler)
    worker.process_one()
    assert task.payload.get("processed") is True


# ── Retry logic ───────────────────────────────────────────────────────────────

def test_failed_task_increments_retries():
    task = Task("t1", {}, max_retries=3)
    q = make_queue(task)
    worker = QueueWorker(q, fail_handler)
    worker.process_one()  # pops, fails, re-queues
    assert task.retries == 1
    assert q.contains("t1")


def test_failed_task_requeued_if_retriable():
    task = Task("t1", {}, max_retries=3)
    q = make_queue(task)
    worker = QueueWorker(q, fail_handler)
    worker.process_one()
    assert q.size == 1


def test_failed_task_status_pending_when_requeued():
    task = Task("t1", {}, max_retries=3)
    q = make_queue(task)
    worker = QueueWorker(q, fail_handler)
    worker.process_one()
    assert task.status == "pending"


def test_exhausted_task_goes_to_dead_letter():
    task = Task("t1", {}, max_retries=2)
    task.retries = 1  # one retry left
    q = make_queue(task)
    dlq = DeadLetterQueue()
    worker = QueueWorker(q, fail_handler, dead_letter=dlq)
    worker.process_one()  # fails, retries == 2 == max_retries → dead
    assert q.empty
    assert dlq.count == 1
    assert task.status == "dead"


def test_exhausted_task_without_dlq():
    """With no DLQ, exhausted tasks are simply dropped (status=failed)."""
    task = Task("t1", {}, max_retries=1)
    task.retries = 0
    q = make_queue(task)
    worker = QueueWorker(q, fail_handler, dead_letter=None)
    worker.process_one()  # fails, retries=1 == max_retries, no DLQ
    assert q.empty
    assert task.status == "failed"


def test_error_stored_on_task():
    task = Task("t1", {}, max_retries=0)
    q = make_queue(task)
    worker = QueueWorker(q, fail_handler)
    worker.process_one()
    assert task.error == "handler error"


# ── process_all ───────────────────────────────────────────────────────────────

def test_process_all_returns_count():
    q = make_queue(Task("t1", {}), Task("t2", {}), Task("t3", {}))
    worker = QueueWorker(q, ok_handler)
    count = worker.process_all()
    assert count == 3
    assert q.empty


def test_process_all_empty_queue():
    worker = QueueWorker(TaskQueue(), ok_handler)
    assert worker.process_all() == 0


def test_process_all_with_failures_and_retries():
    """Tasks that keep failing should eventually exhaust retries."""
    tasks = [Task(f"t{i}", {}, max_retries=1) for i in range(3)]
    q = make_queue(*tasks)
    dlq = DeadLetterQueue()
    worker = QueueWorker(q, fail_handler, dead_letter=dlq)
    count = worker.process_all()
    # Each task fails once: retries becomes 1 == max_retries → dead
    assert q.empty
    assert dlq.count == 3
    assert count == 3  # 3 tasks × 1 attempt each


def test_process_all_mixed_success_failure():
    results = []

    def mixed_handler(task: Task) -> None:
        if task.payload.get("fail"):
            raise RuntimeError("deliberate failure")
        results.append(task.id)

    q = TaskQueue()
    q.push(Task("ok1", {}))
    q.push(Task("bad1", {"fail": True}, max_retries=0))
    q.push(Task("ok2", {}))

    worker = QueueWorker(q, mixed_handler)
    worker.process_all()

    assert "ok1" in results
    assert "ok2" in results
    assert "bad1" not in results
