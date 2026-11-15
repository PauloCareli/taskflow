import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import pytest
from httpx import AsyncClient, Response

PASSWORD = "s3cret-pass"
TASK_KEYS = {
    "id",
    "title",
    "description",
    "status",
    "due_date",
    "created_at",
    "updated_at",
    "completed_at",
    "creator",
    "assignee",
}


@dataclass
class Person:
    id: str
    name: str
    headers: dict[str, str]


async def sign_up(client: AsyncClient, name: str) -> Person:
    email = f"{name.lower()}@example.com"
    await client.post("/auth/register", json={"email": email, "name": name, "password": PASSWORD})
    login = await client.post("/auth/login", json={"email": email, "password": PASSWORD})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    me = await client.get("/auth/me", headers=headers)
    return Person(id=me.json()["id"], name=name, headers=headers)


@pytest.fixture
async def alice(client: AsyncClient) -> Person:
    return await sign_up(client, "Alice")


@pytest.fixture
async def bob(client: AsyncClient) -> Person:
    return await sign_up(client, "Bob")


@pytest.fixture
async def carol(client: AsyncClient) -> Person:
    return await sign_up(client, "Carol")


def in_days(days: float) -> str:
    return (datetime.now(UTC) + timedelta(days=days)).isoformat()


async def create(client: AsyncClient, who: Person, **body: Any) -> dict[str, Any]:
    response = await client.post("/tasks", json={"title": "Task", **body}, headers=who.headers)
    assert response.status_code == 201, response.text
    task: dict[str, Any] = response.json()
    return task


def assert_error(response: Response, status: int, code: str) -> dict[str, Any]:
    assert response.status_code == status, response.text
    error: dict[str, Any] = response.json()["error"]
    assert error["code"] == code
    assert isinstance(error["message"], str)
    assert isinstance(error["details"], list)
    return error


# --- AC-01: authentication ---------------------------------------------------------------

SOME_ID = str(uuid4())
ENDPOINTS: list[tuple[str, str, dict[str, Any] | None]] = [
    ("GET", "/tasks", None),
    ("POST", "/tasks", {"title": "x"}),
    ("GET", f"/tasks/{SOME_ID}", None),
    ("PATCH", f"/tasks/{SOME_ID}", {"title": "x"}),
    ("DELETE", f"/tasks/{SOME_ID}", None),
    ("POST", f"/tasks/{SOME_ID}/assign", {"assignee_id": None}),
    ("POST", f"/tasks/{SOME_ID}/complete", None),
    ("GET", "/users", None),
]


@pytest.mark.parametrize(("method", "path", "body"), ENDPOINTS)
async def test_ac01_every_endpoint_requires_a_valid_token(
    client: AsyncClient, method: str, path: str, body: dict[str, Any] | None
) -> None:
    for headers in ({}, {"Authorization": "Bearer not-a-token"}):
        response = await client.request(method, path, json=body, headers=headers)

        assert_error(response, 401, "invalid_token")


async def test_ac01_rejected_requests_change_nothing(
    client: AsyncClient, alice: Person, bob: Person
) -> None:
    task = await create(client, alice, assignee_id=bob.id)
    await client.post("/tasks", json={"title": "no token"})
    await client.patch(f"/tasks/{task['id']}", json={"title": "hijacked"})
    await client.post(f"/tasks/{task['id']}/assign", json={"assignee_id": None})
    await client.post(f"/tasks/{task['id']}/complete")
    await client.delete(f"/tasks/{task['id']}")

    listing = (await client.get("/tasks", headers=alice.headers)).json()
    assert listing["total"] == 1
    assert listing["items"] == [task]


# --- AC-02: create -----------------------------------------------------------------------


async def test_ac02_create_returns_the_full_task_owned_by_the_caller(
    client: AsyncClient, alice: Person
) -> None:
    response = await client.post("/tasks", json={"title": "Write spec"}, headers=alice.headers)

    assert response.status_code == 201
    task = response.json()
    assert set(task) == TASK_KEYS
    assert task["title"] == "Write spec"
    assert task["status"] == "todo"
    assert task["description"] is None
    assert task["due_date"] is None
    assert task["completed_at"] is None
    assert task["assignee"] is None
    assert task["creator"] == {"id": alice.id, "name": "Alice"}


