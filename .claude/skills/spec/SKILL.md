---
name: spec
description: Draft the slice spec (goal, numbered acceptance criteria, edge cases, open questions) from a GitHub issue, for the user to review and approve. Use before /feature. Writes the draft locally and never commits or pushes it.
args: "<issue number>"
---

Draft the spec for one slice. Do NOT plan, write tests or write code in this skill.

## Steps
1. Read the issue (`gh issue view <n>`), `AGENTS.md`, `spec/00-overview.md`, `spec/_template.md`, and the relevant `ENGINEERING.md`. Find the highest AC number already used under `spec/` (`grep -rhoE "AC-[0-9]+" spec | sort -u | tail -1`) and continue from the next one.
2. Write the draft to `spec/NN-<slice>.md` (NN = the issue's slice number) from the template: goal, out of scope, ACs in Given/When/Then, edge cases, API contract if any, and an empty AC -> test table.
3. Keep every AC testable and about behavior, not implementation. Cover auth/ownership, validation, boundaries and error cases explicitly. Follow the rules in the overview (statuses, pagination, error format, permissions) instead of inventing new ones.
4. Add an **Open questions** section for everything the issue and overview do not settle. Never silently decide business rules; ask.
5. Leave the file **untracked**. Do not `git add`, commit or push it, and do not post it anywhere. Tell the user the path and ask them to review, edit and answer the open questions.
6. Iterate on the user's feedback until they say the spec is approved. Remove the Open questions section once resolved. Then stop; the next step is `/feature`.

## Rules
- The spec is the contract: it says what must be true, not how to build it (no layer maps or test lists; that is `/feature`).
- Write it as ordinary project documentation: no meta-commentary, no local paths.
- Never mark a spec approved on your own.
