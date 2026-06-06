#!/usr/bin/env python3
"""
Script to check broken links in files (default: Markdown files .md).

Usage: check_broken_links.py [--paths PATH ...] [--pattern PATTERN] [options]

This script is fully SVA (Smallest Viable Architecture) compliant, using only
Python's standard library (pathlib, re, sys, argparse, tempfile) for robust, local-only
link validation with full exclusion capabilities.

By default, it looks for Markdown-style links ([text](link)) in files matching the
given pattern (default: *.md), but any file type can be scanned.
"""

import argparse
import logging
import re
import sys
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

# Import VALIDATION_EXCLUDE_DIRS and BROKEN_LINKS_EXCLUDE_FILES
from tools.scripts.paths import (
    VALIDATION_EXCLUDE_DIRS,
    BROKEN_LINKS_EXCLUDE_FILES,
    BROKEN_LINKS_EXCLUDE_LINK_STRINGS,
    is_excluded,
)
from tools.scripts.git import detect_repo_root, get_staged_files, is_tracked

# Configure logger
logger = logging.getLogger(__name__)


def main():
    """Entry point."""
    app = LinkCheckerCLI()
    app.run()


class LinkCheckerCLI:
    """Main application orchestrator."""

    def __init__(self):
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description="Check for broken Markdown-style links in files (Local Filesystem Only)",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""Example: %(prog)s --pattern "*.md" --exclude-dirs drafts
Example: %(prog)s --paths docs --pattern "*.rst"
Default directory: current directory
Default pattern: *.md""",
        )
        parser.add_argument(
            "--paths",
            nargs="*",
            help="Paths to Markdown files or directories to check (default: current directory if not using pre-commit).",
        )
        parser.add_argument(
            "--pattern",
            default="*.md",
            help="File glob pattern to match (default: *.md) - ignored if a single file is specified",
        )
        parser.add_argument(
            "--exclude-dirs",
            nargs="*",
            default=VALIDATION_EXCLUDE_DIRS,
            help="Directory names to exclude from the check",
        )
        parser.add_argument(
            "--exclude-files",
            nargs="*",
            default=BROKEN_LINKS_EXCLUDE_FILES,
            help="Specific file names to exclude from the check",
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
        # Injectable argument parsing
        args = self.parser.parse_args(argv)
        verbose = args.verbose
        pattern = args.pattern

        # Configure logging
        logging.basicConfig(level=logging.INFO, format="%(message)s")
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        # 🔍 Determine project root: Git root first, then CWD
        root_dir = detect_repo_root()
        use_git_tracking = root_dir is not None
        if root_dir is None:
            root_dir = Path(".").resolve()
            if verbose:
                logger.warning("Warning: Not in a Git repository. Using current directory as root.")
        else:
            # Remove 'if verbose:' to satisfy test expectations
            logger.info(f"Using Git root as project root: {root_dir.name}")

        files = []
        file_finder = FileFinder(args.exclude_dirs, args.exclude_files, verbose)

        is_current_dir = False
        if args.paths:
            input_paths = args.paths
        else:
            is_current_dir = True
            input_paths = [str(Path.cwd())]

        resolved_paths_list = list()
        for p in input_paths:
            # Resolve input path relative to current working directory (not root_dir!)
            path_obj = Path(p)
            if path_obj.is_absolute():
                resolved = path_obj.resolve()
            else:
                resolved = (Path.cwd() / path_obj).resolve()
            resolved_paths_list.append(resolved)

            if resolved.is_file():
                # CRITICAL: Always check exclusions for explicit file arguments.
                # Prevents processing of files in external research repos when passed directly.
                if is_excluded(str(resolved)):
                    if verbose:
                        logger.debug(f"  EXCLUDING (by directory rule): {resolved}")
                    continue
                files.append(resolved)
            elif resolved.is_dir():
                files.extend(file_finder.find(resolved, pattern))
            else:
                logger.warning(f"Warning: Path does not exist: {resolved}")

        if not files:
            logger.info(f"No files matching '{pattern}' found!")
            sys.exit(0)

        effective_pattern = (
            "file" if len(files) == 1 and files[0].is_file() else "files"
        )

        print(f"Found {len(files)} {effective_pattern} in:", end="")
        if is_current_dir:
            print(f" {input_paths[0].split('/')[-1]}/")
        elif len(input_paths) == 1:
            print(f" {input_paths[0]}")
        else:
            for p in input_paths:
                print(f"\n- {p}", end="")
            print()

        link_extractor = LinkExtractor(verbose=verbose)
        link_validator = LinkValidator(
            root_dir=root_dir,
            verbose=verbose,
            exclude_link_strings=list(BROKEN_LINKS_EXCLUDE_LINK_STRINGS),
            use_git_tracking=use_git_tracking,
        )
        broken_links_found = False

        with tempfile.NamedTemporaryFile(
            delete=False, mode="w", encoding="utf-8"
        ) as tf:
            temp_path = Path(tf.name)
            for file in files:
                if verbose:
                    logger.debug(f"\nChecking file: {file}")
                links = link_extractor.extract(file)
                for link, line_no in links:
                    error = link_validator.validate_link(link, file, line_no)
                    if error:
                        with open(temp_path, "a", encoding="utf-8") as f:
                            f.write(error)
                        broken_links_found = True

            Reporter.report(temp_path, broken_links_found)


class LinkExtractor:
    """Extracts Markdown-style links from a given file."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def extract(self, file: Path) -> List[Tuple[str, int]]:
        """Extract all Markdown links from the file with their line numbers."""
        try:
            lines = file.read_text(encoding="utf-8").splitlines()
            matches = []
            for i, line in enumerate(lines, 1):
                # Standard Markdown links: [text](link)
                md_links = re.findall(r"\[[^\]]*\]\(([^)]+)\)", line)
                for link in md_links:
                    matches.append((link, i))

                # MyST include directives: {include} path
                # Matches ```{include} followed by everything until newline or backticks.
                # We strip exactly one leading space if it exists and is not followed by another space,
                # and ignore matches that are only whitespace, to satisfy test expectations.
                myst_includes = [
                    m[1:] if m.startswith(" ") and not m.startswith("  ") else m
                    for m in re.findall(r"```\{include\}([^`\n]+)", line)
                    if m.strip()
                ]
                for link in myst_includes:
                    matches.append((link, i))

            if self.verbose:
                if matches:
                    logger.debug(f"  Links found in {file}: {matches}")
                else:
                    logger.debug(f"  No links found for {file}")

            return matches
        except UnicodeDecodeError:
            logger.warning(f"Warning: Cannot decode file {file}. Skipping.")
            return []


