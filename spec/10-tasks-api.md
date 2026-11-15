# 10 - Tasks API

Issue: #10 · Depends on: 00-overview, 8-task-domain, 9-persistence-and-auth · Layers: application / infrastructure / api

## Goal
REST endpoints over the task use cases of `8-task-domain`, behind the bearer-token authentication of `9-persistence-and-auth`, with the ownership, pagination, filter and error rules of `00-overview`, and a user list for the assignee picker. Every endpoint is documented in Swagger. Business rules stay in `domain` and `application`; this slice only exposes them.

## Out of scope
- Rate limiting, background jobs and the delivery of the assignment notification (`11-rate-limit-jobs-seed`). Until then the running app passes the assignment message to a notifier that only logs it.
- Registration, login and token handling (`9-persistence-and-auth`).
- Task fields or statuses beyond those in `00-overview`.

## Acceptance criteria
- AC-01: Given a request without a valid bearer token, when it targets any of `GET /tasks`, `POST /tasks`, `GET|PATCH|DELETE /tasks/{id}`, `POST /tasks/{id}/assign`, `POST /tasks/{id}/complete` or `GET /users`, then it receives `401` with the uniform error body and nothing is read or changed.
- AC-02: Given a signed-in user, when they `POST /tasks` with a valid title (and optionally description, due date and assignee), then they receive `201` with the full `Task` (status `todo`, the caller as creator, `completed_at` null); given an invalid title, description or due date (empty or too long, in the past, naive, not a date), then they receive `422` and nothing is stored; given an `assignee_id` of an unknown user, then they receive `404` and nothing is stored.
- AC-03: Given a task the caller created or is assigned to, when they `GET /tasks/{id}`, then they receive `200` with the `Task`; given a task they neither created nor are assigned to, or an id that does not exist, then they receive the same `404`; given an id that is not a UUID, then they receive `422`.
- AC-04: Given a signed-in user, when they `GET /tasks`, then they receive `200 {items, total, page, size}` containing only tasks they created or are assigned to, with `status` (repeatable), `due_before` and `due_after` applied together as in `8-task-domain/AC-08`, sorted by due date ascending (no due date last) then newest first; `size` defaults to 25; `size` above 100 returns `422` with a message saying the maximum size is 100, and `size` below 1, `page` below 1, an unknown `status` or a naive or malformed date also return `422`; a page past the end returns no items with the correct `total`.
- AC-05: Given a task, when the creator sends `PATCH /tasks/{id}` with `title`, `description` and/or `due_date`, then they receive `200` with the updated `Task` (`null` clears description or due date; omitted fields are unchanged); given `status`, then the creator or the assignee receives `200` and the status follows the transitions in `00-overview`, an invalid transition returns `409`, and setting the status the task already has returns `200` unchanged; given a request that combines fields and status, then it is applied entirely or not at all; given the assignee sends fields other than `status`, then they receive `403` and nothing changes; given a task the caller cannot see, then `404`; given invalid values, then `422`.
- AC-06: Given a task, when its creator sends `DELETE /tasks/{id}`, then they receive `204` and the task is gone (`GET` then returns `404`); given the assignee, then `403` and the task remains; given a task the caller cannot see, then `404`.
- AC-07: Given a task, when its creator sends `POST /tasks/{id}/assign` with a user id, then they receive `200` with the updated assignee and one assignment message is passed to the notifier; given `null`, then the assignee is cleared; given the user is already the assignee, then `200` with no change and no message; given an unknown user, then `404` and nothing changes; given a non-creator, then `403`; given a task the caller cannot see, then `404`. When the creator or the assignee sends `POST /tasks/{id}/complete`, then they receive `200` with status `completed` and `completed_at` set, completing an already completed task returns `200` unchanged, completing a cancelled task returns `409`, and a user who cannot see the task gets `404`.
- AC-08: Given a signed-in user, when they `GET /users`, then they receive `200` with every registered user as `{id, email, name}` sorted by name, and never any password data; given the running API, then `/openapi.json` and `/docs` describe every endpoint above with its request and response schemas and the bearer security scheme.

## Edge cases
- A `Task` always contains `creator {id, name}` and `assignee {id, name}` (or `null`); dates are ISO 8601 in UTC.
- Unknown fields in a request body are rejected with `422`; `assignee_id` and `creator_id` cannot be changed through `PATCH`.
- An empty `PATCH` body is accepted and changes nothing.
- Query parameters that are repeated (`status=todo&status=blocked`) combine with OR within the parameter and AND across parameters.
- A failure part-way through a request leaves nothing stored and sends no message.
- Domain errors reach the client only through the single error mapping, with codes `validation_error`, `task_not_found`, `user_not_found`, `permission_denied` and `invalid_transition`.

## API contract
| Method | Path | Request | Response | Errors |
|---|---|---|---|---|
| GET | `/tasks` | query: `page`, `size`, `status` (repeatable), `due_before`, `due_after` | `200 {items: Task[], total, page, size}` | 401, 422 |
| POST | `/tasks` | `{title, description?, due_date?, assignee_id?}` | `201 Task` | 401, 404, 422 |
| GET | `/tasks/{id}` | | `200 Task` | 401, 404, 422 |
| PATCH | `/tasks/{id}` | `{title?, description?, due_date?, status?}` | `200 Task` | 401, 403, 404, 409, 422 |
| DELETE | `/tasks/{id}` | | `204` | 401, 403, 404, 422 |
| POST | `/tasks/{id}/assign` | `{assignee_id: uuid \| null}` | `200 Task` | 401, 403, 404, 422 |
| POST | `/tasks/{id}/complete` | | `200 Task` | 401, 403, 404, 409, 422 |
| GET | `/users` | | `200 [{id, email, name}]` | 401 |

`Task` = `{id, title, description, status, due_date, created_at, updated_at, completed_at, creator: {id, name}, assignee: {id, name} | null}`.

All errors use the uniform error body from `00-overview`.

## AC -> test traceability
| AC | Test | Layer |
|---|---|---|
| AC-01 | `test_tasks_api.py`: `test_ac01_*` (all eight endpoints, missing and invalid token, nothing changed) | api |
| AC-02 | `test_tasks_api.py`: `test_ac02_*` (full task, optional fields, invalid input, unknown assignee); `test_update_and_delete_task.py`, `test_task_views_and_users.py`: task views | api, application |
| AC-03 | `test_tasks_api.py`: `test_ac03_*` (creator and assignee, identical 404, malformed id) | api |
| AC-04 | `test_tasks_api.py`: `test_ac04_*` (visibility, default page, filters, sort, size limit message, invalid query); `test_repositories.py`: batched user lookup; `test_task_views_and_users.py`: size message | api, application, infrastructure |
| AC-05 | `test_tasks_api.py`: `test_ac05_*`; `test_update_and_delete_task.py`: `test_ac05_*` (fields and status together, atomic, no-ops) | api, application |
| AC-06 | `test_tasks_api.py`: `test_ac06_*` | api |
| AC-07 | `test_tasks_api.py`: `test_ac07_*` (assign, unassign, message, errors, complete); `test_notifier.py` | api, infrastructure |
| AC-08 | `test_tasks_api.py`: `test_ac08_*` (users, Swagger and bearer scheme); `test_repositories.py`: `test_ac08_*`; `test_task_views_and_users.py`: `test_ac08_*` | api, application, infrastructure |
