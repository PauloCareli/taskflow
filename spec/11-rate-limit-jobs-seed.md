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
| AC-01 | `test_ac01_forwarded_for_headers_do_not_change_the_client_key` (`tests/integration/test_rate_limit.py`) | api |
| AC-01 | `test_ac01_health_is_exempt_from_the_limit` (`tests/integration/test_rate_limit.py`) | api |
| AC-01 | `test_ac01_requests_over_the_limit_get_429` (`tests/integration/test_rate_limit.py`) | api |
| AC-02 | `test_ac02_a_429_is_still_answered_when_the_storage_fails_afterwards` (`tests/integration/test_rate_limit.py`) | api |
| AC-02 | `test_ac02_a_429_uses_the_uniform_error_body_and_retry_after` (`tests/integration/test_rate_limit.py`) | api |
| AC-03 | `test_ac03_a_client_is_served_again_after_the_window_elapsed` (`tests/integration/test_rate_limit.py`) | api |
| AC-03 | `test_ac03_each_client_ip_has_its_own_budget` (`tests/integration/test_rate_limit.py`) | api |
| AC-04 | `test_ac04_an_invalid_rate_limit_fails_and_names_the_setting` (`tests/unit/test_settings.py`) | infrastructure |
| AC-04 | `test_ac04_default_rate_limit_is_100_per_minute` (`tests/unit/test_settings.py`) | infrastructure |
| AC-04 | `test_ac04_main_app_applies_the_configured_default_limit` (`tests/integration/test_health.py`) | api |
| AC-04 | `test_ac04_rate_limit_comes_from_the_environment` (`tests/unit/test_settings.py`) | infrastructure |
| AC-05 | `test_ac05_requests_are_served_when_the_storage_is_unreachable` (`tests/integration/test_rate_limit.py`) | api |
| AC-05 | `test_ac05_the_redis_storage_gives_up_quickly_instead_of_hanging_requests` (`tests/integration/test_rate_limit.py`) | api |
| AC-06 | `test_ac06_celery_eager_can_be_switched_on` (`tests/unit/test_settings.py`) | infrastructure |
| AC-06 | `test_ac06_celery_runs_tasks_through_the_broker_by_default` (`tests/unit/test_settings.py`) | infrastructure |
| AC-06 | `test_ac06_creating_the_app_does_not_connect_to_the_broker` (`tests/unit/test_celery_app.py`) | infrastructure |
| AC-06 | `test_ac06_eager_mode_runs_tasks_in_process_without_a_broker` (`tests/unit/test_celery_app.py`) | infrastructure |
| AC-06 | `test_ac06_only_json_is_accepted_and_returned` (`tests/unit/test_celery_app.py`) | infrastructure |
| AC-06 | `test_ac06_the_broker_is_the_configured_redis_url` (`tests/unit/test_celery_app.py`) | infrastructure |
| AC-07 | `test_ac07_just_worker_starts_a_celery_worker_for_the_project_app` (`tests/unit/test_compose_and_just.py`) | compose |
| AC-07 | `test_ac07_the_worker_entrypoint_module_exposes_the_app` (`tests/unit/test_celery_app.py`) | infrastructure |
| AC-08 | `test_ac08_api_and_worker_only_start_with_the_full_profile` (`tests/unit/test_compose_and_just.py`) | compose |
| AC-08 | `test_ac08_api_and_worker_report_health_and_use_service_hostnames` (`tests/unit/test_compose_and_just.py`) | compose |
| AC-08 | `test_ac08_api_and_worker_wait_for_healthy_dependencies` (`tests/unit/test_compose_and_just.py`) | compose |
| AC-08 | `test_ac08_postgres_and_redis_start_without_a_profile` (`tests/unit/test_compose_and_just.py`) | compose |
| AC-08 | `test_ac08_the_api_is_checked_through_health_and_the_worker_through_a_celery_ping` (`tests/unit/test_compose_and_just.py`) | compose |
| AC-08 | `test_ac08_the_worker_runs_the_celery_app_and_nothing_runs_migrations` (`tests/unit/test_compose_and_just.py`) | compose |
