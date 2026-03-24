<div align="center">
<img src="assets/hero.svg" width="100%"/>
</div>

# agent-queue

**Priority task queue for multi-agent systems**

[![PyPI version](https://img.shields.io/pypi/v/agent-queue?color=blue&style=flat-square)](https://pypi.org/project/agent-queue/) [![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square)](https://python.org) [![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE) [![Tests](https://img.shields.io/badge/tests-passing-brightgreen?style=flat-square)](#)

---

## The Problem

Without a task queue, agents under load drop work silently, process tasks in arrival order regardless of urgency, and have no back-pressure — a burst of requests causes cascading timeouts rather than graceful queuing.

## Installation

```bash
pip install agent-queue
```

## Quick Start

```python
from agent_queue import DeadLetterQueue, DeduplicatingQueue, QueueFullError

# Initialise
instance = DeadLetterQueue(name="my_agent")

# Use
# see API reference below
print(result)
```

## API Reference

### `DeadLetterQueue`

```python
class DeadLetterQueue:
    """Stores tasks that have exhausted all retries or failed permanently."""
    def __init__(self, maxsize: int = 100) -> None:
    def add(self, task: Task, reason: str) -> None:
        """Add a failed task with an explanatory reason.
    def list(self) -> list[dict]:
        """Return a list of all dead-letter entries (copies)."""
    def count(self) -> int:
        """Number of entries in the dead-letter queue."""
```

### `DeduplicatingQueue`

```python
class DeduplicatingQueue(TaskQueue):
    """
    def __init__(self, max_size: int = 1000) -> None:
    def put(
    def put_nowait(self, task: Task) -> None
```

### `QueueFullError`

```python
class QueueFullError(Exception):
    """Raised when pushing to a full bounded queue."""
```

### `TaskQueue`

```python
class TaskQueue:
    """In-memory priority queue for Task objects.
    def __init__(self, maxsize: int = 0) -> None:
        """
    def push(self, task: Task) -> None:
        """Enqueue a task.
    def pop(self) -> Optional[Task]:
        """Remove and return the highest-priority task, or None if empty."""
    def peek(self) -> Optional[Task]:
        """Return the highest-priority task without removing it, or None."""
```


## How It Works

### Flow

```mermaid
flowchart LR
    A[User Code] -->|create| B[DeadLetterQueue]
    B -->|configure| C[DeduplicatingQueue]
    C -->|execute| D{Success?}
    D -->|yes| E[Return Result]
    D -->|no| F[Error Handler]
    F --> G[Fallback / Retry]
    G --> C
```

### Sequence

```mermaid
sequenceDiagram
    participant App
    participant DeadLetterQueue
    participant DeduplicatingQueue

    App->>+DeadLetterQueue: initialise()
    DeadLetterQueue->>+DeduplicatingQueue: configure()
    DeduplicatingQueue-->>-DeadLetterQueue: ready
    App->>+DeadLetterQueue: run(context)
    DeadLetterQueue->>+DeduplicatingQueue: execute(context)
    DeduplicatingQueue-->>-DeadLetterQueue: result
    DeadLetterQueue-->>-App: WorkflowResult
```

## Philosophy

> *Antya karma* — the final action is determined by the order of deeds; FIFO is dharma applied to tasks.

---

*Part of the [arsenal](https://github.com/darshjme/arsenal) — production stack for LLM agents.*

*Built by [Darshankumar Joshi](https://github.com/darshjme), Gujarat, India.*
