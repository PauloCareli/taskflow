# Backend engineering rules

## Workflow
- Spec-driven: no code without ACs in the slice spec under `/spec`. TDD: red commit, green commit, refactor commit.
- Tests named after ACs: `test_ac07_...`. Update the AC -> test table in the slice spec.

## Layers (`src/taskapp/`)
| Layer | May import | Contains |
|---|---|---|
| `domain` | stdlib only | entities, value objects, enums, domain errors. Business rules live here. |
| `application` | domain | use cases, ports (`TaskRepository`, `UnitOfWork`, `TokenService`, `PasswordHasher`, `Notifier`), DTOs |
| `infrastructure` | domain, application | SQLAlchemy models + repos, JWT/pwdlib impls, Celery tasks, settings, rate-limit storage |
| `api` | application, domain | FastAPI routers, Pydantic schemas, dependency wiring, error mapping |
Enforced by import-linter (`just lint`, pre-commit, CI). A failing contract is a bug in the change, not in the contract.

## Rules
- **Domain is framework-free**: no FastAPI, SQLAlchemy, Pydantic, Celery or settings imports. Use dataclasses/enums.
- **Pydantic only at the boundaries**: request/response schemas in `api`, settings in `infrastructure`. Never pass ORM models or Pydantic schemas into use cases; map to domain objects.
- **Routers are thin**: parse input, call one use case, map the result. No business logic, no queries.
- **Use cases** take ports via constructor, return domain objects or DTOs, raise domain errors. One public `execute`.
- **Repositories** never commit; the `UnitOfWork` owns transactions.
- **Errors**: domain errors -> one mapping table in `api` -> uniform error body (see `spec/00-overview.md`).
- **Async everywhere** on I/O paths; no blocking calls in request handlers.
- **Time**: timezone-aware UTC only; inject a clock into use cases, never call `datetime.now()` in domain.
- **Auth**: `pyjwt` + `pwdlib[argon2]` (never python-jose or passlib). Secrets only from settings/env. Ownership checks live in use cases, not routers.
- **Celery tasks** are thin wrappers that call use cases and are idempotent.
- **Typing**: mypy strict. No `Any`, no bare `except`, no mutable default args.
- **Queries**: avoid N+1 (eager load or join), paginate in SQL, index filter columns (status, due_date, assignee_id).

## Testing
- Unit tests (`tests/unit`): use cases and domain against in-memory fakes. No DB, no network, milliseconds.
- Integration tests (`tests/integration`): repositories and API via `httpx.AsyncClient` against real Postgres (compose).
- Coverage gate 80% (`--cov-fail-under=80`); aim higher on domain/application.
- Test behavior, not implementation; no tautological or over-mocked tests.

## Naming
- Modules snake_case, classes PascalCase, use cases as verbs (`CompleteTask`), ports as nouns (`TaskRepository`), fakes `InMemoryTaskRepository`.
- Conventional commits (`test:`, `feat:`, `fix:`, `refactor:`, `chore:`, `docs:`), with `Refs #n`.

## Definition of done
- [ ] ACs covered by tests named after them, red-before-green in history
- [ ] `just check` green (ruff, ruff format, mypy, import-linter, pytest + coverage)
- [ ] No layer violations; independent review done (see `/implement`)
- [ ] README updated if commands, env vars, setup or endpoints changed
- [ ] AI mistakes logged in `docs/ai/corrections.md`
