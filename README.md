# Taskflow

Task management app: FastAPI backend + React frontend.

> Work in progress. Demo credentials and key decisions will be added here.

## Requirements
- [uv](https://docs.astral.sh/uv/) and Python 3.13
- [just](https://github.com/casey/just)
- Node 22 (see `frontend/.nvmrc`) and npm
- Docker (only for local Postgres and Redis)

## Getting started
```bash
cd backend && uv sync   # install backend dependencies
cp backend/.env.example backend/.env   # then set TASKAPP_JWT_SECRET (see the file)
cd frontend && npm ci   # install frontend dependencies
just up                 # start Postgres and Redis
just migrate            # create the database schema
just be                 # run the API at http://localhost:8000
just fe                 # run the frontend at http://localhost:5173
```
Check it works: `curl localhost:8000/health` returns `{"status":"ok"}`, and the home page at http://localhost:5173 shows the API as healthy.

The frontend calls the API under `VITE_API_BASE_URL`. `just fe` sets it to `/api` when unset, and the Vite dev server proxies `/api` to `http://localhost:8000`. The value must be an absolute `http(s)` URL or an absolute path; anything else stops the dev server and the build with a clear message. `frontend/.env.example` shows the variable.

The app runs on your machine, not in Docker; compose only provides infrastructure.
Settings come from `TASKAPP_*` environment variables or `backend/.env` (see `backend/.env.example` and `backend/src/taskapp/infrastructure/settings.py`). `TASKAPP_JWT_SECRET` (at least 32 characters) is required: the API refuses to start without it.

## API
| Method | Path | Notes |
|---|---|---|
| GET | `/health` | `{"status":"ok"}` |
| POST | `/auth/register` | `{email, name, password}` -> `201 {id, email, name}`; `409` if the email is taken (any case) |
| POST | `/auth/login` | `{email, password}` -> `200 {access_token, token_type, expires_in}` (30 minutes); `401` for any bad credentials |
| GET | `/auth/me` | Bearer token -> `{id, email, name}`; `401` for a missing, malformed, expired or tampered token |

Errors use the body `{"error": {"code", "message", "details"}}`. Passwords are stored as argon2 hashes only.

## Commands
| Command | What it does |
|---|---|
| `just up` | Start Postgres and Redis and wait until healthy |
| `just down` | Stop the infrastructure containers |
| `just migrate` | Apply database migrations to `TASKAPP_DATABASE_URL` (default: the local Postgres) |
| `just be` | Run the API with auto-reload |
| `just test` | Run pytest with coverage (fails under 80%) |
| `just lint` | ruff check, ruff format check and import-linter contracts |
| `just typecheck` | mypy in strict mode |
| `just fe` | Run the frontend dev server with the `/api` proxy |
| `just fe-lint` | eslint and prettier check |
| `just fe-typecheck` | `tsc` in strict mode |
| `just fe-test` | vitest with coverage (fails under 80%) |
| `just check` | backend and frontend lint, typecheck and tests; the same checks CI runs |

`just check` needs the local Postgres from `just up`: the backend integration tests create a throwaway `taskflow_test_<pid>` database on it, build it from the migrations, and drop it afterwards. They never touch the `taskflow` database. CI provides a Postgres service.

## Using the app
Open the frontend, create an account on `/register` (or sign in on `/login`), and manage tasks on `/`. The session token is kept in `localStorage` and discarded on logout or when the API answers 401. The API health page is at `/status`.

## Frontend versions
React 19.3, Vite 8, TypeScript 6.0, Tailwind 4.3, TanStack Query 5, React Router 7, zod 4, React Hook Form, Vitest 5, MSW 3, ESLint 9. ESLint stays on 9 because `eslint-plugin-jsx-a11y` does not support 10 yet, and TypeScript stays on 6.0 because `typescript-eslint` does not support 7 yet. Exact versions are pinned in `frontend/package-lock.json`.

## Git hooks
Install once per clone: `cd backend && uv run pre-commit install`. The hooks run ruff, ruff format, mypy and import-linter from the versions pinned in `backend/uv.lock`, plus gitleaks and basic file checks pinned in `.pre-commit-config.yaml`. The ruff hooks fix files in place; `just lint` only checks. Run them on demand with `uv run --project backend pre-commit run --all-files`.

CI runs `just check`, the file-hygiene hooks, and a gitleaks scan over the pushed commits.
