# Agent instructions

Cross-tool instructions for AI coding agents working in this repo.

## Workflow
- Spec-driven: `docs/spec.md` is the source of truth (numbered acceptance criteria, AC-xx).
- TDD: write the failing test first, then the code. Name tests after ACs (`test_ac07_...`).
- Work in small slices; the human reviews every diff. No giant one-shot commits.
- One GitHub issue per slice (with AC ids). One branch `slice/<name>` and one PR per slice; never push to `main` directly.
- Merge PRs with a merge commit, never squash: the test-first commit history is evidence.
- Parallel or dirty checkout? Work in a git worktree under `../taskflow-worktrees/` (see `/feature`).

## Architecture
Clean Architecture: `domain` <- `application` <- `infrastructure` / `api`. Boundaries are enforced by import-linter.

## Definition of done
- Tests pass, coverage >= 80%, lint + type checks clean.
- If commands, env vars, setup or endpoints change, update `README.md` in the same commit.
- If the user rejects or corrects your approach, propose an entry for `docs/ai/corrections.md`.
- Never commit secrets.
