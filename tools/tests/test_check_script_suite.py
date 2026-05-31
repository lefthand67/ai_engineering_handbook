"""Tests for check_script_suite.py — the script+test dyad convention.

Scope: Validates that check_script_suite.py enforces the dyad (every script
has a matching test) and nothing more. Doc checks were removed when ADR-26011
was superseded by ADR-26045.

Contracts tested:
- script_name_to_paths: name → (script_path, test_path) tuple
- get_staged_files / get_renamed_files: git plumbing wrappers
- is_mode_only_change: distinguishes permission-only from content changes
- get_all_scripts: discovers scripts, respects exclusion list
- check_naming_convention: errors when test is missing, silent when present
- main: exit 0 when clean, exit 1 when errors

What does NOT belong here: doc staging, doc rename, config file staging.
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

import tools.scripts.check_script_suite as _module


# =======================
# Unit Tests: script_name_to_paths
# =======================


class TestScriptNameToPaths:
    """Contract: converts a script stem to (script_path, test_path)."""

    def test_converts_name_to_paths(self):
        script, test = _module.script_name_to_paths("check_broken_links")
        assert script == _module.SCRIPTS_DIR / "check_broken_links.py"
        assert test == _module.TESTS_DIR / "test_check_broken_links.py"

    def test_handles_simple_name(self):
        script, test = _module.script_name_to_paths("foo")
        assert script == _module.SCRIPTS_DIR / "foo.py"
        assert test == _module.TESTS_DIR / "test_foo.py"


# ======================
# Unit Tests: get_staged_files
# ======================


class TestGetStagedFiles:
    """Contract: returns a set of staged file paths from git."""

    def test_returns_set_of_staged_files(self):
        mock_result = MagicMock()
        mock_result.stdout = "file1.py\nfile2.py\nfile3.md\n"
        with patch("subprocess.run", return_value=mock_result):
            result = _module.get_staged_files()
        assert result == {"file1.py", "file2.py", "file3.md"}

    def test_returns_empty_set_when_no_staged_files(self):
        mock_result = MagicMock()
        mock_result.stdout = ""
        with patch("subprocess.run", return_value=mock_result):
            result = _module.get_staged_files()
        assert result == set()

    def test_handles_single_file(self):
        mock_result = MagicMock()
        mock_result.stdout = "single.py\n"
        with patch("subprocess.run", return_value=mock_result):
            result = _module.get_staged_files()
        assert result == {"single.py"}


# ======================
# Unit Tests: get_renamed_files
# ======================


class TestGetRenamedFiles:
    """Contract: returns {old_path: new_path} for renames in staging area."""

    def test_detects_renamed_file(self):
        mock_result = MagicMock()
        mock_result.stdout = "R100\told_name.md\tnew_name.md\n"
        with patch("subprocess.run", return_value=mock_result):
            result = _module.get_renamed_files()
        assert result == {"old_name.md": "new_name.md"}

    def test_detects_multiple_renames(self):
        mock_result = MagicMock()
        mock_result.stdout = "R100\ta.md\tb.md\nR095\tc.py\td.py\n"
        with patch("subprocess.run", return_value=mock_result):
            result = _module.get_renamed_files()
        assert result == {"a.md": "b.md", "c.py": "d.py"}

    def test_ignores_non_rename_statuses(self):
        mock_result = MagicMock()
        mock_result.stdout = "M\tmodified.py\nA\tadded.py\nD\tdeleted.py\n"
        with patch("subprocess.run", return_value=mock_result):
            result = _module.get_renamed_files()
        assert result == {}

    def test_returns_empty_when_no_changes(self):
        mock_result = MagicMock()
        mock_result.stdout = ""
        with patch("subprocess.run", return_value=mock_result):
            result = _module.get_renamed_files()
        assert result == {}


# ======================
# Unit Tests: is_mode_only_change
# ======================


class TestIsModeOnlyChange:
    """Contract: True when staged diff has only mode lines, no hunks."""

    def test_returns_true_for_mode_only_change(self):
        mock_result = MagicMock()
        mock_result.stdout = """diff --git a/script.py b/script.py
