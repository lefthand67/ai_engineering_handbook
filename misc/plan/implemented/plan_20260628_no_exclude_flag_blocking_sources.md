# Plan: Add --no-exclude Flag and Fix Blocking Source Exclusion Bypass

**Date:** 2026-06-28  
**Branch:** `release/3.2.0`  
**Plan ID:** `plan_20260628_no_exclude_flag_blocking_sources`  

## Full Context Section

### Problem

`check_broken_links.py` has a bug: when pre-commit passes staged files as positional arguments (`args.files`), they are collected into `blocking_sources` with **zero exclusion checks** (lines 155–159). These files are then force-appended to the scan list (lines 187–190), bypassing `VALIDATION_EXCLUDE_DIRS` and `is_excluded()`.

This caused a real failure: `misc/plan/implemented/plan_20260628_fix_pre_commit_failures.md` (staged) was passed by pre-commit as a positional argument. The `FileFinder` correctly excluded it from directory scanning (`misc` is in `VALIDATION_EXCLUDE_DIRS`), but the force-append loop re-added it, and broken links were reported as `[BLOCKING]` — blocking the commit.

Additionally, there is no way to force-check files in excluded directories via CLI. The `--paths` flag applies `is_excluded()` (line 169), so you cannot check a file in `misc/` even if you explicitly request it. There is also no verbose logging when a positional argument is excluded — the file silently disappears from the scan.

### Current State

**`tools/scripts/check_broken_links.py`** — key sections:

- **Lines 85–111**: CLI argument parser. Has `files` (positional), `--paths`, `--pattern`, `--exclude-dirs`, `--exclude-files`, `--fail-on-legacy`, `--verbose`. No `--no-exclude` flag exists.
- **Lines 155–159**: Blocking sources collection from `args.files` — no exclusion check:
  ```python
  blocking_sources = set()
  if args.files:
      for f in args.files:
          p = Path(f).resolve()
          blocking_sources.add(p)
  ```
- **Lines 165–178**: `--paths` processing — applies `is_excluded()` for single files (line 169):
  ```python
  if resolved.is_file():
      if is_excluded(str(resolved)):
          if verbose:
              logger.debug(f"  EXCLUDING (by directory rule): {resolved}")
          continue
      files.append(resolved)
  ```
- **Lines 187–190**: Force-append blocking sources — no exclusion check:
  ```python
  for bs in blocking_sources:
      if bs not in files:
          files.append(bs)
  ```

**`tools/scripts/paths.py`** — exclusion logic:

- **Lines 97–106**: `_STATIC_EXCLUDE_DIRS` — includes `"misc"` (line 106).
- **Line 115**: `VALIDATION_EXCLUDE_DIRS = _STATIC_EXCLUDE_DIRS | get_external_repo_paths(...)`.
- **Lines 158–160**: `is_excluded()` — substring match against `VALIDATION_EXCLUDE_DIRS`:
  ```python
  def is_excluded(path: str) -> bool:
      return any(excl in path for excl in VALIDATION_EXCLUDE_DIRS)
  ```

**`.pre-commit-config.yaml`** — hook configuration (lines 5–11):

```yaml
- id: check-broken-links
  name: Check Broken Links
  entry: uv run --active tools/scripts/check_broken_links.py
  language: python
  pass_filenames: true
  verbose: true
  stages: [pre-commit, manual]
```

No `files` filter, no `exclude` pattern. `pass_filenames: true` means all staged files are passed as positional arguments.

**`tools/tests/test_check_broken_links.py`** — test structure:

- `TestLinkExtractor` — unit tests for link extraction.
- `TestLinkValidator` — unit tests for link validation.
- `TestFileFinder` — unit tests for file discovery with exclusions.
- `TestReporter` — unit tests for exit code behavior.
- `TestLinkCheckerGitIntegration` — integration tests using real git repos in `tmp_path`.
- `TestLinkCheckerCLI` — CLI-level tests.
- `TestLinkExtractorContextAware` — context-aware extraction tests.
- `TestContextAwareBlocking` — blocking behavior for `.py` files.

Existing test `test_run_explicit_file_in_excluded_dir_is_skipped` (line ~780) already verifies that `--paths` to a `misc/` file is excluded. But there is **no test** for positional arguments (`args.files`) being excluded — this is the gap.

### Content Mapping Table

