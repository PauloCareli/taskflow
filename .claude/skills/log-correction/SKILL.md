---
name: log-correction
description: Append an AI mistake and its fix to docs/ai/corrections.md
---

Append a row to the table in `docs/ai/corrections.md` with: date, what the AI produced, what was wrong, how it was caught (test/review/runtime), the fix, and the commit hash (use `git log -1 --format=%h` or leave blank if not yet committed). Ask the user for any missing detail.
