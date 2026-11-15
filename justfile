set shell := ["bash", "-euo", "pipefail", "-c"]

backend := "backend"

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

# Everything CI runs: lint + typecheck + test
check: lint typecheck test
