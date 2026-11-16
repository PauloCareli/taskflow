# Overview spec

Product-wide rules. Slice specs (`spec/NN-<slice>.md`) add numbered ACs and refer back here.

## Product
Taskflow: users create tasks, assign them to other users, track status, and filter/page through them.

## Users and permissions
- Any registered user can create tasks and becomes the **creator**.
- **Creator**: edit, delete, assign/reassign.
- **Creator or assignee**: change status, including complete.
- A user sees only tasks they created or are assigned to. Others get 404 (not 403) to avoid leaking existence.

## Task
| Field | Rule |
|---|---|
| id | UUID |
| title | required, 1-120 chars |
| description | optional, up to 2000 chars |
| status | `todo`, `in_progress`, `completed`, `cancelled`, `blocked`; default `todo` |
| due_date | optional, timezone-aware UTC; must not be in the past when set on create |
| creator_id | required |
| assignee_id | optional |
| created_at, updated_at | UTC, set by the system |
| completed_at | set when status becomes `completed`, otherwise null |

## Status transitions
- `todo`, `in_progress`, `blocked` may move between each other and to `completed` or `cancelled`.
- `completed` and `cancelled` are terminal in v1 (no reopening).
- Invalid transitions are a domain error (HTTP 409).

## Listing
- Pagination: `page` (>= 1) and `size` (default **25**, max **100**). Response: `{items, total, page, size}`.
- Filters now: `status` (one or more), `due_before`, `due_after`. More filters will be added later, so the filter parsing must be extensible (one object, not per-endpoint params).
- Default sort: `due_date` ascending, nulls last, then `created_at` descending.

## Errors
Uniform body: `{"error": {"code": "<machine_code>", "message": "<human text>", "details": [...]}}`. Codes map from domain errors in one place (the api layer).

## Auth
- Register and login with email + password, JWT access token (short-lived, 30 min).
- Passwords hashed with argon2 (pwdlib). No refresh tokens in v1.

## Rate limiting
- Default 100 requests/minute per user (per IP when anonymous).
- `POST /auth/login` and `/auth/register`: 20/minute per IP.
- 429 with the standard error body and `Retry-After`.

## Background jobs
- On assignment, a Celery task (Redis broker) sends a notification. v1 logs it.

## Seed data
- 3 demo users and about 15 tasks across all statuses and due dates (some overdue). Credentials documented in the README.

## Slice index
| Spec | Issue | Status |
|---|---|---|
| `08-frontend-scaffold.md` | #4 | done |

## AC conventions
- Format: `AC-NN: Given ..., when ..., then ...`. Numbers restart at AC-01 in each slice spec; refer to them as `<spec>/AC-NN` across specs.
- New slice specs are named after their GitHub issue number: `spec/<issue>-<slug>.md`.
- Tests are named after them: `test_ac07_complete_sets_completed_at`.
