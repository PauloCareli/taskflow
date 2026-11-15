# 8 - Task domain and use cases

Issue: #8 · Depends on: 00-overview, backend scaffold (#1) · Layers: domain / application

## Goal
The framework-free core of the product: the `Task` and `User` entities with their rules, and the application use cases (create, get, update, delete, assign, change status, complete, list) behind ports, verified against in-memory fakes. Rules come from `00-overview`; this spec adds no HTTP, database, auth or background-job behavior.

## Out of scope
- SQLAlchemy repositories, migrations, HTTP routes and error mapping, JWT and password handling, Celery.
- Registration and login; users are given to the use cases as already-authenticated callers.
- Overdue flagging.

## Acceptance criteria
- AC-01: Given a caller and valid input, when they create a task, then it is stored with status `todo`, the caller as creator, `completed_at` empty, `created_at` and `updated_at` taken from the clock, and an optional description, due date and assignee as given.
- AC-02: Given a title that is empty or longer than 120 characters or a description longer than 2000 characters, when a task is created or updated, then a validation error is raised and nothing is stored; titles of 1 and 120 characters and a description of 2000 characters are accepted. Given a due date earlier than the clock's current time, when a task is created, then a validation error is raised; when a task is updated, then a past due date is accepted. The creator can update the title, description and due date; the other fields change only through assign and status change.
- AC-03: Given a task, when its status changes, then `todo`, `in_progress` and `blocked` may move to any other status; given `completed` or `cancelled`, then a change to a different status raises an invalid-transition error and the task is unchanged. Given a change to the status the task already has, then the call succeeds as a no-op: nothing is stored, `updated_at` is unchanged and no transaction is committed.
- AC-04: Given a task moved to `completed`, then `completed_at` is set from the clock; given it ends in any other status, then `completed_at` is empty.
- AC-05: Given a task the caller can see, when a non-creator edits, deletes or assigns it, then a permission error is raised and nothing changes; when the creator or the assignee changes its status (including completing it), then it succeeds; when a user who is neither does, then a permission error is raised.
- AC-06: Given a task the caller neither created nor is assigned to (or that does not exist), when they get, update, delete, assign, change the status of, or complete it, then a task-not-found error is raised, the same as for a missing id; and when they list tasks, then it is never included.
- AC-07: Given the creator assigns a task (including to themselves) to an existing user other than its current assignee, then the assignee is saved and exactly one message (task id and new assignee id) is passed to the notifier; given the user is already the assignee, then the call succeeds as a no-op with nothing stored and no message; given the creator unassigns the task, then the assignee is cleared and no message is sent; given the user does not exist, then a user-not-found error is raised, nothing changes and no message is sent. The notifier only receives the message: delivery is not implemented in this slice.
- AC-08: Given tasks visible to the caller, when they list with optional `status` (one or more), `due_before` and `due_after` filters, `page` and `size`, then only matching tasks are returned, sorted by due date ascending (no due date last) then creation time descending, with `total`, `page` and `size`; `size` defaults to 25, a `size` above 100 or below 1 or a `page` below 1 raises a validation error.

## Edge cases
- Any failed operation leaves stored data unchanged and sends no message (the unit of work does not commit).
- A task created with an assignee passes one message to the notifier, as for an assignment.
- Terminal tasks (`completed`, `cancelled`) can still have title, description and due date updated by the creator.
- Every successful change sets `updated_at` from the clock.
- A page beyond the last returns no items with the correct `total`.
- Combining filters applies all of them; filters never widen visibility.
- Times are timezone-aware UTC; naive datetimes are rejected as validation errors.

## API contract
None. This slice has no HTTP surface.

## AC -> test traceability
| AC | Test | Layer |
|---|---|---|
