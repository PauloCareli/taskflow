set shell := ["bash", "-euo", "pipefail", "-c"]

backend := "backend"
frontend := "frontend"

# List available targets
default:
    @just --list

# Start Postgres and Redis and wait until healthy
up:
    docker compose up -d --wait

# Stop infrastructure
down:
    docker compose down

# Run the API with auto-reload on http://localhost:8000
be:
    cd {{backend}} && uv run uvicorn taskapp.main:app --reload

# Apply database migrations (uses TASKAPP_DATABASE_URL, default: the local compose Postgres)
migrate:
    cd {{backend}} && uv run alembic upgrade head

# Load demo users and tasks (run `just migrate` first; does nothing if they are already there)
seed:
    cd {{backend}} && uv run python -m taskapp.seed

# Run a Celery worker (needs Redis: just up)
worker:
    cd {{backend}} && uv run celery -A taskapp.infrastructure.celery_app worker --loglevel=info

# Run tests with coverage (fails under 80%)
test:
    cd {{backend}} && uv run pytest

# Ruff lint, ruff format check and import-linter contracts
lint:
    cd {{backend}} && uv run ruff check .
    cd {{backend}} && uv run ruff format --check .
    cd {{backend}} && uv run lint-imports

# mypy in strict mode
typecheck:
    cd {{backend}} && uv run mypy src tests

# Run the frontend dev server on http://localhost:5173 (proxies /api to the backend)
fe:
    cd {{frontend}} && VITE_API_BASE_URL="${VITE_API_BASE_URL:-/api}" npm run dev

# eslint and prettier check
fe-lint:
    cd {{frontend}} && npm run lint

# tsc in strict mode
fe-typecheck:
    cd {{frontend}} && npm run typecheck

# Frontend tests with coverage (fails under 80%)
fe-test:
    cd {{frontend}} && npm test

# Everything CI runs: lint + typecheck + test, backend and frontend
check: lint typecheck test fe-lint fe-typecheck fe-test
