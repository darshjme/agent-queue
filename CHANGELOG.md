# Changelog

All notable changes to **agent-queue** are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

_Nothing pending._

---

## [0.1.0] — 2026-03-24

### Added

- **`Task`** dataclass with auto UUID4 id, monotonic `created_at`, configurable `priority`, and `attempts` counter.
- **`TaskQueue`** — bounded, thread-safe priority queue backed by `queue.PriorityQueue`.  Exposes `put`, `put_nowait`, `get`, `get_nowait`, `size`, `is_empty`, `is_full`, and `stats()`.
- **`QueueFullError`** / **`QueueEmptyError`** — typed exceptions replacing the raw stdlib errors.
- **`DeduplicatingQueue`** — `TaskQueue` subclass that silently drops tasks whose `id` is already present in the queue. Tracks `dedup_hits` and exposes `is_duplicate(task_id)`.
- **`WorkerPool`** — fixed-size thread pool consuming from any `TaskQueue`. Supports `start()`, `stop(wait=True/False)`, `is_running`, and `stats()`.
- Full pytest test suite (22+ tests).
- Zero runtime dependencies — pure Python stdlib (`queue`, `threading`, `uuid`, `dataclasses`).

[Unreleased]: https://github.com/example/agent-queue/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/example/agent-queue/releases/tag/v0.1.0
