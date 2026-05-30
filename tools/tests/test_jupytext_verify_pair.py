"""Tests for jupytext_verify_pair.py script."""
import sys
import runpy
from unittest.mock import MagicMock, patch, call

import pytest

from tools.scripts.jupytext_verify_pair import (
    main,
    get_pair_path,
    is_staged,
    has_unstaged_changes,
    sync_pair,
)


class TestGetPairPath:
    """Test the get_pair_path helper function."""

    def test_md_to_ipynb(self):
        """Markdown file should return corresponding ipynb path."""
        assert get_pair_path("test.md") == "test.ipynb"
        assert get_pair_path("path/to/file.md") == "path/to/file.ipynb"

    def test_ipynb_to_md(self):
        """Ipynb file should return corresponding md path."""
        assert get_pair_path("test.ipynb") == "test.md"
        assert get_pair_path("path/to/file.ipynb") == "path/to/file.md"

    def test_other_extension_returns_none(self):
        """Non md/ipynb files should return None."""
        assert get_pair_path("test.py") is None
        assert get_pair_path("test.txt") is None
        assert get_pair_path("test") is None


class TestIsStaged:
    """Test the is_staged helper function."""

    @patch("tools.scripts.jupytext_verify_pair.subprocess.run")
    def test_file_staged_with_changes(self, mock_run):
        """File with staged changes should return True."""
        # First call: git ls-files --error-unmatch --cached
        # Second call: git diff --cached --name-only
        mock_run.side_effect = [
            MagicMock(returncode=0),  # File is tracked
            MagicMock(returncode=0, stdout="test.md\n"),  # Has staged changes
        ]
        assert is_staged("test.md") is True

    @patch("tools.scripts.jupytext_verify_pair.subprocess.run")
    def test_file_not_tracked(self, mock_run):
        """Untracked file should return False."""
        mock_run.return_value = MagicMock(returncode=1)  # Not tracked
        assert is_staged("untracked.md") is False

    @patch("tools.scripts.jupytext_verify_pair.subprocess.run")
    def test_file_tracked_no_staged_changes(self, mock_run):
        """Tracked file without staged changes should return False."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # File is tracked
            MagicMock(returncode=0, stdout=""),  # No staged changes
        ]
        assert is_staged("test.md") is False


class TestHasUnstagedChanges:
    """Test the has_unstaged_changes helper function."""

    @patch("tools.scripts.jupytext_verify_pair.subprocess.run")
    def test_has_unstaged_changes(self, mock_run):
        """File with unstaged changes should return True."""
        mock_run.return_value = MagicMock(returncode=1)  # diff exits 1 if changes
        assert has_unstaged_changes("test.md") is True

    @patch("tools.scripts.jupytext_verify_pair.subprocess.run")
    def test_no_unstaged_changes(self, mock_run):
        """File without unstaged changes should return False."""
        mock_run.return_value = MagicMock(returncode=0)  # diff exits 0 if no changes
        assert has_unstaged_changes("test.md") is False


class TestSyncPair:
    """Test the sync_pair helper function."""

    @patch("tools.scripts.jupytext_verify_pair.subprocess.run")
    def test_sync_pair_success(self, mock_run, capsys):
        """Successful sync should print stdout if present."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="[jupytext] Syncing test.md\n", stderr=""
        )
        sync_pair("test.md")

        captured = capsys.readouterr()
        assert "[jupytext] Syncing test.md" in captured.out
        mock_run.assert_called_once_with(
            ["uv", "run", "jupytext", "--sync", "test.md"],
            capture_output=True,
            text=True,
        )

    @patch("tools.scripts.jupytext_verify_pair.subprocess.run")
    def test_sync_pair_failure(self, mock_run, capsys):
        """Failed sync should print error message and stderr."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="Error: file not found\n"
        )
        sync_pair("test.md")

        captured = capsys.readouterr()
        assert "FAIL: test.md cannot be synced." in captured.out
        assert "Error: file not found" in captured.out

    @patch("tools.scripts.jupytext_verify_pair.subprocess.run")
    def test_sync_pair_called_when_one_staged(self, mock_run, monkeypatch, tmp_path, capsys):
        """Verify sync_pair is called when one file is staged but not the other."""
        md_file = tmp_path / "test.md"
        md_file.touch()
        ipynb_file = tmp_path / "test.ipynb"
        ipynb_file.touch()

        call_log = []

        def mock_git_response(cmd, **kwargs):
            call_log.append(cmd)
            if "jupytext" in cmd:
                return MagicMock(returncode=0, stdout="Synced\n", stderr="")
            if "ls-files" in cmd:
                return MagicMock(returncode=0)
            if "diff" in cmd and "--cached" in cmd:
                # Only md file is staged
                if str(md_file) in cmd:
                    return MagicMock(returncode=0, stdout=f"{md_file}\n")
                return MagicMock(returncode=0, stdout="")
            return MagicMock(returncode=0)

        mock_run.side_effect = mock_git_response
        monkeypatch.setattr("sys.argv", ["jupytext_verify_pair.py", str(md_file)])

        result = main()

        assert result == 1
        # Verify jupytext --sync was called
        jupytext_calls = [c for c in call_log if "jupytext" in c]
        assert len(jupytext_calls) == 1
        assert "--sync" in jupytext_calls[0]


class TestVerifyPairNoFiles:
    """Test behavior when no files are provided."""

    def test_no_args_returns_zero(self, monkeypatch):
        """No arguments should return 0."""
        monkeypatch.setattr("sys.argv", ["jupytext_verify_pair.py"])
        assert main() == 0

    def test_empty_files_list_returns_zero(self, monkeypatch):
        """Empty files list should return 0."""
        monkeypatch.setattr("sys.argv", ["jupytext_verify_pair.py"])
        assert main() == 0


class TestVerifyPairFileFiltering:
    """Test file filtering logic."""

    def test_non_md_ipynb_files_filtered(self, monkeypatch, tmp_path):
        """Non-.md/.ipynb files should be filtered out."""
        txt_file = tmp_path / "test.txt"
        txt_file.touch()

        monkeypatch.setattr("sys.argv", ["jupytext_verify_pair.py", str(txt_file)])
        assert main() == 0

    def test_excluded_dirs_skipped(self, monkeypatch, tmp_path):
        """Files in excluded directories should be skipped."""
        venv_dir = tmp_path / ".venv"
        venv_dir.mkdir()
        venv_file = venv_dir / "test.md"
        venv_file.touch()

        monkeypatch.setattr("sys.argv", ["jupytext_verify_pair.py", str(venv_file)])
        assert main() == 0

    def test_all_files_excluded_returns_zero(self, monkeypatch, tmp_path):
        """If all provided files are excluded, should return 0."""
        venv_file = tmp_path / ".venv" / "test.md"
        venv_file.parent.mkdir()
        venv_file.touch()
        monkeypatch.setattr("sys.argv", ["jupytext_verify_pair.py", str(venv_file)])
        assert main() == 0


class TestVerifyPairPairNotExists:
    """Test when pair file doesn't exist."""

    @patch("tools.scripts.jupytext_verify_pair.subprocess.run")
    def test_pair_file_not_exists_ok(self, mock_run, monkeypatch, tmp_path):
        """If pair file doesn't exist, should skip (OK)."""
        md_file = tmp_path / "standalone.md"
        md_file.touch()
        # No corresponding .ipynb file

        monkeypatch.setattr("sys.argv", ["jupytext_verify_pair.py", str(md_file)])
        result = main()
        assert result == 0
        # subprocess.run should not be called for git checks
        mock_run.assert_not_called()


