# 11 - Rate limiting and background jobs (infrastructure)

Issue: #11 · Depends on: 00-overview, backend scaffold · Layers: infrastructure, api, compose, justfile

## Goal
The infrastructure half of issue #11: a global request rate limit backed by Redis that answers with the uniform error body, a Celery application on the Redis broker with a worker entrypoint, and a compose `full` profile that runs the API and the worker next to Postgres and Redis. No use case is wired to Celery yet.

This is the first of two PRs for #11 and does not close it.

## Out of scope
Left for the second PR, after the tasks API (#10) is merged:
- The notification on assignment (Celery adapter for the `Notifier` port, thin idempotent task).
- Stricter limits on `POST /auth/login` and `POST /auth/register`.
- Per-user rate-limit keys (anonymous and authenticated clients are both keyed by client IP for now).
- Seed data, `just seed` and the documented demo credentials.
- Email delivery and periodic jobs.

## Acceptance criteria

### Rate limiting
- AC-01: Given a default limit of N requests per minute per client IP, when a client sends N requests and then one more within the window, then the first N succeed and the extra one is answered with `429`.
- AC-02: Given a `429` response, then its body is the uniform error body `{"error": {"code": "rate_limited", "message": <human text>, "details": []}}` and it carries a `Retry-After` header with a whole number of seconds greater than zero.
- AC-03: Given two clients with different IPs, when one exceeds the limit, then the other is still served; and given the window has elapsed, then the first client is served again.
- AC-04: Given the setting `TASKAPP_RATE_LIMIT_DEFAULT` (a limit string such as `100/minute`) is unset, then the limit is 100 requests per minute; given it is set to a valid limit string, then that limit applies; given it is invalid, then the application fails to start with a message naming the setting.
- AC-05: Given the rate-limit storage (Redis) is unreachable, when a request arrives, then it is served normally instead of failing with a 5xx.

### Background jobs
- AC-06: Given the Celery application, then it uses `TASKAPP_REDIS_URL` as broker, accepts and returns JSON only, importing the module opens no connection to Redis, and it can be switched to run tasks eagerly with `TASKAPP_CELERY_EAGER` so tests need neither Redis nor a worker.
- AC-07: Given `just worker`, then a Celery worker starts from the project's Celery application with the local settings, and shuts down cleanly on interrupt.

### Docker
- AC-08: Given `docker compose --profile full up`, then `api` and `worker` start next to `postgres` and `redis`, built from the existing backend Dockerfile, each waiting for the services it needs to be healthy and each reporting healthy itself (API via `GET /health`, worker via a Celery ping), without running migrations; given `docker compose up` without the profile, then only `postgres` and `redis` start, as today.

## Edge cases
- `GET /health` is exempt from the limit.
- Requests rejected with `429` do not count against the window again.
- Behind the compose network the limit is applied per client IP as seen by the API; trusting proxy headers is not enabled.
- The worker runs as the same non-root user as the API image.

## API contract
No new endpoints.

| Status | When | Body | Headers |
|---|---|---|---|
| 429 | client exceeded the default limit | uniform error body, code `rate_limited` | `Retry-After: <seconds>` |

## AC -> test traceability
| AC | Test | Layer |
|---|---|---|
