---
name: feature
description: Plan one vertical slice (layer map, tests first) on the branch created by /spec, where the approved spec is already committed, and log the plan. Use after /spec, before writing any code.
---

Plan a slice. Do NOT write production code or tests in this skill.

## Steps
1. Check the workspace: you must be on the slice's `feat/*` branch, with the approved spec committed as `docs: spec for <slice>` and a clean tree. If not, stop and run `/spec` first (or ask the user to switch to the right branch or worktree).
2. Read `AGENTS.md`, `spec/00-overview.md`, the slice's `spec/NN-*.md`, and the relevant `ENGINEERING.md` (backend and/or frontend).
3. Take the ACs from the spec (one slice = one coherent behavior, usually 1-4 ACs). Quote their ids.
4. Produce a plan with these sections:
   - **ACs covered**: ids + one-line summary.
   - **Layer map**: what goes in `domain` (entities, value objects, domain errors), `application` (use case + ports), `infrastructure` (adapters), `api` (router, schemas, wiring), `frontend` if relevant (structure per `frontend/ENGINEERING.md`). Mark layers untouched as "none".
   - **Dependency check**: confirm no inward-pointing rule is broken (domain imports nothing; application imports only domain; api never imports infrastructure models). Flag anything that would need a new port.
   - **Test list, in order**: names like `test_ac07_complete_sets_completed_at`, each tagged unit (in-memory fakes) or integration (real Postgres). Start with the unit tests of the innermost layer.
   - **Edge cases**: from the spec, plus anything the plan adds.
   - **Out of scope**: what this slice deliberately does not do.
   - **Risks / assumptions**.
5. Show the plan and wait for the user's approval or edits. Do not proceed to implementation.
6. After approval, commit `docs: plan log for <slice>`: append the approved plan to `docs/ai/prompts.md` under a new dated heading (slice name, the request, the plan, branch). Then post a short plan summary on the GitHub issue with `gh issue comment`. Do not push; `/ship` does that.

## Rules
- Plans are short and checkable. No speculative features.
- Prefer the smallest slice that works end to end.
- Write everything as ordinary project documentation (see Repository hygiene in `AGENTS.md`).