old mode 100644
new mode 100755"""
        with patch("subprocess.run", return_value=mock_result):
            result = _module.is_mode_only_change("script.py")
        assert result is True

    def test_returns_false_for_content_change(self):
        mock_result = MagicMock()
        mock_result.stdout = """diff --git a/script.py b/script.py
index abc123..def456 100644
--- a/script.py
+++ b/script.py
@@ -1,3 +1,4 @@
 line1
+new line
 line2"""
        with patch("subprocess.run", return_value=mock_result):
            result = _module.is_mode_only_change("script.py")
        assert result is False

    def test_returns_false_for_mode_and_content_change(self):
        mock_result = MagicMock()
        mock_result.stdout = """diff --git a/script.py b/script.py
old mode 100644
new mode 100755
index abc123..def456
--- a/script.py
+++ b/script.py
@@ -1,3 +1,4 @@
 line1
+new line"""
        with patch("subprocess.run", return_value=mock_result):
            result = _module.is_mode_only_change("script.py")
        assert result is False

    def test_returns_true_for_empty_diff(self):
        mock_result = MagicMock()
        mock_result.stdout = ""
        with patch("subprocess.run", return_value=mock_result):
            result = _module.is_mode_only_change("script.py")
        assert result is True

    def test_calls_git_diff_with_correct_arguments(self):
        mock_result = MagicMock()
        mock_result.stdout = ""
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            _module.is_mode_only_change("tools/scripts/my_script.py")
        mock_run.assert_called_once_with(
            ["git", "diff", "--cached", "--", "tools/scripts/my_script.py"],
            capture_output=True,
            text=True,
        )


# =======================
# Unit Tests: check_staging_dyad
# =======================


class TestCheckStagingDyad:
    """Contract: verifies that staged scripts have staged tests."""

    def test_errors_when_script_staged_but_test_not(self):
        staged = {"tools/scripts/my_script.py"}
        # Mock is_mode_only_change to return False (meaning it has content changes)
        with patch("tools.scripts.check_script_suite.is_mode_only_change", return_value=False):
            errors = _module.check_staging_dyad(staged_files=staged)
        assert len(errors) == 1
        assert "Staging violation" in errors[0]
        assert "tools/tests/test_my_script.py" in errors[0]

    def test_passes_when_both_staged(self):
        staged = {"tools/scripts/my_script.py", "tools/tests/test_my_script.py"}
        with patch("tools.scripts.check_script_suite.is_mode_only_change", return_value=False):
            errors = _module.check_staging_dyad(staged_files=staged)
        assert errors == []

    def test_ignores_mode_only_changes(self):
        staged = {"tools/scripts/my_script.py"}
        # Mock is_mode_only_change to return True
        with patch("tools.scripts.check_script_suite.is_mode_only_change", return_value=True):
            errors = _module.check_staging_dyad(staged_files=staged)
        assert errors == []

    def test_ignores_excluded_scripts(self):
        staged = {"tools/scripts/paths.py"}
        with patch("tools.scripts.check_script_suite.is_mode_only_change", return_value=False):
            errors = _module.check_staging_dyad(staged_files=staged)
        assert errors == []

    def test_ignores_non_script_files(self):
        staged = {"README.md", "pyproject.toml"}
        errors = _module.check_staging_dyad(staged_files=staged)
        assert errors == []


# ======================
# Unit Tests: get_all_scripts
# ======================


class TestGetAllScripts:
    """Contract: returns script stems, excluding EXCLUDED_SCRIPTS."""

    def test_finds_scripts_in_directory(self, tmp_path):
        scripts_dir = tmp_path / "tools" / "scripts"
        scripts_dir.mkdir(parents=True)
        (scripts_dir / "script_a.py").touch()
        (scripts_dir / "script_b.py").touch()
        (scripts_dir / "paths.py").touch()  # excluded

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir):
            result = _module.get_all_scripts()

        assert set(result) == {"script_a", "script_b"}

    def test_excludes_paths_py(self, tmp_path):
        scripts_dir = tmp_path / "tools" / "scripts"
        scripts_dir.mkdir(parents=True)
        (scripts_dir / "paths.py").touch()

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir):
            result = _module.get_all_scripts()

        assert "paths" not in result

    def test_excludes_init_py(self, tmp_path):
        scripts_dir = tmp_path / "tools" / "scripts"
        scripts_dir.mkdir(parents=True)
        (scripts_dir / "__init__.py").touch()

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir):
            result = _module.get_all_scripts()

        assert "__init__" not in result

    def test_returns_empty_when_dir_not_exists(self, tmp_path):
        nonexistent = tmp_path / "nonexistent"
        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", nonexistent):
            result = _module.get_all_scripts()
        assert result == []

        assert set(result) == {"script_a", "script_b"}

    def test_excludes_paths_py(self, tmp_path):
        scripts_dir = tmp_path / "tools" / "scripts"
        scripts_dir.mkdir(parents=True)
        (scripts_dir / "paths.py").touch()

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir):
            result = _module.get_all_scripts()

        assert "paths" not in result

    def test_excludes_init_py(self, tmp_path):
        scripts_dir = tmp_path / "tools" / "scripts"
        scripts_dir.mkdir(parents=True)
        (scripts_dir / "__init__.py").touch()

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir):
            result = _module.get_all_scripts()

        assert "__init__" not in result

    def test_returns_empty_when_dir_not_exists(self, tmp_path):
        nonexistent = tmp_path / "nonexistent"
        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", nonexistent):
            result = _module.get_all_scripts()
        assert result == []


# ======================
# Integration Tests: Staging Dyad
# ======================


class TestStagingDyadIntegration:
    """Contract: verifies staging dyad enforcement using a real Git repository."""

    def setup_repo(self, tmp_path):
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo_dir, capture_output=True)
        
        # Create initial commit to establish state
        (repo_dir / "init.txt").write_text("init")
        subprocess.run(["git", "add", "init.txt"], cwd=repo_dir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo_dir, capture_output=True)
        
        return repo_dir

    def test_fails_when_script_staged_without_test(self, tmp_path, monkeypatch):
        repo = self.setup_repo(tmp_path)
        monkeypatch.chdir(repo)

        # Create script and test
        script_path = Path("tools/scripts/my_script.py")
        script_path.parent.mkdir(parents=True)
        script_path.write_text("print('hello')")

        test_path = Path("tools/tests/test_my_script.py")
        test_path.parent.mkdir(parents=True)
        test_path.write_text("def test_hello(): pass")

        # Stage ONLY the script
        subprocess.run(["git", "add", str(script_path)], capture_output=True)

        errors = _module.check_staging_dyad()

        assert len(errors) == 1
        assert "Staging violation" in errors[0]

    def test_passes_when_both_staged(self, tmp_path, monkeypatch):
        repo = self.setup_repo(tmp_path)
        monkeypatch.chdir(repo)

        script_path = Path("tools/scripts/my_script.py")
        script_path.parent.mkdir(parents=True)
        script_path.write_text("print('hello')")

        test_path = Path("tools/tests/test_my_script.py")
        test_path.parent.mkdir(parents=True)
        test_path.write_text("def test_hello(): pass")

        # Stage BOTH
        subprocess.run(["git", "add", str(script_path)], capture_output=True)
        subprocess.run(["git", "add", str(test_path)], capture_output=True)

        errors = _module.check_staging_dyad()

        assert errors == []

    def test_handles_renamed_script_dyad(self, tmp_path, monkeypatch):
        """Adversary: verify that renaming a script still requires staging the renamed test."""
        repo = self.setup_repo(tmp_path)
        monkeypatch.chdir(repo)

        # Setup initial state
        script = Path("tools/scripts/old_script.py")
        script.parent.mkdir(parents=True)
        script.write_text("content")
        test = Path("tools/tests/test_old_script.py")
        test.parent.mkdir(parents=True)
        test.write_text("test")

        subprocess.run(["git", "add", "."], capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], capture_output=True)

        # Rename script
        new_script = Path("tools/scripts/new_script.py")
        new_script.write_text("content")
        script.unlink()

        # Stage only the renamed script
        subprocess.run(["git", "add", "."], capture_output=True)

        errors = _module.check_staging_dyad()

        assert len(errors) == 1
        assert "test_new_script.py" in errors[0]

    def test_error_when_test_missing(self, tmp_path):
        scripts_dir = tmp_path / "tools" / "scripts"
        tests_dir = tmp_path / "tools" / "tests"
        scripts_dir.mkdir(parents=True)
        tests_dir.mkdir(parents=True)

        (scripts_dir / "my_script.py").touch()
        # test file missing

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir), \
             patch("tools.scripts.check_script_suite.TESTS_DIR", tests_dir):
            errors = _module.check_naming_convention()

        assert len(errors) == 1
        assert "Missing test" in errors[0]

    def test_no_error_for_missing_doc(self, tmp_path):
        """Docs are not part of the dyad — missing doc must not cause an error."""
        scripts_dir = tmp_path / "tools" / "scripts"
        tests_dir = tmp_path / "tools" / "tests"
        scripts_dir.mkdir(parents=True)
        tests_dir.mkdir(parents=True)

        (scripts_dir / "my_script.py").touch()
        (tests_dir / "test_my_script.py").touch()
        # no doc file — should be fine

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir), \
             patch("tools.scripts.check_script_suite.TESTS_DIR", tests_dir):
            errors = _module.check_naming_convention()

        assert errors == []

    def test_multiple_scripts_missing_tests(self, tmp_path):
        scripts_dir = tmp_path / "tools" / "scripts"
        tests_dir = tmp_path / "tools" / "tests"
        scripts_dir.mkdir(parents=True)
        tests_dir.mkdir(parents=True)

        (scripts_dir / "script_a.py").touch()
        (scripts_dir / "script_b.py").touch()
        # both tests missing

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir), \
             patch("tools.scripts.check_script_suite.TESTS_DIR", tests_dir):
            errors = _module.check_naming_convention()

        assert len(errors) == 2


# ======================
# Integration Tests: main
# ======================

class TestCommitScopedValidation:
    """Contract: when files are passed as args, only those files are validated."""

    def test_ignores_non_passed_files_when_args_provided(self, tmp_path, capsys):
        scripts_dir = tmp_path / "tools" / "scripts"
        tests_dir = tmp_path / "tools" / "tests"
        scripts_dir.mkdir(parents=True)
        tests_dir.mkdir(parents=True)

        # Script A: OK (has test)
        (scripts_dir / "script_ok.py").touch()
        (tests_dir / "test_script_ok.py").touch()

        # Script B: BAD (missing test)
        (scripts_dir / "script_bad.py").touch()

        # Simulate pre-commit passing only script_ok.py
        passed_file = str(scripts_dir / "script_ok.py")

        mock_staged = MagicMock()
        mock_staged.stdout = ""

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir), \
             patch("tools.scripts.check_script_suite.TESTS_DIR", tests_dir), \
             patch("subprocess.run", return_value=mock_staged), \
             patch("sys.argv", ["check_script_suite.py", passed_file]):
            result = _module.main()

        captured = capsys.readouterr()
        # Should be 0 because script_bad.py was not in the arguments
        assert result == 0
        assert "Missing test" not in captured.out

    def test_ignores_non_python_files_in_args(self, tmp_path):
        scripts_dir = tmp_path / "tools" / "scripts"
        scripts_dir.mkdir(parents=True)
        (scripts_dir / "readme.txt").touch()

        passed_file = str(scripts_dir / "readme.txt")
        mock_staged = MagicMock()
        mock_staged.stdout = ""

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir), \
             patch("subprocess.run", return_value=mock_staged), \
             patch("sys.argv", ["check_script_suite.py", passed_file]):
            result = _module.main()

        assert result == 0

    def test_ignores_files_outside_scripts_dir_in_args(self, tmp_path):
        other_dir = tmp_path / "other"
        other_dir.mkdir(parents=True)
        (other_dir / "script.py").touch()

        passed_file = str(other_dir / "script.py")
        mock_staged = MagicMock()
        mock_staged.stdout = ""

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", tmp_path / "tools" / "scripts"), \
             patch("subprocess.run", return_value=mock_staged), \
             patch("sys.argv", ["check_script_suite.py", passed_file]):
            result = _module.main()

        assert result == 0

    def test_errors_when_passed_script_missing_test(self, tmp_path, capsys):
        scripts_dir = tmp_path / "tools" / "scripts"
        tests_dir = tmp_path / "tools" / "tests"
        scripts_dir.mkdir(parents=True)
        tests_dir.mkdir(parents=True)

        (scripts_dir / "script_bad.py").touch()
        passed_file = str(scripts_dir / "script_bad.py")

        mock_staged = MagicMock()
        mock_staged.stdout = ""

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir), \
             patch("tools.scripts.check_script_suite.TESTS_DIR", tests_dir), \
             patch("subprocess.run", return_value=mock_staged), \
             patch("sys.argv", ["check_script_suite.py", passed_file]):
            result = _module.main()

        captured = capsys.readouterr()
        assert result == 1
        assert "Missing test" in captured.out

class TestMain:
    """Contract: exit 0 when all scripts have tests, exit 1 otherwise."""



    def test_exits_zero_when_no_errors(self, tmp_path):
        scripts_dir = tmp_path / "tools" / "scripts"
        tests_dir = tmp_path / "tools" / "tests"
        scripts_dir.mkdir(parents=True)
        tests_dir.mkdir(parents=True)

        (scripts_dir / "my_script.py").touch()
        (tests_dir / "test_my_script.py").touch()

        mock_staged = MagicMock()
        mock_staged.stdout = ""

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir), \
             patch("tools.scripts.check_script_suite.TESTS_DIR", tests_dir), \
             patch("subprocess.run", return_value=mock_staged), \
             patch("sys.argv", ["check_script_suite.py"]):
            result = _module.main()

        assert result == 0

    def test_verbose_output_on_success(self, tmp_path, capsys):
        scripts_dir = tmp_path / "tools" / "scripts"
        tests_dir = tmp_path / "tools" / "tests"
        scripts_dir.mkdir(parents=True)
        tests_dir.mkdir(parents=True)

        (scripts_dir / "my_script.py").touch()
        (tests_dir / "test_my_script.py").touch()

        mock_staged = MagicMock()
        mock_staged.stdout = ""

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir), \
             patch("tools.scripts.check_script_suite.TESTS_DIR", tests_dir), \
             patch("subprocess.run", return_value=mock_staged), \
             patch("sys.argv", ["check_script_suite.py", "-v"]):
            result = _module.main()

        captured = capsys.readouterr()
        assert result == 0
        assert "All checks passed" in captured.out

    def test_exits_one_when_test_missing(self, tmp_path, capsys):
        scripts_dir = tmp_path / "tools" / "scripts"
        tests_dir = tmp_path / "tools" / "tests"
        scripts_dir.mkdir(parents=True)
        tests_dir.mkdir(parents=True)

        (scripts_dir / "my_script.py").touch()
        # missing test

        mock_staged = MagicMock()
        mock_staged.stdout = ""

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir), \
             patch("tools.scripts.check_script_suite.TESTS_DIR", tests_dir), \
             patch("subprocess.run", return_value=mock_staged), \
             patch("sys.argv", ["check_script_suite.py"]):
            result = _module.main()

        captured = capsys.readouterr()
        assert result == 1
        assert "Missing test" in captured.out

    def test_check_convention_only_skips_staging_checks(self, tmp_path):
        scripts_dir = tmp_path / "tools" / "scripts"
        tests_dir = tmp_path / "tools" / "tests"
        scripts_dir.mkdir(parents=True)
        tests_dir.mkdir(parents=True)

        (scripts_dir / "my_script.py").touch()
        (tests_dir / "test_my_script.py").touch()

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir), \
             patch("tools.scripts.check_script_suite.TESTS_DIR", tests_dir), \
             patch("tools.scripts.check_script_suite.get_staged_files") as mock_staged, \
             patch("sys.argv", ["check_script_suite.py", "--check-convention-only"]):
            result = _module.main()

        mock_staged.assert_not_called()
        assert result == 0
