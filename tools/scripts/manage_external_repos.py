"""
Manage external product source code repositories.

Scope: clone new external repos, pull updates for existing ones, and synchronize
state with a central manifest.

Designed for three use cases:
1) One-time setup: cloning a new external product for research
2) Pre-session refresh: ensuring all researched products have latest code
3) State-based synchronization: reconciling actual state (disk + registry)
   with a desired state defined in a manifest.

Supports multiple directories from the external repo registry (ADR-26046).

Public interface (CLI commands):
    setup <url> [--dir <dir_name>]         — Clone repo to specified directory
    update [--parallel] [repo ...]         — Refresh existing repos (pull latest code)
    list                                    — Display all repos with branch/date/remote
    register <path> <description>           — Add new directory to registry
    unregister <path>                       — Remove directory from registry
    relocate <old> <new>                    — Rename directory and update consumers
    sync [--update] [--dry-run]             — Reconcile state with manifest
    sync-consumers                          — Align .gitignore and myst.yml with manifest

State-Based Sync Contract:
    SSoT: .vadocs/inventory/manage_external_repos.json

    Sync vs Update:
    - 'update' is a "refresh" command: it only pulls latest code for repos already on disk.
    - 'sync' is a "reconciliation" command: it ensures the filesystem and registry
      exactly match the manifest (clones missing, prompts to prune orphans).
    - 'sync --dry-run' allows verifying the reconciliation plan without modifying the disk.
    - 'sync --update' is a "complete alignment": it reconciles the structure AND
      updates all repositories to the latest version.
    - 'sync-consumers' ensures that the project's consumer files (.gitignore, myst.yml)
      are synchronized with the current registered directories in the manifest.

    Ignore Mechanisms:
    - Persistent Ignores (Git/MyST): These external tools cannot read our JSON manifest.
      Run 'sync-consumers' to write the manifest's registered directories into
      .gitignore and myst.yml.
    - Runtime Ignores (Validation Scripts): Our internal tools (e.g., check_broken_links.py)
      import 'tools.scripts.paths.py', which reads the manifest at import time and
      adds registered directories to the exclusion set (VALIDATION_EXCLUDE_DIRS) automatically.

    The 'sync' reconciliation loop:
    1. Discovery: Maps Desired (manifest), Registered (config), and Actual (disk) states.
    2. Delta Calculation: Identifies Orphans (disk not in manifest), Ghost Dirs
       (registered not in manifest), and Missing repos (manifest not on disk).
    3. Resolution: Interactively asks the user to Resolve Orphans (Remove/Move/Ignore)
       and Ghost Dirs (Unregister/Keep).
    4. Execution: Performs relocation, deletion, registration, and cloning.
    5. Update: If --update is passed, runs 'git pull --rebase' on all manifest repos.

Configuration:
    EXTERNAL_REPO_DIRS (set[Path]) — All directories from the registry.
        Loaded from .vadocs/validation/external-repos.conf.json at import time.
        Falls back to a default path when the registry has no entries.

Dependencies:
    - git CLI
    - tools.scripts.git (clone_repo, pull_repo, get_repo_status, detect_repo_root)
    - tools.scripts.paths (get_external_repo_paths)
    - concurrent.futures (stdlib) for parallel updates

Key design decisions:
    - Reuses git.py functions — does NOT duplicate git operations
    - All directories excluded from git, validation, and docs via registry
    - Setup requires --dir when multiple directories are registered
    - Pull uses --rebase to maintain linear history
    - Structure follows project conventions: data classes → config → main → helpers
    - Exit codes: 0 = success, 1 = failure (standard CLI contract)

Usage examples:
    # Before starting work — update all repos across all directories
    uv run tools/scripts/manage_external_repos.py update

    # Update specific repos in parallel
    uv run tools/scripts/manage_external_repos.py update --parallel langgraph autogen

    # Add a new repository to the default directory
    uv run tools/scripts/manage_external_repos.py setup https://github.com/langchain-ai/langgraph

    # Add a new repository to a specific directory
    uv run tools/scripts/manage_external_repos.py setup https://github.com/example/agent --dir research/my_repos

    # Register a new directory
    uv run tools/scripts/manage_external_repos.py register research/new_agents "New agent research"

    # Synchronize state with manifest
    uv run tools/scripts/manage_external_repos.py sync --update

    # List all repos and their status
    uv run tools/scripts/manage_external_repos.py list
"""

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger("manage_external_repos")

from tools.scripts.git import clone_repo, detect_repo_root, get_repo_status, pull_repo, reset_repo
from tools.scripts.paths import get_external_repo_paths

# Configuration constants
# EXTERNAL_REPO_DIRS is resolved from the unified manifest at import time.
# Falls back to a default path when the manifest has no entries.
_repo_root = detect_repo_root()
_external_paths = get_external_repo_paths(_repo_root)
_FALLBACK_DIRS: Set[Path] = {Path("research/ai_coding_agents")}

if _external_paths:
    EXTERNAL_REPO_DIRS: Set[Path] = {Path(p) for p in _external_paths}
else:
    EXTERNAL_REPO_DIRS: Set[Path] = _FALLBACK_DIRS

# Unified SSoT manifest path
_MANIFEST_CONFIG = ".vadocs/inventory/manage_external_repos.json"


@dataclass
class AgentRepo:
    """Represents an external product source code repository."""

    name: str
    path: Path
    url: str
    parent_dir: Path  # Which registered directory contains this repo
    branch: Optional[str] = None


