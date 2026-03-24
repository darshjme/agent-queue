"""
DeduplicatingQueue — TaskQueue that silently drops tasks whose ID is already
present in the queue.

Tracking set is kept in sync with the underlying PriorityQueue via a thin
put/get override.  A threading.Lock guards all mutations.
"""

from __future__ import annotations

import threading
from typing import Optional

from .queue import TaskQueue, QueueFullError
from .task import Task


class DeduplicatingQueue(TaskQueue):
    """
    Priority queue with task-ID deduplication.

    If a task with the same ``id`` already exists anywhere in the queue,
    subsequent puts are silently dropped and ``dedup_hits`` is incremented.
    Once the task is consumed via ``get`` / ``get_nowait``, its ID is removed
    from the tracking set and the same ID may be re-enqueued.
    """

    def __init__(self, max_size: int = 1000) -> None:
        super().__init__(max_size=max_size)
        self._seen_ids: set[str] = set()
        self._dedup_hits: int = 0
        self._dedup_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Overrides
    # ------------------------------------------------------------------

    def put(
        self,
        task: Task,
        block: bool = True,
        timeout: Optional[float] = None,
    ) -> None:
        """Enqueue *task* unless its ID is already present in the queue."""
        with self._dedup_lock:
            if task.id in self._seen_ids:
                self._dedup_hits += 1
                return
            # Reserve the slot *before* we relinquish the lock so that a
            # concurrent put with the same id is also rejected.
            self._seen_ids.add(task.id)

        try:
            super().put(task, block=block, timeout=timeout)
        except QueueFullError:
            # Undo the reservation so the caller can retry later.
            with self._dedup_lock:
                self._seen_ids.discard(task.id)
            raise

    def put_nowait(self, task: Task) -> None:
        self.put(task, block=False)

    def get(
        self,
        block: bool = True,
        timeout: Optional[float] = None,
    ) -> Task:
        task = super().get(block=block, timeout=timeout)
        with self._dedup_lock:
            self._seen_ids.discard(task.id)
        return task

    def get_nowait(self) -> Task:
        return self.get(block=False)

    # ------------------------------------------------------------------
    # Extra API
    # ------------------------------------------------------------------

    def is_duplicate(self, task_id: str) -> bool:
        """Return True if *task_id* is currently tracked in the queue."""
        with self._dedup_lock:
            return task_id in self._seen_ids

    @property
    def dedup_hits(self) -> int:
        """Number of tasks dropped due to duplicate IDs."""
        with self._dedup_lock:
            return self._dedup_hits

    def stats(self) -> dict:
        base = super().stats()
        base["dedup_hits"] = self.dedup_hits
        return base
