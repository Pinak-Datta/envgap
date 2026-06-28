# Roadmap

envgap should stay small, practical, and diagnostic. The goal is to explain environment config drift, not become another settings framework.

## Done: v0.2 Framework-Aware Python Detection

- Detect Pydantic `BaseSettings` classes.
- Infer required fields from annotations without defaults.
- Treat fields with defaults as optional.
- Convert field names such as `database_url` to `DATABASE_URL`.
- Add a FastAPI/Pydantic example project.

## v0.3: Deployment Drift

- Detect Docker Compose `environment` and `env_file` usage.
- Explain local `.env` vs Docker-provided env differences.
- Add CI examples for GitHub Actions.
- Add GitHub Actions annotations for inline CI feedback.
- Document false-positive limits clearly.

## v0.4: Framework Helpers

- Detect common Django settings patterns.
- Improve Flask/FastAPI examples.
- Add support for common env aliases and prefixes.

## Later

- Richer JSON schema for editor integrations.
- Config file for project-specific ignores.
- More precise typo matching with fewer false positives.
- Documentation pages with real config-drift recipes.

## Not Planned

- Loading environment variables for your app.
- Writing or mutating `.env` files automatically.
- Managing secrets.
- Replacing Pydantic, Django, python-dotenv, or deployment config.
