# Agent instructions

Cross-tool instructions for AI coding agents working in this repo.

## Workflow
- Spec-driven: `spec/` is the source of truth: `spec/00-overview.md` (product-wide rules) plus one spec per issue, each with numbered acceptance criteria (AC-xx) and an AC -> test table.
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

## Repository hygiene
- Everything pushed here is visible to others, including branches, PRs, issues and commit messages. Keep drafts (specs, prompts, docs) local and unpushed until the maintainer has read and approved them.
- Write repo files as ordinary project documentation. No meta-commentary, no references to the maintainer's machine or local folder layout, and no wording that depends on outside context.
- Before any push, re-read the full diff for both of the above.