| File | Current State | Action | Why |
|------|--------------|--------|-----|
| `tools/scripts/check_broken_links.py` lines 85–111 | CLI parser has no `--no-exclude` flag | Add `--no-exclude` argument | Allow bypassing exclusions for explicit CLI requests |
| `tools/scripts/check_broken_links.py` lines 155–159 | Positional args go to `blocking_sources` with no exclusion check | Add `is_excluded()` check + verbose logging | Prevent excluded files from being force-scanned |
| `tools/scripts/check_broken_links.py` lines 165–178 | `--paths` applies `is_excluded()` but has no bypass | Add `--no-exclude` bypass | Allow force-checking excluded files via `--paths` |
| `tools/tests/test_check_broken_links.py` | No tests for positional arg exclusion or `--no-exclude` | Add test class with TDD tests | Verify new behavior |

## Cross-Reference Map

### Files referencing the changed files

| Referencing File | Line(s) | Reference | Status |
|-----------------|---------|-----------|--------|
| `.pre-commit-config.yaml` | 5–11 | `check-broken-links` hook calls `check_broken_links.py` with `pass_filenames: true` | ✅ No change needed — hook already passes positional args, script will now filter them |
| `.pre-commit-config.yaml` | 106–110 | `test-check-broken-links` hook runs pytest on the test file | ✅ Must stage both script and test (script-test dyad rule) |
| `tools/scripts/paths.py` | 97–106, 158–160 | `VALIDATION_EXCLUDE_DIRS` and `is_excluded()` imported by `check_broken_links.py` | ✅ No change needed — existing function reused |

### Cross-reference diagram (final state)

```
Pre-commit stages misc/plan/file.md
    └──► passed as positional arg to check_broken_links.py
    └──► is_excluded("misc/...") → True
    └──► verbose: "EXCLUDING (by directory rule): ..." logged
    └──► file NOT added to blocking_sources → NOT force-appended
    └──► commit proceeds

CLI: check_broken_links.py misc/plan/file.md
    └──► is_excluded("misc/...") → True → excluded
    └──► "No files matching '*.md' found!" → exit 0

CLI: check_broken_links.py --no-exclude misc/plan/file.md
    └──► is_excluded() bypassed
    └──► file added to blocking_sources → scanned
    └──► broken links reported as [BLOCKING]

CLI: check_broken_links.py --no-exclude --paths misc/plan/file.md
    └──► is_excluded() bypassed
    └──► file added to files list → scanned
```

## Rationale for Each Task

### Task 1: Add `--no-exclude` CLI flag

**Why:** Users need a way to force-check files in excluded directories (e.g., `misc/`, `research/`). Without this, there is no CLI path to validate a file that lives in an excluded directory, even when explicitly requested. The flag must be opt-in (default: exclusions apply) to preserve the safety of pre-commit runs.

**Why a flag and not a separate subcommand:** A boolean flag is the simplest extension to the existing argparse-based CLI. It composes naturally with `--paths` and positional arguments. A subcommand would over-engineer the interface for a single escape hatch.

### Task 2: Apply `is_excluded()` to positional arguments (`args.files`)

**Why:** Pre-commit passes all staged `.md` files as positional arguments with `pass_filenames: true`. If a file in `misc/` is staged (e.g., a plan file), it lands in `blocking_sources` and is force-appended to the scan list — bypassing the exclusion that `FileFinder` already correctly applies during directory scanning. This is the root cause of the commit failure.

**Why not add `exclude: ^misc/` to the pre-commit hook:** That would only fix `misc/` — other excluded directories (e.g., `research/`, `__pycache__/`) would still bypass the check. The script-level fix is universal.

### Task 3: Apply `--no-exclude` bypass to `--paths` arguments

**Why:** The `--paths` flag already applies `is_excluded()` (line 169). Without the bypass, `--no-exclude` would only work for positional arguments, creating an inconsistent UX. The bypass must apply to both entry points (`--paths` and positional) for the flag to be useful.

### Task 4: Add verbose logging when positional arguments are excluded

**Why:** When a user runs `check_broken_links.py file.md` and the file is in `misc/`, the script silently reports "No files matching '*.md' found!" — there is no indication why. The `--paths` path already logs `"EXCLUDING (by directory rule): ..."` (line 171). Positional arguments should log the same message for consistency and discoverability.

### Task 5: Write TDD tests first

