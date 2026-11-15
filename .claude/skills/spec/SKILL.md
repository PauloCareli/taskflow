---
name: spec
description: Create the slice branch (or worktree) and draft the slice spec from a GitHub issue for the user to review; once approved, commit it as the first commit of the branch. Use before /feature. Never pushes.
args: "<issue number>"
---

Start a slice: branch, spec draft, review, spec commit. Do NOT plan, write tests or write code in this skill.

## Steps
1. Read the issue (`gh issue view <n>`), `AGENTS.md`, `spec/00-overview.md`, `spec/_template.md`, and the relevant `ENGINEERING.md`. Find the highest AC number already used under `spec/` (`grep -rhoE "AC-[0-9]+" spec | sort -u | tail -1`) and continue from the next one.
2. Set up the workspace (see **Branch and worktree** below). All further work happens there.
3. Write the draft to `spec/NN-<slice>.md` (NN = the issue's slice number) from the template: goal, out of scope, ACs in Given/When/Then, edge cases, API contract if any, and an empty AC -> test table.
4. Keep every AC testable and about behavior, not implementation. Cover auth/ownership, validation, boundaries and error cases explicitly. Follow the rules in the overview (statuses, pagination, error format, permissions) instead of inventing new ones.
5. Add an **Open questions** section for everything the issue and overview do not settle. Never silently decide business rules; ask.
6. Leave the draft **uncommitted** and tell the user the path. Ask them to review, edit and answer the open questions. Iterate until the user says the spec is approved; never mark it approved yourself.
7. After approval: remove the Open questions section, commit only the spec as `docs: spec for <slice>` (`Refs #<n>`), and tell the user to run `/feature`. Do not push; `/ship` does that.

## Branch and worktree
Branch name: `feat/<short-kebab-name>` (use `feat/` for slices; small fixes and chores go through `/chore`), created from an up-to-date `main` (`git fetch origin` first).
- **Current checkout is free** (on `main`, no tracked changes, no other work branch in progress): `git switch -c feat/<name> origin/main` and work here.
- **Current checkout is in use** (tracked changes, or already on another work branch, or `git worktree list` shows another active slice): create a worktree instead, in a sibling directory:
  `git worktree add ../taskflow-worktrees/feat-<name> -b feat/<name> origin/main`
  then tell the user the path to open/`cd` into. Do all further work in that directory.
- In a new worktree, untracked files do not carry over: run `uv sync` in `backend/` and `npm ci` in `frontend/` as needed, and copy `.env` from the main checkout (never commit it).
- Ask the user if it is unclear which case applies. Never stash or discard someone's uncommitted work to free the checkout.

## Rules
- The spec is the contract: it says what must be true, not how to build it (no layer maps or test lists; that is `/feature`).
- Write it as ordinary project documentation: no meta-commentary, no local paths.
