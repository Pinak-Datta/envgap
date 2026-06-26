# Show HN: envgap - find gaps in your Python environment config

Hi HN,

I built `envgap`, a small Python CLI that checks whether your app's expected environment variables match what your project actually defines and documents.

It compares:

- shell environment
- `.env`
- `.env.example`
- Python code using `os.environ` / `os.getenv`

It reports things like:

- missing keys
- duplicate keys
- placeholder values like `changeme`
- undocumented extra keys
- likely typos like `DB_URL` vs `DATABASE_URL`
- required env vars used in code but missing from `.env.example`
- cases where something works locally only because the key exists in your shell

Install:

```console
pip install envgap
envgap check
```

The goal is not to become another config framework or `.env` loader. It is a practical diagnostic tool for the annoying "why does config work here but fail in CI/Docker/on another machine?" class of bugs.

Repo: https://github.com/Pinak-Datta/envgap
PyPI: https://pypi.org/project/envgap/

Feedback welcome, especially false positives from real projects.

