# r/Python Draft

Title:

```text
I built envgap, a CLI that finds gaps between .env, .env.example, shell env, and Python code
```

Post:

```text
I built a small open-source Python CLI called envgap.

It checks whether the environment variables your Python app expects match what your project actually defines and documents.

It currently compares:

- shell environment
- .env
- .env.example
- Python code using os.environ / os.getenv

It can report missing keys, duplicate keys, placeholder values like changeme, undocumented extra keys, likely typo pairs like DB_URL vs DATABASE_URL, and code-used variables missing from .env.example.

Install:

pip install envgap
envgap check

The goal is not to load env vars or become a config framework. It is just a practical diagnostic tool for the “why does this work locally but fail in CI/Docker/on another machine?” problem.

Repo: https://github.com/Pinak-Datta/envgap
PyPI: https://pypi.org/project/envgap/

I’d love feedback, especially false positives or patterns from real FastAPI/Django/Flask projects.
```

