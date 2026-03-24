"""DeadLetterQueue — stores permanently failed tasks."""

from __future__ import annotations

import time
from typing import Any

from .task import Task


class DeadLetterQueue:
    """Stores tasks that have exhausted all retries or failed permanently."""

    def __init__(self, maxsize: int = 100) -> None:
        self._maxsize = maxsize
        self._entries: list[dict] = []

    def add(self, task: Task, reason: str) -> None:
        """Add a failed task with an explanatory reason.

        If maxsize is reached, the oldest entry is evicted (FIFO eviction).
        """
        entry = {
            "task": task.to_dict(),
            "reason": reason,
            "failed_at": time.time(),
        }
        if self._maxsize > 0 and len(self._entries) >= self._maxsize:
            self._entries.pop(0)  # evict oldest
        self._entries.append(entry)
        task.status = "dead"

    def list(self) -> list[dict]:
        """Return a list of all dead-letter entries (copies)."""
        return list(self._entries)

    @property
    def count(self) -> int:
        """Number of entries in the dead-letter queue."""
        return len(self._entries)

    def clear(self) -> None:
        """Remove all entries."""
        self._entries.clear()

    def __repr__(self) -> str:
        return f"DeadLetterQueue(count={self.count}, maxsize={self._maxsize})"
