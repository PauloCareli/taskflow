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

## 2026-11-15 — Frontend scaffold (#4), plan
**Request:** plan slice `spec/08-frontend-scaffold.md` (AC-01 to AC-13) on branch `feat/frontend-scaffold`.

**Plan (approved):**
- **Layers:** backend none. Frontend per `frontend/ENGINEERING.md`: `shared/api` (zod-validated env, fetch client with 10s timeout, `ApiError`, token-provider hook point), `shared/ui` (Button, status message), `features/health` (schema, API call, `useHealth` with `retry: false`, `HealthStatus`), `app` (StrictMode, QueryClient, Router, ErrorBoundary, shell, routes), `test/` (MSW setup, console guard), `styles/tokens.css` (tokens defined once, mapped into Tailwind). Vite dev proxy for `/api` with config-time base URL validation. eslint (typescript-eslint, react-hooks, jsx-a11y, no-console, no-explicit-any, ban-ts-comment), prettier, vitest coverage at 80% (entry file excluded). justfile `fe`, `fe-lint`, `fe-typecheck`, `fe-test` included in `check`; CI gains Node setup and `npm ci`; README, `.env.example`, `.nvmrc`.
- **Tests, in order:** `parseEnv` (AC-07, AC-08), client success/bearer/`ApiError` variants/timeout/URL joining (AC-05, AC-06, AC-07), health schema and no-auto-retry (AC-03), home page loading/healthy/error/retry (AC-01 to AC-03), routing and error boundary (AC-04), StrictMode single request (AC-11), shell and keyboard retry (AC-10), token mapping and no hardcoded colors (AC-09), console guard (AC-12). AC-12 lint bans and AC-13 are checked by running the gates.
- **Out of scope:** auth and 401 handling, task screens, hosting and Docker image, light theme, backend changes.
- **Risks:** Tailwind v4 CSS-first theme mapping (fall back to v3 if it conflicts); jsdom cannot verify layout or computed styles, so 360px and 1280px are checked manually in a browser; `just check` now requires Node 22.
- **Commits:** tooling, then red tests, then green, then refactor, as small commits.

**Branch:** `feat/frontend-scaffold`
**Output:** commits `6862189` (tooling); red/green pairs `e0decfd`/`f7da3a4` (AC-12), `d112caf`/`23e3c91` (AC-07, AC-08), `8a1eebd`/`0597aee` (AC-05 to AC-07), `139e603`/`c9c4bec` (AC-01 to AC-03), `c9d446a`/`4871850` (AC-04, AC-10, AC-11), `36e0006`/`6f437ef` (AC-09); `dbf0573` (just, CI, README); `71c70f9` (AC to test table)
**Review notes:** `just check` green (76 frontend tests, 98.9% statement coverage); the build fails without or with an invalid `VITE_API_BASE_URL` and succeeds with `/api`. Layout at 360px and 1280px and `just fe` serving the page were not verified in a browser.

## 2026-11-15 18:40 — Frontend auth and task management (#12)
**Prompt:**
> Spec for `spec/12-frontend-app.md` drafted from issue #12. Decisions on the open questions: token in localStorage; sign in automatically after register; current user taken from the token `sub` claim; create and edit in modal dialogs; page size default 25 with previous/next and a dropdown to choose it; due date rejected in the past only on create; date filters read as UTC. Approved, implement.

**Output:** spec `33fc91e`; red/green pairs `6ca278c`/`f298977` (API client writes and 401 hook), `e05a6bf`/`e62f3e8` (AC-01 to AC-03), `02d115e`/`c769635` (AC-04, AC-05), `86f1112`/`6278a3a` (AC-06 to AC-08), `70c725d`/`62eae5a` (review fixes); `1cc1d51` (AC to test table, README); `16a8086` (corrections)
**Review notes:** `npm run lint`, `npm run typecheck` and `npm test` green (123 tests, 95.9% line coverage). One independent review; three findings confirmed and fixed (dialog focus on re-render, page clamp after deletes, sign-in failure after register), logged in `docs/ai/corrections.md`. Not verified: layout at 360px and 1280px in a browser, and the app against the real API (mocked with MSW until the backend is merged).

