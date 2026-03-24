# Contributing to agent-queue

Thank you for your interest in improving **agent-queue**!

## Development setup

```bash
git clone https://github.com/example/agent-queue.git
cd agent-queue
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Running tests

```bash
python -m pytest tests/ -v
```

All tests must pass before opening a PR.

## Code style

- Follow PEP 8.
- Type-annotate all public functions and methods.
- Keep zero runtime dependencies — stdlib only.

## Submitting changes

1. Fork the repo and create a feature branch.
2. Write tests that cover your change.
3. Update `CHANGELOG.md` under `[Unreleased]`.
4. Open a pull request with a clear description.

## Reporting bugs

Open a GitHub issue. Include Python version, OS, and a minimal reproducible example.
