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

## Parallel implementation (only when it is safe)
Default is sequential: inner layers (domain, then application) feed the outer ones. Dispatch implementer subagents in parallel (Agent tool, one message, multiple calls) ONLY for parts with disjoint files and no shared interface still undecided, e.g. backend api layer vs. frontend screen once the API contract in the plan is fixed, or independent use cases. Each implementer gets: its plan section, the AC ids, the paths it may touch, and the TDD + commit rules above. Never let two agents edit the same file. If agents must share a worktree, they commit sequentially; prefer separate directories.

## Independent review (mandatory, fresh context)
After the gates pass, dispatch reviewer subagents in parallel, in ONE message. They must be fresh agents (no fork, do not pass the implementation conversation or your reasoning), so they judge the diff cold. Give each only: the diff command (`git diff origin/main...HEAD`), the AC ids and the spec path, and pointers to `AGENTS.md` and the relevant `ENGINEERING.md`. They are read-only: they may run tests and gates but must not edit files.
- **Architecture reviewer**: layer boundaries, business rules outside domain/application, ORM or Pydantic leaking inward, fat routers, port design, import-linter intent.
- **Test reviewer**: does each AC have a test named after it, are tests meaningful (not tautological or over-mocked), are error paths and edge cases covered, does the red/green commit history show test-first.
- **Correctness and security reviewer**: auth and ownership checks, validation, N+1 queries, sync calls in async paths, deprecated libs (`python-jose`, `passlib`, `datetime.utcnow`), swallowed exceptions, timezone handling, secrets.
- For frontend changes add a **Frontend reviewer**: zod/TS types, server-state vs. local-state, accessibility, console warnings, responsive behavior.
Ask each for findings as: severity, file:line, the problem, a concrete failure scenario. No praise, no style nitpicks.

## After the review
- Verify each finding yourself before acting; reviewers can be wrong. Fix confirmed ones test-first (red/green commits), and rerun the gates.
- Summarize for the user: findings raised, which were confirmed, which were rejected and why.
- Every confirmed mistake that came from AI-generated code gets a `/log-correction` entry (caught by: review). Also check: README updated if commands, env vars, setup or endpoints changed; AC -> test table in `docs/spec.md` is current.
