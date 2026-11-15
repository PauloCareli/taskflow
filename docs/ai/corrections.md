# AI corrections log

Where the AI got it wrong, how it was caught, and the fix.

| Date | What the AI produced | What was wrong | Caught by (test/review/runtime) | Fix | Commit |
|---|---|---|---|---|---|
| 2026-11-15 | Ran `git checkout pyproject.toml uv.lock` to discard an unrelated uv change while scaffolding the import-linter contracts | It also discarded the uncommitted import-linter and build-system edits to `pyproject.toml` | Runtime: the follow-up violation demo reported no broken contracts, which exposed the missing config | Re-applied the edits and re-ran the demo (both violations now reported as broken). Rule: never run checkout/restore on files with uncommitted work; commit first or work on a copy | 9f9fb36 |
