"""
WorkerPool — fixed-size thread pool that consumes tasks from a TaskQueue.

Workers run *worker_func(task)* in a loop until stop() is called.
Exceptions inside worker_func are caught, logged to stderr, and counted —
the worker thread survives and continues processing.
"""

from __future__ import annotations

import sys
import threading
import time
from typing import Callable

from .queue import TaskQueue, QueueEmptyError
from .task import Task

# Sentinel placed on the queue to wake up blocked workers during stop().
_STOP_SENTINEL = object()


class WorkerPool:
    """
    Fixed-size thread pool consuming tasks from a :class:`TaskQueue`.

    Example::

        pool = WorkerPool(queue, my_handler, num_workers=8)
        pool.start()
        # ... produce tasks ...
        pool.stop()
    """

    def __init__(
        self,
        queue: TaskQueue,
        worker_func: Callable[[Task], None],
        num_workers: int = 4,
    ) -> None:
        if num_workers < 1:
            raise ValueError("num_workers must be >= 1")
        self._queue = queue
        self._worker_func = worker_func
        self._num_workers = num_workers

        self._threads: list[threading.Thread] = []
        self._stop_event = threading.Event()
        self._start_time: float | None = None

        # Stats
        self._lock = threading.Lock()
        self._tasks_processed: int = 0
        self._tasks_failed: int = 0

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Spawn worker threads and begin consuming the queue."""
        if self._threads:
            raise RuntimeError("WorkerPool is already running")
        self._stop_event.clear()
        self._start_time = time.monotonic()
        for i in range(self._num_workers):
            t = threading.Thread(
                target=self._worker_loop,
                name=f"agent-queue-worker-{i}",
                daemon=True,
            )
            t.start()
            self._threads.append(t)

    def stop(self, wait: bool = True) -> None:
        """
        Signal all workers to stop.

        If *wait* is True (default) block until every worker thread exits.
        If *wait* is False return immediately (workers finish their current
        task and then exit on their own).
        """
        self._stop_event.set()
        if wait:
            for t in self._threads:
                t.join()
        self._threads.clear()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_running(self) -> bool:
        """True while at least one worker thread is alive."""
        return any(t.is_alive() for t in self._threads)

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def stats(self) -> dict:
        uptime = (
            time.monotonic() - self._start_time
            if self._start_time is not None
            else 0.0
        )
        with self._lock:
            return {
                "workers_active": sum(1 for t in self._threads if t.is_alive()),
                "tasks_processed": self._tasks_processed,
                "tasks_failed": self._tasks_failed,
                "uptime_seconds": round(uptime, 3),
            }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _worker_loop(self) -> None:
        """Main loop executed by each worker thread."""
        while not self._stop_event.is_set():
            try:
                task: Task = self._queue.get(block=True, timeout=0.1)
            except QueueEmptyError:
                # Timeout — loop back and check stop_event.
                continue

            try:
                self._worker_func(task)
                with self._lock:
                    self._tasks_processed += 1
            except Exception as exc:  # noqa: BLE001
                with self._lock:
                    self._tasks_failed += 1
                print(
                    f"[WorkerPool] worker_func raised {type(exc).__name__}: {exc}",
                    file=sys.stderr,
                )
            finally:
                try:
                    self._queue.task_done()
                except Exception:  # noqa: BLE001
                    pass
