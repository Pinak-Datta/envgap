# FastAPI-Style Example

This intentionally broken example mimics a small API service settings module.

Run:

```console
envgap check examples/fastapi
```

It demonstrates:

- `OPENAI_API_KEY` required in code but missing from `.env`
- `.env` using `OPENAI_KEY`, a likely undocumented/misnamed key
- placeholder value detection with `changeme`
- `REDIS_URL` documented and used, but missing locally
- a local-only extra key that is not documented