def main() -> int:
    """Entry point for the CLI.

    Contract: Parses CLI arguments and dispatches to appropriate command function.
    Returns exit code (0 = success, 1 = failure).

    Returns:
        Exit code for sys.exit().
    """
    parser = _create_parser()
    args = parser.parse_args()

    # Configure logging based on verbosity flag
    log_level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format="%(levelname)s    %(name)s:%(filename)s:%(lineno)d %(message)s",
        stream=sys.stdout,
    )
    logger.setLevel(log_level)

    if args.command == "setup":
        return setup_command(args.url, target_dir_name=args.dir)
    elif args.command == "update":
        repo_names = args.repos if args.repos else []
        return update_command(repo_names=repo_names, parallel=args.parallel, reset=args.reset)
    elif args.command == "list":
        return list_command(dirs_only=getattr(args, 'dirs', False))
    elif args.command == "register":
        return register_command(args.path, args.description)
    elif args.command == "unregister":
        return unregister_command(args.path)
    elif args.command == "relocate":
        return relocate_command(args.old_path, args.new_path)
    elif args.command == "sync":
        return sync_command(update=args.update, dry_run=args.dry_run)
    elif args.command == "sync-consumers":
        return sync_consumers_command(dry_run=args.dry_run)
    else:
        parser.print_help()
        return 1


def _create_parser() -> argparse.ArgumentParser:
    """Create argument parser with comprehensive help.

    Returns:
        Configured ArgumentParser with subcommands and examples.
    """
    epilog = """
Configuration:
  External product repos are cloned to directories registered in
  .vadocs/validation/external-repos.conf.json (ADR-26046).
  All registered directories are excluded from git tracking, validation
  scripts, and documentation builds.

  Consumer files (.gitignore, myst.yml) are defined per-entry in the registry.
  The relocate command updates all consumers atomically.

  To see registered directories: %(prog)s list --dirs

Examples:
  # Pre-session refresh: update all repos
  %(prog)s update

  # Run with verbose output
  %(prog)s -v update

  # Update specific repos in parallel
  %(prog)s update --parallel langgraph autogen

  # Clone a new external repository
  %(prog)s setup https://github.com/langchain-ai/langgraph

  # Clone to specific registered directory (required when multiple dirs exist)
  %(prog)s setup https://github.com/example/agent --dir research/my_repos

  # Register a new directory
  %(prog)s register research/new_agents "New agent research"

  # Remove a directory from the registry
  %(prog)s unregister research/old_agents

  # Rename a directory — updates registry AND all consumer files atomically
  %(prog)s relocate old/path/external_repos new/path/external_repos

  # Synchronize state with manifest
  %(prog)s sync --update

  # Synchronize state with manifest (dry-run)
  %(prog)s sync --dry-run

  # Synchronize consumer files (.gitignore, myst.yml)
  %(prog)s sync-consumers

  # List all repos with status
  %(prog)s list

  # Show registered directories
  %(prog)s list --dirs
"""

    parser = argparse.ArgumentParser(
        description="Manage external product source code repositories",
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Increase output verbosity (INFO level)",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # setup command
    setup_parser = subparsers.add_parser(
        "setup",
        help="Clone a new external repository",
        description="Clone a git repository into a registered directory. "
        "When multiple directories are registered, --dir is required.",
    )
    setup_parser.add_argument(
        "url",
        help="Repository URL to clone (e.g., https://github.com/org/repo)",
    )
    setup_parser.add_argument(
        "--dir",
        help="Target registered directory (required when multiple directories exist)",
        default=None,
    )

    # update command
    update_parser = subparsers.add_parser(
        "update",
        help="Pull updates for external repositories",
        description="Run 'git pull --rebase' on all (or specified) repositories. "
        "Use --parallel flag to update multiple repositories simultaneously. "
        "NOTE: With --parallel, SSH passphrase prompts from multiple repos "
        "will interleave on the terminal. Use sequential mode (default) if your "
        "repos require passphrase authentication.",
    )
    update_parser.add_argument(
        "repos",
        nargs="*",
        help="Specific repository names to update (empty = update all)",
    )
    update_parser.add_argument(
        "--parallel",
        action="store_true",
        help="Update repositories concurrently. WARNING: SSH passphrase prompts "
        "from multiple repos will interleave on terminal — use sequential mode "
        "if keys require passphrase. Recommended for 3+ repos with SSH agent.",
    )
    update_parser.add_argument(
        "--reset",
        action="store_true",
        help="Forcibly clear unstaged changes in external repositories if "
        "git pull --rebase fails due to local modifications.",
    )

    # list command
    list_parser = subparsers.add_parser(
        "list",
        help="List all external repositories with branch, date, and remote URL",
        description="Display a table of all cloned repositories with their "
        "current branch, last commit date, and remote URL.",
    )
    list_parser.add_argument(
        "--dirs",
        action="store_true",
        help="Show registered directories instead of repositories",
    )

    # register command
    register_parser = subparsers.add_parser(
        "register",
        help="Add a new directory to the external repos registry",
        description="Register a new directory for external product repos. "
        "Updates .vadocs/validation/external-repos.conf.json.",
    )
    register_parser.add_argument(
        "path",
        help="Relative path for the new directory (e.g., research/new_agents)",
    )
    register_parser.add_argument(
        "description",
        help="Description of what this directory contains",
    )

    # unregister command
    unregister_parser = subparsers.add_parser(
        "unregister",
        help="Remove a directory from the external repos registry",
        description="Remove a registered directory from the registry. "
        "Does NOT delete the directory on disk — only updates the config.",
    )
    unregister_parser.add_argument(
        "path",
        help="Relative path of the directory to remove from registry",
    )

    # relocate command
    relocate_parser = subparsers.add_parser(
        "relocate",
        help="Update registered path across all consumer files",
        description="Rename a registered directory path in the registry AND all consumer "
        "files (.gitignore, myst.yml). Moves the directory on disk if it still exists, "
        "or updates consumers only if it was already moved manually (e.g., git mv).",
    )
    relocate_parser.add_argument(
        "old_path",
        help="Current registered path (e.g., old_dir/external_repos)",
    )
    relocate_parser.add_argument(
        "new_path",
        help="New path to relocate to (e.g., new_dir/external_repos)",
    )

    # sync command
    sync_parser = subparsers.add_parser(
        "sync",
        help="Synchronize repositories with the manifest",
        description="Reconcile actual state (disk + registry) with desired state "
        "defined in .vadocs/inventory/manage_external_repos.json.",
    )
    sync_parser.add_argument(
        "--update",
        action="store_true",
        help="Pull latest changes for all manifest repositories",
    )
    sync_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without applying modifications",
    )

    # sync-consumers command
    consumers_parser = subparsers.add_parser(
        "sync-consumers",
        help="Sync consumer files (.gitignore, myst.yml)",
        description="Rebuild consumer file exclusions to match the current registry.",
    )
    consumers_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes to consumer files without applying them",
    )

    return parser


