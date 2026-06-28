# envgap

[![PyPI version](https://img.shields.io/pypi/v/envgap.svg)](https://pypi.org/project/envgap/)
[![Python versions](https://img.shields.io/pypi/pyversions/envgap.svg)](https://pypi.org/project/envgap/)
[![CI](https://github.com/Pinak-Datta/envgap/actions/workflows/ci.yml/badge.svg)](https://github.com/Pinak-Datta/envgap/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Find gaps between `.env`, `.env.example`, shell variables, and Python code.

`envgap` is a diagnostic CLI for Python projects that use `.env` files, `.env.example`, shell variables, and `os.environ` / `os.getenv` in code. It does not load your config. It shows the gaps between what your app expects, what your project documents, and what your environment actually provides.

New in v0.2: envgap detects Pydantic `BaseSettings` fields for FastAPI-style projects.

![envgap animated terminal demo](https://raw.githubusercontent.com/Pinak-Datta/envgap/main/docs/assets/envgap-demo.gif)

## Why Developers Try It

- Catch missing env vars before CI, Docker, or another developer's machine fails.
- Spot stale `.env.example` files that no longer match real code.
- Find typo-shaped drift like `DB_URL` vs `DATABASE_URL`.
- Detect placeholder secrets such as `changeme`, `todo`, and `your-key-here`.
- Add a lightweight config check to CI without adopting a new settings framework.

`envgap` is intentionally not a `.env` loader. It is the tool you run when you want the project to explain why config works in one place and breaks somewhere else.

## Contents

- [30-Second Demo](#30-second-demo)
- [When It Helps](#when-it-helps)
- [Why](#why)
- [Install](#install)
- [Quick Start](#quick-start)
- [What It Checks Today](#what-it-checks-today)
- [Exit Codes](#exit-codes)
- [CI](#ci)
- [Example Diagnosis](#example-diagnosis)
- [Why Not Just python-dotenv?](#why-not-just-python-dotenv)
- [Current Scope](#current-scope)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Development](#development)

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

## When It Helps

Use envgap when a Python project has config spread across:

- local `.env`
- documented `.env.example`
- shell exports
- Python code
- CI or Docker conventions

It is especially useful for Python backend projects, FastAPI/Django/Flask apps, AI/data apps with API keys, and open-source projects where `.env.example` must stay useful for new contributors.

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
- Pydantic `BaseSettings` fields used by FastAPI-style settings modules

It detects:

- missing keys
- undocumented extra keys
- duplicate keys
- empty values
- placeholder values like `your-key-here`, `changeme`, `todo`, and `replace-me`
- likely typo pairs like `DB_URL` vs `DATABASE_URL`
- required env vars used in Python code but missing from `.env.example`
- required Pydantic settings fields missing from `.env` or `.env.example`
- missing `.env`
- missing `.env.example`

It scans Python code for:

```python
os.environ["DATABASE_URL"]
os.getenv("DATABASE_URL")
os.getenv("DATABASE_URL", "sqlite:///local.db")
os.environ.get("DATABASE_URL", "sqlite:///local.db")
```

It also scans Pydantic Settings classes:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    openai_api_key: str
    debug: bool = False
```

Required vs optional behavior:

- `os.environ["KEY"]` is required
- `os.getenv("KEY")` is required
- `os.getenv("KEY", default)` is optional
- `os.environ.get("KEY", default)` is optional
- `BaseSettings` fields without defaults are required
- `BaseSettings` fields with defaults are optional

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

## How envgap Differs from Other Tools

| Tool | Purpose | How envgap differs |
|------|---------|--------------------|
| python-dotenv | Loads `.env` files | envgap diagnoses drift between code, `.env`, `.env.example`, and shell variables. |
| pydantic-settings | Validates application settings | envgap diagnoses configuration drift instead of validating settings. |
| django-environ | Reads environment configuration for Django | envgap is framework-independent and diagnoses configuration drift. |
| Secret scanners | Detect leaked secrets | envgap finds missing or inconsistent configuration rather than exposed secrets. |

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
- validating every framework-specific settings edge case
- Docker Compose parsing
- GitHub Actions secrets parsing
- Pydantic aliases, prefixes, and nested settings

## Roadmap

- Pydantic aliases, prefixes, and nested settings
- Django settings helper detection
- Docker Compose env detection
- GitHub Actions env/secrets detection
- precedence explanations for shell vs `.env` vs framework defaults
- GitHub Actions annotations
- richer JSON schema for editor and CI integrations

See the [full roadmap](docs/ROADMAP.md).

## Contributing

Real-world config examples are the most useful contribution right now.

New contributors can start with [good first issues](https://github.com/Pinak-Datta/envgap/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22), [help wanted issues](https://github.com/Pinak-Datta/envgap/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22), or false positives from their own Python projects.

Good first contributions:

- report a false positive with a tiny redacted example
- add a missing framework pattern
- improve docs for CI, FastAPI, Django, or Docker users
- add tests for typo detection edge cases

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SUPPORT.md](SUPPORT.md).

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

## License

MIT
