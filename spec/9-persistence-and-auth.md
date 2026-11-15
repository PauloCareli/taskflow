# 9 - Persistence and authentication

Issue: #9 · Depends on: 00-overview, 8-task-domain · Layers: application / infrastructure / api

## Goal
Real adapters for the ports defined in `8-task-domain` (PostgreSQL through SQLAlchemy, migrations with Alembic), and JWT authentication: register, login, and a dependency that identifies the caller on protected routes. Business rules stay in `domain` and `application`; this slice only stores, authenticates and exposes the two auth endpoints.

## Out of scope
- Task endpoints, refresh tokens, roles, password reset, email verification.
- Rate limiting and background jobs.
- Seed data.

## Acceptance criteria
- AC-01: Given a valid email, name and password, when a client calls `POST /auth/register`, then it receives `201 {id, email, name}`, the user is stored with an argon2 hash of the password and never the password itself, and the response never contains the password or its hash.
- AC-02: Given an invalid email, name or password, when a client registers, then it receives `422` with the uniform error body and nothing is stored; given an email already registered in any letter case, then it receives `409` with the uniform error body and the stored user is unchanged.
- AC-03: Given registered credentials (the email matched in any letter case), when a client calls `POST /auth/login`, then it receives `200 {access_token, token_type: "bearer", expires_in}` with `expires_in` of 1800 seconds, and the token identifies the user and stops being accepted after 30 minutes.
- AC-04: Given an unknown email or a wrong password, when a client logs in, then both cases return the same `401` uniform error body, with no hint about which part was wrong.
- AC-05: Given a protected route (`GET /auth/me`, which returns `{id, email, name}` of the caller), when a request has no token, a malformed token, an expired token, a token with a wrong signature or altered payload, or a token for a user that no longer exists, then it receives `401` with the uniform error body; given a valid token, then the route receives the authenticated user and `GET /auth/me` returns `200` with that user's `{id, email, name}`.
- AC-06: Given the database, when the repositories and unit of work are exercised against real PostgreSQL, then they behave as the ports in `8-task-domain` require: tasks and users are stored and read back unchanged; the visibility, filter (inclusive bounds, no-due-date exclusion), sort and pagination rules of `8-task-domain/AC-08` hold with `total` counted in the database; a failed unit of work leaves nothing stored; and listing issues a number of statements that does not grow with the page size.
- AC-07: Given the schema, then email is unique regardless of letter case, a task's creator and assignee must reference existing users, and indexes exist on `status`, `due_date`, `assignee_id` and `creator_id`; violations are rejected by the database.
- AC-08: Given an empty database, when migrations run, then the schema is created and matches the models (no pending differences); `just migrate` runs them against the configured database.

## Field rules
Email: valid format, at most 254 characters, stored trimmed and lowercased, unique on that value. Name: 1-100 characters. Password: 8-128 characters, no other composition rule. The JWT uses HS256 with claims `sub` (user id), `iat` and `exp`, signed with `TASKAPP_JWT_SECRET` (required, no default). The domain `User` carries `id`, `email` and `name`; the password hash is kept outside the domain.

## Edge cases
- Registering the same email concurrently stores one user; the other request gets `409`.
- Login treats the email case-insensitively and ignores surrounding whitespace.
- Unknown-email login takes comparable time to a wrong-password login (a password check is still performed).
- A token signed with a different secret or algorithm is rejected, including `alg: none`.
- A missing or empty JWT secret stops the app from starting with a clear message; secrets are read only from settings, and `.env.example` documents them.
- Deleting a user referenced by tasks is not supported in this slice.

## API contract
| Method | Path | Request | Response | Errors |
|---|---|---|---|---|
| POST | `/auth/register` | `{email, name, password}` | `201 {id, email, name}` | 409 email taken, 422 validation |
| POST | `/auth/login` | `{email, password}` | `200 {access_token, token_type: "bearer", expires_in}` | 401 invalid credentials, 422 validation |
| GET | `/auth/me` | bearer token | `200 {id, email, name}` | 401 missing or invalid token |

All errors use the uniform error body from `00-overview`.

## AC -> test traceability
| AC | Test | Layer |
|---|---|---|
