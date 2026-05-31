---
name: recover-uncommitted-corruption
description: How to detect and recover from accidental local file overwrites using git history.
source: auto-skill
extracted_at: '2026-05-30T20:40:00.000Z'
token_size: 800
options:
  type: skill
---

# Recovering from Uncommitted File Corruption

When a file is accidentally overwritten, corrupted, or deleted in the working directory before being committed, standard `git status` only shows that the file is "modified." To recover the original content without losing other uncommitted work in the same file (if any) or to simply revert to the last known good state.

## Diagnosis: Identifying the Overwrite
When a file's content changes drastically or a "correct" file suddenly triggers "missing field" errors, use `git log -p` to see the last committed state.

```bash
# View the last patch for a specific file to verify the last known good content
git log -p -n 1 <file_path>
```

If the `git log` shows the expected content but the current file does not, you have an "uncommitted corruption."

## Recovery: Restoring from HEAD
To restore a corrupted file to its state at the last commit (`HEAD`):

```bash
# Restore specific files from the index/last commit
git restore <file_path>
```

### Critical Considerations for Paired Files
In repositories using Jupytext (paired `.md` and `.ipynb` files), **always restore both files**. Restoring only one will lead to synchronization conflicts or the corrupted version being re-introduced during the next sync.

```bash
git restore path/to/file.md path/to/file.ipynb
```

## Workflow Summary
1. **Detect**: Notice unexpected content loss or misleading validation errors.
2. **Verify**: Use `git log -p -n 1 <file>` to confirm the last commit was correct.
3. **Restore**: Use `git restore <file>` to wipe local changes and revert to the committed state.
4. **Re-apply**: Manually re-apply the intentional changes, ensuring structural integrity (e.g., Dual-Block fences) is maintained.
