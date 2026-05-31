"""
Test suite for git.py — shared git utilities.

Scope: tests for detect_repo_root() and get_staged_files().
Does NOT test git itself — mocks subprocess calls.

Test classes and their contracts:
- TestDetectRepoRoot: returns resolved Path from git rev-parse, falls back to __file__
- TestGetStagedFiles: returns set of repo-relative paths from git diff --cached

Naming convention: one class per public function.
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import tools.scripts.git as _module


class TestDetectRepoRoot:
    """Contract: detect_repo_root() returns repo root via git, or __file__ fallback."""

    @patch.object(_module.subprocess, "run")
    def test_returns_path_from_git(self, mock_run):
        """git rev-parse succeeds → return its output as resolved Path."""
        mock_run.return_value = MagicMock(stdout="/fake/repo\n")
        result = _module.detect_repo_root()
        assert result == Path("/fake/repo").resolve()
        mock_run.assert_called_once_with(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )

    @patch.object(_module.subprocess, "run")
    def test_fallback_on_git_failure(self, mock_run):
        """git rev-parse fails → fallback to __file__-based path."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        result = _module.detect_repo_root()
        expected = Path(_module.__file__).resolve().parent.parent.parent
        assert result == expected

    @patch.object(_module.subprocess, "run")
    def test_fallback_on_git_not_installed(self, mock_run):
        """git not found → fallback to __file__-based path."""
        mock_run.side_effect = FileNotFoundError()
        result = _module.detect_repo_root()
        expected = Path(_module.__file__).resolve().parent.parent.parent
        assert result == expected

    @patch.object(_module.subprocess, "run")
    def test_strips_whitespace(self, mock_run):
        """Output whitespace (newlines, spaces) is stripped."""
        mock_run.return_value = MagicMock(stdout="  /fake/repo  \n")
        result = _module.detect_repo_root()
        assert result == Path("/fake/repo").resolve()


class TestGetHistoricalPaths:
    """Contract: get_historical_paths(dir) returns all paths that ever existed in that dir."""

    @patch.object(_module.subprocess, "run")
    def test_returns_historical_paths(self, mock_run):
        """git log returns files → return filtered and stripped paths."""
        # Simulate git log --oneline --name-only output
        # format: commit_hash message\nfile_path\n...
        mock_run.return_value = MagicMock(
            stdout="a1b2c3d initial commit\narch/evidence/S-1.md\narch/evidence/S-2.md\nother/file.txt\n"
        )
        result = _module.get_historical_paths("arch/evidence")
        assert result == {"arch/evidence/S-1.md", "arch/evidence/S-2.md"}
        mock_run.assert_called_once_with(
            ["git", "log", "--oneline", "--name-only", "--", "arch/evidence/"],
            capture_output=True,
            text=True,
            check=True,
        )

    @patch.object(_module.subprocess, "run")
    def test_returns_empty_when_no_files(self, mock_run):
        """git log returns nothing → return empty set."""
        mock_run.return_value = MagicMock(stdout="")
        result = _module.get_historical_paths("empty/dir")
        assert result == set()

    @patch.object(_module.subprocess, "run")
    def test_returns_empty_on_failure(self, mock_run):
        """git fails → return empty set (graceful degradation)."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        result = _module.get_historical_paths("fail/dir")
        assert result == set()


class TestIsGitRepo:
    """Contract: is_git_repo(path) returns True if path is inside a git repo, False otherwise."""

    @patch.object(_module.subprocess, "run")
    def test_returns_true_when_inside_repo(self, mock_run):
        """git rev-parse --is-inside-work-tree succeeds → return True."""
        mock_run.return_value = MagicMock(returncode=0)
        assert _module.is_git_repo(Path("/fake/repo")) is True
        mock_run.assert_called_once_with(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=Path("/fake/repo"),
            capture_output=True,
            check=True,
        )

    @patch.object(_module.subprocess, "run")
    def test_returns_false_when_outside_repo(self, mock_run):
        """git rev-parse --is-inside-work-tree fails → return False."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        assert _module.is_git_repo(Path("/fake/not-a-repo")) is False

    @patch.object(_module.subprocess, "run")
    def test_returns_false_on_git_not_found(self, mock_run):
        """git binary not found → return False."""
        mock_run.side_effect = FileNotFoundError()
        assert _module.is_git_repo(Path("/fake/repo")) is False