**Why:** The project mandates TDD (Red → Green → Refactor). Tests must be written first to verify the bug exists, then the implementation makes them pass. Tests also serve as regression protection for the exclusion bypass.

## Complete File Content

No new files are created. All changes are edits to existing files.

## Exact Edit Operations

### Edit 1: Add `--no-exclude` argument to CLI parser

**File:** `tools/scripts/check_broken_links.py`

**old_string** (lines 103–111, with 3 lines context before and after):
```python
        parser.add_argument(
            "--fail-on-legacy",
            action="store_true",
            default=False,
            help="Fail the build even if only legacy (unstaged) broken links are found.",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            default=False,
            help="Enable verbose mode for more output information.",
        )
        return parser

    def run(self, argv: Optional[List[str]] = None) -> None:
        """
        Execute logic.
        :param argv: Optional list of strings. If None, uses sys.argv[1:].
        """
```

**new_string**:
```python
        parser.add_argument(
            "--fail-on-legacy",
            action="store_true",
            default=False,
            help="Fail the build even if only legacy (unstaged) broken links are found.",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            default=False,
            help="Enable verbose mode for more output information.",
        )
        parser.add_argument(
            "--no-exclude",
            action="store_true",
            default=False,
            help="Bypass directory exclusion rules — force-check files in excluded dirs (e.g., misc/, research/).",
        )
        return parser

    def run(self, argv: Optional[List[str]] = None) -> None:
        """
        Execute logic.
        :param argv: Optional list of strings. If None, uses sys.argv[1:].
        """
```

### Edit 2: Add `no_exclude` variable in `run()` method

**File:** `tools/scripts/check_broken_links.py`

**old_string** (lines 117–124, with 3 lines context before and after):
```python
        # Injectable argument parsing
        args = self.parser.parse_args(argv)
        verbose = args.verbose
        pattern = args.pattern
        fail_on_legacy = args.fail_on_legacy

        # Configure logging
        logging.basicConfig(level=logging.INFO, format="%(message)s")
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
```

**new_string**:
```python
        # Injectable argument parsing
        args = self.parser.parse_args(argv)
        verbose = args.verbose
        pattern = args.pattern
        fail_on_legacy = args.fail_on_legacy
        no_exclude = args.no_exclude

        # Configure logging
        logging.basicConfig(level=logging.INFO, format="%(message)s")
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
```

### Edit 3: Apply `is_excluded()` to positional arguments with `--no-exclude` bypass

**File:** `tools/scripts/check_broken_links.py`

**old_string** (lines 141–148, with 3 lines context before and after):
```python
        else:
            logger.info(f"Using Git root as project root: {root_dir.name}")

        # Blocking sources are files passed as positional arguments (e.g. by pre-commit)
        blocking_sources = set()
        if args.files:
            for f in args.files:
                p = Path(f).resolve()
                blocking_sources.add(p)

        files = []
```

**new_string**:
```python
        else:
            logger.info(f"Using Git root as project root: {root_dir.name}")

        # Blocking sources are files passed as positional arguments (e.g. by pre-commit)
        blocking_sources = set()
        if args.files:
            for f in args.files:
                p = Path(f).resolve()
                if not no_exclude and is_excluded(str(p)):
                    if verbose:
                        logger.debug(f"  EXCLUDING (by directory rule): {p}")
                    continue
                blocking_sources.add(p)

        files = []
```

### Edit 4: Apply `--no-exclude` bypass to `--paths` single-file check

**File:** `tools/scripts/check_broken_links.py`

**old_string** (lines 165–177, with 3 lines context before and after):
```python
            resolved_paths_list.append(resolved)

            if resolved.is_file():
                if is_excluded(str(resolved)):
                    if verbose:
                        logger.debug(f"  EXCLUDING (by directory rule): {resolved}")
                    continue
                files.append(resolved)
            elif resolved.is_dir():
                files.extend(file_finder.find(resolved, pattern))
            else:
                logger.warning(f"Warning: Path does not exist: {resolved}")

        # Ensure blocking sources are included in the scan if they weren't already
```

**new_string**:
```python
            resolved_paths_list.append(resolved)

            if resolved.is_file():
                if not no_exclude and is_excluded(str(resolved)):
                    if verbose:
                        logger.debug(f"  EXCLUDING (by directory rule): {resolved}")
                    continue
                files.append(resolved)
            elif resolved.is_dir():
                files.extend(file_finder.find(resolved, pattern))
            else:
                logger.warning(f"Warning: Path does not exist: {resolved}")

        # Ensure blocking sources are included in the scan if they weren't already
```

