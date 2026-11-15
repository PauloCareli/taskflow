---
name: implement
description: Implement an approved slice test-first (red, green, refactor), run all quality gates, then self-review the diff for architecture violations and AI mistakes. Use after /feature.
---

Implement the approved plan for the current slice. If there is no approved plan in the conversation, run `/feature` first.

## TDD loop (repeat per test in the plan, innermost layer first)
1. **Red**: write the next failing test, named after its AC. Run it and confirm it fails for the right reason. Commit: `test(ac-xx): <behavior>`.
2. **Green**: write the minimum code to pass. No extras. Commit: `feat(ac-xx): <behavior>`.
3. **Refactor**: clean up with tests green. Commit separately if non-trivial: `refactor: ...`.
Never squash or batch red and green into one commit; the history is evidence of test-first work.

## Stack conventions (see ENGINEERING.md for the full rules)
- Backend: FastAPI, SQLAlchemy 2.0 async, Alembic, Pydantic at the API boundary only. JWT via `pyjwt` + `pwdlib[argon2]` (never `python-jose` or `passlib`). Rate limiting via `slowapi`. Celery + Redis for background work.
- Domain is pure Python: no FastAPI, SQLAlchemy, Pydantic, Celery or settings imports. Business rules (status transitions, due-date rules, ownership) live in entities or use cases, never in routers or repositories.
- Use cases depend on ports (`TaskRepository`, `UnitOfWork`, `TokenService`, `Notifier`) and are unit-tested against in-memory fakes. Infrastructure adapters get integration tests against real Postgres.
- Routers are thin: parse, call one use case, map domain errors to HTTP errors with the project's error format. No ORM models in the api layer.
- Frontend: React + TS + Vite, TanStack Query for server state, react-hook-form + zod with types from `z.infer`, Tailwind mapped to the design tokens in `frontend/STYLE.md`. No `any`, no state duplication of server data.
- Type everything (mypy strict), no bare `except`, no mutable default args, timezone-aware datetimes only.

## Quality gates (all must pass before finishing)
Backend (from `backend/`): `uv run ruff check . && uv run ruff format --check . && uv run mypy . && uv run lint-imports && uv run pytest --cov --cov-fail-under=80`
Frontend (from `frontend/`): `npm run lint && npm run typecheck && npm test -- --run`, plus no `console.error`/`console.warn` in tests.
If a gate fails, fix the cause; never lower a threshold or add `# type: ignore` / `noqa` to silence it without explaining why.

## Self-review (before reporting done)
Read the full diff (`git diff main...HEAD` or the slice's commits) and check:
- Layer boundaries: any import pointing the wrong way? Any business rule outside domain/application?
- Common AI mistakes: fat routers, ORM models leaking into use cases, deprecated libs (`python-jose`, `passlib`, `datetime.utcnow`), sync calls in async paths, N+1 queries, missing auth/ownership checks, over-broad exception handling, untested error paths, invented APIs.
- Edge cases from the plan: each has a test.
- Every AC in the slice has a test named after it, and the AC -> test table in `docs/spec.md` is updated.
- README updated if commands, env vars, setup or endpoints changed.
Report findings honestly. For each real mistake found in AI-generated code (yours or earlier), propose a `docs/ai/corrections.md` entry via `/log-correction`.