class SyncManager:
    """Reconciles actual external repo state with a desired manifest.

    Contract:
    1. Discovery: Maps Manifest, Registry, and Disk.
    2. Delta: Calculates Missing, Orphans, and Ghost Dirs.
    3. Resolution: Interactively resolves deltas.
    4. Execution: Applies changes (Clone, Register, Delete, Relocate).
    """

    def __init__(self, repo_root: Path, manifest_path: Path):
        self.repo_root = repo_root
        self.manifest_path = manifest_path

    def load_manifest(self) -> dict:
        """Load the SSoT manifest file."""
        if not self.manifest_path.exists():
            print(f"❌ Error: Manifest not found: {self.manifest_path}")
            return {}
        with open(self.manifest_path) as f:
            return json.load(f)

    def calculate_delta(self, manifest: dict):
        """Calculate differences between manifest, registry, and disk."""
        # Desired state from manifest
        desired_dirs = manifest.get("directories", {})
        desired_repos = {}
        for dir_path, data in desired_dirs.items():
            for repo_name, repo_data in data.get("repos", {}).items():
                desired_repos[repo_name] = {
                    "url": repo_data["url"],
                    "path": Path(dir_path) / repo_name
                }

        # Registered state from manifest
        registered_dirs = set(desired_dirs.keys())

        # Actual state from disk
        actual_repos = {}
        actual_dirs = set()

        # Scan all registered directories for repos
        for dir_path in EXTERNAL_REPO_DIRS:
            full_dir = self.repo_root / dir_path
            if full_dir.exists():
                actual_dirs.add(str(dir_path))
                repos = discover_repos(full_dir, parent_dir=dir_path)
                for r in repos:
                    actual_repos[r.name] = r

        # Discovery of Orphans: Scan for any .git directories not in manifest
        for path in self.repo_root.rglob(".git"):
            if path.is_dir():
                # Skip the project's own .git folder
                if path == self.repo_root / ".git":
                    continue
                repo_dir = path.parent
                try:
                    rel_parent = repo_dir.parent.relative_to(self.repo_root)
                    if str(rel_parent) not in desired_dirs:
                        actual_dirs.add(str(rel_parent))
                except ValueError:
                    continue

        # Deltas
        missing_repos = []
        for name, data in desired_repos.items():
            if name not in actual_repos:
                missing_repos.append((name, data["url"], data["path"]))

        orphans = []
        for dir_path in actual_dirs:
            if dir_path not in desired_dirs:
                orphans.append(dir_path)

        ghost_dirs = []
        for reg_dir in registered_dirs:
            if reg_dir not in desired_dirs:
                ghost_dirs.append(reg_dir)

        return {
            "missing": missing_repos,
            "orphans": orphans,
            "ghosts": ghost_dirs,
            "desired_dirs": desired_dirs
        }

    def interactive_resolve(self, delta: dict):
        """Handle user prompts for Orphans and Ghost Dirs."""
        resolutions = {"orphans": [], "ghosts": []}

        print("\n🔍 State Reconciliation")
        print("-" * 30)

        # Resolve Orphans
        for orphan in delta["orphans"]:
            print(f"\n📂 Orphan directory found: {orphan}")
            choice = input("Action: [R]emove, [I]gnore, [C]ancel? ").strip().lower()
            if choice in ("r", "remove"):
                resolutions["orphans"].append(("remove", orphan))
            elif choice in ("c", "cancel"):
                return None
            else:
                resolutions["orphans"].append(("ignore", orphan))

        # Resolve Ghosts
        for ghost in delta["ghosts"]:
            print(f"\n👻 Ghost registry entry found: {ghost}")
            choice = input("Action: [U]nregister, [K]eep, [C]ancel? ").strip().lower()
            if choice in ("u", "unregister"):
                resolutions["ghosts"].append(("unregister", ghost))
            elif choice in ("c", "cancel"):
                return None
            else:
                resolutions["ghosts"].append(("keep", ghost))

        return resolutions

    def apply_reconciliation(self, delta: dict, resolutions: dict, dry_run: bool = False):
        """Execute the decided changes."""
        if dry_run:
            logger.info("🧪 Dry-run mode: No changes will be applied to disk or registry")
            logger.info("-" * 60)

        # 1. Handle Orphans
        for action, path in resolutions["orphans"]:
            if action == "remove":
                full_path = self.repo_root / path
                logger.info(f"🗑 {'[Dry-run] Would remove' if dry_run else 'Removing'} orphan: {path}")
                if not dry_run:
                    import shutil
                    shutil.rmtree(full_path, ignore_errors=True)

        # 2. Handle Ghosts
        for action, path in resolutions["ghosts"]:
            if action == "unregister":
                logger.info(f"📝 {'[Dry-run] Would unregister' if dry_run else 'Unregistering'} ghost: {path}")
                if not dry_run:
                    unregister_command(path)

        # 3. Register Missing Directories
        for dir_path in delta["desired_dirs"]:
            desc = delta["desired_dirs"][dir_path]["description"]
            logger.info(f"📁 {'[Dry-run] Would register' if dry_run else 'Registering'} directory: {dir_path}")
            if not dry_run:
                register_command(dir_path, desc)

        # 4. Clone Missing Repos
        for name, url, rel_path in delta["missing"]:
            parent_dir = str(rel_path.parent)
            logger.info(f"📦 {'[Dry-run] Would clone' if dry_run else 'Cloning'} missing repo: {name}")
            if not dry_run:
                setup_command(url, target_dir_name=parent_dir)

    def perform_updates(self, manifest: dict):
        """Pull latest changes for all manifest repos."""
        print("\n🔄 Updating all manifest repositories...")
        for dir_path, data in manifest.get("directories", {}).items():
            for repo_name, repo_data in data.get("repos", {}).items():
                full_path = self.repo_root / dir_path / repo_name
                if full_path.exists():
                    print(f"   Updating {repo_name}...")
                    pull_repo(full_path)


