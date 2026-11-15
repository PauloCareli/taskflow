---
name: ship
description: Verify a finished slice, push its branch and open a PR for the user to review. Never merges and never pushes to main. Use after /implement.
---

Ship the current slice as a pull request. The user reviews and merges manually.

## Steps
1. Confirm you are on a `<type>/<name>` branch (never `main`). `git status` and `git log origin/main..HEAD --oneline`: show what will be shipped. Stop if there are unexpected uncommitted changes or `.env` / secrets are staged.
2. Re-run the full quality gates from `/implement` (backend and/or frontend, whichever changed). Do not ship on red.
3. Re-read the full diff against the **Repository hygiene** rules in `AGENTS.md`: nothing the maintainer has not approved, no meta-commentary, no references to local paths or outside context. Stop and ask if unsure.
4. Run `gitleaks detect --no-banner` if installed; stop on any finding.
5. Check docs: README updated if setup/commands/env/endpoints changed; AC -> test table in `docs/spec.md` current; `docs/ai/prompts.md` has this slice's entry with commit hashes; corrections logged.
6. Confirm commits are conventional and reference the issue (`Refs #n`). Do not rewrite history that is already pushed.
7. `git push -u origin HEAD`, then open the PR with `gh pr create --base main` using `.github/pull_request_template.md`: summary, AC ids covered, issue link (`Closes #n`), test evidence (coverage number), and a note on anything the AI got wrong with a link to the corrections entries.
8. Check CI with `gh pr checks` (watch briefly if running). Report the result honestly; if red, say so and offer to fix.
9. **Return the PR URL to the user** with a short summary: slice, ACs, commits, coverage, CI status. Stop there.

## Rules
- Always a PR. Never merge it, never push to `main`, never force-push, never skip hooks (`--no-verify`).
- Merge method, when the user merges: merge commit, not squash (keeps the test-first history).
- Never change repo visibility.
- Cleanup of the branch and worktree happens later via `/clean-worktrees`.
