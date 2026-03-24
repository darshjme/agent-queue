# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | ✅ Yes     |

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Email: darshjme@gmail.com

Include:
- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fix (optional)

You will receive a response within 72 hours. If confirmed, a patch will be released within 14 days and you will be credited in the changelog (unless you prefer anonymity).

## Scope

`agent-queue` is a pure in-memory library with no network I/O, no file system access beyond explicit serialization calls by the user, and zero external dependencies. The primary security concern is safe deserialization: always validate `Task.from_dict()` input when loading from untrusted sources.
