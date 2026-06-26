# Newsletter Blurb

`envgap` is a new Python CLI that finds gaps between `.env`, `.env.example`, shell environment, and Python code. It detects missing keys, duplicate keys, placeholder values, undocumented variables, likely typos like `DB_URL` vs `DATABASE_URL`, and required env vars used in code but missing from `.env.example`. It is designed as a diagnostic tool for config drift, not another `.env` loader.

Install:

```console
pip install envgap
envgap check
```

GitHub: https://github.com/Pinak-Datta/envgap
PyPI: https://pypi.org/project/envgap/