class TestVerifyPairNeitherStaged:
    """Test when neither file is staged."""

    @patch("tools.scripts.jupytext_verify_pair.subprocess.run")
    def test_neither_staged_ok(self, mock_run, monkeypatch, tmp_path):
        """Neither file staged should return OK."""
        md_file = tmp_path / "test.md"
        md_file.touch()
        ipynb_file = tmp_path / "test.ipynb"
        ipynb_file.touch()

        # Mock git responses: both files not staged
        def mock_git_response(cmd, **kwargs):
            if "ls-files" in cmd:
                return MagicMock(returncode=0)  # File tracked
            if "diff" in cmd and "--cached" in cmd:
                return MagicMock(returncode=0, stdout="")  # No staged changes
            return MagicMock(returncode=0)

        mock_run.side_effect = mock_git_response
        monkeypatch.setattr("sys.argv", ["jupytext_verify_pair.py", str(md_file)])

        result = main()
        assert result == 0


class TestVerifyPairBothStaged:
    """Test when both files are staged."""

    @patch("tools.scripts.jupytext_verify_pair.subprocess.run")
    def test_both_staged_no_unstaged_changes_ok(self, mock_run, monkeypatch, tmp_path):
        """Both staged with no unstaged changes should return OK."""
        md_file = tmp_path / "test.md"
        md_file.touch()
        ipynb_file = tmp_path / "test.ipynb"
        ipynb_file.touch()

        call_count = {"count": 0}

        def mock_git_response(cmd, **kwargs):
            call_count["count"] += 1
            if "ls-files" in cmd:
                return MagicMock(returncode=0)  # File tracked
            if "diff" in cmd and "--cached" in cmd:
                # Return the file path to indicate staged changes
                if str(md_file) in cmd:
                    return MagicMock(returncode=0, stdout=f"{md_file}\n")
                if str(ipynb_file) in cmd:
                    return MagicMock(returncode=0, stdout=f"{ipynb_file}\n")
            if "diff" in cmd and "--exit-code" in cmd:
                return MagicMock(returncode=0)  # No unstaged changes
            return MagicMock(returncode=0)

        mock_run.side_effect = mock_git_response
        monkeypatch.setattr("sys.argv", ["jupytext_verify_pair.py", str(md_file)])

        result = main()
        assert result == 0


