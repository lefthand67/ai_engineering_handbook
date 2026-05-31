---
name: pre-commit-commit-scoped-validation
description: Implementing commit-scoped validation in pre-commit hooks to avoid blocking noise from unrelated files.
source: auto-skill
extracted_at: '2026-05-30T14:00:00.000Z'
---

# Pre-commit Commit-Scoped Validation

When implementing validation scripts for `pre-commit` hooks, a common pitfall is performing a global scan of the repository (e.g., using `glob` on a directory) instead of validating only the files being changed in the current commit. This leads to "blocking noise," where unrelated existing errors prevent a developer from committing a small, correct change.

## The Principle: Commit-Scoped Validation
A hook should only validate files passed to it by the `pre-commit` framework. If a file is not part of the current commit, its existing state should not block the commit process.

## Implementation Strategy

### 1. Pre-commit Configuration
In `.pre-commit-config.yaml`, ensure the hook is configured to pass the list of changed filenames to the script:

```yaml
- repo: local
  hooks:
    - id: check-script-suite
      name: Check Script Suite
      entry: uv run tools/scripts/check_script_suite.py
      language: python
      pass_filenames: true  # CRITICAL: Sends changed files as positional arguments
      files: ^tools/scripts/
```

### 2. Script Logic Update
The script must be updated to prioritize the arguments provided in `sys.argv`.

**Incorrect (Global Scan):**
```python
def main():
    # This scans everything, regardless of what changed
    scripts = list(Path("tools/scripts").glob("*.py")) 
    # ... validate all scripts ...
```

**Correct (Scoped Scan):**
```python
import sys
from pathlib import Path

def main():
    # 1. Extract files passed by pre-commit (excluding the script name itself)
    passed_files = sys.argv[1:]
    
    if passed_files:
        # Targeted check: Only validate the files passed as arguments
        files_to_validate = [Path(f) for f in passed_files]
    else:
        # Fallback: Perform global scan (useful for manual runs or full-repo CI)
        files_to_validate = list(Path("tools/scripts").glob("*.py"))
    
    # ... validate only files_to_validate ...
```

## Verification via TDD (Red $\rightarrow$ Green $\rightarrow$ Refactor)

To ensure the fix works without introducing regressions:

1.  **Red Phase**: Create a test case that mocks `sys.argv` with a single "correct" file, while a "broken" file exists in the directory. The test should assert that the script exits with `0` (ignoring the broken file).
2.  **Green Phase**: Update the script to handle `sys.argv` as shown above.
3.  **Refactor Phase**: Ensure that the "global scan" fallback still works for manual execution (`uv run script.py`).

## Key Benefits
- **Atomic Commits**: Developers can fix one issue at a time without being forced to fix the entire repository.
- **Faster Feedback**: Reducing the number of files checked per commit speeds up the pre-commit pipeline.
- **Reduced Friction**: Eliminates "blocking noise" that leads developers to use `--no-verify` (which should be strictly prohibited).
