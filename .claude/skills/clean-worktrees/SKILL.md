---
name: clean-worktrees
description: Remove git worktrees and local branches for slices whose PRs are merged. Lists first, confirms before deleting. Use after merging PRs.
---

Clean up finished slice worktrees safely.

## Steps
1. `git fetch origin --prune` and `git worktree list --porcelain`. Only consider worktrees under `../taskflow-worktrees/` and branches named `slice/*`; never touch the main checkout.
2. For each candidate, gather: branch, path, `git status --porcelain` (dirty?), unpushed commits (`git log origin/<branch>..<branch>`), and PR state (`gh pr list --head <branch> --state all --json state,number,url`).
3. Classify and show a table:
   - **Safe**: PR is MERGED, tree clean, nothing unpushed.
   - **Needs attention**: PR open/closed-unmerged, dirty tree, unpushed commits, or no PR. Explain why; do not remove these unless the user explicitly says so for that specific worktree.
4. Ask the user to confirm the **Safe** list. Then for each: `git worktree remove <path>`, `git branch -d slice/<name>` (lowercase `-d` so git refuses unmerged branches), and delete the remote branch only if the user agrees (`git push origin --delete slice/<name>`).
5. `git worktree prune`, then show the final `git worktree list` and `git branch`.

## Rules
- Never use `--force`, `-D`, or `rm -rf` on worktrees.
- Never delete a worktree with uncommitted changes without explicit per-worktree approval.