class TestCloneRepo:


    @patch.object(_module.subprocess, "run")
    def test_clone_success(self, mock_run):
        """git clone succeeds → return True."""
        mock_run.return_value = MagicMock(returncode=0)
        result = _module.clone_repo(
            "https://github.com/test/repo",
            Path("/tmp/test/repo"),
        )
        assert result is True
        mock_run.assert_called_once_with(
            ["git", "clone", "https://github.com/test/repo", "/tmp/test/repo"],
        )

    @patch.object(_module.subprocess, "run")
    def test_clone_with_branch(self, mock_run):
        """git clone with branch → includes --branch flag."""
        mock_run.return_value = MagicMock(returncode=0)
        result = _module.clone_repo(
            "https://github.com/test/repo",
            Path("/tmp/test/repo"),
            branch="main",
        )
        assert result is True
        mock_run.assert_called_once_with(
            [
                "git",
                "clone",
                "--branch",
                "main",
                "https://github.com/test/repo",
                "/tmp/test/repo",
            ],
        )

    @patch.object(_module.subprocess, "run")
    def test_clone_failure(self, mock_run):
        """git clone fails → return False."""
        mock_run.return_value = MagicMock(returncode=1, stderr="repository not found")
        result = _module.clone_repo(
            "https://github.com/test/invalid",
            Path("/tmp/test/invalid"),
        )
        assert result is False

    @patch.object(_module.subprocess, "run")
    def test_clone_git_not_found(self, mock_run):
        """git binary not found → return False."""
        mock_run.side_effect = FileNotFoundError()
        result = _module.clone_repo(
            "https://github.com/test/repo",
            Path("/tmp/test/repo"),
        )
        assert result is False


class TestPullRepo:
    """Contract: pull_repo(path) pulls latest changes, returns (success, message)."""

    @patch.object(_module.subprocess, "run")
    def test_pull_up_to_date(self, mock_run):
        """Repo is up to date → return True with status message."""
        mock_run.return_value = MagicMock(returncode=0)
        success, message = _module.pull_repo(Path("/tmp/test/repo"))
        assert success is True
        assert message == "Updated"

    @patch.object(_module.subprocess, "run")
    def test_pull_updates(self, mock_run):
        """Pull with updates → return True with status message."""
        mock_run.return_value = MagicMock(returncode=0)
        success, message = _module.pull_repo(Path("/tmp/test/repo"))
        assert success is True
        assert message == "Updated"

    @patch.object(_module.subprocess, "run")
    def test_pull_failure(self, mock_run):
        """git pull fails → return False with error."""
        mock_run.return_value = MagicMock(returncode=1)
        success, message = _module.pull_repo(Path("/tmp/test/repo"))
        assert success is False
        assert "git pull failed" in message.lower()

    @patch.object(_module.subprocess, "run")
    def test_pull_git_not_found(self, mock_run):
        """git binary not found → return False with error."""
        mock_run.side_effect = FileNotFoundError("git not found")
        success, message = _module.pull_repo(Path("/tmp/test/repo"))
        assert success is False
        assert "git not found" in message