## 2026-11-15 19:30 — Rate limiting and background jobs, infrastructure half (#11)
**Prompt:**
> Spec for `spec/11-rate-limit-jobs-seed.md` drafted from issue #11, scoped to the infrastructure half. Decisions: fail-open when Redis is down; `GET /health` exempt; healthchecks via `GET /health` and a Celery ping; settings `TASKAPP_RATE_LIMIT_DEFAULT` and `TASKAPP_CELERY_EAGER`; no migrations in the `full` profile, keep it short and on point. Approved.

**Output:** spec `023bb68`; red/green pairs `059a926`/`8945756` (settings), `760da9e`/`6ca289d` (rate limit), `f432df4`/`97dfe1f` (Celery), `1e01dc0`/`b324755` (compose, just)
**Review notes:** `just check` backend gates green (35 tests, 100% coverage; no Redis or worker needed). The `full` profile was started for real: api, worker, postgres and redis all healthy, and 103 requests against the Redis-backed limiter gave 100 x 200 then 429 with `Retry-After: 60` and the uniform body.

## 2026-11-15 — Task domain and use cases (#8), plan
**Request:** plan slice `spec/8-task-domain.md` (AC-01 to AC-08) on branch `feat/task-domain`.

**Plan (approved):**
- **Layers:** `domain` (stdlib only): `TaskStatus`, `User`, `Task` with the rules as methods (create, update, change status, assign, visibility and permission checks, time passed in), and domain errors. `application`: `Protocol` ports `TaskRepository`, `UserRepository`, `UnitOfWork`, `Clock`, `Notifier`; `AssignmentMessage`, `TaskFilters`, `Page`; one use case per operation (create, get, update, delete, assign, change status, complete, list). Infrastructure and api: none. In-memory fakes for all ports in `backend/tests/fakes/`.
- **Tests, in order:** fakes as test support; domain tests (defaults, validation boundaries, transitions, same-status no-op, `completed_at`, permissions, visibility); use-case tests for create, visibility across every operation, update and delete, status and complete, assign, list.
- **Edge cases:** failed operations commit and send nothing; the message is sent after commit; not-found is checked before permission; terminal tasks can still be updated by the creator.
- **Out of scope:** SQLAlchemy, HTTP, JWT, passwords, Celery, notification delivery, overdue flagging.
- **Risks:** filter, sort and pagination logic is exercised through the fake, so the Postgres repository must meet the same expectations; the `UnitOfWork` shape may be adjusted when infrastructure is built.

**Branch:** `feat/task-domain`

**Output:** red/green pairs `cf0c215`/`f9c83f1` (task rules), `0395c45`/`9b2f7bc` (create, get), `662d121`/`496b93c` (update, delete), `9573c7d`/`ea34db4` (status, complete), `eaa8194`/`24118c8` (assign), `da1947d`/`433e5a3` (list); ports and fakes `6c7ce0d`; refactor `75c72f2`; review fix `2c0bc73`/`8a15121`
**Review notes:** one independent reviewer. Confirmed and fixed: naive due date filters were not validated. Noted, not changed: aware non-UTC datetimes are accepted as given (conversion belongs at the API boundary); an update with no fields still writes; a notifier failure after commit propagates (delivery is decided with the Celery slice); filter and sort run against the in-memory fake, so the Postgres repository needs the same tests.

## 2026-11-15 — Persistence and authentication (#9)
**Prompt:**
> Spec for `spec/9-persistence-and-auth.md` drafted from issue #9; the open questions (field rules, `name` on the domain user, `GET /auth/me` as the protected route, error mapping in `api`, `TASKAPP_JWT_SECRET`, lowercased emails, a throwaway test database on the compose Postgres) were answered and the spec approved before any code. Implementation followed the approved ACs, test first.

