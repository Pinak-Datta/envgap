# envgap

[![PyPI version](https://img.shields.io/pypi/v/envgap.svg)](https://pypi.org/project/envgap/)
[![Python versions](https://img.shields.io/pypi/pyversions/envgap.svg)](https://pypi.org/project/envgap/)
[![CI](https://github.com/Pinak-Datta/envgap/actions/workflows/ci.yml/badge.svg)](https://github.com/Pinak-Datta/envgap/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Find the gaps in your Python environment config.

`envgap` is a diagnostic CLI for Python projects that use `.env` files, `.env.example`, shell variables, and `os.environ` / `os.getenv` in code. It does not load your config. It shows the gaps between what your app expects, what your project documents, and what your environment actually provides.

![envgap terminal diagnosis screenshot](https://raw.githubusercontent.com/Pinak-Datta/envgap/main/docs/assets/envgap-terminal.svg)

## 30-Second Demo

Given a project with:

```dotenv
# .env
DB_URL=postgres://localhost/app
OPENAI_API_KEY=changeme
```

```python
# app.py
import os

DATABASE_URL = os.environ["DATABASE_URL"]
```

Run:

```console
$ DATABASE_URL=postgres://shell/app envgap check examples/basic

envgap check
===============

Checked:
  shell environment: available (1/4 expected key(s) found)
  .env: found (3 key(s))
  .env.example: found (3 key(s))
  Python code: 3 env usage(s)

Diagnosis:
  DATABASE_URL
    ! Missing value: DATABASE_URL is missing from .env (app.py:3)
      It is present in your shell environment, so local commands may work while CI or Docker still fails.
      Suggested fix: Add DATABASE_URL=... to .env or document how CI/Docker should provide it.

  DB_URL
    ~ Possible typo: DB_URL may be a typo for DATABASE_URL (.env:1)
      Suggested fix: Rename DB_URL to DATABASE_URL if they represent the same setting.
```

## Why

Environment config bugs are boring until they eat an afternoon.

Common examples:

- The app expects `DATABASE_URL`, but `.env` contains `DB_URL`.
- `.env.example` says a key exists, but local `.env` never got it.
- A secret is still set to `changeme`.
- A variable works locally only because it is exported in your shell.
- CI, Docker, or another developer's machine fails because the real required variables are not documented.

`envgap` is for that moment when you want the project to explain itself.

## Install

```console
pip install envgap
```

From a local checkout:

```console
pip install -e ".[dev]"
```

## Quick Start

Run a check in the current project:

```console
envgap check
```

Try the included broken example:

```console
envgap check examples/basic
```

Try a FastAPI-style settings example:

```console
envgap check examples/fastapi
```

Show machine-readable output:

```console
envgap check --json
```

Ignore shell variables for deterministic CI checks:

```console
envgap check --no-shell
```

Fail on warnings as well as errors:

```console
envgap check --strict
```

`--ci` is supported as a CI-friendly alias for `--strict`:

```console
envgap check --ci
```

Use custom dotenv filenames:

```console
envgap check --env-file .env.local --example-file .env.example
```

## What It Checks Today

`envgap check` currently inspects:

- current shell environment
- `.env`
- `.env.example`
- Python files using common environment variable APIs

It detects:

- missing keys
- undocumented extra keys
- duplicate keys
- empty values
- placeholder values like `your-key-here`, `changeme`, `todo`, and `replace-me`
- likely typo pairs like `DB_URL` vs `DATABASE_URL`
- required env vars used in Python code but missing from `.env.example`
- missing `.env`
- missing `.env.example`

It scans Python code for:

```python
os.environ["DATABASE_URL"]
os.getenv("DATABASE_URL")
os.getenv("DATABASE_URL", "sqlite:///local.db")
os.environ.get("DATABASE_URL", "sqlite:///local.db")
```

Required vs optional behavior:

- `os.environ["KEY"]` is required
- `os.getenv("KEY")` is required
- `os.getenv("KEY", default)` is optional
- `os.environ.get("KEY", default)` is optional

## Exit Codes

| Command | Exit code behavior |
| --- | --- |
| `envgap check` | exits `1` when errors are present |
| `envgap check --strict` | exits `1` when errors or warnings are present |
| `envgap check --ci` | same as `--strict` |
| `envgap check --json` | same pass/fail behavior, JSON output |
| `envgap check --no-shell` | ignores current shell variables when diagnosing missing keys |

Warnings do not fail a normal check unless `--strict` or `--ci` is used.

## CI

```yaml
name: envgap

on: [push, pull_request]

jobs:
  envgap:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install envgap
      - run: envgap check --ci
```

## Example Diagnosis

Given:

```dotenv
# .env
DB_URL=postgres://localhost/app
OPENAI_API_KEY=changeme
```

```dotenv
# .env.example
DATABASE_URL=
OPENAI_API_KEY=your-key-here
```

```python
# app.py
import os

DATABASE_URL = os.environ["DATABASE_URL"]
DEBUG = os.getenv("DEBUG", "false")
```

`envgap` can report:

- `DATABASE_URL` is required in code but missing from `.env`
- `DB_URL` may be a typo for `DATABASE_URL`
- `OPENAI_API_KEY` still looks like a placeholder
- `DEBUG` is optional because it has a default

## Why Not Just python-dotenv?

`python-dotenv` loads environment variables.

`envgap` explains whether the environment variables your app expects match the variables your project defines and documents.

The useful question is not only:

> Did `.env` load?

It is:

> What does my app expect, where should it come from, and why is it missing or wrong here?

## Current Scope

This is intentionally a small diagnostic tool, not a config framework.

In scope now:

- `.env`
- `.env.example`
- shell environment
- Python `os.environ` / `os.getenv` scanning
- terminal and JSON reports
- CI-friendly exit codes

Not in scope yet:

- loading or mutating your environment
- validating every framework-specific settings pattern
- Docker Compose parsing
- GitHub Actions secrets parsing
- Pydantic `BaseSettings` extraction

## Roadmap

- Pydantic `BaseSettings` support
- Django settings helper detection
- Docker Compose env detection
- GitHub Actions env/secrets detection
- precedence explanations for shell vs `.env` vs framework defaults
- GitHub Actions annotations
- richer JSON schema for editor and CI integrations

## Development

```console
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Run the example locally:

```console
envgap check examples/basic
```

Run the FastAPI-style example:

```console
envgap check examples/fastapi
```

Run the shell-aware example:

```console
DATABASE_URL=postgres://shell/app envgap check examples/basic
```

## Launch Notes

Release notes and launch post drafts live in [`docs/launch`](docs/launch).

## License

MIT