class TestVerifyPairOneStagedOtherNot:
    """Test when one file is staged but not the other."""

    @patch("tools.scripts.jupytext_verify_pair.subprocess.run")
    def test_md_staged_ipynb_not_fails(self, mock_run, monkeypatch, tmp_path, capsys):
        """MD staged but ipynb not should fail."""
        md_file = tmp_path / "test.md"
        md_file.touch()
        ipynb_file = tmp_path / "test.ipynb"
        ipynb_file.touch()

        def mock_git_response(cmd, **kwargs):
            if "ls-files" in cmd:
                return MagicMock(returncode=0)  # Both tracked
            if "diff" in cmd and "--cached" in cmd:
                # Only md file is staged
                if str(md_file) in cmd:
                    return MagicMock(returncode=0, stdout=f"{md_file}\n")
                return MagicMock(returncode=0, stdout="")  # ipynb not staged
            return MagicMock(returncode=0)

        mock_run.side_effect = mock_git_response
        monkeypatch.setattr("sys.argv", ["jupytext_verify_pair.py", str(md_file)])

        result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "FAIL:" in captured.out
        assert "staged" in captured.out

    @patch("tools.scripts.jupytext_verify_pair.subprocess.run")
    def test_ipynb_staged_md_not_fails(self, mock_run, monkeypatch, tmp_path, capsys):
        """Ipynb staged but md not should fail."""
        md_file = tmp_path / "test.md"
        md_file.touch()
        ipynb_file = tmp_path / "test.ipynb"
        ipynb_file.touch()

        def mock_git_response(cmd, **kwargs):
            if "ls-files" in cmd:
                return MagicMock(returncode=0)  # Both tracked
            if "diff" in cmd and "--cached" in cmd:
                # Only ipynb file is staged
                if str(ipynb_file) in cmd:
                    return MagicMock(returncode=0, stdout=f"{ipynb_file}\n")
                return MagicMock(returncode=0, stdout="")  # md not staged
            return MagicMock(returncode=0)

        mock_run.side_effect = mock_git_response
        monkeypatch.setattr("sys.argv", ["jupytext_verify_pair.py", str(ipynb_file)])

        result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "FAIL:" in captured.out

    @patch("tools.scripts.jupytext_verify_pair.subprocess.run")
    def test_pair_staged_md_not_fails(self, mock_run, monkeypatch, tmp_path, capsys):
        """Ipynb staged but md not should fail (asymmetric check)."""
        md_file = tmp_path / "test.md"
        md_file.touch()
        ipynb_file = tmp_path / "test.ipynb"
        ipynb_file.touch()

        def mock_git_response(cmd, **kwargs):
            if "ls-files" in cmd:
                return MagicMock(returncode=0)
            if "diff" in cmd and "--cached" in cmd:
                # Only ipynb file is staged
                if str(ipynb_file) in cmd:
                    return MagicMock(returncode=0, stdout=f"{ipynb_file}\n")
                return MagicMock(returncode=0, stdout="")
            return MagicMock(returncode=0)

        mock_run.side_effect = mock_git_response
        monkeypatch.setattr("sys.argv", ["jupytext_verify_pair.py", str(md_file)])

        result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "FAIL:" in captured.out
        assert "is staged but" in captured.out


