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
5. After approval: append the final plan to `docs/ai/prompts.md` under a new dated heading (slice name, the prompt/request, the plan). If a GitHub issue for the slice exists, post a short plan summary as a comment via `gh issue comment`; otherwise offer to create one with the AC ids in the body.

## Rules
- Plans are short and checkable. No speculative features.
- Prefer the smallest slice that works end to end.