def setup_command(url: str, target_dir_name: str | None = None) -> int:
    """Clone a repository to a registered directory.

    Contract: Clones repo to specified directory.
    When multiple directories registered, --dir is required.
    Returns 0 if repo already exists or clones successfully, 1 if clone fails.

    Args:
        url: Repository URL to clone.
        target_dir_name: Optional registered directory path (required if multiple dirs).

    Returns:
        0 on success or already present, 1 on failure.
    """
    repo_root = detect_repo_root()
    target_dir = _resolve_target_dir(repo_root, target_dir_name)
    if target_dir is None:
        return 1

    # Create directory if it doesn't exist
    target_dir.mkdir(parents=True, exist_ok=True)

    # Extract repo name from URL
    repo_name = url.rstrip("/").split("/")[-1].replace(".git", "")
    repo_path = target_dir / repo_name

    if repo_path.exists():
        print(f"ℹ Repository already exists at {repo_path}")
        return 0

    # Clone the repository
    print(f"📦 Cloning {url}")
    print(f"   → {repo_path}")
    success = clone_repo(url, repo_path)
    if not success:
        print(f"❌ Error: Failed to clone repository: {url}")
        print(f"   Check the URL and your network connection")
        return 1

    print(f"✅ Repository '{repo_name}' cloned successfully")
    print(f"   Directory: {target_dir.relative_to(repo_root)}")
    print(f"   Excluded from: .gitignore, validation scripts, myst build")
    return 0


def _pull_with_reset(repo_path: Path, reset: bool) -> tuple[bool, str]:
    """Try to pull updates, and optionally reset if unstaged changes block it.

    Contract:
    - Input: repo_path (absolute path), reset (boolean flag)
    - Operation:
        1. execute pull_repo()
        2. If success: return (True, message)
        3. If failure AND reset=True AND error matches local modification patterns:
            a. log warning about forced reset
            b. execute reset_repo()
            c. if reset succeeds, retry pull_repo() and return its result
            d. if reset fails, return (False, "Reset failed...")
        4. Otherwise: return (False, original_error_message)
    - Side Effects: May perform a hard reset of the git repository at repo_path.
    """
    success, message = pull_repo(repo_path)
    if success:
        return success, message

    # Check for common git errors that indicate unstaged local changes
    if reset and ("local changes would be overwritten" in message.lower() or "unstaged changes" in message.lower()):
        logger.warning(f"Local changes detected in {repo_path.name}. Forcibly resetting to match remote...")
        if reset_repo(repo_path):
            return pull_repo(repo_path)
        else:
            return False, f"Reset failed: Could not clear local changes in {repo_path.name}"

    return success, message


