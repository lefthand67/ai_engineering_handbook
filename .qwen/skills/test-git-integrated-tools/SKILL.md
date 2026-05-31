---
name: test-git-integrated-tools
description: High-fidelity integration testing for tools that interact with the Git CLI using temporary repositories and subprocess wrapping.
source: auto-skill
extracted_at: '2026-05-31T06:30:00.000Z'
---

When developing tools that rely on the Git CLI (e.g., checking the staging area, validating commit history, or verifying file status), unit tests with static mocks are often insufficient to capture the nuance of Git's behavior. High-fidelity integration tests using actual temporary repositories are required.

### Implementation Strategy

#### 1. Repository Utility Module (Recommended)
Instead of calling `subprocess.run` directly inside every test setup, encapsulate common Git operations (like `init_repo`, `add_files`, `commit_files`) in a shared utility module (e.g., `tools.scripts.git`).

This creates a high-level DSL for tests, making them more readable and ensuring that the test setup uses the same logic as the production tool.

```python
# tools/tests/test_my_tool.py
import tools.scripts.git as git

def test_feature(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git.init_repo(repo)
    git.add_files(repo, "important.txt")
    # ...
```

#### 2. Temporary Repository Setup (Low Level)
If a shared module is not available, use `pytest`'s `tmp_path` to create an isolated environment for each test case. This prevents side effects between tests and allows for "adversary" cases (like renames or corrupted indices).

```python
def setup_repo(self, tmp_path):
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    subprocess.run(["git", "init"], cwd=repo_dir, capture_output=True)

    # Establish a baseline state (first commit)
    (repo_dir / "init.txt").write_text("init")
    subprocess.run(["git", "add", "init.txt"], cwd=repo_dir, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_dir, capture_output=True)
    return repo_dir
```

#### 3. Context Management
Avoid passing absolute paths into the tool under test if the tool expects to run from the repository root. Use `monkeypatch.chdir()` to move the entire test process into the temporary repository.

```python
def test_staging_logic(self, tmp_path, monkeypatch):
    repo = self.setup_repo(tmp_path)
    monkeypatch.chdir(repo)  # Ensure all relative paths and git commands are rooted here

    # Now call the tool normally
    result = tool.check_something()
```

#### 4. The "Safe Wrap" Pattern for Subprocess
If you need to intercept `subprocess.run` calls (e.g., to verify arguments or inject specific `cwd` values) while still executing the real command, use the `wraps` parameter.

**CRITICAL:** To avoid `RecursionError`, store a reference to the original function *before* starting the patch. Calling the patched `subprocess.run` inside its own `side_effect` creates an infinite loop.

```python
# INCORRECT (Causes RecursionError)
with patch("subprocess.run", wraps=subprocess.run) as mock_run:
    def side_effect(*args, **kwargs):
        return subprocess.run(*args, **kwargs) # Calls the mock again!
    mock_run.side_effect = side_effect

# CORRECT
original_run = subprocess.run
with patch("subprocess.run", wraps=original_run) as mock_run:
    def side_effect(*args, **kwargs):
        if args and args[0] == "git":
            kwargs["cwd"] = repo_path
        return original_run(*args, **kwargs) # Calls the original function
    mock_run.side_effect = side_effect
```

### Checklist for Git Integration Tests
- [ ] **Baseline Commit**: Does the test create at least one commit? (Many git commands like `diff` or `status` behave differently in an empty repo).
- [ ] **Isolation**: Is `tmp_path` used to ensure no leak between tests?
- [ ] **Adversary Cases**: Have you tested renames (`git mv`), mode-only changes (chmod), and untracked files?
- [ ] **Execution Root**: Is the CWD correctly managed via `monkeypatch.chdir` or explicit `cwd` arguments?