### Edit 5: Add TDD test class for `--no-exclude` and blocking source exclusion

**File:** `tools/tests/test_check_broken_links.py`

**old_string** (lines 991–1028 — the last test class, with 3 lines context before):
```python
        extractor = LinkExtractor(verbose=False)
        links = extractor.extract(md_file)
        assert ("link.ipynb", 1) in links
        assert ("/path/to/file.md", 2) in links


class TestContextAwareBlocking:
    """Contract: .py files in tools/scripts/ with broken links are still [BLOCKING]."""

    def test_py_file_broken_link_in_comment_is_blocking(self, tmp_path, monkeypatch, capsys):
        """A .py file with a broken link in a comment must be flagged as [BLOCKING]."""
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True)
        (repo / "init.txt").write_text("init")
        subprocess.run(["git", "add", "init.txt"], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo, capture_output=True)
        monkeypatch.chdir(repo)

        py_file = Path("script.py")
        py_file.write_text(
            '# See [broken](nonexistent.md) for details\n',
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "script.py"], cwd=repo, capture_output=True)

        with pytest.raises(SystemExit) as exc_info:
            LinkCheckerCLI().run(["--pattern", "*.py", str(py_file)])

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "[BLOCKING]" in captured.out
        assert "nonexistent.md" in captured.out
```

