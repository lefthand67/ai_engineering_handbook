# External Repos Reset Feature Implementation Plan (Refined)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `--reset` flag to `manage_external_repos.py update` that forcibly clears unstaged changes in external research repositories when `git pull --rebase` fails, following strict TDD and testing standards.

**Architecture:**
- **`tools/scripts/git.py`**: New `reset_repo(path: Path)` utility for `git reset --hard origin/<branch>`.
- **`tools/scripts/manage_external_repos.py`**: 
    - Updated CLI parser to include `--reset`.
    - Update loop modified to: `pull` $\rightarrow$ `if fail and reset` $\rightarrow$ `warn` $\rightarrow$ `reset` $\rightarrow$ `retry pull`.
- **Testing**: Contract-based assertions in `tools/tests/test_git.py` and `tools/tests/test_manage_external_repos.py`.

**Tech Stack:** Python 3.13, `pytest`, `subprocess`.

---

### Task 1: TDD for Git Reset Utility

**Files:**
- Modify: `tools/scripts/git.py`
- Test: `tools/tests/test_git.py`

- [ ] **Step 1: Write failing test for `reset_repo`**
In `tools/tests/test_git.py`, add a test that:
1. Initializes a temporary git repo.
2. Commits a file.
3. Makes an unstaged modification to that file.
4. Calls `reset_repo()` and asserts the modification is gone (file matches original commit).

```python
def test_reset_repo_clears_unstaged_changes(tmp_path):
    # Setup: create repo, commit file, modify file
    # ...
    import tools.scripts.git as _git
    success = _git.reset_repo(repo_path)
    assert success is True
    assert file_content == original_content
```

- [ ] **Step 2: Run test to verify it fails**
Run: `uv run pytest tools/tests/test_git.py -v`
Expected: FAIL (ImportError or AttributeError: `reset_repo` not found)

- [ ] **Step 3: Implement `reset_repo` in `tools/scripts/git.py`**
```python
def reset_repo(path: Path) -> bool:
    """Forcefully reset a repository to its remote tracking branch."""
    try:
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=path, capture_output=True, text=True, check=True
        )
        branch = branch_result.stdout.strip()
        result = subprocess.run(
            ["git", "reset", "--hard", f"origin/{branch}"],
            cwd=path, capture_output=True, text=True
        )
        return result.returncode == 0
    except (subprocess.CalledProcessError, subprocess.SubprocessError, FileNotFoundError):
        return False
```

- [ ] **Step 4: Run test to verify it passes**
Run: `uv run pytest tools/tests/test_git.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add tools/scripts/git.py tools/tests/test_git.py
git commit -m "feat: add reset_repo utility and tests"
```

---

### Task 2: TDD for CLI Argument and Logic

**Files:**
- Modify: `tools/scripts/manage_external_repos.py`
- Test: `tools/tests/test_manage_external_repos.py`

- [ ] **Step 1: Write failing tests for `--reset` behavior**
In `tools/tests/test_manage_external_repos.py`, add parameterized tests covering:
1. **Standard failure**: Repo has changes, `reset=False` $\rightarrow$ `update_command` returns `1`.
2. **Recovery success**: Repo has changes, `reset=True` $\rightarrow$ `update_command` returns `0`.
3. **Adversary case**: `reset_repo` fails (e.g. no remote) $\rightarrow$ `update_command` returns `1`.

Use `pytest.mark.parametrize` to avoid duplication. Assert on `exit_code`, not output strings.

- [ ] **Step 2: Run tests to verify they fail**
Run: `uv run pytest tools/tests/test_manage_external_repos.py -v`
Expected: FAIL (Argument `--reset` unknown or logic missing)

- [ ] **Step 3: Implement CLI flag and reset logic**
1. Add `--reset` to `_create_parser()` $\rightarrow$ `update_parser`.
2. Update `main()` to pass `args.reset` to `update_command()`.
3. Update `update_command(..., reset: bool = False)` signature.
4. Implement the retry loop in the update logic (both sequential and parallel).

```python
# Example Logic for Update loop
success, message = pull_repo(repo.path)
if not success and reset and "unstaged changes" in message.lower():
    print(f"⚠️  WARNING: Forced reset of {repo.name}...")
    if reset_repo(repo.path):
        success, message = pull_repo(repo.path)
```

- [ ] **Step 4: Run tests to verify they pass**
Run: `uv run pytest tools/tests/test_manage_external_repos.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add tools/scripts/manage_external_repos.py tools/tests/test_manage_external_repos.py
git commit -m "feat: implement --reset flag for external repo updates"
```

---

### Task 3: Full Verification and Coverage

- [ ] **Step 1: Run full test suite with coverage**
Run: `uv run pytest tools/tests/test_manage_external_repos.py --cov=tools.scripts.manage_external_repos`
Verify that the new reset logic paths are fully covered.

- [ ] **Step 2: Manual Integration Test**
1. Go to `ai_agents/research/ai_coding_agents/aider`.
2. `touch some_temp_file` or modify a file.
3. Run `uv run tools/scripts/manage_external_repos.py update` $\rightarrow$ expect failure.
4. Run `uv run tools/scripts/manage_external_repos.py update --reset` $\rightarrow$ expect success and local changes deleted.

- [ ] **Step 3: Final Commit**
```bash
git commit -m "test: verify coverage and integration for reset feature"
```
