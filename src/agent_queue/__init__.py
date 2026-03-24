"""
agent-queue: Production task queue for async LLM agent workloads.

Pure stdlib, thread-safe, with priority ordering and deduplication.
"""

from .task import Task
from .queue import TaskQueue, QueueFullError, QueueEmptyError
from .dedup_queue import DeduplicatingQueue
from .worker_pool import WorkerPool

__all__ = [
    "Task",
    "TaskQueue",
    "QueueFullError",
    "QueueEmptyError",
    "DeduplicatingQueue",
    "WorkerPool",
]

__version__ = "0.1.0"
