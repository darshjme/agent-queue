"""TaskQueue — in-memory priority queue backed by heapq."""

from __future__ import annotations

import heapq
from typing import Optional

from .task import Task


class QueueFullError(Exception):
    """Raised when pushing to a full bounded queue."""


class TaskQueue:
    """In-memory priority queue for Task objects.

    Higher ``priority`` values are served first. FIFO order is preserved
    among tasks with equal priority (older tasks come out first).
    """

    def __init__(self, maxsize: int = 0) -> None:
        """
        Args:
            maxsize: Maximum number of tasks. 0 means unlimited.
        """
        self._maxsize = maxsize
        self._heap: list[Task] = []
        self._id_set: set[str] = set()

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def push(self, task: Task) -> None:
        """Enqueue a task.

        Raises:
            QueueFullError: If maxsize > 0 and the queue is already full.
        """
        if self._maxsize > 0 and len(self._heap) >= self._maxsize:
            raise QueueFullError(
                f"Queue is full (maxsize={self._maxsize})"
            )
        heapq.heappush(self._heap, task)
        self._id_set.add(task.id)

    def pop(self) -> Optional[Task]:
        """Remove and return the highest-priority task, or None if empty."""
        if not self._heap:
            return None
        task = heapq.heappop(self._heap)
        self._id_set.discard(task.id)
        return task

    def peek(self) -> Optional[Task]:
        """Return the highest-priority task without removing it, or None."""
        if not self._heap:
            return None
        return self._heap[0]

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    @property
    def size(self) -> int:
        """Number of tasks currently in the queue."""
        return len(self._heap)

    @property
    def empty(self) -> bool:
        """True when the queue has no tasks."""
        return len(self._heap) == 0

    def contains(self, task_id: str) -> bool:
        """Return True if a task with the given id is in the queue."""
        return task_id in self._id_set

    def __len__(self) -> int:
        return self.size

    def __repr__(self) -> str:
        return f"TaskQueue(size={self.size}, maxsize={self._maxsize})"
