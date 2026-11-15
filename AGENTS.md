# Agent instructions

Cross-tool instructions for AI coding agents working in this repo.

## Workflow
- Spec-driven: `docs/spec.md` is the source of truth (numbered acceptance criteria, AC-xx).
- TDD: write the failing test first, then the code. Name tests after ACs (`test_ac07_...`).
- Work in small slices; the human reviews every diff. No giant one-shot commits.
- One GitHub issue per slice (with AC ids). One branch `<type>/<name>` (feat, fix, chore, refactor, test, docs; same type as the conventional commit) and one PR per slice; never push to `main` directly.
- Merge PRs with a merge commit, never squash: the test-first commit history is evidence.
- Parallel or dirty checkout? Work in a git worktree under `../taskflow-worktrees/` (see `/feature`).

## Architecture
Clean Architecture: `domain` <- `application` <- `infrastructure` / `api`. Boundaries are enforced by import-linter.

## Definition of done
- Tests pass, coverage >= 80%, lint + type checks clean.
- If commands, env vars, setup or endpoints change, update `README.md` in the same commit.
- If the user rejects or corrects your approach, propose an entry for `docs/ai/corrections.md`.
- Never commit secrets.

## Git authorship
- Commits and PRs are authored only by the logged-in GitHub user. Never add `Co-Authored-By`, "Generated with Claude" or any AI attribution to commit messages, PR bodies or issues.