async def test_ac02_create_accepts_description_due_date_and_assignee(
    client: AsyncClient, alice: Person, bob: Person, caplog: pytest.LogCaptureFixture
) -> None:
    due = datetime.now(timezone(timedelta(hours=2))) + timedelta(days=2)

    with caplog.at_level(logging.INFO, logger="taskapp.notifications"):
        task = await create(
            client,
            alice,
            description="details",
            due_date=due.isoformat(),
            assignee_id=bob.id,
        )

    assert task["description"] == "details"
    assert datetime.fromisoformat(task["due_date"]) == due
    assert task["assignee"] == {"id": bob.id, "name": "Bob"}
    assert len(caplog.records) == 1


@pytest.mark.parametrize(
    "body",
    [
        {"title": ""},
        {"title": "x" * 121},
        {"title": "ok", "description": "d" * 2001},
        {"title": "ok", "due_date": "2020-01-01T00:00:00+00:00"},
        {"title": "ok", "due_date": "2999-01-01T00:00:00"},
        {"title": "ok", "due_date": "not a date"},
        {"title": "ok", "due_date": 1893456000},
        {"title": "ok", "due_date": "0001-01-01T00:00:00+05:00"},
        {"title": "ok", "creator_id": str(uuid4())},
        {"title": "ok", "assignee_id": "not-a-uuid"},
        {},
    ],
)
async def test_ac02_invalid_input_is_a_422_and_stores_nothing(
    client: AsyncClient, alice: Person, body: dict[str, Any]
) -> None:
    response = await client.post("/tasks", json=body, headers=alice.headers)

    assert_error(response, 422, "validation_error")
    assert (await client.get("/tasks", headers=alice.headers)).json()["total"] == 0


async def test_ac02_an_unknown_assignee_is_a_404_and_stores_nothing(
    client: AsyncClient, alice: Person
) -> None:
    response = await client.post(
        "/tasks", json={"title": "x", "assignee_id": str(uuid4())}, headers=alice.headers
    )

    assert_error(response, 404, "user_not_found")
    assert (await client.get("/tasks", headers=alice.headers)).json()["total"] == 0


# --- AC-03: get one ----------------------------------------------------------------------


async def test_ac03_the_creator_and_the_assignee_can_read_a_task(
    client: AsyncClient, alice: Person, bob: Person
) -> None:
    task = await create(client, alice, assignee_id=bob.id)

    for who in (alice, bob):
        response = await client.get(f"/tasks/{task['id']}", headers=who.headers)
        assert response.status_code == 200
        assert response.json() == task


async def test_ac03_a_stranger_and_a_missing_id_get_the_same_404(
    client: AsyncClient, alice: Person, carol: Person
) -> None:
    task = await create(client, alice)

    hidden = await client.get(f"/tasks/{task['id']}", headers=carol.headers)
    missing = await client.get(f"/tasks/{uuid4()}", headers=alice.headers)

    assert_error(hidden, 404, "task_not_found")
    assert_error(missing, 404, "task_not_found")
    assert hidden.json() == missing.json()


async def test_ac03_an_id_that_is_not_a_uuid_is_a_422(client: AsyncClient, alice: Person) -> None:
    response = await client.get("/tasks/not-a-uuid", headers=alice.headers)

    assert_error(response, 422, "validation_error")


# --- AC-04: list -------------------------------------------------------------------------


async def test_ac04_lists_only_visible_tasks_with_the_default_page(
    client: AsyncClient, alice: Person, bob: Person, carol: Person
) -> None:
    mine = await create(client, alice, title="mine")
    assigned = await create(client, bob, title="assigned to alice", assignee_id=alice.id)
    await create(client, bob, title="bob's own")
    await create(client, carol, title="carol's own", assignee_id=bob.id)

    response = await client.get("/tasks", headers=alice.headers)

    assert response.status_code == 200
    body = response.json()
    assert (body["total"], body["page"], body["size"]) == (2, 1, 25)
    assert {t["id"] for t in body["items"]} == {mine["id"], assigned["id"]}
    assert all(set(t) == TASK_KEYS for t in body["items"])