class TestGetRepoStatus:
    """Contract: get_repo_status(path) returns (branch, remote_url, last_commit_date)."""

    @patch.object(_module.subprocess, "run")
    def test_get_status_success(self, mock_run):
        """All git commands succeed → return tuple of status info."""
        responses = [
            MagicMock(returncode=0, stdout="main\n"),
            MagicMock(returncode=0, stdout="https://github.com/test/repo.git\n"),
            MagicMock(returncode=0, stdout="2024-01-15\n"),
        ]
        mock_run.side_effect = responses

        branch, remote, date = _module.get_repo_status(Path("/tmp/test/repo"))

        assert branch == "main"
        assert "github.com" in remote
        assert "2024-01-15" in date
        assert mock_run.call_count == 3

    @patch.object(_module.subprocess, "run")
    def test_get_status_not_git_repo(self, mock_run):
        """Directory is not a git repo → return None values."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        branch, remote, date = _module.get_repo_status(Path("/tmp/not-a-repo"))

        assert branch is None
        assert remote is None
        assert date is None


class TestGetStagedFiles:
    """Contract: get_staged_files() returns set[str] of staged file paths."""

    @patch.object(_module.subprocess, "run")
    def test_returns_staged_files(self, mock_run):
        """Normal output → set of file paths."""
        mock_run.return_value = MagicMock(stdout="file1.py\nfile2.md\ndir/file3.txt\n")
        result = _module.get_staged_files()
        assert result == {"file1.py", "file2.md", "dir/file3.txt"}
        mock_run.assert_called_once_with(
            ["git", "diff", "--cached", "--name-only"],
            cwd=None,
            capture_output=True,
            text=True,
            check=True,
        )

    @patch.object(_module.subprocess, "run")
    def test_returns_staged_files_with_cwd(self, mock_run):
        """Should support specifying the repository path."""
        mock_run.return_value = MagicMock(stdout="file1.py\n")
        result = _module.get_staged_files(cwd=Path("/fake/repo"))
        assert result == {"file1.py"}
        mock_run.assert_called_once_with(
            ["git", "diff", "--cached", "--name-only"],
            cwd=Path("/fake/repo"),
            capture_output=True,
            text=True,
            check=True,
        )

    @patch.object(_module.subprocess, "run")
    def test_empty_staging_area(self, mock_run):

        """No staged files → empty set."""
        mock_run.return_value = MagicMock(stdout="")
        result = _module.get_staged_files()
        assert result == set()

    @patch.object(_module.subprocess, "run")
    def test_ignores_blank_lines(self, mock_run):
        """Blank lines in output are filtered out."""
        mock_run.return_value = MagicMock(stdout="file1.py\n\n\nfile2.py\n")
        result = _module.get_staged_files()
        assert result == {"file1.py", "file2.py"}

    @patch.object(_module.subprocess, "run")
    def test_returns_empty_on_git_failure(self, mock_run):
        """git fails → empty set (graceful degradation)."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        result = _module.get_staged_files()
        assert result == set()


class TestResetRepo:
    """Contract: reset_repo(path) resets repository to its remote tracking branch."""

    def test_reset_repo_clears_unstaged_changes(self, tmp_path):
        # Setup: Create a remote repo
        remote_path = tmp_path / "remote"
        remote_path.mkdir()
        subprocess.run(["git", "init", "-b", "main"], cwd=remote_path, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=remote_path, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=remote_path, capture_output=True)

        file_path = remote_path / "test.txt"
        file_path.write_text("original content")
        subprocess.run(["git", "add", "test.txt"], cwd=remote_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=remote_path, capture_output=True)

        # Setup: Create local repo and clone from remote
        local_path = tmp_path / "local"
        subprocess.run(["git", "clone", str(remote_path), str(local_path)], capture_output=True)

        # Modify file in local repo
        local_file = local_path / "test.txt"
        local_file.write_text("modified content")

        # Execute
        success = _module.reset_repo(local_path)

        # Verify
        assert success is True
        assert local_file.read_text() == "original content"

    @patch.object(_module.subprocess, "run")
    def test_reset_repo_fails_on_rev_parse_error(self, mock_run):
        """git rev-parse fails → return False."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git rev-parse")
        result = _module.reset_repo(Path("/fake/path"))
        assert result is False

    @patch.object(_module.subprocess, "run")
    def test_reset_repo_fails_on_git_not_found(self, mock_run):
        """git binary not found → return False."""
        mock_run.side_effect = FileNotFoundError()
        result = _module.reset_repo(Path("/fake/path"))
        assert result is False

    @patch.object(_module.subprocess, "run")
    def test_reset_repo_fails_on_reset_command(self, mock_run):
        """git reset returns non-zero → return False."""
        # First call (rev-parse) succeeds, second (reset) fails
        mock_run.side_effect = [
            MagicMock(stdout="main\n"),
            MagicMock(returncode=1)
        ]
        result = _module.reset_repo(Path("/fake/path"))
        assert result is False


class TestIsRepoDirty:
    """Contract: is_repo_dirty(path) returns True if repo has changes, False otherwise."""

    @patch.object(_module.subprocess, "run")
    def test_returns_false_for_clean_repo(self, mock_run):
        """git status --porcelain is empty → return False."""
        mock_run.return_value = MagicMock(stdout="")
        result = _module.is_repo_dirty(Path("/tmp/test/repo"))
        assert result is False
        mock_run.assert_called_once_with(
            ["git", "status", "--porcelain"],
            cwd=Path("/tmp/test/repo"),
            capture_output=True,
            text=True,
            check=True,
        )

    @patch.object(_module.subprocess, "run")
    def test_returns_true_for_dirty_repo(self, mock_run):
        """git status --porcelain is non-empty → return True."""
        mock_run.return_value = MagicMock(stdout=" M file1.txt\n?? file2.txt\n")
        result = _module.is_repo_dirty(Path("/tmp/test/repo"))
        assert result is True

    @patch.object(_module.subprocess, "run")
    def test_returns_false_on_git_failure(self, mock_run):
        """git fails → return False (graceful degradation)."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        result = _module.is_repo_dirty(Path("/tmp/test/repo"))
        assert result is False


