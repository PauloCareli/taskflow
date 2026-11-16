# Taskflow

A task management app. Users register, create tasks, assign them to other users, track status through a fixed set of states, and filter and page through what they can see. A FastAPI backend (PostgreSQL, Redis, Celery) and a React frontend, built spec-first and test-first.

**Contents:** [Quick start](#quick-start) · [Running in Docker](#running-in-docker) · [Commands](#commands) · [Configuration](#configuration) · [Demo data](#demo-data) · [Using the app](#using-the-app) · [API](#api) · [Architecture](#architecture) · [Key decisions](#key-decisions) · [Quality](#quality) · [AI tooling](#ai-tooling) · [Repository map](#repository-map) · [Troubleshooting](#troubleshooting)

## Quick start

Tested on macOS and Linux. Windows is not supported (use WSL).

### Prerequisites
| Tool | Version | Used for |
|---|---|---|
| [uv](https://docs.astral.sh/uv/) | recent | installs Python 3.13 and the backend dependencies |
| [just](https://github.com/casey/just) | recent | the project's commands |
| [Node.js](https://nodejs.org/) | 22 (`frontend/.nvmrc`) | the frontend |
| [Docker](https://docs.docker.com/get-docker/) with Compose | recent | local PostgreSQL and Redis |

### Run it
```bash
git clone https://github.com/PauloCareli/taskflow.git && cd taskflow

# 1. Dependencies
(cd backend && uv sync)
(cd frontend && npm ci)

# 2. Infrastructure, schema and demo data
just up        # PostgreSQL and Redis in Docker, waits until healthy
just migrate   # create the database schema
just seed      # 3 demo users and 15 tasks

# 3. The app, in two terminals
just be        # API on http://localhost:8000
just fe        # frontend on http://localhost:5173
```
Nothing needs configuring for a local run. The API generates the secret that signs login tokens the first time it needs one and keeps it in `backend/.local-jwt-secret` (git-ignored, owner-only), so you stay signed in when the API restarts; delete that file to sign everyone out, or set `TASKAPP_JWT_SECRET` to use your own (see [Configuration](#configuration)).

Open http://localhost:5173 and sign in as `test1@example.com` with the password `password123` (see [Demo data](#demo-data)). Check the API directly with `curl localhost:8000/health` (`{"status":"ok"}`) or open its Swagger page at http://localhost:8000/docs.

Prefer Docker, with no uv or Node on your machine? See [Running in Docker](#running-in-docker).

To confirm everything works, run `just check` (lint, type checks and all tests, backend and frontend). It needs the PostgreSQL from `just up`.

Stop the infrastructure with `just down`.

## Running in Docker

Docker can run the whole app, the backend only, or the frontend only, so you do not need uv or Node on your machine for it. PostgreSQL and Redis always run in Docker; the profiles add the rest:

| Profile | Starts | Command |
|---|---|---|
| `api` | schema migration, API (http://localhost:8000), Celery worker | `docker compose --profile api up --build --wait` |
| `web` | the frontend (http://localhost:8080) | `docker compose --profile web up --build --wait web` |
| `full` | everything above | `docker compose --profile full up --build --wait` |

```bash
docker compose --profile full up --build --wait   # migrates the database, then starts the API, the worker and the web container
docker compose run --rm seed                      # demo data (see Demo data); safe to run again
```
Then open http://localhost:8080 and sign in with a demo user. No secret has to be set: the API container generates one and keeps it on the `api_data` volume, so people stay signed in across `docker compose down` and `up` (`down -v` deletes the volume and signs everyone out). The API container applies the migrations through a one-shot `migrate` service that the API and the worker wait for, so nothing needs to be run on your machine.

**Frontend only:** name the `web` service, as in the table. Without a service name Compose also starts PostgreSQL and Redis, which belong to no profile. The web container forwards `/api` to the API at `API_UPSTREAM`, which defaults to the `api` service. To use an API that runs on your machine (for example `just be`), set `API_UPSTREAM=http://host.docker.internal:8000`. Without any API the pages load and show the usual "API unavailable" state.

**Backend only:** `docker compose --profile api up --build --wait` is enough; run `just fe` on your machine if you also want the frontend, or start the `web` profile alongside it.

The web container serves the built frontend with Vite's preview server, which Vite documents as meant for local use rather than production. Behind it every client reaches the API from the same address, so anonymous requests (including login and register) share one rate-limit budget; signed-in requests are still counted per user.

Stop with `docker compose --profile full down` (add `-v` to delete the database volume).

## Commands

| Command | What it does |
|---|---|
| `just up` | Start PostgreSQL and Redis and wait until healthy |
| `just down` | Stop the infrastructure containers |
| `just migrate` | Apply database migrations to `TASKAPP_DATABASE_URL` (default: the local PostgreSQL) |
| `just seed` | Load the demo users and tasks (see [Demo data](#demo-data)) |
| `just be` | Run the API with auto-reload on http://localhost:8000 |
| `just worker` | Run a Celery worker (needs Redis from `just up`) |
| `just fe` | Run the frontend dev server on http://localhost:5173, proxying `/api` to the backend |
| `just test` | Backend tests with coverage (fails under 80%) |
| `just lint` | ruff check, ruff format check and import-linter contracts |
| `just typecheck` | mypy in strict mode |
| `just fe-lint` | eslint and prettier check |
| `just fe-typecheck` | `tsc` in strict mode |
| `just fe-test` | Frontend tests with coverage (fails under 80%) |
| `just check` | Everything CI runs: backend and frontend lint, type checks and tests |

## Configuration

Backend settings are read from `TASKAPP_*` environment variables, then from `backend/.env` (a git-ignored file you create from `backend/.env.example`). Defaults suit local development.

| Setting | Default | Meaning |
|---|---|---|
| `TASKAPP_JWT_SECRET` | generated locally, **required elsewhere** | Signs access tokens; at least 32 characters. Unset or empty in a local environment (`TASKAPP_ENVIRONMENT` is `local`, `dev`, `development` or `test`), the API generates one and keeps it in `TASKAPP_JWT_SECRET_FILE`. In any other environment the API refuses to start without it. A value that is set but shorter than 32 characters is an error everywhere. Set your own when several API processes share a database. |
| `TASKAPP_JWT_SECRET_FILE` | `.local-jwt-secret` (`/data/jwt-secret` in the API container) | Where the generated secret is kept: created for its owner only, git-ignored and left out of Docker builds. Delete it to sign everyone out. Never read or written when `TASKAPP_JWT_SECRET` is set or the environment is not local. |
| `TASKAPP_DATABASE_URL` | `postgresql+asyncpg://taskflow:taskflow@localhost:5432/taskflow` | PostgreSQL connection. Also used by `just migrate` and `just seed`. |
| `TASKAPP_REDIS_URL` | `redis://localhost:6379/0` | Celery broker and rate-limit storage. |
| `TASKAPP_ENVIRONMENT` | `local` | `just seed` only runs for `local`, `dev`, `development` or `test`. |
| `TASKAPP_APP_NAME` | `Taskflow API` | Title shown in Swagger. |
| `TASKAPP_RATE_LIMIT_DEFAULT` | `100/minute` | Limit on all endpoints except `/health`, counted per signed-in user, or per client IP for anonymous requests and invalid tokens. |
| `TASKAPP_RATE_LIMIT_AUTH` | `20/minute` | Stricter per-IP limit on `POST /auth/login` and `POST /auth/register`. |
| `TASKAPP_CELERY_EAGER` | `false` | Run Celery tasks in-process instead of on a worker (used by tests). |

Over a limit the API answers `429` with the usual error body and `Retry-After`. Requests are still served if Redis is down. The client address is the connecting IP and `X-Forwarded-For` is ignored, so behind a reverse proxy every anonymous client shares one budget until that is configured on purpose.

Other variables:

| Variable | Default | Meaning |
|---|---|---|
| `VITE_API_BASE_URL` | `/api` (set by `just fe`) | Where the frontend sends API calls: an absolute `http(s)` URL or an absolute path. The Vite dev server proxies `/api` to `http://localhost:8000`. A missing or invalid value stops the dev server and the build with a clear message (`frontend/.env.example`). |
| `POSTGRES_PORT` | `5432` | Host port of the PostgreSQL container. If you change it, change `TASKAPP_DATABASE_URL` too. |
| `REDIS_PORT` | `6379` | Host port of the Redis container. If you change it, change `TASKAPP_REDIS_URL` too. |
| `API_PORT` | `8000` | Host port of the API container (`api` and `full` profiles). |
| `WEB_PORT` | `8080` | Host port of the web container (`web` and `full` profiles). |
| `API_UPSTREAM` | `http://api:8000` | Where the web container forwards `/api`; use `http://host.docker.internal:8000` for an API on your machine. |

## Demo data

`just seed` creates three demo users and 15 tasks covering every status, with overdue and upcoming due dates, some unassigned and some assigned across the users. Running it again changes nothing, and a run that fails halfway removes what it created. These credentials are for local demos only:

| Email | Password |
|---|---|
| `test1@example.com` | `password123` |
| `test2@example.com` | `password123` |
| `test3@example.com` | `password123` |

## Using the app

Sign in on `/login` (or create an account on `/register`), then manage tasks on `/`: filter by status and due date, page through the list, create, edit, assign, complete and delete tasks. A user sees only the tasks they created or are assigned to. The session token is kept in `localStorage` and discarded on sign-out or when the API answers `401`. `/status` shows the API's health.

## API

Swagger documents every endpoint with its schemas at http://localhost:8000/docs (use Authorize and paste the token from `/auth/login`).

| Method | Path | Notes |
|---|---|---|
| GET | `/health` | `{"status":"ok"}`; not rate limited |
| POST | `/auth/register` | `{email, name, password}` -> `201 {id, email, name}`; `409` if the email is taken (any case) |
| POST | `/auth/login` | `{email, password}` -> `200 {access_token, token_type, expires_in}` (30 minutes); `401` for any bad credentials |
| GET | `/auth/me` | Bearer token -> `{id, email, name}` |
| GET | `/tasks` | Your tasks: `status` (repeatable), `due_before`, `due_after`, `page`, `size` (default 25, max 100) -> `{items, total, page, size}`, soonest due date first |
| POST | `/tasks` | `{title, description?, due_date?, assignee_id?}` -> `201` |
| GET | `/tasks/{id}` | `404` if it does not exist or is not yours to see |
| PATCH | `/tasks/{id}` | `{title?, description?, due_date?, status?}` in one transaction; fields for the creator, `status` also for the assignee; `403`, `404`, `409` invalid transition |
| DELETE | `/tasks/{id}` | Creator only -> `204` |
| POST | `/tasks/{id}/assign` | `{assignee_id: uuid \| null}`, creator only; queues one notification |
| POST | `/tasks/{id}/complete` | Creator or assignee; `409` if the task is cancelled |
| GET | `/users` | `[{id, email, name}]` sorted by name, for choosing an assignee |

Errors always use the body `{"error": {"code", "message", "details"}}`. Task statuses are `todo`, `in_progress`, `blocked`, `completed` and `cancelled`; the last two are final.

## Architecture

The backend follows Clean Architecture. Dependencies point inward, and import-linter fails the build (`just lint`) if they do not.

```
api            routes, request and response schemas, error mapping      (FastAPI, Pydantic)
infrastructure PostgreSQL repositories, JWT, argon2, Celery, settings   (SQLAlchemy, Alembic)
      \              /
       application   use cases and the ports they depend on             (Python only)
            |
         domain      Task, User, status rules, domain errors            (standard library only)
```

- **domain** holds the business rules: field limits, status transitions, who may do what, `completed_at`. It imports nothing but the standard library.
- **application** has one use case per operation (`CreateTask`, `UpdateTask`, `AssignTask`, `ListTasks`, `RegisterUser`, `LoginUser`, and so on) and the ports they use: repositories, a unit of work, a clock, a password hasher, a token service and a notifier. Use cases are tested against in-memory fakes.
- **infrastructure** implements the ports: SQLAlchemy repositories and unit of work, Alembic migrations, argon2 and JWT, the Celery notifier and task, rate-limit keys.
- **api** is thin: parse the request, call one use case, map the result. All domain errors become HTTP responses in one table.
- `composition.py`, `main.py` and `seed.py` are the only places that wire the layers together.

**A request:** the rate limiter counts it (per user or per IP), the router parses it and resolves the caller from the bearer token, a use case applies the rules through the ports (nothing is stored unless the unit of work commits), and the result or the mapped error goes back as JSON. Assigning a task queues a Celery task through Redis after the commit; a worker logs the notification.

**The frontend** (`frontend/src`) is React with TypeScript: a feature folder per area (`auth`, `tasks`, `health`), TanStack Query for server state, zod schemas that parse every API response, and Tailwind styled from the tokens in `frontend/STYLE.md`.

More detail: [`backend/ENGINEERING.md`](backend/ENGINEERING.md), [`frontend/ENGINEERING.md`](frontend/ENGINEERING.md) and [`frontend/STYLE.md`](frontend/STYLE.md).

## Key decisions

- **Spec first, then tests, then code.** [`spec/`](spec/) holds the product rules ([`00-overview.md`](spec/00-overview.md)) and one spec per issue with numbered acceptance criteria. Tests are named after them (`test_ac07_...`), each spec ends with an AC-to-test table, and pull requests are merged with merge commits so the red-then-green history stays visible.
- **One error format** (`{"error": {"code", "message", "details"}}`) for every failure, including validation, rate limits and unexpected errors, produced in one place in the API layer.
- **A task you cannot see does not exist for you:** it answers `404`, not `403`, so ids cannot be probed. `403` is for users who can see a task but may not change it (for example an assignee editing the title).
- **Authentication:** access tokens (JWT, 30 minutes, no refresh tokens) and argon2 password hashes. Failed logins are indistinguishable (same response, comparable work) so emails cannot be enumerated.
- **Rate limiting counts signed-in users separately** (the token's signature and expiry are verified, with no database lookup), falls back to the client IP otherwise, and applies a stricter limit to login and register. It fails open if Redis is down.
- **Notifications cannot fail a request.** Assigning commits first, then queues one idempotent Celery task. Publishing is retried a few times and any failure is logged, and the worker retries the task with backoff.
- **PATCH is atomic:** fields and status in one request are applied together or not at all.
- **Time is injected** (a `Clock` port) and always timezone-aware UTC; numbers are not accepted as dates.
- **Not built, on purpose:** refresh tokens, roles beyond creator and assignee, real email delivery, scheduled jobs such as overdue flagging, and Windows support.

## Quality

- `just check` runs what CI runs: ruff, ruff format, mypy (strict), import-linter, eslint, prettier, `tsc` and both test suites. Coverage must stay at or above 80% for the backend (`just test`) and the frontend (`just fe-test`).
- Backend integration tests use the PostgreSQL from `just up`: they create a throwaway `taskflow_test_<pid>` database, build it from the migrations, and drop it afterwards. They never touch the `taskflow` database. Celery runs eagerly in tests, so no worker or broker is needed. Frontend tests fail on any `console.error` or `console.warn`.
- CI (`.github/workflows/ci.yml`) runs `just check` against a PostgreSQL service, the file-hygiene hooks, and a gitleaks scan over the pushed commits.
- Install the git hooks once per clone with `cd backend && uv run pre-commit install`. They run ruff, mypy, import-linter, gitleaks and basic file checks (`.pre-commit-config.yaml`).

## AI tooling

The project was built with Claude Code, working under written rules in [`AGENTS.md`](AGENTS.md) and slash-command workflows in [`.claude/skills/`](.claude/skills/) (`/spec`, `/feature`, `/implement`, `/ship`, `/chore`, `/log-correction`, `/clean-worktrees`). Every change followed the same loop, with a person approving each gate:

1. A GitHub issue per slice, then a spec with acceptance criteria that the maintainer reviews and approves before any code.
2. A plan, where the slice is big enough to need one, logged in the prompts file.
3. Tests first: a failing test is committed before the code that makes it pass, so the history shows red then green.
4. The quality gates (`just check`), then an independent review by a fresh agent with no knowledge of the implementation. Each finding is checked against the code before it is acted on.
5. A pull request that the maintainer reviews and merges.

Where to look:
- [`docs/ai/prompts.md`](docs/ai/prompts.md): the prompts and plans behind each slice, the commits they produced, and what the reviews found.
- [`docs/ai/corrections.md`](docs/ai/corrections.md): every mistake in AI-written code, how it was caught (a test, a review, or running it) and the commit that fixed it.
- [`GENAI.md`](GENAI.md): one page with the prompt, a code sample (a domain rule, a use case and its test) and the evidence for validation, corrections, edge cases and performance.
- [`docs/ai/usage.md`](docs/ai/usage.md): time and usage. Exact figures were not recorded; the page gives an estimate.

Validation did not rely on the AI's own judgment: behavior is pinned by tests written before the code, boundaries by import-linter, types by strict mypy and `tsc`, secrets by gitleaks in the pre-commit hook and in CI, and defects that slipped through were found by the independent review or by running the app and are listed in the corrections log.

## Repository map

```
backend/    FastAPI app (src/taskapp), Alembic migrations, tests, ENGINEERING.md
frontend/   React app (src), tests, ENGINEERING.md, STYLE.md
spec/       product rules and one spec per slice, with acceptance criteria
docs/ai/    prompts, corrections and usage of the AI tooling
.claude/    the project's slash-command workflows
.github/    CI workflow and pull request template
justfile    all project commands
docker-compose.yml   PostgreSQL, Redis and, by profile, the migration, API, worker, web and seed services
```

## Troubleshooting

- **The API stops at start-up with a message about `TASKAPP_JWT_SECRET`.** Either `TASKAPP_ENVIRONMENT` is not a local environment and no secret is set (set one: at least 32 random characters), or the secret you set is shorter than 32 characters. Locally you can simply leave it unset.
- **Everyone is signed out after the API restarted.** The generated secret file (`backend/.local-jwt-secret`, or the `api_data` volume in Docker) was deleted or could not be written, so a new secret was generated; the start-up log says which. Make the location writable, or set `TASKAPP_JWT_SECRET`.
- **`connection refused` from `just migrate`, `just seed`, `just test` or `just check`.** PostgreSQL is not running. Start it with `just up`, and make sure Docker is running.
- **A port is already in use (5432, 6379, 8000, 8080 or 5173).** Stop whatever uses it, or move the containers with `POSTGRES_PORT`, `REDIS_PORT`, `API_PORT` and `WEB_PORT` and update `TASKAPP_DATABASE_URL` or `TASKAPP_REDIS_URL` to match. The frontend dev server expects the API on `http://localhost:8000`.
- **`just seed` says it is refusing to run.** `TASKAPP_ENVIRONMENT` is not one of `local`, `dev`, `development` or `test`. Demo data has published passwords and is never loaded elsewhere.
- **`just seed` says the data is already there.** The demo users exist; the command never changes existing data. To start over, `docker compose down -v` deletes the database volume, then run `just up`, `just migrate` and `just seed` again.
- **`429 Too Many Requests`.** A rate limit was hit; wait for `Retry-After` seconds, or raise `TASKAPP_RATE_LIMIT_DEFAULT` or `TASKAPP_RATE_LIMIT_AUTH` while developing.
- **The frontend stops with a message about `VITE_API_BASE_URL`.** The value must be an absolute `http(s)` URL or an absolute path such as `/api`. `just fe` sets it for you.
- **A Celery worker is not running and assignments log an error.** The assignment itself is saved either way. Start a worker with `just worker`.
