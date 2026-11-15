---
name: feature
description: Plan one vertical slice from docs/spec.md (pick ACs, design layers, list tests first) and log the plan. Use before writing any code for a slice.
---

Plan a slice. Do NOT write production code or tests in this skill.

## Steps
1. Read `AGENTS.md`, `docs/spec.md`, and the relevant `ENGINEERING.md` (backend and/or frontend). If the spec has no ACs for the requested slice, stop and ask the user to define them first.
2. Pick the ACs for this slice (one slice = one coherent behavior, usually 1-4 ACs). Quote their ids.
3. Produce a plan with these sections:
   - **ACs covered**: ids + one-line summary.
   - **Layer map**: what goes in `domain` (entities, value objects, domain errors), `application` (use case + ports), `infrastructure` (adapters), `api` (router, schemas, wiring). Mark layers untouched as "none".
   - **Dependency check**: confirm no inward-pointing rule is broken (domain imports nothing; application imports only domain; api never imports infrastructure models). Flag anything that would need a new port.
   - **Test list, in order**: names like `test_ac07_complete_sets_completed_at`, each tagged unit (in-memory fakes) or integration (real Postgres). Start with the unit tests of the innermost layer.
   - **Edge cases**: auth/ownership, validation, empty/duplicate/boundary inputs, concurrency where relevant.
   - **Out of scope**: what this slice deliberately does not do.
   - **Risks / assumptions**.
4. Show the plan and wait for the user's approval or edits. Do not proceed to implementation.
5. After approval, set up the workspace (see **Branch and worktree** below), then append the final plan to `docs/ai/prompts.md` under a new dated heading (slice name, the prompt/request, the plan). If a GitHub issue for the slice exists, post a short plan summary as a comment via `gh issue comment`; otherwise offer to create one with the AC ids in the body.

## Branch and worktree
Branch name: `feat/<short-kebab-name>` (use `feat/` for slices; small fixes and chores go through `/chore`), created from an up-to-date `main` (`git fetch origin` first).
Decide where to work:
- **Current checkout is free** (on `main`, clean tree, no other slice branch in progress): `git switch -c feat/<name> origin/main` and work here.
- **Current checkout is in use** (uncommitted changes, or already on another work branch, or `git worktree list` shows another active slice): create a worktree instead, in a sibling directory:
  `git worktree add ../taskflow-worktrees/feat-<name> -b feat/<name> origin/main`
  then tell the user the path to open/`cd` into. Do all further work in that directory.
- In a new worktree, untracked files do not carry over: run `uv sync` in `backend/` and `npm ci` in `frontend/` as needed, and copy `.env` from the main checkout (never commit it).
- Ask the user if it is unclear which case applies. Never stash or discard someone's uncommitted work to free the checkout.
Record the branch (and worktree path, if any) in the prompts.md entry and the issue comment.

## Rules
- Plans are short and checkable. No speculative features.
- Prefer the smallest slice that works end to end.
