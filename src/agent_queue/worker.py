"""QueueWorker — processes tasks from a TaskQueue."""

from __future__ import annotations

from typing import Callable, Optional

from .dead_letter import DeadLetterQueue
from .queue import TaskQueue
from .task import Task


class QueueWorker:
    """Processes tasks from a TaskQueue using a user-supplied handler.

    On handler success: task status is set to "done".
    On handler exception:
        - Increments task.retries
        - If task.is_retriable: re-queues with status "pending"
        - Else: sends to dead_letter queue (if provided) with status "dead"
    """

    def __init__(
        self,
        queue: TaskQueue,
        handler: Callable[[Task], None],
        dead_letter: Optional[DeadLetterQueue] = None,
    ) -> None:
        self._queue = queue
        self._handler = handler
        self._dead_letter = dead_letter

    def process_one(self) -> bool:
        """Process the next task in the queue.

        Returns:
            True if a task was processed (success or failure), False if empty.
        """
        task = self._queue.pop()
        if task is None:
            return False

        task.status = "running"
        try:
            self._handler(task)
            task.status = "done"
        except Exception as exc:
            task.retries += 1
            task.error = str(exc)

            if task.is_retriable:
                task.status = "pending"
                self._queue.push(task)
            else:
                task.status = "failed"
                if self._dead_letter is not None:
                    self._dead_letter.add(task, reason=str(exc))

        return True

    def process_all(self) -> int:
        """Drain the queue, processing every task.

        Returns:
            Number of tasks processed.
        """
        count = 0
        while self.process_one():
            count += 1
        return count

    def __repr__(self) -> str:
        return (
            f"QueueWorker(queue_size={self._queue.size}, "
            f"dead_letter={self._dead_letter is not None})"
        )
