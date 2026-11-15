# 08 - Frontend scaffold

Issue: #4 · Depends on: 00-overview, backend scaffold (#1) · Layers: frontend, justfile, CI

## Goal
A Vite + React + TypeScript app that proves the frontend wiring end to end: design tokens, an app shell, routing, server-state fetching and a typed API client, exercised by a home page that reports the backend `/health` status. It runs locally with `just fe`, and its lint, format, typecheck and tests run in `just check` and CI.

## Out of scope
- Auth flow (login, registration, token storage, 401 handling). Only the hook point that lets a bearer token be attached is in scope.
- Task screens and any endpoint other than `GET /health`.
- Production hosting and a frontend Docker image.
- Light theme (dark only in v1, see `frontend/STYLE.md`).

## Acceptance criteria

### Home page
- AC-01: Given the API responds `200 {"status":"ok"}`, when the user opens `/`, then the page shows the API as healthy.
- AC-02: Given the health request is in flight, when the user opens `/`, then the page shows a loading state and neither the healthy nor the error message.
- AC-03: Given the API is unreachable, times out (10 seconds), responds with a non-2xx status, or responds `200` with a body that is not `{"status": <string>}`, when the user opens `/`, then the page shows a clear error saying the API is unavailable and offers a retry; the request is not retried automatically, and retry re-requests without reloading the page.
- AC-04: Given the user opens a path that matches no route, then the page shows a not-found view with a link back to `/`; given an error is thrown while rendering, then the error boundary shows a fallback message and the app shell stays visible.

### API client
- AC-05: Given a request, when it succeeds, then the client resolves with the parsed JSON body; and when a bearer-token provider is registered and returns a token, the request carries `Authorization: Bearer <token>`, otherwise the header is absent.
- AC-06: Given a failed request, when a client call is made, then it rejects with an `ApiError` that is typed and distinguishable by cause: for a non-2xx response with the uniform error body `{"error": {"code", "message", "details"}}` it carries the HTTP status, `code`, `message` and `details`; for a non-2xx response with any other body (empty, HTML, invalid JSON) it carries the HTTP status and a generic message; for a network failure or timeout it carries no HTTP status.

### Configuration
- AC-07: Given `VITE_API_BASE_URL` is an absolute `http`/`https` URL or an absolute path such as `/api`, when the app starts, then requests are sent under it, with or without a trailing slash and keeping any path prefix; given it is unset when running `just fe`, then `/api` is used and the dev server proxies it to the local backend.
- AC-08: Given `VITE_API_BASE_URL` is empty or is neither an absolute `http`/`https` URL nor an absolute path (in the build, the test run, or the dev server started outside `just fe`), when the app starts, then it fails immediately with a message naming the setting and the expected format, and nothing renders.

### Design, layout and accessibility
- AC-09: Given the tokens in `frontend/STYLE.md`, then each is defined once as a CSS variable, the Tailwind theme maps to those variables, and components contain no hardcoded color values; a utility built from a token renders with the variable's value.
- AC-10: Given a viewport of 360px or 1280px wide, when the home page renders in any state, then there is no horizontal scroll, the shell shows a header and a main container, and the retry control is keyboard operable with a visible focus and an accessible name.
- AC-11: Given the app runs under StrictMode, when the home page loads, then exactly one health request is sent and no console warnings or errors are produced.

### Quality gates
- AC-12: Given any test that calls `console.error` or `console.warn`, when the suite runs, then that test fails; and app code has no `console.*`, `any` or `@ts-ignore`, enforced by lint.
- AC-13: Given the frontend, when `just fe` runs, then the dev server serves the home page; and `just check` and CI run the same frontend checks (eslint with typescript-eslint, react-hooks and jsx-a11y; prettier check; `tsc`; vitest with coverage failing under 80%, entry file excluded), each also runnable on its own via `fe-lint`, `fe-typecheck` and `fe-test`, and a failure in any of them fails `just check` and the CI build.

## Edge cases
- Retry while a request is in flight does not send a second concurrent request.
- Unknown extra fields in the error body or the health body are ignored.
- Error body with `details` missing or null is accepted and exposed as an empty list; `details` items are opaque (`unknown[]`).
- Base URL with a trailing slash produces the same request URL as without one.

## API contract
| Method | Path | Request | Response | Errors |
|---|---|---|---|---|
| GET | `/health` | none | `200 {"status": "ok"}` | non-2xx; uniform error body when present |

## AC -> test traceability
| AC | Test | Layer |
|---|---|---|
| AC-01 | `HealthStatus.test.tsx`: `test_ac01_shows_the_api_as_healthy_when_it_responds_ok` | frontend |
| AC-02 | `HealthStatus.test.tsx`: `test_ac02_shows_only_a_loading_state_while_the_request_is_in_flight` | frontend |
| AC-03 | `HealthStatus.test.tsx`: `test_ac03_*` (error states, no automatic retry, retry, no concurrent retry, schema) | frontend |
| AC-04 | `App.test.tsx`: `test_ac04_*` (not found, link home, render error fallback) | frontend |
| AC-05 | `http.test.ts`: `test_ac05_*` (parsed body, bearer token present and absent) | frontend |
| AC-06 | `http.test.ts`: `test_ac06_*` (uniform body, other bodies, network, timeout, invalid JSON) | frontend |
| AC-07 | `env.test.ts`: `test_ac07_*`; `http.test.ts`: `test_ac07_*` (URL joining) | frontend |
| AC-08 | `env.test.ts`: `test_ac08_*`; build and dev server checked by running them without the variable | frontend |
| AC-09 | `tokens.test.ts`: `test_ac09_*` (defined once, Tailwind mapping, no hardcoded colors, utility resolves to variable) | frontend |
| AC-10 | `App.test.tsx`: `test_ac10_*` (shell landmarks, keyboard retry, overflow guards); 360px and 1280px checked in a browser | frontend |
| AC-11 | `App.test.tsx`: `test_ac11_sends_exactly_one_health_request_and_logs_nothing` | frontend |
| AC-12 | `consoleGuard.test.ts`: `test_ac12_*`; lint bans checked with a deliberate violation | frontend |
| AC-13 | `just fe`, `just check` and the CI workflow, run and read | justfile, CI |