def update_command(repo_names: List[str] = None, parallel: bool = False, reset: bool = False) -> int:
    """Pull updates for repositories across all registered directories.

    Contract:
    - Input: repo_names (optional filter), parallel (concurrency flag), reset (force-reset flag)
    - Operation:
        1. Discover all repos in EXTERNAL_REPO_DIRS.
        2. Filter by repo_names if provided.
        3. For each repo:
            - In sequential mode: call _pull_with_reset()
            - In parallel mode: submit _pull_with_reset() to ThreadPoolExecutor
        4. Track overall success status.
    - Output: 0 if all target repos updated successfully, 1 if any failed.
    - Side Effects: Updates local source code of external repositories.
    """
    repo_root = detect_repo_root()

    logger.info("Discovering repositories in registered directories...")
    for dir_path in sorted(EXTERNAL_REPO_DIRS, key=str):
        full_path = repo_root / dir_path
        status = "✓" if full_path.exists() else "✗"
        logger.info(f"   {status} {dir_path}")

    # Discover repositories across all directories
    all_repos = []
    for dir_path in EXTERNAL_REPO_DIRS:
        full_path = repo_root / dir_path
        if full_path.exists():
            repos = discover_repos(full_path, parent_dir=dir_path)
            all_repos.extend(repos)
            if repos:
                logger.info(f"   Found {len(repos)} repo(s) in {dir_path}")

    if not all_repos:
        logger.info("No git repositories found in registered directories")
        dirs_str = ", ".join(str(d) for d in EXTERNAL_REPO_DIRS)
        logger.info(f"   Registered directories: {dirs_str}")
        return 0

    # Filter to specified repos if provided
    if repo_names:
        logger.info(f"Filtering to specified repositories: {', '.join(repo_names)}")
        all_repos = [r for r in all_repos if r.name in repo_names]
        if not all_repos:
            available = ", ".join(r.name for r in _discover_all(repo_root))
            logger.error(f"Specified repositories not found: {', '.join(repo_names)}")
            logger.info(f"   Available: {available}")
            return 1

    logger.info(f"Updating {len(all_repos)} repository/ies (Mode: {'Parallel' if parallel else 'Sequential'})")
    all_success = True

    if parallel:
        from concurrent.futures import ThreadPoolExecutor, as_completed

        logger.info("Using thread pool with max 5 workers")
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Use the reset-aware helper for parallel execution
            future_to_repo = {
                executor.submit(_pull_with_reset, repo.path, reset): repo for repo in all_repos
            }
            for future in as_completed(future_to_repo):
                repo = future_to_repo[future]
                branch, _, _ = get_repo_status(repo.path)
                branch_tag = f" ({branch})" if branch else ""
                try:
                    success, message = future.result()
                    if success:
                        if "Already up to date" in message:
                            logger.info(f"✓ {repo.name}{branch_tag}: Already up to date")
                        else:
                            logger.info(f"✅ {repo.name}{branch_tag}: Updated")
                    else:
                        logger.error(f"❌ Error in {repo.name}{branch_tag} ({repo.path}): {message.strip()}")
                        all_success = False
                except Exception as e:
                    logger.error(f"❌ Error in {repo.name}{branch_tag} ({repo.path}): Unexpected exception: {e}")
                    all_success = False
    else:
        for idx, repo in enumerate(all_repos, 1):
            branch, _, _ = get_repo_status(repo.path)
            branch_tag = f" ({branch})" if branch else ""
            logger.info(f"[{idx}/{len(all_repos)}] {repo.name}{branch_tag}...")
            
            # Use the reset-aware helper for sequential execution
            success, message = _pull_with_reset(repo.path, reset)
            
            if success:
                if "Already up to date" in message:
                    logger.info(f"    ✓ Already up to date")
                else:
                    logger.info(f"    ✅ Updated")
            else:
                logger.error(f"    ❌ FAILED: {message.strip()}")
                all_success = False

    if all_success:
        logger.info("All repositories updated successfully")
    else:
        logger.error("Some repositories failed to update (see errors above)")

    return 0 if all_success else 1


def list_command(dirs_only: bool = False) -> int:
    """List all repositories with status across all registered directories.

    Contract: Displays table of all repos with branch, date, remote.
    With dirs_only=True, shows registered directories from the registry config.
    Always returns 0 (informational command, never fails).

    Args:
        dirs_only: If True, show registered directories with descriptions
                   instead of individual git repositories.

    Returns:
        0 always.
    """
    repo_root = detect_repo_root()

    if dirs_only:
        return _list_dirs(repo_root)

    repos = _discover_all(repo_root)

    if not repos:
        print("ℹ No git repositories found in registered directories")
        dirs_str = ", ".join(str(d) for d in EXTERNAL_REPO_DIRS)
        print(f"   Registered directories: {dirs_str}")
        return 0

    print(f"📚 External Product Repositories ({len(repos)} total):\n")
    print(f"{'Name':<30} {'Directory':<30} {'Branch':<15} {'Last Commit':<12} {'Remote'}")
    print("-" * 120)

    for repo in repos:
        branch, remote, date = get_repo_status(repo.path)
        branch_str = branch if branch else "N/A"
        date_str = date if date else "N/A"
        remote_str = remote if remote else "N/A"
        dir_str = str(repo.parent_dir)
        print(f"{repo.name:<30} {dir_str:<30} {branch_str:<15} {date_str:<12} {remote_str}")

    return 0


def _list_dirs(repo_root: Path) -> int:
    """Show registered directories from the unified manifest.

    Args:
        repo_root: Repository root.

    Returns:
        0 always.
    """
    manifest_path = repo_root / _MANIFEST_CONFIG
    if not manifest_path.exists():
        print("ℹ No manifest config found")
        return 0

    with open(manifest_path) as f:
        data = json.load(f)

    dirs = data.get("directories", {})
    if not dirs:
        print("ℹ No directories registered")
        return 0

    print(f"📂 Registered Directories ({len(dirs)} total):\n")
    print(f"{'Path':<35} {'Type':<25} {'Description'}")
    print("-" * 100)

    for path, info in dirs.items():
        type_str = info.get("product_type", "N/A")
        desc_str = info.get("description", "")
        print(f"{path:<35} {type_str:<25} {desc_str}")

    return 0