**new_string** (preserve existing class, append new test class after it):
```python
        extractor = LinkExtractor(verbose=False)
        links = extractor.extract(md_file)
        assert ("link.ipynb", 1) in links
        assert ("/path/to/file.md", 2) in links


class TestContextAwareBlocking:
    """Contract: .py files in tools/scripts/ with broken links are still [BLOCKING]."""

    def test_py_file_broken_link_in_comment_is_blocking(self, tmp_path, monkeypatch, capsys):
        """A .py file with a broken link in a comment must be flagged as [BLOCKING]."""
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True)
        (repo / "init.txt").write_text("init")
        subprocess.run(["git", "add", "init.txt"], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo, capture_output=True)
        monkeypatch.chdir(repo)

        py_file = Path("script.py")
        py_file.write_text(
            '# See [broken](nonexistent.md) for details\n',
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "script.py"], cwd=repo, capture_output=True)

        with pytest.raises(SystemExit) as exc_info:
            LinkCheckerCLI().run(["--pattern", "*.py", str(py_file)])

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "[BLOCKING]" in captured.out
        assert "nonexistent.md" in captured.out


# =============================================================================
# --no-exclude Flag & Blocking Source Exclusion (TDD)
# =============================================================================

class TestNoExcludeFlag:
    """Contract: --no-exclude bypasses directory exclusion rules for explicit CLI requests.

    Default behavior: files in VALIDATION_EXCLUDE_DIRS (misc/, research/, etc.) are
    excluded from all scan paths (positional args, --paths, directory scan).
    With --no-exclude: all exclusion checks are bypassed, allowing force-checking
    files in excluded directories.
    """

    def setup_repo(self, tmp_path):
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        subprocess.run(["git", "init"], cwd=repo_dir, capture_output=True)
        (repo_dir / "init.txt").write_text("init")
        subprocess.run(["git", "add", "init.txt"], cwd=repo_dir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo_dir, capture_output=True)
        return repo_dir

    def test_positional_arg_in_excluded_dir_is_skipped_by_default(self, tmp_path, monkeypatch, capsys):
        """Red: positional arg (pre-commit style) in misc/ is excluded by default."""
        repo = self.setup_repo(tmp_path)
        monkeypatch.chdir(repo)

        excluded_file = Path("misc") / "plan.md"
        excluded_file.parent.mkdir()
        excluded_file.write_text("[bad](missing.md)", encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            LinkCheckerCLI().run([str(excluded_file)])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "No files matching" in captured.out

    def test_positional_arg_in_excluded_dir_verbose_logs_exclusion(self, tmp_path, monkeypatch, caplog):
        """Verbose mode logs EXCLUDING message for positional args in excluded dirs."""
        repo = self.setup_repo(tmp_path)
        monkeypatch.chdir(repo)

        excluded_file = Path("misc") / "plan.md"
        excluded_file.parent.mkdir()
        excluded_file.write_text("[bad](missing.md)", encoding="utf-8")

        caplog.set_level(logging.DEBUG)
        with pytest.raises(SystemExit):
            LinkCheckerCLI().run(["--verbose", str(excluded_file)])

        assert "EXCLUDING (by directory rule)" in caplog.text
        assert "misc" in caplog.text

    def test_no_exclude_flag_force_checks_positional_arg(self, tmp_path, monkeypatch, capsys):
        """Green: --no-exclude bypasses exclusion for positional args."""
        repo = self.setup_repo(tmp_path)
        monkeypatch.chdir(repo)

        excluded_file = Path("misc") / "plan.md"
        excluded_file.parent.mkdir()
        excluded_file.write_text("[bad](missing.md)", encoding="utf-8")
        subprocess.run(["git", "add", str(excluded_file)], cwd=repo, capture_output=True)

        with pytest.raises(SystemExit) as exc_info:
            LinkCheckerCLI().run(["--no-exclude", str(excluded_file)])

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "[BLOCKING]" in captured.out
        assert "missing.md" in captured.out

    def test_no_exclude_flag_force_checks_paths_arg(self, tmp_path, monkeypatch, capsys):
        """Green: --no-exclude bypasses exclusion for --paths single-file requests."""
        repo = self.setup_repo(tmp_path)
        monkeypatch.chdir(repo)

        excluded_file = Path("misc") / "plan.md"
        excluded_file.parent.mkdir()
        excluded_file.write_text("[bad](missing.md)", encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            LinkCheckerCLI().run(["--no-exclude", "--paths", str(excluded_file)])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "[LEGACY]" in captured.out
        assert "missing.md" in captured.out

    def test_no_exclude_does_not_affect_non_excluded_files(self, tmp_path, monkeypatch, capsys):
        """--no-exclude has no effect on files not in excluded dirs."""
        repo = self.setup_repo(tmp_path)
        monkeypatch.chdir(repo)

        target = Path("target.md")
        target.touch()
        subprocess.run(["git", "add", "target.md"], cwd=repo, capture_output=True)

        source = Path("source.md")
        source.write_text(f"[link]({target.name})", encoding="utf-8")
        subprocess.run(["git", "add", "source.md"], cwd=repo, capture_output=True)

        with pytest.raises(SystemExit) as exc_info:
            LinkCheckerCLI().run(["--no-exclude", str(source)])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "All links are valid" in captured.out

    def test_no_exclude_does_not_affect_directory_scan(self, tmp_path, monkeypatch, capsys):
        """--no-exclude does NOT bypass FileFinder directory-scan exclusions.

        The flag only affects explicitly requested files (positional args and --paths).
        Directory scanning (rglob) still respects VALIDATION_EXCLUDE_DIRS.
        """
        repo = self.setup_repo(tmp_path)
        monkeypatch.chdir(repo)

        # File in excluded dir — should NOT be found by directory scan even with --no-exclude
        excluded_file = Path("misc") / "plan.md"
        excluded_file.parent.mkdir()
        excluded_file.write_text("[bad](missing.md)", encoding="utf-8")

        # Normal file outside excluded dir
        normal_file = Path("docs") / "guide.md"
        normal_file.parent.mkdir()
        normal_file.write_text("[bad](also_missing.md)", encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            LinkCheckerCLI().run(["--no-exclude", "--pattern", "*.md"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "misc" not in captured.out
        assert "also_missing.md" in captured.out
```

## Content Removal List

No sections are removed, moved, or split. All changes are:
- ✅ **Insert**: `--no-exclude` argument in CLI parser (after `--verbose`) — Edit 1
- ✅ **Insert**: `no_exclude` variable in `run()` method (after `fail_on_legacy`) — Edit 2
- ✅ **Modify**: Positional args loop — add `is_excluded()` check with `no_exclude` bypass + verbose logging — Edit 3
- ✅ **Modify**: `--paths` single-file check — add `no_exclude` bypass to `is_excluded()` guard — Edit 4
- ✅ **Append**: New `TestNoExcludeFlag` test class at end of test file — Edit 5

## Commands with Expected Output

### Step 1: Write tests first (TDD Red phase)

Apply **Edit 5** first — add the `TestNoExcludeFlag` test class to `tools/tests/test_check_broken_links.py`.