async def test_ac04_the_default_size_is_25_and_pages_do_not_overlap(
    client: AsyncClient, alice: Person
) -> None:
    for i in range(30):
        await create(client, alice, title=f"t{i:02}")

    first = (await client.get("/tasks", headers=alice.headers)).json()
    second = (await client.get("/tasks?page=2", headers=alice.headers)).json()
    beyond = (await client.get("/tasks?page=9", headers=alice.headers)).json()

    assert (len(first["items"]), first["total"], first["size"]) == (25, 30, 25)
    assert len(second["items"]) == 5
    assert not {t["id"] for t in first["items"]} & {t["id"] for t in second["items"]}
    assert (beyond["items"], beyond["total"], beyond["page"]) == ([], 30, 9)


async def test_ac04_filters_combine_and_status_is_repeatable(
    client: AsyncClient, alice: Person
) -> None:
    soon = await create(client, alice, title="soon", due_date=in_days(1))
    later = await create(client, alice, title="later", due_date=in_days(5))
    await create(client, alice, title="no due date")
    blocked = await create(client, alice, title="blocked", due_date=in_days(2))
    await client.patch(f"/tasks/{blocked['id']}", json={"status": "blocked"}, headers=alice.headers)

    by_status = await client.get(
        "/tasks", params=[("status", "blocked"), ("status", "in_progress")], headers=alice.headers
    )
    window = await client.get(
        "/tasks",
        params={"due_after": soon["due_date"], "due_before": later["due_date"]},
        headers=alice.headers,
    )
    combined = await client.get(
        "/tasks",
        params=[("status", "todo"), ("due_before", in_days(3))],
        headers=alice.headers,
    )

    assert [t["title"] for t in by_status.json()["items"]] == ["blocked"]
    assert [t["title"] for t in window.json()["items"]] == ["soon", "blocked", "later"]
    assert [t["title"] for t in combined.json()["items"]] == ["soon"]


async def test_ac04_sorts_by_due_date_then_newest_first_with_no_due_date_last(
    client: AsyncClient, alice: Person
) -> None:
    await create(client, alice, title="no due, old")
    await create(client, alice, title="no due, new")
    await create(client, alice, title="later", due_date=in_days(5))
    same_day = in_days(1)
    await create(client, alice, title="soon, old", due_date=same_day)
    await create(client, alice, title="soon, new", due_date=same_day)

    items = (await client.get("/tasks", headers=alice.headers)).json()["items"]

    assert [t["title"] for t in items] == [
        "soon, new",
        "soon, old",
        "later",
        "no due, new",
        "no due, old",
    ]


async def test_ac04_a_size_above_100_is_a_422_that_names_the_maximum(
    client: AsyncClient, alice: Person
) -> None:
    response = await client.get("/tasks?size=101", headers=alice.headers)

    error = assert_error(response, 422, "validation_error")
    assert "maximum size is 100" in error["message"]
    assert (await client.get("/tasks?size=100", headers=alice.headers)).status_code == 200


async def test_ac04_a_page_far_beyond_the_end_is_an_empty_page_not_an_error(
    client: AsyncClient, alice: Person
) -> None:
    await create(client, alice)

    response = await client.get("/tasks?page=99999999999999999999", headers=alice.headers)

    assert response.status_code == 200
    body = response.json()
    assert (body["items"], body["total"]) == ([], 1)


@pytest.mark.parametrize(
    "query",
    [
        "size=0",
        "page=0",
        "page=abc",
        "size=abc",
        "status=bogus",
        "status=todo&status=bogus",
        "due_before=2026-01-01T00:00:00",
        "due_after=2026-01-01T00:00:00",
        "due_before=1893456000",
        "due_after=0001-01-01T00:00:00%2B05:00",
    ],
)
async def test_ac04_invalid_query_values_are_a_422(
    client: AsyncClient, alice: Person, query: str
) -> None:
    response = await client.get(f"/tasks?{query}", headers=alice.headers)

    assert_error(response, 422, "validation_error")


