# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅        |

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Instead, email **security@example.com** with:

- A description of the vulnerability
- Steps to reproduce
- Potential impact

We aim to respond within 72 hours and publish a fix within 14 days.

## Scope

agent-queue is a pure-stdlib, in-process library.  
Attack surface is limited to:

- **Resource exhaustion** — callers control `max_size`; set it appropriately.
- **Payload trust** — `task.payload` is arbitrary Python objects; never deserialise untrusted data without validation.
- **Thread safety** — all public methods are designed for concurrent access; avoid monkey-patching internal state.