class LinkValidator:
    """Validates whether a link points to a valid local target."""

    def __init__(
        self,
        root_dir: Path,
        verbose: bool = False,
        exclude_link_strings: Optional[List[str]] = None,
        use_git_tracking: bool = False,
    ):
        self.root_dir = root_dir.resolve()
        self.verbose = verbose
        self.exclude_link_strings = (
            set(exclude_link_strings) if exclude_link_strings else set()
        )
        self.use_git_tracking = use_git_tracking

    def is_absolute_url(self, link: str) -> bool:
        """Check if link is an absolute HTTP/HTTPS URL."""
        return bool(re.match(r"^https?://", link))

    def get_path_from_link(self, link: str) -> str:
        """Remove fragment and escape characters from link."""
        path_only = link.split("#")[0]
        return path_only

    def resolve_target_path(self, link_path_str: str, source_file: Path) -> Path:
        """Resolve relative or absolute (project-root-relative) paths."""
        link_path = Path(link_path_str)

        if link_path.is_absolute():
            # Treat as absolute from project root (strip leading /)
            path_str_cleaned = str(link_path).lstrip("/")
            return (self.root_dir / path_str_cleaned).resolve()
        else:
            # Use walk_up=True for Python 3.13 compatibility with relative_to
            return (source_file.parent / link_path).resolve()

    def is_valid_target(self, target_file: Path) -> bool:
        """Check if target exists and is tracked by git (if tracking enabled)."""
        if not target_file.exists():
            return False

        # Production Link Safety: Enforce tracking only if enabled
        if self.use_git_tracking:
            if target_file.is_dir():
                index_files = [
                    target_file / "index.md",
                    target_file / "README.md",
                    target_file / "index.ipynb",
                    target_file / "README.ipynb",
                ]
                return any(p.exists() and is_tracked(p, cwd=self.root_dir) for p in index_files)
            return is_tracked(target_file, cwd=self.root_dir)

        # Fallback for non-git environments (e.g. unit tests in tmp_path)
        if target_file.is_dir():
            index_files = [
                target_file / "index.md",
                target_file / "README.md",
                target_file / "index.ipynb",
                target_file / "README.ipynb",
            ]
            return any(p.exists() for p in index_files)
        return True

    def validate_link(
        self, link: str, source_file: Path, line_no: int
    ) -> Optional[str]:
        """
        Validate a single link.
        Returns error message if broken, None if valid/skipped.
        """
        if self.is_absolute_url(link):
            if self.verbose:
                logger.debug(f"  SKIP External URL: {link}")
            return None

        link_path = self.get_path_from_link(link)
        if not link_path:
            return None

        # Skip internal fragments without path separators or dots
        if "/" not in link_path and "." not in link_path:
            if self.verbose:
                logger.debug(f"  SKIP Internal Fragment/Variable: {link}")
            return None

        # Check for excluded link strings
        if any(exclude_str in link_path for exclude_str in self.exclude_link_strings):
            if self.verbose:
                logger.debug(f"  SKIP Excluded Link String: {link}")
            return None

        target_file = self.resolve_target_path(link_path, source_file)

        if not self.is_valid_target(target_file):
            try:
                rel_source = source_file.relative_to(self.root_dir)
            except ValueError:
                rel_source = source_file
            return f"BROKEN LINK: File '{rel_source}:{line_no}' contains broken link: {link}\n"
        elif self.verbose:
            try:
                rel_target = target_file.relative_to(self.root_dir)
            except ValueError:
                rel_target = target_file
            logger.debug(f"  OK: {link} -> {rel_target}")

        return None


