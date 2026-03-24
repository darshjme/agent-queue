# agent-queue

**Priority task queue for multi-agent systems.**

Zero dependencies. Pure Python (≥3.10). Built on `heapq`.

---

## Why?

Multi-agent systems generate tasks faster than they can execute them.  
Without a queue, tasks get lost, priorities ignored, and work duplicated.

`agent-queue` gives you:
- ✅ **Priority ordering** — critical > high > normal > low (any int)
- ✅ **FIFO tie-breaking** — equal-priority tasks in insertion order
- ✅ **Dead-letter handling** — permanently failed tasks go to DLQ
- ✅ **Retry tracking** — automatic re-queue with configurable max retries
- ✅ **Status lifecycle** — `pending → running → done / failed / dead`
- ✅ **Bounded queues** — optional maxsize with `QueueFullError`
- ✅ **Serialization** — `to_dict()` / `from_dict()` for persistence

---

## Install

```bash
pip install agent-queue
```

---

## Quick Start — Multi-Agent Task Dispatch

```python
import time
from agent_queue import Task, TaskQueue, DeadLetterQueue, QueueWorker

# ── 1. Create infrastructure ──────────────────────────────────────────────────
queue = TaskQueue(maxsize=1000)
dlq   = DeadLetterQueue(maxsize=500)

# ── 2. Define a handler (the actual work) ─────────────────────────────────────
def dispatch_to_agent(task: Task) -> None:
    agent_id = task.payload.get("agent")
    prompt   = task.payload.get("prompt")
    print(f"[Agent {agent_id}] Processing: {prompt!r}")
    # ... call your LLM, run a subprocess, post to an API, etc.
    time.sleep(0.01)   # simulate work

worker = QueueWorker(queue, dispatch_to_agent, dead_letter=dlq)

# ── 3. Agents push tasks with different priorities ────────────────────────────
# Priority levels (any int — higher = served first):
#   100 = critical, 10 = high, 5 = normal, 1 = low

queue.push(Task("report-gen",     {"agent": "writer",  "prompt": "Write Q1 report"},   priority=5))
queue.push(Task("alert-handler",  {"agent": "monitor", "prompt": "Check system health"}, priority=100))
queue.push(Task("email-draft",    {"agent": "comms",   "prompt": "Draft newsletter"},  priority=1))
queue.push(Task("code-review",    {"agent": "coder",   "prompt": "Review PR #42"},     priority=10))

print(f"Queue size: {queue.size}")
print(f"Next up:    {queue.peek()}")

# ── 4. Process all tasks in priority order ────────────────────────────────────
processed = worker.process_all()
print(f"\nProcessed {processed} tasks")

# ── 5. Inspect dead-letter queue ──────────────────────────────────────────────
if dlq.count:
    print(f"\nFailed tasks ({dlq.count}):")
    for entry in dlq.list():
        print(f"  - {entry['task']['id']}: {entry['reason']}")
```

**Output:**
```
Queue size: 4
Next up:    Task(id='alert-handler', priority=100, status='pending', retries=0/3)

[Agent monitor] Processing: 'Check system health'
[Agent coder]   Processing: 'Review PR #42'
[Agent writer]  Processing: 'Write Q1 report'
[Agent comms]   Processing: 'Draft newsletter'

Processed 4 tasks
```

---

## API Reference

### `Task`

```python
Task(id: str, payload: dict, priority: int = 0, max_retries: int = 3)
```

| Field | Type | Description |
|---|---|---|
| `id` | `str` | Unique task identifier |
| `payload` | `dict` | Arbitrary task data |
| `priority` | `int` | Higher = served first |
| `max_retries` | `int` | Max retry attempts |
| `retries` | `int` | Current retry count |
| `status` | `str` | `pending / running / done / failed / dead` |
| `created_at` | `float` | Unix timestamp |
| `error` | `str \| None` | Last exception message |
| `is_retriable` | `bool` | `retries < max_retries` |

```python
task.to_dict()          # → dict
Task.from_dict(data)    # → Task
```

### `TaskQueue`

```python
q = TaskQueue(maxsize=0)   # 0 = unlimited

q.push(task)               # enqueue; raises QueueFullError if bounded+full
q.pop()                    # → Task | None (highest priority first)
q.peek()                   # → Task | None (no removal)
q.contains("task-id")      # → bool
q.size                     # → int
q.empty                    # → bool
len(q)                     # alias for q.size
```

### `DeadLetterQueue`

```python
dlq = DeadLetterQueue(maxsize=100)

dlq.add(task, reason="handler raised ValueError")
dlq.list()   # → list[dict]  (each: {task, reason, failed_at})
dlq.count    # → int
dlq.clear()
```

### `QueueWorker`

```python
worker = QueueWorker(queue, handler, dead_letter=dlq)

worker.process_one()   # → bool (True if a task was processed)
worker.process_all()   # → int  (count of tasks processed)
```

**Retry flow:**

```
handler(task) raises
  → task.retries += 1
  → task.is_retriable?
      YES → re-queue (status = "pending")
      NO  → dead_letter.add(task, reason) if DLQ else drop (status = "failed")
```

---

## Serialization Example (Persistence)

```python
import json
from agent_queue import Task

task = Task("t1", {"prompt": "hello"}, priority=10)
data = task.to_dict()

# Save to Redis / Postgres / file
json_str = json.dumps(data)

# Restore later
task2 = Task.from_dict(json.loads(json_str))
assert task2.id == task.id
```

---

## License

MIT