# --- AC-05: patch ------------------------------------------------------------------------


async def patch(client: AsyncClient, who: Person, task_id: str, body: dict[str, Any]) -> Response:
    return await client.patch(f"/tasks/{task_id}", json=body, headers=who.headers)


async def test_ac05_the_creator_updates_fields_and_null_clears_them(
    client: AsyncClient, alice: Person
) -> None:
    task = await create(client, alice, description="old", due_date=in_days(3))

    renamed = await patch(client, alice, task["id"], {"title": "New title"})
    cleared = await patch(client, alice, task["id"], {"description": None, "due_date": None})

    assert renamed.status_code == 200
    assert (renamed.json()["title"], renamed.json()["description"]) == ("New title", "old")
    assert renamed.json()["due_date"] is not None
    assert (cleared.json()["description"], cleared.json()["due_date"]) == (None, None)
    assert cleared.json()["title"] == "New title"


async def test_ac05_a_past_due_date_is_accepted_on_update(
    client: AsyncClient, alice: Person
) -> None:
    task = await create(client, alice)

    response = await patch(client, alice, task["id"], {"due_date": in_days(-3)})

    assert response.status_code == 200


async def test_ac05_fields_and_status_can_be_patched_together(
    client: AsyncClient, alice: Person
) -> None:
    task = await create(client, alice)

    response = await patch(client, alice, task["id"], {"title": "Both", "status": "in_progress"})

    assert response.status_code == 200
    assert (response.json()["title"], response.json()["status"]) == ("Both", "in_progress")


async def test_ac05_the_assignee_can_change_the_status_but_not_the_fields(
    client: AsyncClient, alice: Person, bob: Person
) -> None:
    task = await create(client, alice, assignee_id=bob.id)

    status_only = await patch(client, bob, task["id"], {"status": "blocked"})
    with_title = await patch(client, bob, task["id"], {"title": "Mine", "status": "todo"})

    assert status_only.status_code == 200
    assert status_only.json()["status"] == "blocked"
    assert_error(with_title, 403, "permission_denied")
    current = (await client.get(f"/tasks/{task['id']}", headers=alice.headers)).json()
    assert (current["title"], current["status"]) == ("Task", "blocked")


async def test_ac05_a_stranger_gets_404(client: AsyncClient, alice: Person, carol: Person) -> None:
    task = await create(client, alice)

    assert_error(await patch(client, carol, task["id"], {"title": "x"}), 404, "task_not_found")
    assert_error(await patch(client, alice, str(uuid4()), {"title": "x"}), 404, "task_not_found")


async def test_ac05_an_invalid_transition_is_a_409_and_a_mixed_request_changes_nothing(
    client: AsyncClient, alice: Person
) -> None:
    task = await create(client, alice)
    await patch(client, alice, task["id"], {"status": "cancelled"})

    response = await patch(client, alice, task["id"], {"title": "Renamed", "status": "todo"})

    assert_error(response, 409, "invalid_transition")
    current = (await client.get(f"/tasks/{task['id']}", headers=alice.headers)).json()
    assert (current["title"], current["status"]) == ("Task", "cancelled")


async def test_ac05_the_current_status_and_an_empty_body_change_nothing(
    client: AsyncClient, alice: Person
) -> None:
    task = await create(client, alice)

    same = await patch(client, alice, task["id"], {"status": "todo"})
    empty = await patch(client, alice, task["id"], {})

    assert same.status_code == 200
    assert empty.status_code == 200
    assert same.json() == task
    assert empty.json() == task


