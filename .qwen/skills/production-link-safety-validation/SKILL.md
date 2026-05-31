---
name: production-link-safety-validation
description: Ensuring that links/references in a commit point to targets that are tracked by Git to prevent "works on my machine" production breakages.
source: auto-skill
extracted_at: '2026-05-31T11:20:00.000Z'
---

# Production Link Safety Validation

When validating links or references (e.g., Markdown links, file imports, configuration paths) in a pre-commit hook, simply checking if the target file exists on the local filesystem (`Path.exists()`) is insufficient. This leads to "works on my machine" bugs, where a developer links to a local file they forgot to stage/track, causing the link to be broken in production (the remote server) despite passing local validation.

## The Principle: Production Link Safety
A reference is only considered "valid" if its target is **tracked by the Git index**. If a file exists on disk but is untracked, it must be treated as a broken link to force the developer to `git add` the target.

## Implementation Strategy

### 1. The Git Primitive
Use `git ls-files --error-unmatch <path>` to verify if a specific path is tracked by Git.

- **Exit Code 0**: The file is tracked.
- **Exit Code 1**: The file is untracked or does not exist.

### 2. Integration into Validation Logic
Update the target validation method to check both existence and tracking status.

**Critical Requirement: CWD Management**
Git commands must be executed relative to the repository root to avoid failures when the script is called from subdirectories. Always pass an explicit `cwd` (e.g., the resolved project root) to the Git wrapper.

**Correct (Production-Safe with CWD and Fallback):**
```python
from tools.scripts.git import is_tracked

def is_valid_target(self, target_file: Path) -> bool:
    # 1. Basic existence check
    if not target_file.exists():
        return False

    # 2. Production Safety Check: Target must be tracked by Git
    # Only enforce tracking if we are actually in a Git repository
    if self.use_git_tracking:
        # Pass root_dir as CWD to ensure git ls-files finds the target
        if not is_tracked(target_file, cwd=self.root_dir):
            return False

    return True
```

## Verification via TDD

To implement this safely, use temporary Git repositories in your tests:

1.  **Scenario: Valid Tracked Target**
    -   Create `target.md`, `git add target.md`.
    -   Create `source.md` with link to `target.md`, `git add source.md`.
    -   **Expected**: PASS.
2.  **Scenario: Untracked Target (The Loophole)**
    -   Create `target.md` (do NOT `git add`).
    -   Create `source.md` with link to `target.md`, `git add source.md`.
    -   **Expected**: FAIL (Target is untracked).
3.  **Scenario: Non-existent Target**
    -   Create `source.md` with link to `missing.md`.
    -   **Expected**: FAIL (Target does not exist).
4.  **Scenario: Non-Git Environment (Isolation)**
    -   Run the validator in a directory without a `.git` folder.
    -   **Expected**: PASS (if file exists), ensuring unit tests in `tmp_path` don't fail unnecessarily.

## Key Benefits
- **Zero-Regression Production Deploys**: Guarantees that every reference validated locally will also be resolved on the remote server.
- **Developer Guidance**: Forces developers to remember to stage dependency files.
- **SVA Compliance**: Leverages existing Git CLI capabilities without requiring heavy libraries like `GitPython`.
