# Taskflow

Task management app: FastAPI backend + React frontend.

> Work in progress. Demo credentials and key decisions will be added here.

## Requirements
- [uv](https://docs.astral.sh/uv/) and Python 3.13
- [just](https://github.com/casey/just)
- Docker (only for local Postgres and Redis)

## Getting started
```bash
cd backend && uv sync   # install dependencies
just up                 # start Postgres and Redis
just be                 # run the API at http://localhost:8000
```
Check it works: `curl localhost:8000/health` returns `{"status":"ok"}`.

The app runs on your machine, not in Docker; compose only provides infrastructure.
Settings come from `TASKAPP_*` environment variables (see `backend/src/taskapp/infrastructure/settings.py`).

## Commands
| Command | What it does |
|---|---|
| `just up` | Start Postgres and Redis and wait until healthy |
| `just down` | Stop the infrastructure containers |
| `just be` | Run the API with auto-reload |
| `just test` | Run pytest with coverage (fails under 80%) |
| `just lint` | ruff check, ruff format check and import-linter contracts |
| `just typecheck` | mypy in strict mode |
| `just check` | `lint` + `typecheck` + `test`; the same checks CI runs |

`just check` does not need Docker.

## Git hooks
Install once per clone: `cd backend && uv run pre-commit install`. Hooks run ruff, ruff format, mypy, import-linter and gitleaks, using the versions pinned in `backend/uv.lock`, so they match `just check` and CI. Run them on demand with `uv run --project backend pre-commit run --all-files`.