@pytest.mark.parametrize(
    "body",
    [
        {"title": ""},
        {"title": None},
        {"title": "x" * 121},
        {"description": "d" * 2001},
        {"due_date": "2999-01-01T00:00:00"},
        {"due_date": 1893456000},
        {"due_date": "0001-01-01T00:00:00+05:00"},
        {"status": None},
        {"status": "nonsense"},
        {"assignee_id": str(uuid4())},
        {"creator_id": str(uuid4())},
    ],
)
async def test_ac05_invalid_values_and_unknown_fields_are_a_422(
    client: AsyncClient, alice: Person, body: dict[str, Any]
) -> None:
    task = await create(client, alice)

    response = await patch(client, alice, task["id"], body)

    assert_error(response, 422, "validation_error")
    assert (await client.get(f"/tasks/{task['id']}", headers=alice.headers)).json() == task


# --- AC-06: delete -----------------------------------------------------------------------


async def test_ac06_the_creator_deletes_the_task(client: AsyncClient, alice: Person) -> None:
    task = await create(client, alice)

    response = await client.delete(f"/tasks/{task['id']}", headers=alice.headers)

    assert response.status_code == 204
    assert response.content == b""
    gone = await client.get(f"/tasks/{task['id']}", headers=alice.headers)
    assert_error(gone, 404, "task_not_found")


async def test_ac06_the_assignee_cannot_delete_and_a_stranger_gets_404(
    client: AsyncClient, alice: Person, bob: Person, carol: Person
) -> None:
    task = await create(client, alice, assignee_id=bob.id)

    by_assignee = await client.delete(f"/tasks/{task['id']}", headers=bob.headers)
    by_stranger = await client.delete(f"/tasks/{task['id']}", headers=carol.headers)

    assert_error(by_assignee, 403, "permission_denied")
    assert_error(by_stranger, 404, "task_not_found")
    assert (await client.get(f"/tasks/{task['id']}", headers=alice.headers)).json() == task


# --- AC-07: assign and complete ----------------------------------------------------------


async def assign(
    client: AsyncClient, who: Person, task_id: str, assignee_id: str | None
) -> Response:
    return await client.post(
        f"/tasks/{task_id}/assign", json={"assignee_id": assignee_id}, headers=who.headers
    )


async def test_ac07_assigning_sets_the_assignee_and_sends_one_message(
    client: AsyncClient, alice: Person, bob: Person, caplog: pytest.LogCaptureFixture
) -> None:
    task = await create(client, alice)

    with caplog.at_level(logging.INFO, logger="taskapp.notifications"):
        response = await assign(client, alice, task["id"], bob.id)
        again = await assign(client, alice, task["id"], bob.id)

    assert response.status_code == 200
    assert response.json()["assignee"] == {"id": bob.id, "name": "Bob"}
    assert again.status_code == 200
    assert again.json() == response.json()
    assert len(caplog.records) == 1


async def test_ac07_assigning_null_clears_the_assignee_without_a_message(
    client: AsyncClient, alice: Person, bob: Person, caplog: pytest.LogCaptureFixture
) -> None:
    task = await create(client, alice, assignee_id=bob.id)
    caplog.clear()

    with caplog.at_level(logging.INFO, logger="taskapp.notifications"):
        response = await assign(client, alice, task["id"], None)

    assert response.status_code == 200
    assert response.json()["assignee"] is None
    assert caplog.records == []


async def test_ac07_assign_errors_change_nothing_and_send_nothing(
    client: AsyncClient,
    alice: Person,
    bob: Person,
    carol: Person,
    caplog: pytest.LogCaptureFixture,
) -> None:
    task = await create(client, alice, assignee_id=bob.id)
    caplog.clear()
    url = f"/tasks/{task['id']}/assign"

    with caplog.at_level(logging.INFO, logger="taskapp.notifications"):
        unknown = await assign(client, alice, task["id"], str(uuid4()))
        by_assignee = await assign(client, bob, task["id"], carol.id)
        stranger = await assign(client, carol, task["id"], carol.id)
        bad_body = await client.post(url, json={"assignee_id": "nope"}, headers=alice.headers)
        missing_field = await client.post(url, json={}, headers=alice.headers)

    assert_error(unknown, 404, "user_not_found")
    assert_error(by_assignee, 403, "permission_denied")
    assert_error(stranger, 404, "task_not_found")
    assert_error(bad_body, 422, "validation_error")
    assert_error(missing_field, 422, "validation_error")
    assert caplog.records == []
    current = (await client.get(f"/tasks/{task['id']}", headers=alice.headers)).json()
    assert current["assignee"]["id"] == bob.id


