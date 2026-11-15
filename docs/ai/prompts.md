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