class TestVerifyPairUnstagedChanges:
    """Test when staged files have unstaged changes."""

    @patch("tools.scripts.jupytext_verify_pair.subprocess.run")
    def test_both_staged_md_has_unstaged_fails(self, mock_run, monkeypatch, tmp_path, capsys):
        """Both staged but md has unstaged changes should fail with a descriptive message."""
        md_file = tmp_path / "test.md"
        md_file.touch()
        ipynb_file = tmp_path / "test.ipynb"
        ipynb_file.touch()

        def mock_git_response(cmd, **kwargs):
            if "ls-files" in cmd:
                return MagicMock(returncode=0)
            if "diff" in cmd and "--cached" in cmd:
                # Both staged
                if str(md_file) in cmd:
                    return MagicMock(returncode=0, stdout=f"{md_file}\n")
                if str(ipynb_file) in cmd:
                    return MagicMock(returncode=0, stdout=f"{ipynb_file}\n")
            if "diff" in cmd and "--exit-code" in cmd:
                # md has unstaged changes
                if str(md_file) in cmd:
                    return MagicMock(returncode=1)  # Has unstaged changes
                return MagicMock(returncode=0)  # No unstaged changes
            return MagicMock(returncode=0)

        mock_run.side_effect = mock_git_response
        monkeypatch.setattr("sys.argv", ["jupytext_verify_pair.py", str(md_file)])

        result = main()

        assert result == 1
        captured = capsys.readouterr()
        expected_msg = f"FAIL: {md_file} has unstaged changes. If this occurred during a commit, it likely means the file was updated by jupytext-sync. Please run 'git add {md_file}' to stage the changes."
        assert expected_msg in captured.out

    @patch("tools.scripts.jupytext_verify_pair.subprocess.run")
    def test_both_staged_ipynb_has_unstaged_fails(self, mock_run, monkeypatch, tmp_path, capsys):
        """Both staged but ipynb has unstaged changes should fail with a descriptive message."""
        md_file = tmp_path / "test.md"
        md_file.touch()
        ipynb_file = tmp_path / "test.ipynb"
        ipynb_file.touch()

        def mock_git_response(cmd, **kwargs):
            if "ls-files" in cmd:
                return MagicMock(returncode=0)
            if "diff" in cmd and "--cached" in cmd:
                # Both staged
                if str(md_file) in cmd:
                    return MagicMock(returncode=0, stdout=f"{md_file}\n")
                if str(ipynb_file) in cmd:
                    return MagicMock(returncode=0, stdout=f"{ipynb_file}\n")
            if "diff" in cmd and "--exit-code" in cmd:
                # ipynb has unstaged changes
                if str(ipynb_file) in cmd:
                    return MagicMock(returncode=1)
                return MagicMock(returncode=0)
            return MagicMock(returncode=0)

        mock_run.side_effect = mock_git_response
        monkeypatch.setattr("sys.argv", ["jupytext_verify_pair.py", str(md_file)])

        result = main()

        assert result == 1
        captured = capsys.readouterr()
        expected_msg = f"FAIL: {ipynb_file} has unstaged changes. If this occurred during a commit, it likely means the file was updated by jupytext-sync. Please run 'git add {ipynb_file}' to stage the changes."
        assert expected_msg in captured.out


class TestVerifyPairDuplicateHandling:
    """Test duplicate pair handling when both .md and .ipynb are passed."""

    @patch("tools.scripts.jupytext_verify_pair.subprocess.run")
    def test_both_files_passed_checks_only_once(self, mock_run, monkeypatch, tmp_path):
        """When both md and ipynb are passed, pair should only be checked once."""
        md_file = tmp_path / "test.md"
        md_file.touch()
        ipynb_file = tmp_path / "test.ipynb"
        ipynb_file.touch()

        git_calls = []

        def mock_git_response(cmd, **kwargs):
            git_calls.append(cmd)
            if "ls-files" in cmd:
                return MagicMock(returncode=0)
            if "diff" in cmd and "--cached" in cmd:
                return MagicMock(returncode=0, stdout="")  # Not staged
            return MagicMock(returncode=0)

        mock_run.side_effect = mock_git_response
        monkeypatch.setattr(
            "sys.argv", ["jupytext_verify_pair.py", str(md_file), str(ipynb_file)]
        )

        result = main()

        assert result == 0
        # With duplicate handling, we check each file in the pair once for staging
        # So we should see 4 calls (2 for is_staged of md, 2 for is_staged of ipynb)
        # But NOT 8 calls (which would happen if we checked both pairs separately)
        # The key is that the second file's pair (which is the first file) is already checked
        assert len(git_calls) == 4  # ls-files + diff --cached for each file