def register_command(path: str, description: str, config_path: Path | None = None) -> int:
    """Add a new directory to the external repos manifest.

    Contract: Updates manage_external_repos.json with new entry.
    Returns 0 if success or already registered, 1 on failure.

    Args:
        path: Relative path for the new directory.
        description: Human-readable description.
        config_path: Optional explicit config path (for testing).

    Returns:
        0 on success or already present, 1 on failure.
    """
    repo_root = detect_repo_root()
    if config_path is None:
        config_path = repo_root / _MANIFEST_CONFIG

    # Load existing manifest
    if config_path.exists():
        with open(config_path) as f:
            data = json.load(f)
    else:
        data = {"settings": {}, "directories": {}}

    # Check for duplicate
    if path in data.get("directories", {}):
        print(f"ℹ Directory already registered: {path}")
        return 0

    # Determine consumers and managed_by from settings
    settings = data.get("settings", {})
    default_consumers = settings.get("default_consumers", [".gitignore"])
    default_managed_by = settings.get("managed_by", "tools/scripts/manage_external_repos.py")
    
    # Create directory entry
    data.setdefault("directories", {})[path] = {
        "description": description,
        "product_type": "external_product",
        "managed_by": default_managed_by,
        "consumers": list(default_consumers),
        "repos": {}
    }

    # Write back
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    reload_registry()

    # Update consumer files — add exclusion for the new path
    consumers = data["directories"][path]["consumers"]
    _add_path_to_consumers(repo_root, path, consumers)

    print(f"✅ Registered directory: {path}")
    print(f"   Description: {description}")
    try:
        config_rel = config_path.relative_to(repo_root)
        print(f"   Config: {config_rel}")
    except ValueError:
        print(f"   Config: {config_path}")
    return 0


def _add_path_to_consumers(repo_root: Path, path: str, consumers: List[str]) -> None:
    """Append a new exclusion path to all consumer files if not already present.

    When a directory is registered, it needs to be excluded from:
    - .gitignore: prevent git from tracking the cloned repos
    - myst.yml project.exclude: prevent docs build from processing nested repos

    Args:
        repo_root: Repository root.
        path: Relative path to add (e.g., "research/new_agents").
        consumers: List of relative consumer file paths from registry entry.
    """
    for consumer_rel in consumers:
        consumer_path = repo_root / consumer_rel
        if not consumer_path.exists():
            continue
        content = consumer_path.read_text()
        # Use trailing slash for gitignore (directory match), bare path for YAML
        exclusion = f"{path}/"
        if exclusion in content:
            # Already excluded — skip to avoid duplicates
            continue
        if consumer_rel.endswith(".gitignore"):
            # .gitignore: append as a bare directory path with trailing slash
            content = content.rstrip() + f"\n{exclusion}\n"
        else:
            # myst.yml: append as a quoted glob item under project.exclude
            yaml_entry = f'    - "{path}/*"'
            content = content.rstrip() + f"\n{yaml_entry}\n"
        consumer_path.write_text(content)


def _remove_path_from_consumers(repo_root: Path, path: str, consumers: List[str]) -> None:
    """Remove all occurrences of a path from consumer files.

    When a directory is unregistered, its exclusion entries should be cleaned up
    so future moves/renames don't leave stale entries in .gitignore or myst.yml.

    Args:
        repo_root: Repository root.
        path: Relative path to remove (e.g., "ai_agents/agents_source_code").
        consumers: List of relative consumer file paths from registry entry.
    """
    for consumer_rel in consumers:
        consumer_path = repo_root / consumer_rel
        if not consumer_path.exists():
            continue
        content = consumer_path.read_text()
        # Filter out any line containing the old path (handles both trailing-slash
        # gitignore entries and quoted YAML glob items)
        lines = content.split("\n")
        filtered = [l for l in lines if path not in l]
        updated = "\n".join(filtered)
        if updated != content:
            consumer_path.write_text(updated)