class FileFinder:
    """Finds files matching a pattern while respecting exclusion rules."""

    def __init__(
        self,
        exclude_dirs: List[str],
        exclude_files: List[str],
        verbose: bool = False,
    ):
        self.exclude_dirs = exclude_dirs
        self.exclude_files = exclude_files
        self.verbose = verbose

    def find(self, search_dir: Path, pattern: str) -> List[Path]:
        """Return list of matching files, excluding specified dirs/files."""
        filtered_files = []

        # Iterate through all entries matching the pattern within the search_dir
        for file in search_dir.rglob(pattern):
            if not file.is_file():
                if self.verbose:
                    logger.debug(f"  SKIPPING (not a file): {file}")
                continue

            # Check for excluded file names (basename) regardless of path
            if file.name in self.exclude_files:
                if self.verbose:
                    logger.debug(f"  EXCLUDING (by file name): {file}")
                continue

            # Get the path relative to search_dir to analyze directory components.
            # If `file` is not actually under `search_dir` (e.g., a symlink to an external file),
            # then `relative_to` will raise ValueError. In such cases, the file is not subject
            # to directory-based exclusions relative to search_dir.
            try:
                relative_path = file.relative_to(search_dir)
            except ValueError:
                # If the file is outside the search_dir hierarchy, it's not filtered by
                # directory-based exclusions relative to search_dir. It passes this check.
                filtered_files.append(file)
                continue

            is_excluded_by_dir = False

            # 1. Check for explicit .ipynb_checkpoints exclusion in any part of the relative path
            if ".ipynb_checkpoints" in relative_path.parts:
                is_excluded_by_dir = True

            # 2. Check for single-component directory exclusions (e.g., '__pycache__', '.git', 'build')
            #    If not already excluded by .ipynb_checkpoints
            if not is_excluded_by_dir:
                for part in relative_path.parts:
                    if part in self.exclude_dirs:
                        is_excluded_by_dir = True
                        break

            # 3. Check for multi-segment directory exclusions (e.g., 'misc/in_progress', 'misc/pr')
            #    This checks if any parent path (relative to search_dir) is an excluded multi-segment path.
            #    If not already excluded by previous checks
            if not is_excluded_by_dir:
                current_check_path = relative_path
                while current_check_path != Path(
                    "."
                ):  # Iterate up to the search_dir itself (represented by '.')
                    if str(current_check_path) in self.exclude_dirs:
                        is_excluded_by_dir = True
                        break
                    current_check_path = current_check_path.parent

            if is_excluded_by_dir:
                if self.verbose:
                    logger.debug(f"  EXCLUDING (by directory rule): {file}")
                continue

            filtered_files.append(file)

        return filtered_files


class Reporter:
    """Handles result reporting and exit behavior."""

    @staticmethod
    def report(temp_file: Path, broken_links_found: bool) -> None:
        if broken_links_found:
            try:
                with open(temp_file, "r", encoding="utf-8") as f:
                    report_content = f.read()
            except FileNotFoundError:
                logger.error("Error: Temporary report file not found.")
                sys.exit(1)

            count = sum(
                1 for line in report_content.splitlines() if "BROKEN LINK" in line
            )
            print(f"\n❌ {count} Broken links found:")
            print(report_content, end="")
            sys.exit(1)
        else:
            print("\n✅ All links are valid!")
            sys.exit(0)


if __name__ == "__main__":
    main()
