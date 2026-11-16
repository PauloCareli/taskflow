# GenAI: how the AI output was checked

How AI was used in this project, on one page: how output was validated, how it was corrected, how edge cases, auth and validation were handled, and how performance and idiomatic quality were assessed. The logs behind it are [`docs/ai/prompts.md`](docs/ai/prompts.md) and [`docs/ai/corrections.md`](docs/ai/corrections.md).

## The prompt

Every slice started from a GitHub issue and the same prompt shape. This is the clean version, with the slice-specific parts in brackets:

> Read `AGENTS.md` and `backend/ENGINEERING.md` first.
>
> Goal: implement issue #[N] and nothing else. The approved spec is `spec/[N]-[slug].md`; its numbered acceptance criteria (AC-01, AC-02, ...) are the definition of done.
>
> Work test-first. For each AC, commit a failing test named after it (`test_ac03_...`), then commit the code that makes it pass. Conventional commits, `Refs #[N]`.
>
> Constraints: `domain` imports only the standard library; `application` imports only `domain`; time comes from the `Clock` port; no `python-jose` or `passlib`. Do not invent library APIs: if unsure, say so.
>
> Stop and show me the diff summary after each step. When done, run `just check` and report the real output, then list your assumptions.

What made this one prompt enough was what sat around it: the spec gate (a person approves the ACs before any code), the red/green commit history, the architecture rules enforced by import-linter, and a final review by a fresh agent that never saw the implementation.

## Sample: a domain rule, a use case and its test

**Rule** (`backend/src/taskapp/domain/task.py`): `completed` and `cancelled` are terminal.

```python
def change_status(self, new_status: TaskStatus, *, now: datetime) -> bool:
    """Move to `new_status`. Returns False (and changes nothing) if already there."""
    if new_status == self.status:
        return False
    if self.status in TERMINAL_STATUSES:
        raise InvalidTransition(f"cannot change a {self.status} task to {new_status}")
    self.status = new_status
    self.completed_at = now if new_status is TaskStatus.COMPLETED else None
    self.updated_at = now
    return True
```

**Test of the rule** (`tests/unit/domain/test_task.py`), parametrized over every terminal-to-other pair, also asserting nothing changed:

```python
@pytest.mark.parametrize(("source", "target"), TERMINAL_TO_DIFFERENT)
def test_ac03_terminal_statuses_cannot_change_to_a_different_status(source, target) -> None:
    task = make_task(status=source)

    with pytest.raises(InvalidTransition):
        task.change_status(target, now=LATER)

    assert task.status is source
    assert task.updated_at == NOW
```

**Use case** (`application/complete_task.py`): no rule of its own, it delegates to the status use case, which loads the task, checks the actor may see it, applies the domain rule and commits.

```python
class CompleteTask:
    def __init__(self, uow: UnitOfWork, clock: Clock) -> None:
        self._change_status = ChangeTaskStatus(uow, clock)

    async def execute(self, actor_id: UUID, task_id: UUID) -> Task:
        return await self._change_status.execute(actor_id, task_id, TaskStatus.COMPLETED)
```

**Test of the use case**, against in-memory fakes (no database, no framework). The clock is a port, so `completed_at` is exact:

```python
async def test_ac04_complete_sets_completed_at_from_the_clock(uow, clock, tasks, alice, bob) -> None:
    task = await seed_task(tasks, alice.id, assignee_id=bob.id)
    clock.set(clock.now() + timedelta(hours=3))

    completed = await CompleteTask(uow, clock).execute(bob.id, task.id)

    assert completed.status is TaskStatus.COMPLETED
    assert completed.completed_at == clock.now()
    assert uow.commits == 1
```

Here the assignee (not the creator) completes the task, which also covers the permission rule from the overview spec.

## Validation: how output was checked

The AI's own judgment was never the check. Each layer has a mechanical gate:

| What | Gate |
|---|---|
| Behaviour | Tests written first, named after the spec's ACs; the commit history shows red then green |
| Architecture | import-linter contracts: `domain` is stdlib only, `application` sees only `domain`. A deliberate violation was committed once to prove the contract fails, then reverted |
| Types and style | `mypy --strict`, `ruff`, `tsc` |
| Secrets | gitleaks in pre-commit and in CI over the pushed commits |
| Coverage | Backend coverage gate at 80% in `just check` and CI |
| Everything else | An independent review by a fresh agent with no knowledge of the implementation; each finding was reproduced against the code before it was acted on |

## Corrections

[`docs/ai/corrections.md`](docs/ai/corrections.md) lists 19 defects in AI-written code with how each was caught and the commit that fixed it. The review caught most of them, a failing test or running the app against Postgres caught others. Examples worth reading:

- The rate limiter was registered in a way that silently never applied to routes mounted through `include_router`. A test for per-user keys on a real route exposed it.
- The CI secret scan reused the pre-commit hook, which only scans staged files, so it scanned nothing on CI and always passed.
- A huge `page` number overflowed the database integer and returned a 500; reproduced over HTTP, then clamped in the repository.

## Edge cases, auth and validation

- **Auth:** `pyjwt` with a 30-minute token and `pwdlib[argon2]`, never `python-jose` or `passlib`. Missing, malformed, expired and tampered tokens all return 401. Wrong email and wrong password return the same generic 401. Emails are unique case-insensitively through a `lower(email)` index.
- **Permissions:** only the creator edits, deletes and assigns; the creator or assignee changes status. A task the user can neither see nor own returns 404, not 403, so ids do not leak.
- **Validation:** title and description lengths, no past due date on create, timezone-aware UTC only, page and size bounds, filters validated before reaching the database. Review found and fixed naive datetimes, Unix timestamps accepted as dates, and control characters in names and emails that PostgreSQL rejected.
- **Errors:** one body shape, `{"error": {"code", "message", "details"}}`, including a catch-all handler so an unexpected failure never leaks a stack trace or returns plain text.
- **Rate limits:** 100 requests a minute by default, 5 a minute on login and register, with short Redis timeouts so a dead Redis cannot stall the API.

## Performance and idiomatic quality

**N+1 queries.** Listing tasks runs a fixed number of statements however many rows come back. `test_ac06_listing_runs_the_same_number_of_statements_whatever_the_page_size` (`tests/integration/test_repositories.py`) listens to the engine's `before_cursor_execute` event, lists 2 and then 40 tasks out of 40 in the database, and asserts the statement count is equal and at most 3: one count, one page, one batched load of the people involved.

**Work done in SQL, not Python.** Filters, the sort (`due_date` ascending with nulls last, then newest first) and the offset and limit all run in the query. The repository clamps the offset so absurd pages return an empty list instead of an error.

**Indexes.** `status`, `due_date`, `creator_id` and `assignee_id` on `tasks`, and a unique index on `lower(email)` on `users` (`infrastructure/db/models.py`). `test_schema.py` covers the schema.

**Nothing CPU-bound on the event loop.** argon2 hashing and verification run through `asyncio.to_thread` (`infrastructure/security.py`), so a login does not stall other requests. The Celery publish does the same, and the notifier failing never fails the request.

**Idiomatic quality.** The code follows the layering in `backend/ENGINEERING.md`: thin routers that parse, call one use case and map the result; Pydantic schemas only in `api`; ORM models never leaving `infrastructure`; ports and in-memory fakes in place of mocks. Strict typing and import-linter keep it that way without relying on review.

**What was not measured.** There is no load test and no latency figure. The performance claims above are structural (query count, indexes, nothing blocking), checked by tests, not by benchmarks.
