#!/usr/bin/env python3
"""Check that each script has a matching test file (dyad convention).

Scope: Enforces the script+test dyad. Contract docstrings (ADR-26045) serve
as the authoritative documentation — no separate instruction docs required.
Supersedes the former triad convention (ADR-26011).

Naming convention:
- Script: tools/scripts/<name>.py
- Test:   tools/tests/test_<name>.py

Validates:
1. Each script has a matching test file (naming convention)

Does NOT validate: documentation existence, doc staging, config co-staging.
"""

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path("tools/scripts")
TESTS_DIR = Path("tools/tests")

# Scripts excluded from test requirement
EXCLUDED_SCRIPTS = {"paths.py", "__init__.py"}


def get_staged_files() -> set[str]:
    """Get list of staged files."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
    )
    return set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()


def get_renamed_files() -> dict[str, str]:
    """Get renamed files from staging area. Returns {old_path: new_path}."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-status"],
        capture_output=True,
        text=True,
    )
    renamed = {}
    for line in result.stdout.strip().split("\n"):
        if line.startswith("R"):
            parts = line.split("\t")
            if len(parts) >= 3:
                renamed[parts[1]] = parts[2]
    return renamed


def is_mode_only_change(file_path: str) -> bool:
    """Check if a staged file has only mode (permission) changes, no content changes.

    Uses git diff --cached to check if there are actual content changes.
    Mode-only changes show only the mode line in diff output, no hunks.
    """
    result = subprocess.run(
        ["git", "diff", "--cached", "--", file_path],
        capture_output=True,
        text=True,
    )
    diff_output = result.stdout.strip()

    if not diff_output:
        return True  # No diff content means no content changes

    # Check if diff contains only mode change (old mode ... new mode) and no actual hunks
    lines = diff_output.split("\n")
    has_mode_change = False
    has_content_change = False

    for line in lines:
        if line.startswith("old mode") or line.startswith("new mode"):
            has_mode_change = True
        elif line.startswith("@@"):
            # Hunk header indicates actual content change
            has_content_change = True
            break

    return has_mode_change and not has_content_change


def has_content_changed(file_path: str, staged_files: set[str]) -> bool:
    """Check if a file is staged and has content changes."""
    return file_path in staged_files and not is_mode_only_change(file_path)


def script_name_to_paths(name: str) -> tuple[Path, Path]:
    """Convert script name to script and test paths."""
    script = SCRIPTS_DIR / f"{name}.py"
    test = TESTS_DIR / f"test_{name}.py"
    return script, test


def get_all_scripts() -> list[str]:
    """Get all script names (without .py extension) from scripts directory."""
    if not SCRIPTS_DIR.exists():
        return []
    return [
        f.stem
        for f in SCRIPTS_DIR.glob("*.py")
        if f.name not in EXCLUDED_SCRIPTS
    ]


def check_naming_convention(verbose: bool = False, files: list[str] | None = None) -> list[str]:
    """Check that each script has a matching test file.
    
    If 'files' is provided, only validate those specific files.
    Otherwise, validate all discovered scripts.
    """
    errors = []
    
    if files:
        # Validate only the provided files
        for file_path in files:
            path = Path(file_path)
            if path.suffix != ".py" or "tools/scripts/" not in str(path):
                continue
                
            name = path.stem
            script, test = script_name_to_paths(name)

            if not test.exists():
                errors.append(f"Missing test: {test} (for script {script})")

            if verbose and test.exists():
                print(f"OK: {name} has script and test")
    else:
        # Fallback: validate all discovered scripts
        for name in get_all_scripts():
            script, test = script_name_to_paths(name)

            if not test.exists():
                errors.append(f"Missing test: {test} (for script {script})")

            if verbose and test.exists():
                print(f"OK: {name} has script and test")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check that each script has a matching test (dyad convention)."
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Optional list of files to validate",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )
    parser.add_argument(
        "--check-convention-only",
        action="store_true",
        help="Only check naming convention, skip staging checks",
    )
    args = parser.parse_args()

    errors = []

    # Check naming convention (every script has a test)
    errors.extend(check_naming_convention(args.verbose, files=args.files))

    if errors:
        print("\nErrors found:")
        for error in errors:
            print(f"  ERROR: {error}")
        return 1

    if args.verbose:
        print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
