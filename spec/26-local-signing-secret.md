# 26 - Local runs generate and keep a signing secret

Issue: #26 · Delivered with the Docker stack pull request (#25), which it fixes · Depends on: 9-persistence-and-auth, 22-docker-stack · Layers: infrastructure (settings, composition), image, compose, documentation

## Goal
Trying the app locally, including with `docker compose`, no longer needs `TASKAPP_JWT_SECRET` to be set first. In a local environment the API generates a signing secret the first time it needs one, keeps it in a git-ignored file, and reuses it on every later start, so people stay signed in across API restarts. Every other environment still refuses to start without a real secret. This replaces the rule in `9-persistence-and-auth` that the secret is required with no exceptions.

## Out of scope
- Key rotation, refresh tokens, and changing token contents, lifetime or algorithm.
- Sharing one generated secret between several API processes on different machines (a real secret is for that).
- Anything beyond the API's start-up (the Celery worker, the seed and migrations never verify tokens).

## Acceptance criteria
- AC-01: Given `TASKAPP_ENVIRONMENT` is one of `local`, `dev`, `development` or `test` (`local` is the default), `TASKAPP_JWT_SECRET` is unset or empty and the secret file does not exist, when the API starts, then it starts, creates the file (readable and writable by its owner only) holding a new random secret, a user can register, sign in and use the token, and one warning is logged that names the file and says deleting it signs everyone out.
- AC-02: Given the same conditions and the secret file already exists with a valid secret, when the API starts again, then it uses that secret, so a token issued before the restart is still accepted afterwards, and the file is not changed.
- AC-03: Given the file exists but holds an invalid secret (empty or shorter than 32 characters), then it is replaced by a new random one and a warning says so; given the file cannot be created or written (a read-only location), then the API still starts with a secret kept in memory for that process only, and a warning says that everyone is signed out on restart.
- AC-04: Given any other value of `TASKAPP_ENVIRONMENT` (for example `production`, `staging` or an unknown value, with surrounding spaces and letter case ignored) and no secret, when the API starts, then it refuses to start with a message that names `TASKAPP_JWT_SECRET` and points to the README, and the secret file is neither read nor created; given `TASKAPP_JWT_SECRET` is set to a non-empty value shorter than 32 characters, then it refuses to start in every environment.
- AC-05: Given `TASKAPP_JWT_SECRET` is set to a valid secret, then it is used in every environment and the secret file is neither read nor created.
- AC-06: Given a generated secret, then it is random with at least 32 bytes of entropy, is the same for every part of the API within one process (a token issued at sign-in is accepted by the request that follows, including by the per-user rate limit), and never appears in logs or error messages.
- AC-07: Given a local environment, when `just seed`, the Celery worker, `just migrate` or any other command that does not issue or verify tokens runs, then none of them creates the secret file or logs the warning.
- AC-08: Given the repository and the images, then the secret file is ignored by git and left out of every Docker build context, the API container keeps it on a named volume owned by the non-root user so it survives `docker compose down` and `up` (and `down -v` signs everyone out), and the README, `backend/.env.example` and the compose file explain all of this, including that setting a real secret is what to do in any shared or non-local environment.

## Edge cases
- Two API processes starting at the same moment create the file once, and both end up using the same secret.
- An empty `TASKAPP_JWT_SECRET` passed through by `docker compose` from a host that has no value counts as unset.
- The file's location is a setting (`TASKAPP_JWT_SECRET_FILE`), defaulting to a hidden file in the directory the API runs from (`backend/` for `just be`) and `/data/jwt-secret` in the container.
- The environment check uses the same list of local environments as `just seed`; there is one definition.
- The warning is logged once per process, and never contains the secret.
- In a non-local environment every process that builds the settings, including the worker, still needs `TASKAPP_JWT_SECRET`, as today; only the API ever uses it.

## API contract
No API changes.

## AC -> test traceability
| AC | Test | Layer |
|---|---|---|
