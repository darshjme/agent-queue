"""agent-queue: Priority task queue for multi-agent systems."""

from .task import Task
from .queue import TaskQueue
from .dead_letter import DeadLetterQueue
from .worker import QueueWorker

__all__ = ["Task", "TaskQueue", "DeadLetterQueue", "QueueWorker"]
__version__ = "1.0.0"
