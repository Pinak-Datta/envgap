# Contributing

Thanks for helping improve envgap.

envgap is intentionally a practical diagnostic tool, not a configuration framework. Good contributions make broken environment config easier to understand without adding surprising runtime behavior.

## Where To Start

If you are new to the project, good first contributions are:

- add a failing config example that envgap should explain better
- add tests for a false positive
- improve a diagnostic message or suggested fix
- add support for one small framework pattern
- improve README examples for FastAPI, Django, Docker, or CI users

Good issue searches:

- [good first issue](https://github.com/Pinak-Datta/envgap/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
- [help wanted](https://github.com/Pinak-Datta/envgap/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22)
- [false positives](https://github.com/Pinak-Datta/envgap/issues?q=is%3Aissue+is%3Aopen+label%3Afalse-positive)

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
envgap check examples/fastapi
```

## Useful Reports

The most useful reports include:

- a small `.env`
- a small `.env.example`
- the Python code that reads environment variables
- the envgap output
- what you expected instead

Please redact real API keys, tokens, passwords, and connection strings.

## Small PR Ideas

These are intentionally small enough for a first contribution:

- add one placeholder value envgap should recognize
- add one typo case envgap should catch or avoid
- add one README example for a common config drift bug
- add one test around Pydantic Settings behavior
- improve JSON output docs

If a change touches detection behavior, add or update a test.

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
