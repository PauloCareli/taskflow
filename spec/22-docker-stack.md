# 22 - Run the app in Docker: backend and frontend profiles

Issue: #22 · Depends on: 11-rate-limit-jobs-seed, 12-frontend-app, 13-documentation-release · Layers: compose, Dockerfiles, serving configuration, CI

## Goal
`docker compose` can run the backend (API, worker, schema migration) and the frontend (a web container) on their own or together, so the whole app starts from Docker without installing uv or Node on the host. The `just` workflow for development is unchanged.

## Out of scope
- Production hosting, TLS, image publishing and scaling.
- Changes to the API or the frontend application code.
- Trusting proxy headers for the client address (the existing rate-limit behavior is unchanged).

## Acceptance criteria
- AC-01: Given no profile, when `docker compose up` runs, then only PostgreSQL and Redis start, as today; given the `api` profile, then a one-shot migration step brings the database schema to the latest version, after which the API and the worker start and report healthy.
- AC-02: Given the `web` profile, when it starts, then a web container serves the built frontend on `WEB_PORT` (default 8080), answers client-side routes such as `/login` with the application, forwards `/api/*` to the API at `API_UPSTREAM` (default the `api` service) with the `/api` prefix removed, and reports healthy; it starts without the API, the worker, PostgreSQL or Redis, and an API running on the host can be used by setting `API_UPSTREAM`.
- AC-03: Given the `full` profile, when it starts, then everything from AC-01 and AC-02 runs together, the web container waits for a healthy API, and after the demo data is loaded a user can sign in at `http://localhost:8080` as `test1@example.com` and use the app through the web container.
- AC-04: Given the stack is running, when `docker compose run --rm seed` runs, then it loads the demo users and tasks, running it again changes nothing, and it needs no tools on the host beyond Docker.
- AC-05: Given the migration step, when `up` runs repeatedly, then it succeeds each time and changes nothing once the schema is current; given it fails, then the API and the worker do not start.
- AC-06: Given the images, then the frontend image is built in stages: Node builds the application, and the final image holds only the build output and Vite's preview server with its own dependencies (served from a small dedicated configuration, not the development one), runs as a non-root user, and contains no application source, test or build tooling, or `.env` files; `.dockerignore` files keep those out of the build context, and the API image carries the migrations.
- AC-07: Given the configuration, then the host ports are `WEB_PORT`, `API_PORT`, `POSTGRES_PORT` and `REDIS_PORT` with unchanged defaults for the existing ones, an empty `TASKAPP_JWT_SECRET` stops the API with a clear message, and the README documents the profiles, the variables and every route to start the app (Docker, backend only, frontend only, development with `just`).
- AC-08: Given CI, when a pull request changes the Dockerfiles or the compose file, then CI builds both images and fails if a build fails; and given a fresh clone, then each of the three routes (`api`, `web` against an API on the host, `full`) starts healthy and passes a smoke check (sign in through the route and list tasks), recorded in the pull request.

## Edge cases
- Starting `web` alone shows the application, and its API calls fail with the normal "API unavailable" state until an API is reachable.
- On Linux the web container reaches an API on the host through `host.docker.internal` (mapped to the host gateway).
- Behind the web container every client reaches the API from the same address, so anonymous requests (including login and register) share one rate-limit budget; signed-in requests are still counted per user. The README says so.
- Ports already in use are covered by the troubleshooting section and the port variables.
- The web container serves the same build whatever the API address, because `/api` is resolved by the proxy at start-up, not at build time.
- The web container uses Vite's preview server, which Vite documents as meant for local use rather than production; replacing it with a production web server later does not change the profiles or the variables.

## API contract
No API changes.

| Container | Port | Notes |
|---|---|---|
| `web` | `WEB_PORT` -> 8080 | static frontend, `/api/*` proxied to `API_UPSTREAM` |
| `api` | `API_PORT` -> 8000 | unchanged |

## AC -> test traceability
| AC | Test | Layer |
|---|---|---|
