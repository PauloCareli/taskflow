# 13 - Documentation and release readiness

Issue: #13 · Depends on: every earlier spec · Layers: documentation (plus small fixes the clean-clone run turns up)

## Goal
Anyone can clone the repository, follow the README and run, test and understand the project. The README is rewritten as a single guide that is accurate against the repository as it is now, and a literal run of it from a fresh clone is the test of whether it is.

## Out of scope
- New features or behavior changes. Fixes are limited to what stops the README from working as written.
- Windows (macOS and Linux only; the README says so).
- Production deployment and hosting.

## Acceptance criteria
- AC-01: Given the README, when a reader looks for how to get started, then it names the prerequisites with the versions the project needs and gives one copy-pasteable quick start that ends with the app running, seeded demo data, and a successful sign-in with the documented demo credentials; the "work in progress" banner is gone.
- AC-02: Given an empty folder, no containers and an empty database, when someone runs `git clone` and follows the README literally, then they reach a running API (`/health`, `/docs`) and frontend, the demo data loaded, and a green `just check`, and every gap found on the way is fixed in the README or the code. The run uses its own containers and database, built from nothing, with the host ports configurable so it can run next to another stack.
- AC-03: Given the repository, then the README lists every `just` recipe, every `TASKAPP_*` and `VITE_*` setting (meaning, default, whether it is required) and the Docker route (the `full` profile, the secret it needs, and how to migrate and seed), the demo credentials, and a minimal quick fix for the common failure (a missing JWT secret, a port already in use, Docker not running); a test fails when a recipe or setting exists but the README does not mention it.
- AC-04: Given the README, which is the single reference document (there is no separate architecture file), then it gives an architecture overview (the layers and the dependency rule, how a request flows through them, where the frontend fits) and a key decisions section (spec-driven and test-first work, the error format, 404 instead of 403 for tasks a user cannot see, authentication and rate-limit choices, the notification flow, what is deliberately not built), each linking to the spec or guide that holds the detail.
- AC-05: Given the README, then an AI tooling section explains how AI was used in the project, where the prompts are kept (`docs/ai/prompts.md`), how its output was validated (red and green commits, quality gates, independent review, secret scanning) and corrected (`docs/ai/corrections.md`), and `docs/ai/usage.md` says plainly that exact hours, tokens and cost were not recorded, giving the author's own rough estimate instead (about one full Claude usage window plus roughly 20% of another) marked as an estimate.
- AC-06: Given the documentation, then no placeholder or stale document remains (`docs/spec.md` is deleted and the README points to `spec/`), and a test fails if a relative link or file path in the README does not exist.
- AC-07: Given the full history of the repository, when a secret scan runs over it, then it reports no findings (the documented demo credentials are not flagged); and given `main`, then CI is green and test coverage is at least 80% for both the backend (`just test`) and the frontend (`just fe-test`), with the figures recorded in the pull request.
- AC-08: Given the running app in a real browser, when the main flows are exercised (register, sign in, create, edit, assign, complete and delete a task, filter and page the list, sign out), then the browser console shows no errors and no warnings, and the result is recorded in the pull request.

## Edge cases
- A reader without `backend/.env` gets a clear message that points to the README when the API starts.
- A host that already uses port 5432, 6379, 8000 or 5173 is covered by a troubleshooting note.
- The README never contains a real secret; the demo credentials are marked demo-only.

## AC -> test traceability
| AC | Test | Layer |
|---|---|---|
| AC-01 | `test_readme.py`: `test_ac01_the_readme_is_not_marked_as_work_in_progress`; quick start run literally in AC-02 | docs |
| AC-02 | clean-clone run (below); `test_compose_and_just.py`: `test_ac02_host_ports_can_be_changed_*`; `test_settings.py`: `test_ac02_starting_without_a_secret_*` | compose, infrastructure |
| AC-03 | `test_readme.py`: `test_ac03_*` (every recipe, every setting, the env examples, demo credentials, troubleshooting) | docs |
| AC-04 | `test_readme.py`: `test_ac04_the_readme_has_the_required_sections` | docs |
| AC-05 | `test_readme.py`: `test_ac05_*` (AI logs linked, usage page honest) | docs |
| AC-06 | `test_readme.py`: `test_ac06_*` (no stale spec, every link and path resolves) | docs |
| AC-07 | full-history `gitleaks` scan and CI on `main` (below); coverage from `just test` and `just fe-test` | CI |
| AC-08 | browser run (below); `document.test.ts`: `test_ac08_declares_an_icon_that_exists_*` | frontend |

### Verification record
- **Clean clone (AC-02):** a fresh `git clone` of this branch, with its own containers and an empty database, followed the README literally: configuration, `uv sync`, `npm ci`, `just up`, `just migrate`, `just seed`, `just be`, `just fe`. `/health`, `/docs`, the frontend and its `/api` proxy answered, `test1@example.com` signed in and saw its tasks, and `just check` passed (409 backend tests, 123 frontend tests). The Docker route (`docker compose --profile full up --build --wait`) started a healthy API and worker, and an assignment through the API was delivered to the worker. Starting without a secret printed a message that points to the README.
- **Secret scan and CI (AC-07):** `gitleaks detect --log-opts="--all"` scanned 161 commits and found no leaks; CI on `main` is green. Backend coverage is 98.2% (`just test`); frontend coverage is 95.9% statements, 85.8% branches, 97.4% lines (`just fe-test`).
- **Browser (AC-08):** headless Chrome drove registration, sign-in, creating, editing, assigning, changing the status of, completing and deleting tasks, filtering by status and due date, paging, the status and not-found pages, and sign-out, at 1280px and 360px wide (24 steps). It found no console errors or warnings, no failed requests, no HTTP error responses and no horizontal scroll, after one fix: the page had no favicon and the browser logged a 404 for it.
