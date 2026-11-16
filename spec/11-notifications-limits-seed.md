# 11 - Assignment notifications, per-user limits and seed data

Issue: #11 · Depends on: 00-overview, 11-rate-limit-jobs-seed, 8-task-domain, 9-persistence-and-auth, 10-tasks-api · Layers: application / infrastructure / api / justfile

## Goal
The second half of issue #11, on top of what `11-rate-limit-jobs-seed` already delivered (the default limit, the Celery application, `just worker` and the compose `full` profile): a Celery adapter for the `Notifier` port so assigning a task queues one background notification, a stricter limit on login and register and per-user limit keys, and a seed command with documented demo credentials. This PR closes #11.

## Out of scope
- Email delivery and periodic jobs (the notification is only logged, as in `00-overview`).
- Retrying a failed notification.
- Trusting proxy headers for client addresses (unchanged from `11-rate-limit-jobs-seed`).

## Acceptance criteria
- AC-01: Given the stricter limit for authentication (20 requests per minute per client IP unless `TASKAPP_RATE_LIMIT_AUTH` says otherwise), when a client sends more `POST /auth/login` or `POST /auth/register` requests than that within a minute, then the extra requests are answered `429` with the uniform error body and `Retry-After` while other endpoints keep the default limit; given an invalid `TASKAPP_RATE_LIMIT_AUTH`, then the application fails to start with a message naming the setting.
- AC-02: Given a request with a valid bearer token, when the default limit is applied, then it is counted per user, so two users behind one address have separate budgets; given a request with no token or an invalid, expired or forged token, then it is counted per client address and can never use another user's budget.
- AC-03: Given a task is assigned to a user other than its current assignee (by `POST /tasks/{id}/assign`, or at creation with an assignee), when the change is saved, then exactly one notification task carrying the task id and the new assignee id is enqueued on the Celery broker after the change is committed; given the assignee is unchanged, the assignee is cleared, or the request fails, then nothing is enqueued.
- AC-04: Given a notification task, when a worker runs it, then it writes one log line naming the task and the assignee and changes nothing else; running it again for the same task and assignee gives the same outcome (it is idempotent, so retries and duplicates are safe); if running it fails, the worker retries a bounded number of times and, if it keeps failing, logs the error; with `TASKAPP_CELERY_EAGER` it runs in the same process, so tests need neither Redis nor a worker.
- AC-05: Given the broker cannot be reached, when a task is assigned, then the assignment is still stored and the request still succeeds; enqueueing is retried a bounded number of times within about a second (safe because the task is idempotent), and if every attempt fails the failure is logged as an error.
- AC-06: Given an empty database, when the seed command runs, then it creates three demo users (`test1@example.com`, `test2@example.com`, `test3@example.com`, all with the password `password123`) and about fifteen tasks that cover all five statuses, with some tasks overdue (due date passed, not completed or cancelled), some due soon and some without a due date, created and assigned across the demo users, and each demo user can log in with those credentials.
- AC-07: Given the seed has run, when it runs again, then nothing is added or changed and it says the data is already there.
- AC-08: Given `just seed`, then it runs the seed command against the configured database without needing Redis, a worker or a JWT secret; given `TASKAPP_ENVIRONMENT` is `production`, then the command refuses to run and changes nothing; and the README documents `just seed` and the demo credentials.

## Edge cases
- The authentication limit is per route and independent of the default budget: rejected login attempts do not use up a client's default budget on other endpoints beyond the one request each.
- A user with a valid token who is also over the limit by address is limited by their user budget, not their address.
- Assigning a task to its creator enqueues one notification, like any other assignee.
- Seeded tasks are created through the same application use cases as the API, so their invariants hold.
- If the rate-limit storage is unreachable, requests are served (unchanged).

## API contract
No new endpoints.

| Status | When | Body | Headers |
|---|---|---|---|
| 429 | a client exceeded the default, per-user or authentication limit | uniform error body, code `rate_limited` | `Retry-After: <seconds>` |

## AC -> test traceability
| AC | Test | Layer |
|---|---|---|
| AC-01 | `test_auth_rate_limit.py`: `test_ac01_*` (login and register limits, uniform 429, per route, per address, other endpoints unaffected); `test_settings.py`: `test_ac01_*` (default, environment, invalid value) | api, infrastructure |
| AC-02 | `test_rate_limit_key.py`, `test_user_rate_limit.py`, `test_composition.py`: `test_ac02_*` (valid token, anonymous, forged and expired tokens, separate budgets, default limit on every route) | infrastructure, api |
| AC-03 | `test_notifications.py`: `test_ac03_*`; `test_tasks_api.py`: `test_ac07_*` (one message on assign, none for no-ops, unassign or failures); `test_notification_failure.py` | infrastructure, api |
| AC-04 | `test_notifications.py`: `test_ac04_*` (log line, idempotent, retry configuration, final failure logged) | infrastructure |
| AC-05 | `test_notifications.py`: `test_ac05_*` (retries, bounded, unreachable broker); `test_notification_failure.py`: `test_ac05_*` (request succeeds, assignment stored) | infrastructure, api |
| AC-06 | `test_seed.py`: `test_ac06_*` (users, statuses, overdue and upcoming, logins) | composition |
| AC-07 | `test_seed.py`: `test_ac07_*` (second run changes nothing, message) | composition |
| AC-08 | `test_seed.py`: `test_ac08_*` (production guard); `test_compose_and_just.py`: `test_ac08_just_seed_runs_the_seed_command`; README | composition, justfile |
