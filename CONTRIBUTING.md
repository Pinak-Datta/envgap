# Contributing

Thanks for helping improve envgap.

envgap is intentionally a practical diagnostic tool, not a configuration framework. Good contributions make broken environment config easier to understand without adding surprising runtime behavior.

## Setup

```console
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

## Run Tests

```console
pytest
```

You can also run the sample broken project:

```console
envgap check examples/basic
```

## Good Issues

The most useful reports include:

- a small `.env`
- a small `.env.example`
- the Python code that reads environment variables
- the envgap output
- what you expected instead

Please redact real API keys, tokens, passwords, and connection strings.

## Scope

In scope:

- clearer diagnostics
- fewer false positives
- Python env usage detection
- `.env` / `.env.example` drift detection
- CI-friendly output
- common framework support when it can be explained clearly

Out of scope:

- loading environment variables for the app
- mutating your shell environment
- becoming a general secrets manager
- replacing framework settings systems

## Pull Requests

Before opening a PR:

```console
pytest
```

For user-facing behavior changes, add or update tests and include a short README or changelog update when useful.

