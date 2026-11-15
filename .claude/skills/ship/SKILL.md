---
name: ship
description: Verify a finished slice, push to main with issue references, and close out the slice. Optional PR mode. Use after /implement.
args: "[--pr]"
---

Ship the current slice. Be conservative: confirm with the user before any push.

## Steps
1. `git status` and `git log origin/main..HEAD --oneline`: show what will be shipped. Stop if there are uncommitted changes the user didn't expect, or if `.env` / secrets are staged.
2. Re-run the full quality gates from `/implement` (backend and/or frontend, whichever changed). Do not ship on red.
3. Run `gitleaks detect --no-banner` if installed; stop on any finding.
4. Check docs: README updated if setup/commands/env/endpoints changed; AC -> test table in `docs/spec.md` current; `docs/ai/prompts.md` has this slice's entry with commit hashes; corrections logged.
5. Confirm commit messages are conventional and reference the issue (`Refs #n`, final commit `Closes #n`). Never squash or rewrite history that is already pushed.
6. Ask the user to confirm, then:
   - Default (solo workflow): `git push origin main`.
   - With `--pr`: push a branch `slice/<name>` and open a PR with `gh pr create` using `.github/` PR template, AC ids covered, test evidence (coverage number), and a note on anything the AI got wrong. Merge with a merge commit, not squash.
7. Verify CI: `gh run watch` (or `gh run list -L 1`). Report the result honestly; if CI is red, say so and fix.
8. Print a one-paragraph summary: slice, ACs, commits, coverage, CI status, what's next.

## Rules
- Never force-push. Never skip hooks (`--no-verify`).
- Never publish or change repo visibility from this skill.