class TestVerifyPairMixedScenarios:
    """Test mixed scenarios with multiple pairs."""

    @patch("tools.scripts.jupytext_verify_pair.subprocess.run")
    def test_multiple_pairs_one_fails(self, mock_run, monkeypatch, tmp_path, capsys):
        """Multiple pairs where one fails should return 1."""
        # First pair - OK
        good_md = tmp_path / "good.md"
        good_md.touch()
        good_ipynb = tmp_path / "good.ipynb"
        good_ipynb.touch()

        # Second pair - FAIL (md staged, ipynb not)
        bad_md = tmp_path / "bad.md"
        bad_md.touch()
        bad_ipynb = tmp_path / "bad.ipynb"
        bad_ipynb.touch()

        def mock_git_response(cmd, **kwargs):
            if "ls-files" in cmd:
                return MagicMock(returncode=0)
            if "diff" in cmd and "--cached" in cmd:
                # good pair: neither staged
                if str(good_md) in cmd or str(good_ipynb) in cmd:
                    return MagicMock(returncode=0, stdout="")
                # bad pair: only md staged
                if str(bad_md) in cmd:
                    return MagicMock(returncode=0, stdout=f"{bad_md}\n")
                if str(bad_ipynb) in cmd:
                    return MagicMock(returncode=0, stdout="")
            return MagicMock(returncode=0)

        mock_run.side_effect = mock_git_response
        monkeypatch.setattr(
            "sys.argv", ["jupytext_verify_pair.py", str(good_md), str(bad_md)]
        )

        result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "FAIL:" in captured.out

class TestVerifyPairAdversarial:
    """Adversarial tests for jupytext_verify_pair.py."""

    @patch("tools.scripts.jupytext_verify_pair.subprocess.run")
    def test_sync_pair_failure_during_verification(self, mock_run, monkeypatch, tmp_path, capsys):
        """Verify that if sync_pair fails during the 'one staged, other not' check, it's handled gracefully."""
        md_file = tmp_path / "test.md"
        md_file.touch()
        ipynb_file = tmp_path / "test.ipynb"
        ipynb_file.touch()

        def mock_git_response(cmd, **kwargs):
            if "ls-files" in cmd:
                return MagicMock(returncode=0)
            if "diff" in cmd and "--cached" in cmd:
                if str(md_file) in cmd:
                    return MagicMock(returncode=0, stdout=f"{md_file}\n")
                return MagicMock(returncode=0, stdout="")
            if "jupytext" in cmd:
                return MagicMock(returncode=1, stdout="", stderr="Critical Jupytext Error\n")
            return MagicMock(returncode=0)

        mock_run.side_effect = mock_git_response
        monkeypatch.setattr("sys.argv", ["jupytext_verify_pair.py", str(md_file)])

        result = main()
        assert result == 1
        captured = capsys.readouterr()
        assert f"FAIL: {md_file} is staged but {ipynb_file} is not" in captured.out
        assert f"FAIL: {md_file} cannot be synced." in captured.out
        assert "Critical Jupytext Error" in captured.out

    @patch("tools.scripts.jupytext_verify_pair.subprocess.run")
    def test_git_diff_fails_unexpectedly(self, mock_run, monkeypatch, tmp_path):
        """Verify behavior when git diff returns an unexpected error code."""
        md_file = tmp_path / "test.md"
        md_file.touch()
        ipynb_file = tmp_path / "test.ipynb"
        ipynb_file.touch()

        def mock_git_response(cmd, **kwargs):
            if "diff" in cmd and "--exit-code" in cmd:
                return MagicMock(returncode=128, stderr="fatal: not a git repository")
            return MagicMock(returncode=0)

        mock_run.side_effect = mock_git_response
        monkeypatch.setattr("sys.argv", ["jupytext_verify_pair.py", str(md_file)])
        
        result = main()
        assert result == 1

def test_main_entry_point():
    # Cover the __main__ block
    with patch("sys.argv", ["jupytext_verify_pair.py", "--help"]), pytest.raises(SystemExit):
        runpy.run_path("tools/scripts/jupytext_verify_pair.py", run_name="__main__")
