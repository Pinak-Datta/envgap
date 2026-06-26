# envdoctor

envdoctor explains why your Python environment config is broken.

It is not another `.env` loader. It is a diagnostic CLI for missing, duplicated, placeholder, undocumented, and misnamed environment variables across `.env`, `.env.example`, and Python code.

```console
$ envdoctor check
envdoctor check
===============

Checked:
  shell environment: available (0/3 expected key(s) found)
  .env: found
  .env.example: found
  Python code: 3 env usage(s)

Diagnosis:
  DATABASE_URL
    ! Missing value: DATABASE_URL is missing from .env (settings.py:2)
      DATABASE_URL is required by os.environ["DATABASE_URL"] in settings.py:2 but was not found in .env.
      Checked:
        shell environment: not found
        .env: not found
        .env.example: found
      Suggested fix: Add DATABASE_URL=... to .env.

  DB_URL
    ~ Possible typo: DB_URL may be a typo for DATABASE_URL (.env:1)
      .env contains DB_URL, but the expected variable is DATABASE_URL.
      Suggested fix: Rename DB_URL to DATABASE_URL if they represent the same setting.
```

## Install

```console
pip install envdoctor
```

From a checkout:

```console
pip install -e ".[dev]"
```

## Usage

Run a check in the current project:

```console
envdoctor check
```

Check another directory:

```console
envdoctor check path/to/project
```

Use custom dotenv filenames:

```console
envdoctor check --env-file .env.local --example-file .env.example
```

Emit JSON:

```console
envdoctor check --json
```

Fail CI on warnings as well as errors:

```console
envdoctor check --strict
```

`--ci` is also supported as a CI-friendly alias:

```console
envdoctor check --ci
```

## What v0 Checks

- Parses `.env`
- Parses `.env.example`
- Detects missing keys
- Detects extra or undocumented keys
- Detects duplicate keys
- Detects empty values
- Detects placeholders like `your-key-here`, `changeme`, and `todo`
- Masks secret-like placeholder values in output
- Detects similar-name typos like `DB_URL` vs `DATABASE_URL`
- Checks whether missing values are present in the current shell environment
- Scans Python AST for `os.environ["KEY"]`, `os.getenv("KEY")`, `os.getenv("KEY", default)`, and `os.environ.get("KEY", default)`
- Reports Python file and line number
- Returns non-zero exit codes when errors are present
- Supports `--strict` / `--ci` to fail on warnings too

## CI

```yaml
name: envdoctor

on: [push, pull_request]

jobs:
  envdoctor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install envdoctor
      - run: envdoctor check --ci
```

## Try The Example

```console
envdoctor check examples/basic
```

## Why Not Just python-dotenv?

`python-dotenv` loads environment variables. envdoctor explains why the variables your app expects do not match the variables your project documents and defines.

The useful question is not only "did `.env` load?" It is:

- Which variables does my app expect?
- Which variables are missing locally?
- Which variables are present but undocumented?
- Which values are placeholders?
- Which names are probably typos?
- Which code usage is missing from `.env.example`?

## Roadmap

- Pydantic `BaseSettings` extraction
- Django settings helpers
- Docker Compose and GitHub Actions env detection
- Precedence explanations for shell vs dotenv vs framework defaults
- GitHub Actions annotations
- Richer JSON schema for editor and CI integrations

## Development

```console
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## License

MIT