class TestIsTracked:
    """Contract: is_tracked(path) returns True if path is in the git index, False otherwise."""

    @patch.object(_module.subprocess, "run")
    def test_returns_true_when_tracked(self, mock_run):
        """git ls-files --error-unmatch succeeds → return True."""
        mock_run.return_value = MagicMock(returncode=0)
        result = _module.is_tracked(Path("/fake/repo/file.txt"))
        assert result is True
        mock_run.assert_called_once_with(
            ["git", "ls-files", "--error-unmatch", "/fake/repo/file.txt"],
            cwd=None,
            capture_output=True,
            text=True,
        )

    @patch.object(_module.subprocess, "run")
    def test_returns_false_when_untracked(self, mock_run):
        """git ls-files --error-unmatch returns non-zero → return False."""
        mock_run.return_value = MagicMock(returncode=1)
        result = _module.is_tracked(Path("/fake/repo/untracked.txt"))
        assert result is False

    @patch.object(_module.subprocess, "run")
    def test_returns_false_on_git_failure(self, mock_run):
        """git binary not found or other system error → return False."""
        mock_run.side_effect = FileNotFoundError()
        result = _module.is_tracked(Path("/fake/repo/file.txt"))
        assert result is False


class TestInitAndAdd:
    """Contract: init_repo initializes a repo, add_files stages files."""

    @patch.object(_module.subprocess, "run")
    def test_init_repo_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        assert _module.init_repo(Path("/fake/repo")) is True
        mock_run.assert_called_once_with(
            ["git", "init"],
            cwd=Path("/fake/repo"),
            capture_output=True,
            check=True,
        )

    @patch.object(_module.subprocess, "run")
    def test_add_files_single_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        assert _module.add_files(Path("/fake/repo"), "file.txt") is True
        mock_run.assert_called_once_with(
            ["git", "add", "file.txt"],
            cwd=Path("/fake/repo"),
            capture_output=True,
            check=True,
        )

    @patch.object(_module.subprocess, "run")
    def test_add_files_multiple_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        assert _module.add_files(Path("/fake/repo"), ["f1.txt", "f2.txt"]) is True
        mock_run.assert_called_once_with(
            ["git", "add", "f1.txt", "f2.txt"],
            cwd=Path("/fake/repo"),
            capture_output=True,
            check=True,
        )

    @patch.object(_module.subprocess, "run")
    def test_init_repo_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        assert _module.init_repo(Path("/fake/repo")) is False

    @patch.object(_module.subprocess, "run")
    def test_add_files_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        assert _module.add_files(Path("/fake/repo"), "file.txt") is False


class TestCommitFiles:
    """Contract: commit_files(path, message) commits staged files, returns bool success."""

    @patch.object(_module.subprocess, "run")
    def test_commit_success(self, mock_run):
        """git commit succeeds → return True."""
        mock_run.return_value = MagicMock(returncode=0)
        assert _module.commit_files(Path("/fake/repo"), "feat: test commit") is True
        mock_run.assert_called_once_with(
            ["git", "commit", "-m", "feat: test commit"],
            cwd=Path("/fake/repo"),
            capture_output=True,
            check=True,
        )

    @patch.object(_module.subprocess, "run")
    def test_commit_failure(self, mock_run):
        """git commit fails → return False."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        assert _module.commit_files(Path("/fake/repo"), "feat: test commit") is False

    @patch.object(_module.subprocess, "run")
    def test_commit_git_not_found(self, mock_run):
        """git binary not found → return False."""
        mock_run.side_effect = FileNotFoundError()
        assert _module.commit_files(Path("/fake/repo"), "feat: test commit") is False
