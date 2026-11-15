---
name: chore
description: Small bug fix, small improvement or maintenance task, done test-first on its own branch with a quick independent review and a PR. Use instead of /feature when no new AC or design is needed.
args: "<fix|chore|refactor|docs|test> <description>"
---

For work too small for a full slice plan: bug fixes, dependency bumps, config tweaks, small refactors, doc fixes. If it needs a new AC, a new port, or touches more than ~3 files across layers, stop and use `/feature` instead.

## Steps
1. Pick the type (`fix`, `chore`, `refactor`, `docs`, `test`) and a short kebab name. Set up the workspace exactly as in `/feature` (**Branch and worktree** section): `<type>/<name>` from fresh `origin/main`, using a worktree under `../taskflow-worktrees/<type>-<name>` if the current checkout is in use.
2. State in 2-3 lines what changes and which AC (if any) it relates to. Ask only if truly ambiguous.
3. **Bug fix**: reproduce first with a failing test (red commit `test: reproduce <bug>`), then fix (green commit `fix: ...`). No fix without a regression test.
   **Refactor**: tests must already cover the behavior; add them first if not. Behavior must not change.
   **Chore/docs**: no test needed unless behavior changes; still run the gates.
4. Run the quality gates from `/implement`.
5. Dispatch ONE fresh reviewer subagent (no fork, no implementation context; give only the diff command, `AGENTS.md`, and a note to check layer boundaries, test adequacy and correctness). Verify its findings before acting.
6. If an AI mistake was involved (yours or earlier), propose a `/log-correction` entry.
7. Hand off to `/ship`, which opens the PR.

## Rules
- Keep the diff small and focused; no drive-by refactors.
- Never push to `main`; never skip hooks.
