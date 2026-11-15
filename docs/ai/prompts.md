# Prompts log

Prompts used to drive the AI tools, in chronological order. Log the prompt text, the intent, and the outcome (accepted / edited / rejected).

Entry format:

## YYYY-MM-DD HH:MM — <phase / slice>
**Prompt:**
> ...

**Output:** commit `<hash>` or summary
**Review notes:** what was checked, what changed

## 2026-11-15 17:41 — Backend scaffold (#1)
**Prompt:**
> You are a senior Python engineer pairing with me. We work test-first.
>
> Read first, in order: AGENTS.md, backend/ENGINEERING.md.
>
> Goal: implement GitHub issue #1 (backend scaffold) and nothing else.
>
> Deliver, as separate commits in this order (conventional commit messages, "Refs #1"):
> 1. backend/ uv project: pyproject.toml with ruff, mypy (strict), pytest, pytest-asyncio, pytest-cov (--cov-fail-under=80), import-linter, pre-commit.
> 2. src/taskapp/{domain,application,infrastructure,api}/ with a 5-line README each stating only the import rules (not file inventories), plus import-linter contracts matching backend/ENGINEERING.md.
> 3. GET /health: write the failing test test_health_returns_ok first, commit it, then implement it. FastAPI app factory in api/, settings in infrastructure/ via pydantic-settings.
> 4. docker-compose.yml at repo root: postgres and redis with healthchecks (no app services yet) and a Dockerfile for the backend. Dev workflow runs the app outside Docker.
> 5. justfile at repo root: up, down, be (run API with reload), test, lint, typecheck, check (= lint + typecheck + test with coverage). Document each target in the README.
> 6. .pre-commit-config.yaml (ruff, ruff-format, mypy, import-linter, gitleaks, hygiene hooks) and .github/workflows/ci.yml running the same as `just check`.
>
> Constraints:
> - FastAPI, SQLAlchemy 2.0 async, Alembic, PostgreSQL. For auth later: pyjwt and pwdlib[argon2]. Do NOT use python-jose or passlib.
> - No business logic, models, auth or migrations yet. No frontend.
> - Pin dependency versions through uv.lock. Use the latest stable versions you know of and tell me which you chose.
> - Do not invent APIs: if unsure about a library's current API, say so instead of guessing.
>
> Process: stop after each numbered item and show me the diff summary and the commands you ran. When all six are done, run `just check` and report real output. List any assumptions you made.
>
> Done when:
> - GET /health returns 200 with {"status": "ok"}, covered by a test written first.
> - import-linter contracts fail if domain imports FastAPI, SQLAlchemy, Pydantic, Celery, or any other layer (demonstrate once with a deliberate violation, then revert it).
> - `just check` passes from a clean checkout without Docker running.
> - `just up` starts Postgres and Redis healthy.
> - CI runs the same checks as `just check`.
> - The gitleaks pre-commit hook blocks a staged secret.

**Output:** commits `0eb270b`, `9f9fb36`, `08e5394` (red), `f742f97` (green), `83bf6a2`, `55d0793`, `9e68a23`, `175b2a6`; review fixes `3a0e5a2`, `99195ab`, `621c227`, `4338aec`, `59b6ddf`
**Steering:**
- Prompt scoped to the issue only (no spec dependency); constraints named the libraries to avoid (python-jose, passlib).
- One commit per deliverable, review after each, and the `/health` test committed red before the implementation.
- Demanded evidence rather than claims: a deliberate import violation, a staged fake secret, `just check` without Docker.
- A separate reviewer agent checked the branch. Three defects were fixed: gitleaks was a no-op in CI, import contracts were missing libraries, and a settings test depended on the environment (see `corrections.md`).