Then run:

```bash
uv run pytest tools/tests/test_check_broken_links.py::TestNoExcludeFlag -q
```

**Expected:** Tests fail (Red). Specifically:
- `test_positional_arg_in_excluded_dir_is_skipped_by_default` — FAIL (file IS scanned because no exclusion check exists yet, so it reports `[BLOCKING]` and exits 1 instead of the expected exit 0 with "No files matching")
- `test_positional_arg_in_excluded_dir_verbose_logs_exclusion` — FAIL (no EXCLUDING log message)
- `test_no_exclude_flag_force_checks_positional_arg` — FAIL (`--no-exclude` flag doesn't exist yet, argparse errors)
- `test_no_exclude_flag_force_checks_paths_arg` — FAIL (`--no-exclude` flag doesn't exist yet)
- `test_no_exclude_does_not_affect_non_excluded_files` — FAIL (`--no-exclude` flag doesn't exist yet)
- `test_no_exclude_does_not_affect_directory_scan` — FAIL (`--no-exclude` flag doesn't exist yet)

### Step 2: Apply Edits 1–4 (implementation — TDD Green phase)

Apply **Edit 1** (add `--no-exclude` flag to parser), **Edit 2** (add `no_exclude` variable), **Edit 3** (exclusion check for positional args), **Edit 4** (`--no-exclude` bypass for `--paths`).

Use the `edit` tool with the exact `old_string` and `new_string` from Edits 1, 2, 3, and 4 above.

### Step 3: Run new tests (TDD Green phase)

```bash
uv run pytest tools/tests/test_check_broken_links.py::TestNoExcludeFlag -q
```

**Expected:** All 6 tests pass (Green).

### Step 4: Run full test suite to verify no regressions

```bash
uv run pytest tools/tests/test_check_broken_links.py -q
```

**Expected:** All tests pass (existing + new).

### Step 5: Verify the real-world scenario is fixed

```bash
uv run tools/scripts/check_broken_links.py misc/plan/implemented/plan_20260628_fix_pre_commit_failures.md
```

**Expected:** Exit code 0, "No files matching '*.md' found!" (file excluded because `misc/` is in `VALIDATION_EXCLUDE_DIRS`).

### Step 6: Verify `--no-exclude` force-checks the file

```bash
uv run tools/scripts/check_broken_links.py --no-exclude misc/plan/implemented/plan_20260628_fix_pre_commit_failures.md
```

**Expected:** Exit code 0 or 1 depending on whether the broken links in that file are still present. The file IS scanned (not excluded).

### Step 7: Verify verbose logging for excluded positional args

```bash
uv run tools/scripts/check_broken_links.py --verbose misc/plan/implemented/plan_20260628_fix_pre_commit_failures.md
```

**Expected:** Log output contains `EXCLUDING (by directory rule):` and the file path.

### Step 8: Stage and commit (script + test dyad)

```bash
git add tools/scripts/check_broken_links.py tools/tests/test_check_broken_links.py
```

**Expected:** Both files staged. Verify with `git diff --cached --name-only`:
```
tools/scripts/check_broken_links.py
tools/tests/test_check_broken_links.py
```

## Self-Review Section

- [x] **Spec coverage verified:** All three requirements covered — (1) `--no-exclude` flag, (2) exclusion check for positional args, (3) verbose logging for excluded positional args.
- [x] **Placeholder scan completed:** No "..." or "TBD" in the plan. All file content is explicit.
- [x] **Cross-reference consistency checked:** All files referencing `check_broken_links.py` are listed. The pre-commit hook config does not need changes (script-level fix is sufficient).
- [x] **Scope check completed:** Plan only addresses the exclusion bypass bug and `--no-exclude` flag. No unrelated changes. `FileFinder.find()` directory scanning is NOT modified — it already correctly excludes `misc/`.
- [x] **Edit precision verified:** All `old_string` values match the exact file content (verified by reading the file).
- [x] **Test dyad satisfied:** Both `check_broken_links.py` and `test_check_broken_links.py` are staged together.
- [x] **TDD ordering:** Tests written first (Red), then implementation (Green). Tests verify both the bug fix and the new `--no-exclude` flag.
- [x] **`--no-exclude` scope:** Flag affects positional args and `--paths` single-file checks only. Directory scanning (`FileFinder.find()`) is NOT affected — this is intentional and tested.