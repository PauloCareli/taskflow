# AI corrections log

Where the AI got it wrong, how it was caught, and the fix.

| Date | What the AI produced | What was wrong | Caught by (test/review/runtime) | Fix | Commit |
|---|---|---|---|---|---|
| 2026-11-15 | `git checkout pyproject.toml uv.lock` to discard an unrelated uv change | Also discarded uncommitted import-linter and build-system edits | Runtime: the violation demo reported no broken contracts | Re-applied the edits and re-ran the demo. Rule: never restore files that hold uncommitted work | `9f9fb36` |
| 2026-11-15 | gitleaks pre-commit hook reused as the CI secret check | The hook scans only staged files, so on a clean CI checkout it scanned nothing and always passed | Independent review | Dedicated CI job that scans the pushed commits | `621c227` |
| 2026-11-15 | import-linter contracts forbidding a short list of libraries in `domain` and `application` | Unlisted libraries (requests, httpx, asyncpg, jose, passlib, pydantic in `application`) passed, so "stdlib only" was not enforced | Independent review, reproduced with deliberate imports | Extended both blocklists and checked each import fails | `99195ab` |
| 2026-11-15 | Settings test that built `Settings()` directly | Read real `TASKAPP_*` variables and `.env`, so it failed on a developer machine with either set | Independent review | Test clears the variables and runs in a temp directory | `3a0e5a2` |