**Output:** spec `b29d824`; dependencies `3c08c30`; red/green pairs `c27750e`/`a1dafef` (user rules), `eb64bd7`/`7f28f15` (register, login, authenticate), `43c3d94`/`c3761f1` (hasher, JWT), `6f15e27`/`1f26295` (schema, migration, `just migrate`), `b38306f`/`c6b7eab` (repositories, unit of work), `60b81df`/`9200636` (endpoints); CI and README `d68ea93`; review fixes `9608e8c`/`a8f804d`, `187fb07`/`ecdaefc`, `34638eb`/`85c476b`, refactor `44cc52f`
**Review notes:** one independent reviewer. Confirmed and fixed: control characters in an email or name reached Postgres and caused a 500; unexpected errors returned a plain-text 500; `just migrate` ignored `backend/.env`; login had no password length bound; the password was hashed while a database connection was held. Noted, not changed: `save` re-inserts a task deleted in between and updates are last-write-wins (belongs with the task endpoints); a float `exp` such as `1e999` and a future `iat` need the signing secret to reach; `total` and the page are two statements at read committed isolation.

## 2026-11-15 — Tasks API (#10)
**Prompt:**
> Spec for `spec/10-tasks-api.md` drafted from issue #10; the open questions (404 for an unknown assignee, 422 with a message naming the maximum for `size` above 100, no 403 on complete, `/users` open to every signed-in user, 422 for a malformed id, a logging notifier until slice 11, PATCH applying fields and status together, unknown fields rejected) were answered and the spec approved before any code. Implementation followed the approved ACs, test first, with no separate planning step.

**Output:** spec `ccad8bd`; red/green pairs `7a8a7e4`/`7059422` (task views, user list, size message), `5443571`/`b27a558` (update fields and status together), `adc67f7`/`c5758f0` (batched user lookup, user listing, logging notifier), `b8f102c`/`c659953` (endpoints and Swagger); docs `0cb7161`; review fixes `4a8dba1`/`b8afa87`
**Review notes:** one independent reviewer. Confirmed and fixed: a huge `page` number overflowed the database offset (500); integer timestamps were accepted as dates; dates whose UTC conversion is out of range reached the database (500); the "rejected request changes nothing" test covered one endpoint only. Noted, not changed: a notifier that fails after commit would surface as a 500 for a stored change (matters once slice 11 swaps in a real broker); a self-assignment sends a message (decided in `8-task-domain`); `/users` exposes every email to any signed-in user (decided in the spec); `page` and `size` limits are enforced in the use case, not described by constraints in OpenAPI.

## 2026-11-15 — Notifications, per-user limits and seed (#11, second half)
**Prompt:**
> Spec for `spec/11-notifications-limits-seed.md` drafted from issue #11 and the first half already merged (`11-rate-limit-jobs-seed`); the open questions (authentication limit of 20 per minute per IP, per-user keys from a verified token, bounded retries with an idempotent task and an error log when they fail, demo users `test1`-`test3@example.com` with `password123`, seed does nothing when the demo users exist, a production guard) were answered and the spec approved before any code. The overview was updated to the 20 per minute limit.

**Output:** spec `98ec0de`, overview `81a082b`; red/green pairs `26d6e0e`/`07d22b6` (authentication limit), `ddd2e91`/`10853e0` and `3bef27b`/`f299ed9` (per-user keys), `81d3559`/`408e831` with `ae6a494` (Celery notification), `fa96d82`/`18633af` (seed), docs `00f3a44`; review fixes `332d060`/`bc63324`, `d42e1f1`/`0a9005a`, `a98e8a0`/`761fe6b`
**Review notes:** one independent reviewer. Confirmed and fixed: mounting routes directly (needed so the rate limiter can see them) silently dropped FastAPI dependency overrides; the short broker timeouts meant for publishing were also applied to the worker; a seed run that failed halfway left partial data that a rerun would call "already seeded"; the production guard missed `prod` and padded values, so seeding is now an allowlist. Noted, not changed: 404s and unmatched paths are not counted by the limiter (slowapi finds no handler for them); a limiter shared by several apps would stack route limits (tests only); a valid token escapes the per-address limit, bounded by the registration limit; `on_failure` expects positional task arguments; the retry behavior is tested through configuration and the failure hook, because Celery's eager mode re-runs retries.
