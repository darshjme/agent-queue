"""Task dataclass — the unit of work flowing through agent-queue."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Task:
    """
    A single unit of work for an LLM agent.

    Comparable: higher priority sorts first; ties broken by created_at (FIFO).
    """

    payload: Any
    priority: int = 0
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.monotonic)
    attempts: int = 0

    # ------------------------------------------------------------------
    # Comparison — used by heapq / PriorityQueue internals.
    # Python's heapq is a *min*-heap, so we invert priority so that the
    # highest integer priority is dequeued first.
    # Tie-break on created_at (lower = older = FIFO).
    # ------------------------------------------------------------------

    def _sort_key(self) -> tuple:
        return (-self.priority, self.created_at)

    def __lt__(self, other: "Task") -> bool:
        return self._sort_key() < other._sort_key()

    def __le__(self, other: "Task") -> bool:
        return self._sort_key() <= other._sort_key()

    def __gt__(self, other: "Task") -> bool:
        return self._sort_key() > other._sort_key()

    def __ge__(self, other: "Task") -> bool:
        return self._sort_key() >= other._sort_key()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Task):
            return NotImplemented
        return self._sort_key() == other._sort_key()

    def to_dict(self) -> dict:
        """Serialise the task to a plain dict."""
        return {
            "id": self.id,
            "payload": self.payload,
            "priority": self.priority,
            "created_at": self.created_at,
            "attempts": self.attempts,
        }
