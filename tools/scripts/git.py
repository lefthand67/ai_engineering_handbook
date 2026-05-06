"""
Shared git utilities for validation scripts and tooling.

Scope: repo root detection, staged file queries, historical file discovery,
and common git operations (clone, pull, status). Pure git operations only —
does NOT contain validation logic or domain-specific business rules.

Public interface:
    detect_repo_root() — resolve repository root via git, with __file__ fallback
    get_staged_files() — list of files in the git staging area
    get_historical_paths(directory) — all paths that ever matched a glob in git history
    clone_repo(url, path, branch=None) — clone a repository (returns bool success)
    pull_repo(path) — pull latest changes with --rebase (returns success, message tuple)
    get_repo_status(path) — get branch, remote URL, and last commit date

Dependencies:
    - git CLI (subprocess calls)
    - pathlib (stdlib)
    - subprocess (stdlib)

Key design decisions:
    - detect_repo_root() uses git rev-parse with Path(__file__) fallback,
      matching project conventions (see QWEN.md/AGENTS.md Python section)
    - get_staged_files() returns set[str] of repo-relative paths
    - get_historical_paths() uses git log --diff-filter=A to find all files
      ever added, including deleted ones (needed because evidence sources
      are deleted after extraction — filesystem alone misses retired IDs)
    - clone_repo() and pull_repo() return bool/tuple (no printing — caller handles UX)
    - get_repo_status() returns tuple of (branch, remote_url, last_commit_date)
      or (None, None, None) on failure — no exceptions raised
    - On vadocs extraction: becomes vadocs.git or vadocs.vcs module

Usage examples:
    >>> from tools.scripts.git import detect_repo_root, clone_repo, pull_repo
    >>> root = detect_repo_root()
    >>> success = clone_repo("https://github.com/example/repo", root / "dest")
    >>> ok, msg = pull_repo(root / "existing_repo")
"""

import subprocess
from pathlib import Path


def detect_repo_root() -> Path:
    """Detect repository root via git, with __file__ fallback."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip()).resolve()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return Path(__file__).resolve().parent.parent.parent


def get_staged_files() -> set[str]:
    """Get repo-relative paths of staged files from git."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
        )
        return {line.strip() for line in result.stdout.splitlines() if line.strip()}
    except subprocess.CalledProcessError:
        return set()


def get_historical_paths(directory: str) -> set[str]:
    """Get all repo-relative paths that ever existed in a directory.

    Scans full git history via `git log --name-only`, filters to the
    given directory, and deduplicates. Includes files that were later
    deleted (e.g., evidence sources removed after extraction).

    Args:
        directory: Repo-relative directory path (e.g., "architecture/evidence/sources/").
                   Trailing slash is normalized.

    Returns:
        Set of repo-relative file paths (e.g., {"architecture/evidence/sources/S-26001_foo.md"}).
        Empty set if git is unavailable or directory never existed.
    """
    directory = directory.rstrip("/") + "/"
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "--name-only", "--", directory],
            capture_output=True,
            text=True,
            check=True,
        )
        return {
            line.strip()
            for line in result.stdout.splitlines()
            if line.strip().startswith(directory)
        }
    except (subprocess.CalledProcessError, FileNotFoundError):
        return set()


def clone_repo(url: str, path: Path, branch: str | None = None) -> bool:
    """Clone a git repository.

    Args:
        url: Repository URL to clone.
        path: Destination path for the cloned repository.
        branch: Optional branch to checkout (uses default branch if None).

    Returns:
        True if clone succeeded, False otherwise.
    """
    cmd = ["git", "clone"]
    if branch:
        cmd.extend(["--branch", branch])
    cmd.extend([url, str(path)])

    try:
        result = subprocess.run(cmd)
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def pull_repo(path: Path) -> tuple[bool, str]:
    """Pull latest changes for a git repository.

    Args:
        path: Path to the git repository.

    Returns:
        Tuple of (success: bool, message: str).
        message contains stdout on success, stderr on failure.
    """
    try:
        result = subprocess.run(
            ["git", "pull", "--rebase"],
            cwd=path,
        )
        if result.returncode == 0:
            return True, "Updated"
        return False, "Git pull failed"
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        return False, str(e)


def get_repo_status(path: Path) -> tuple[str | None, str | None, str | None]:
    """Get repository status: branch, remote URL, and last commit date.

    Args:
        path: Path to the git repository.

    Returns:
        Tuple of (branch, remote_url, last_commit_date).
        Returns (None, None, None) if path is not a git repository.
    """
    try:
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True,
        )
        remote_result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True,
        )
        date_result = subprocess.run(
            ["git", "log", "-1", "--format=%cd", "--date=short"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True,
        )
        return (
            branch_result.stdout.strip(),
            remote_result.stdout.strip(),
            date_result.stdout.strip()[:10],  # Extract YYYY-MM-DD
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None, None, None


def is_repo_dirty(path: Path) -> bool:
    """Check if a git repository has unstaged or uncommitted changes.

    Args:
        path: Path to the git repository.

    Returns:
        True if the repository is dirty, False otherwise.
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True,
        )
        return bool(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def reset_repo(path: Path) -> bool:
    """Forcefully reset a repository to its remote tracking branch.

    Args:
        path: Path to the git repository.

    Returns:
        True if reset succeeded, False otherwise.
    """
    try:
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True,
        )
        branch = branch_result.stdout.strip()
        result = subprocess.run(
            ["git", "reset", "--hard", f"origin/{branch}"],
            cwd=path,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except (subprocess.CalledProcessError, subprocess.SubprocessError, FileNotFoundError):
        return False
