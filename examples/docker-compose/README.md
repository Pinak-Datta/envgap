# Docker Compose Example

This intentionally broken example mimics a small service with environment config split across `.env`, `.env.example`, and Docker Compose.

Run:

```console
envgap check examples/docker-compose
```

It demonstrates:

- `DATABASE_URL` documented in `.env.example` and passed through Compose
- `REDIS_URL` declared in Compose but missing from `.env.example`
- `WORKER_QUEUE` declared in Compose but missing from `.env.example`
- `CELERY_BROKER_URL` loaded through `env_file` but missing from `.env.example`
- project-local `env_file` scanning without reading unrelated files outside the project
