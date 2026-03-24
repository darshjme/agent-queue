# Contributing to agent-queue

Thank you for your interest in contributing!

## Development Setup

```bash
git clone https://github.com/darshjme-codes/agent-queue
cd agent-queue
pip install -e ".[dev]"
```

## Running Tests

```bash
python -m pytest tests/ -v
```

All tests must pass before submitting a PR.

## Guidelines

- **Zero dependencies** — keep `agent_queue` stdlib-only
- **Python ≥ 3.10** — use modern type hints (`str | None`, etc.)
- **Tests first** — add tests for any new behaviour
- **Docstrings** — public API must have clear docstrings
- **Conventional commits** — `feat:`, `fix:`, `docs:`, `test:`, `refactor:`

## Pull Request Process

1. Fork the repo and create a feature branch
2. Write tests for your change
3. Ensure `python -m pytest` passes with no failures
4. Open a PR with a clear description of what changed and why

## Code of Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
