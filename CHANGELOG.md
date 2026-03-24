# Changelog

All notable changes to `agent-queue` are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)  
Versioning: [Semantic Versioning](https://semver.org/)

---

## [1.0.0] — 2026-03-24

### Added
- `Task` — unit of work with id, payload, priority, retry tracking, status lifecycle, and serialization
- `TaskQueue` — in-memory heapq-backed priority queue with O(log n) push/pop
- `DeadLetterQueue` — bounded store for permanently failed tasks with FIFO eviction
- `QueueWorker` — single-threaded task processor with automatic retry and dead-letter routing
- `QueueFullError` for bounded queue overflow
- Zero external dependencies; requires Python ≥ 3.10
- 45 pytest tests with 100% pass rate
