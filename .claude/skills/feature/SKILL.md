---
name: feature
description: Plan one vertical slice from its approved spec (layer map, tests first), set up the branch, and make the spec the first commit. Use after /spec, before writing any code.
---

Plan a slice. Do NOT write production code or tests in this skill.

## Steps
1. Read `AGENTS.md`, `spec/00-overview.md`, the slice's `spec/NN-*.md`, and the relevant `ENGINEERING.md` (backend and/or frontend). If the slice has no spec, or the user has not approved it, stop and run `/spec` first. The spec may still be untracked at this point; that is expected.
2. Take the ACs from the spec (one slice = one coherent behavior, usually 1-4 ACs). Quote their ids.
3. Produce a plan with these sections:
   - **ACs covered**: ids + one-line summary.
   - **Layer map**: what goes in `domain` (entities, value objects, domain errors), `application` (use case + ports), `infrastructure` (adapters), `api` (router, schemas, wiring), `frontend` if relevant. Mark layers untouched as "none".
   - **Dependency check**: confirm no inward-pointing rule is broken (domain imports nothing; application imports only domain; api never imports infrastructure models). Flag anything that would need a new port.
   - **Test list, in order**: names like `test_ac07_complete_sets_completed_at`, each tagged unit (in-memory fakes) or integration (real Postgres). Start with the unit tests of the innermost layer.
   - **Edge cases**: from the spec, plus anything the plan adds.
   - **Out of scope**: what this slice deliberately does not do.
   - **Risks / assumptions**.
4. Show the plan and wait for the user's approval or edits. Do not proceed to implementation.
5. After approval, set up the workspace (see **Branch and worktree**), then make the commits in this order on the slice branch:
   1. `docs: spec for <slice>` containing the approved spec file (this is always the first commit of the slice).
   2. `docs: plan log for <slice>`: append the approved plan to `docs/ai/prompts.md` under a new dated heading (slice name, the request, the plan, branch).
   Then post a short plan summary on the GitHub issue with `gh issue comment`. Do not push; `/ship` does that.

## Branch and worktree
Branch name: `feat/<short-kebab-name>` (use `feat/` for slices; small fixes and chores go through `/chore`), created from an up-to-date `main` (`git fetch origin` first).
Decide where to work. An untracked, approved spec file does NOT make a checkout "in use"; it is carried over to the branch.
- **Current checkout is free** (on `main`, no tracked changes, no other work branch in progress): `git switch -c feat/<name> origin/main` and work here.
- **Current checkout is in use** (tracked changes, or already on another work branch, or `git worktree list` shows another active slice): create a worktree instead, in a sibling directory:
  `git worktree add ../taskflow-worktrees/feat-<name> -b feat/<name> origin/main`
  then **move the spec file into the worktree** (same relative path), so the original checkout stays clean, and tell the user the path to open/`cd` into. Do all further work in that directory.
- In a new worktree, untracked files do not carry over: run `uv sync` in `backend/` and `npm ci` in `frontend/` as needed, and copy `.env` from the main checkout (never commit it).
- Ask the user if it is unclear which case applies. Never stash or discard someone's uncommitted work to free the checkout.

## Rules
- Plans are short and checkable. No speculative features.
- Prefer the smallest slice that works end to end.
- Write everything as ordinary project documentation (see Repository hygiene in `AGENTS.md`).
