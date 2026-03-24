"""
TaskQueue — thread-safe priority task queue backed by stdlib queue.PriorityQueue.

Uses a thin wrapper so callers work with Task objects directly instead of
(priority, counter, task) tuples.
"""

from __future__ import annotations

import queue
import threading
from typing import Optional

from .task import Task


class QueueFullError(Exception):
    """Raised by put_nowait when the queue has reached max_size."""


class QueueEmptyError(Exception):
    """Raised by get_nowait when the queue is empty."""


class TaskQueue:
    """
    Thread-safe, bounded priority queue for Task objects.

    Priority ordering: higher ``task.priority`` values are dequeued first.
    Equal-priority tasks are ordered FIFO (by task.created_at).
    """

    def __init__(self, max_size: int = 1000) -> None:
        if max_size < 1:
            raise ValueError("max_size must be >= 1")
        self._max_size = max_size
        self._pq: queue.PriorityQueue = queue.PriorityQueue(maxsize=max_size)
        self._lock = threading.Lock()

        # Stats counters — protected by _lock
        self._enqueued: int = 0
        self._dequeued: int = 0
        self._dropped: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def put(
        self,
        task: Task,
        block: bool = True,
        timeout: Optional[float] = None,
    ) -> None:
        """
        Enqueue *task*.

        If *block* is True and the queue is full, block until space is
        available (or *timeout* seconds elapse, raising QueueFullError).
        """
        try:
            self._pq.put(task, block=block, timeout=timeout)
        except queue.Full as exc:
            with self._lock:
                self._dropped += 1
            raise QueueFullError(
                f"Queue is full (max_size={self._max_size})"
            ) from exc
        with self._lock:
            self._enqueued += 1

    def put_nowait(self, task: Task) -> None:
        """Enqueue without blocking; raises QueueFullError if full."""
        self.put(task, block=False)

    def get(
        self,
        block: bool = True,
        timeout: Optional[float] = None,
    ) -> Task:
        """
        Dequeue the highest-priority task.

        Blocks if empty (when *block* is True), raising QueueEmptyError on
        timeout or when non-blocking and the queue is empty.
        """
        try:
            task: Task = self._pq.get(block=block, timeout=timeout)
        except queue.Empty as exc:
            raise QueueEmptyError("Queue is empty") from exc
        with self._lock:
            self._dequeued += 1
        return task

    def get_nowait(self) -> Task:
        """Dequeue without blocking; raises QueueEmptyError if empty."""
        return self.get(block=False)

    def task_done(self) -> None:
        """Signal that a formerly enqueued task is complete (mirrors stdlib)."""
        self._pq.task_done()

    def join(self) -> None:
        """Block until all items have been processed (mirrors stdlib)."""
        self._pq.join()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def size(self) -> int:
        """Current number of items in the queue."""
        return self._pq.qsize()

    @property
    def is_empty(self) -> bool:
        return self._pq.empty()

    @property
    def is_full(self) -> bool:
        return self._pq.full()

    @property
    def max_size(self) -> int:
        return self._max_size

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def stats(self) -> dict:
        """Return a snapshot of queue metrics."""
        with self._lock:
            return {
                "enqueued": self._enqueued,
                "dequeued": self._dequeued,
                "dropped": self._dropped,
                "current_size": self.size,
            }
