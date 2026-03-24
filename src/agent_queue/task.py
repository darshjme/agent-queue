"""Task — a unit of work for multi-agent systems."""

from __future__ import annotations

import time
from typing import Any


class Task:
    """A unit of work with priority, retry logic, and status tracking."""

    def __init__(
        self,
        id: str,
        payload: dict,
        priority: int = 0,
        max_retries: int = 3,
    ) -> None:
        self.id = id
        self.payload = payload
        self.priority = priority
        self.max_retries = max_retries
        self.retries: int = 0
        self.status: str = "pending"
        self.created_at: float = time.time()
        self.error: str | None = None

    @property
    def is_retriable(self) -> bool:
        """True if this task can still be retried."""
        return self.retries < self.max_retries

    def to_dict(self) -> dict:
        """Serialize task to a dictionary."""
        return {
            "id": self.id,
            "payload": self.payload,
            "priority": self.priority,
            "max_retries": self.max_retries,
            "retries": self.retries,
            "status": self.status,
            "created_at": self.created_at,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Deserialize a task from a dictionary."""
        task = cls(
            id=data["id"],
            payload=data["payload"],
            priority=data.get("priority", 0),
            max_retries=data.get("max_retries", 3),
        )
        task.retries = data.get("retries", 0)
        task.status = data.get("status", "pending")
        task.created_at = data.get("created_at", time.time())
        task.error = data.get("error", None)
        return task

    def __repr__(self) -> str:
        return (
            f"Task(id={self.id!r}, priority={self.priority}, "
            f"status={self.status!r}, retries={self.retries}/{self.max_retries})"
        )

    # Comparison for heapq (lower number = lower priority in min-heap,
    # so we negate priority so that higher int = served first)
    def __lt__(self, other: "Task") -> bool:
        if not isinstance(other, Task):
            return NotImplemented
        # Negate priority: higher priority number served first
        # Tie-break by created_at (older tasks served first)
        if self.priority != other.priority:
            return self.priority > other.priority
        return self.created_at < other.created_at

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Task):
            return NotImplemented
        return self.id == other.id
