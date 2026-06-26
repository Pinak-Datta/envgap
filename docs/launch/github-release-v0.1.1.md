# envgap v0.1.1

First public release of `envgap`: a Python CLI that finds gaps between your app's expected environment variables, `.env`, `.env.example`, shell environment, and Python code.

## Highlights

- Parse `.env` and `.env.example`
- Detect missing, empty, duplicate, placeholder, and undocumented keys
- Detect likely typo pairs like `DB_URL` vs `DATABASE_URL`
- Scan Python code for `os.environ[...]`, `os.getenv(...)`, and `os.environ.get(...)`
- Classify required vs optional env vars
- Show file and line number for code usage
- Explain when a missing `.env` key exists in the shell, which can hide CI/Docker failures
- Provide terminal and JSON output
- Support CI-friendly exits with `--strict` / `--ci`
- Support deterministic checks with `--no-shell`

## Install

```console
pip install envgap
```

## Try It

```console
envgap check
envgap check examples/basic
envgap check --json
envgap check --ci
```