async def test_ac07_the_creator_and_the_assignee_can_complete_a_task(
    client: AsyncClient, alice: Person, bob: Person
) -> None:
    mine = await create(client, alice)
    theirs = await create(client, alice, assignee_id=bob.id)

    by_creator = await client.post(f"/tasks/{mine['id']}/complete", headers=alice.headers)
    by_assignee = await client.post(f"/tasks/{theirs['id']}/complete", headers=bob.headers)

    for response in (by_creator, by_assignee):
        assert response.status_code == 200
        assert response.json()["status"] == "completed"
        assert response.json()["completed_at"] is not None


async def test_ac07_completing_twice_changes_nothing_and_a_cancelled_task_is_a_409(
    client: AsyncClient, alice: Person
) -> None:
    done = await create(client, alice)
    first = await client.post(f"/tasks/{done['id']}/complete", headers=alice.headers)
    second = await client.post(f"/tasks/{done['id']}/complete", headers=alice.headers)
    cancelled = await create(client, alice)
    await patch(client, alice, cancelled["id"], {"status": "cancelled"})

    refused = await client.post(f"/tasks/{cancelled['id']}/complete", headers=alice.headers)

    assert second.json() == first.json()
    assert_error(refused, 409, "invalid_transition")


async def test_ac07_a_stranger_cannot_complete_a_task(
    client: AsyncClient, alice: Person, carol: Person
) -> None:
    task = await create(client, alice)

    response = await client.post(f"/tasks/{task['id']}/complete", headers=carol.headers)

    assert_error(response, 404, "task_not_found")


# --- AC-08: users and Swagger ------------------------------------------------------------


async def test_ac08_users_are_listed_sorted_by_name_without_secrets(
    client: AsyncClient, carol: Person, alice: Person, bob: Person
) -> None:
    response = await client.get("/users", headers=carol.headers)

    assert response.status_code == 200
    users = response.json()
    assert [u["name"] for u in users] == ["Alice", "Bob", "Carol"]
    assert all(set(u) == {"id", "email", "name"} for u in users)
    assert "hash" not in response.text
    assert PASSWORD not in response.text


DOCUMENTED = [
    ("get", "/tasks"),
    ("post", "/tasks"),
    ("get", "/tasks/{task_id}"),
    ("patch", "/tasks/{task_id}"),
    ("delete", "/tasks/{task_id}"),
    ("post", "/tasks/{task_id}/assign"),
    ("post", "/tasks/{task_id}/complete"),
    ("get", "/users"),
]
WITH_BODY = {"/tasks", "/tasks/{task_id}", "/tasks/{task_id}/assign"}


async def test_ac08_swagger_describes_every_endpoint_with_its_schemas(
    client: AsyncClient,
) -> None:
    docs = await client.get("/docs")
    spec = (await client.get("/openapi.json")).json()

    assert docs.status_code == 200
    assert "text/html" in docs.headers["content-type"]
    for method, path in DOCUMENTED:
        operation = spec["paths"][path][method]
        assert operation["summary"], f"{method} {path} has no summary"
        assert operation["security"], f"{method} {path} does not declare the bearer scheme"
        success = next(code for code in operation["responses"] if code.startswith("2"))
        if success != "204":
            assert operation["responses"][success]["content"]["application/json"]["schema"]
        if method in {"post", "patch"} and path in WITH_BODY:
            assert operation["requestBody"]["content"]["application/json"]["schema"]
    assert any(
        scheme.get("type") == "http" and scheme.get("scheme") == "bearer"
        for scheme in spec["components"]["securitySchemes"].values()
    )
    documented_errors = spec["paths"]["/tasks/{task_id}"]["patch"]["responses"]
    assert {"401", "403", "404", "409", "422"} <= set(documented_errors)