def unregister_command(path: str, config_path: Path | None = None) -> int:
    """Remove a directory from the external repos manifest.

    Contract: Removes an entry from manage_external_repos.json.
    Returns 1 if path not found. Does NOT delete the directory on disk.

    Args:
        path: Relative path of the directory to remove from registry.
        config_path: Optional explicit config path (for testing).

    Returns:
        0 on success, 1 on failure.
    """
    repo_root = detect_repo_root()
    if config_path is None:
        config_path = repo_root / _MANIFEST_CONFIG

    # Load existing manifest
    if not config_path.exists():
        print(f"❌ Error: Manifest not found: {config_path}")
        return 1
    with open(config_path) as f:
        data = json.load(f)

    dirs = data.get("directories", {})
    if path not in dirs:
        print(f"❌ Error: Directory not in registry: {path}")
        reg_dirs = ", ".join(dirs.keys())
        print(f"   Registered: {reg_dirs}")
        return 1

    # Capture consumers before removing the entry
    consumers = dirs[path].get("consumers", [])
    del dirs[path]

    # Write back
    with open(config_path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    reload_registry()

    # Update consumer files — remove exclusion for the old path
    if consumers:
        _remove_path_from_consumers(repo_root, path, consumers)

    print(f"✅ Unregistered directory: {path}")
    try:
        config_rel = config_path.relative_to(repo_root)
        print(f"   Config: {config_rel}")
    except ValueError:
        print(f"   Config: {config_path}")
    return 0


def sync_consumers_command(dry_run: bool = False, config_path: Path | None = None) -> int:
    """Rebuild consumer file exclusions to match the current registry.

    Contract: Reads all registered paths, then rebuilds .gitignore and
    myst.yml exclude sections. Removes stale entries, adds missing ones.
    Returns 0 on success, 1 on failure.

    Args:
        dry_run: If True, show changes without applying them.
        config_path: Optional explicit config path (for testing).

    Returns:
        0 on success, 1 on failure.
    """
    repo_root = detect_repo_root()
    if config_path is None:
        config_path = repo_root / _MANIFEST_CONFIG

    if not config_path.exists():
        print("❌ Error: Manifest not found")
        return 1

    with open(config_path) as f:
        data = json.load(f)

    dirs = data.get("directories", {})
    if not dirs:
        print("ℹ No directories in manifest")
        return 0

    # Collect all registered paths grouped by consumer
    # consumer_rel -> set of registered paths
    consumer_paths: dict[str, set[str]] = {}
    for path, info in dirs.items():
        for consumer_rel in info.get("consumers", []):
            consumer_paths.setdefault(consumer_rel, set()).add(path)

    action = "Would update" if dry_run else "Updating"
    for consumer_rel, registered_paths in sorted(consumer_paths.items()):
        consumer_path = repo_root / consumer_rel
        if not consumer_path.exists():
            print(f"⚠ Consumer file not found: {consumer_rel}")
            continue

        content = consumer_path.read_text()
        lines = content.split("\n")

        # Determine which lines to keep:
        # - Lines not containing any registered or unregistered path pattern
        # - Then re-add all registered paths
        registered_in_file = {p for p in registered_paths if p in content}
        # Find paths in file that are NOT in registry (stale)
        all_in_file = set()
        for line in lines:
            for p in registered_paths:
                if p in line:
                    all_in_file.add(p)
        stale = all_in_file - registered_paths

        if not stale and len(registered_in_file) == len(registered_paths):
            print(f"✓ {consumer_rel}: already in sync")
            continue

        print(f"{action} {consumer_rel}:")
        for p in sorted(stale):
            print(f"  - {p}")
        for p in sorted(registered_paths - registered_in_file):
            print(f"  + {p}")

        if dry_run:
            continue

        # Remove ALL lines containing any registered or stale path
        filtered = [l for l in lines if not any(p in l for p in registered_paths | stale)]
        # Re-add registered paths
        for p in sorted(registered_paths):
            if consumer_rel.endswith(".gitignore"):
                filtered.append(f"{p}/")
            else:
                filtered.append(f'    - "{p}/*"')

        consumer_path.write_text("\n".join(filtered))

    return 0


def _resolve_target_dir(repo_root: Path, target_dir_name: str | None) -> Path | None:
    """Resolve the target directory for setup command.

    Contract: Returns the target Path if resolvable, None otherwise.
    When multiple directories registered, target_dir_name is required.

    Args:
        repo_root: Repository root.
        target_dir_name: Optional registered directory name.

    Returns:
        Resolved Path or None (with error message printed).
    """
    # If target is provided, it MUST be in the registry
    if target_dir_name is not None:
        target = Path(target_dir_name)
        if target not in EXTERNAL_REPO_DIRS and str(target) not in EXTERNAL_REPO_DIRS:
            dirs_str = ", ".join(str(d) for d in sorted(EXTERNAL_REPO_DIRS, key=str))
            print(f"❌ Error: Directory not in registry: {target_dir_name}")
            print(f"   Registered: {dirs_str}")
            return None
        resolved_dir = repo_root / target
    else:
        # No target provided - use single registered dir if available
        if len(EXTERNAL_REPO_DIRS) == 1:
            resolved_dir = repo_root / next(iter(EXTERNAL_REPO_DIRS))
        else:
            dirs_str = "\n".join(f"  - {d}" for d in sorted(EXTERNAL_REPO_DIRS, key=str))
            print(f"❌ Error: Multiple directories registered. Specify --dir:")
            print(dirs_str)
            return None

    return resolved_dir


def relocate_command(old_path: str, new_path: str,
                     config_path: Path | None = None,
                     repo_root: Path | None = None) -> int:
    """Move an external repo directory and update the registry atomically.

    Contract: Moves directory on disk (if it exists) AND updates
    the registry entry. Safe relocation — validates before moving.

    Args:
        old_path: Current registered path (relative to repo root).
        new_path: New path to relocate to (relative to repo root).
        config_path: Optional explicit config path (for testing).
        repo_root: Optional repo root (for testing).

    Returns:
        0 on success, 1 on failure.
    """
    if repo_root is None:
        repo_root = detect_repo_root()
    if config_path is None:
        config_path = repo_root / _MANIFEST_CONFIG

    # Load manifest
    if not config_path.exists():
        print(f"❌ Error: Manifest not found: {config_path}")
        return 1
    with open(config_path) as f:
        data = json.load(f)

    dirs = data.get("directories", {})

    # Validate old_path exists in manifest
    if old_path not in dirs:
        print(f"❌ Error: Path not in manifest: {old_path}")
        return 1

    old_entry = dirs[old_path]

    # Validate new_path not already registered
    if new_path in dirs:
        print(f"❌ Error: New path already registered: {new_path}")
        return 1

    # Move directory on disk (if it exists)
    old_dir = repo_root / old_path
    new_dir = repo_root / new_path
    if old_dir.exists():
        new_dir.parent.mkdir(parents=True, exist_ok=True)
        old_dir.rename(new_dir)
        print(f"📁 Moved: {old_path} → {new_path}")
    else:
        print(f"ℹ Directory not on disk (already moved manually): {old_path}")

    # Update manifest entry
    # Pop old path and insert under new path
    dirs[new_path] = dirs.pop(old_path)

    with open(config_path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    print(f"✅ Manifest updated: {old_path} → {new_path}")

    # Update all consumer files listed in the manifest entry
    consumers = old_entry.get("consumers", [])
    for consumer_rel in consumers:
        consumer_path = repo_root / consumer_rel
        if consumer_path.exists():
            _update_path_in_file(consumer_path, old_path, new_path)
        else:
            print(f"   Skipped (not found): {consumer_rel}")

    print(f"✅ All consumers updated: {old_path} → {new_path}")
    return 0


def _update_path_in_file(file_path: Path, old_path: str, new_path: str) -> None:
    """Replace all occurrences of old_path with new_path in a text file.

    Args:
        file_path: Path to the file to update.
        old_path: Old path string to replace.
        new_path: New path string to replace with.
    """
    content = file_path.read_text()
    updated = content.replace(old_path, new_path)
    if updated != content:
        file_path.write_text(updated)
        print(f"   Updated: {file_path.name}")


def _discover_all(repo_root: Path) -> List[AgentRepo]:
    """Discover repositories across all registered directories.

    Args:
        repo_root: Repository root.

    Returns:
        List of AgentRepo from all directories.
    """
    all_repos = []
    for dir_path in EXTERNAL_REPO_DIRS:
        full_path = repo_root / dir_path
        if full_path.exists():
            all_repos.extend(discover_repos(full_path, parent_dir=dir_path))
    return all_repos


def reload_registry():
    """Refresh the EXTERNAL_REPO_DIRS global set from the unified manifest."""
    global EXTERNAL_REPO_DIRS
    repo_root = detect_repo_root()
    manifest_path = repo_root / _MANIFEST_CONFIG
    if manifest_path.exists():
        with open(manifest_path) as f:
            data = json.load(f)
            EXTERNAL_REPO_DIRS = {Path(d) for d in data.get("directories", {}).keys()}
    else:
        EXTERNAL_REPO_DIRS = set()


def discover_repos(scan_dir: Path, parent_dir: Path = None) -> List[AgentRepo]:
    """Discover all git repositories in a directory.

    Contract: Returns AgentRepo for each directory containing .git subdirectory.
    Sorted alphabetically by name for deterministic output.

    Args:
        scan_dir: Path to the directory to scan.
        parent_dir: Which registered directory contains this (for list display).

    Returns:
        List of AgentRepo objects (empty list if directory doesn't exist).
    """
    if not scan_dir.exists():
        return []

    repos = []
    for item in sorted(scan_dir.iterdir()):
        if item.is_dir() and (item / ".git").exists():
            repos.append(
                AgentRepo(
                    name=item.name,
                    path=item,
                    url="",  # Will be populated by get_repo_status if needed
                    parent_dir=parent_dir or scan_dir,
                )
            )
    return repos


def sync_command(update: bool = False, dry_run: bool = False) -> int:
    """Synchronize actual state with the manifest.

    Contract:
    1. Load manifest as SSoT.
    2. Calculate delta between manifest, registry, and disk.
    3. Interactively resolve orphans and ghosts.
    4. Apply reconciliation (Clone, Register, Delete, Unregister).
    5. Optionally update all repos.
    Returns 0 on success, 1 on failure or cancellation.

    Args:
        update: Whether to pull latest changes for all manifest repos.
        dry_run: Whether to show changes without applying them.

    Returns:
        0 on success, 1 on failure.
    """
    repo_root = detect_repo_root()
    manifest_path = repo_root / ".vadocs" / "inventory" / "manage_external_repos.json"

    manager = SyncManager(repo_root, manifest_path)
    manifest = manager.load_manifest()
    if not manifest:
        return 1

    delta = manager.calculate_delta(manifest)

    # If no deltas, we can skip interactive resolution
    if not delta["missing"] and not delta["orphans"] and not delta["ghosts"]:
        if dry_run:
            logger.info("🔍 Verification: System is already synchronized with manifest")
            logger.info(f"  - Checked {len(delta['desired_dirs'])} directories")
            # Calculate total desired repos for better verbosity
            total_repos = sum(len(d.get("repos", {})) for d in delta["desired_dirs"].values())
            logger.info(f"  - All {total_repos} repositories are present and accounted for")
        else:
            logger.info("✅ System is already synchronized with manifest")
    else:
        resolutions = manager.interactive_resolve(delta)
        if resolutions is None:
            logger.warning("⚠️ Sync cancelled by user")
            return 1

        manager.apply_reconciliation(delta, resolutions, dry_run=dry_run)

    if update:
        manager.perform_updates(manifest)

    logger.info(f"\n{'='*60}")
    logger.info(f"✅ Synchronization complete")
    logger.info(f"{'='*60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
