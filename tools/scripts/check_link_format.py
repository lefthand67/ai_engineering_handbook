#!/usr/bin/env python3
"""
Script to check and fix link format in Markdown files - ensures ipynb priority.

Usage: check_link_format.py [--paths PATH ...] [--pattern PATTERN] [options]

When a .md file has a paired .ipynb file (Jupytext pair), links should point to
the .ipynb version because myst.yml only renders .ipynb files. Links to .md files
cause downloads instead of opening as web pages.

NOTE: This script only validates link FORMAT (.md vs .ipynb extension), NOT whether
the link target actually exists. Use check_broken_links.py to verify link targets.

This script is fully SVA (Smallest Viable Architecture) compliant, using only
Python's standard library (pathlib, re, sys, argparse, tempfile).
"""

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from tools.scripts.paths import (
    VALIDATION_EXCLUDE_DIRS,
    BROKEN_LINKS_EXCLUDE_FILES,
    BROKEN_LINKS_EXCLUDE_LINK_STRINGS,
    is_excluded,
)


def main():
    """Entry point."""
    app = LinkFormatCLI()
    app.run()


class LinkFormatCLI:
    """Main application orchestrator."""

    def __init__(self):
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description="Check link format in Markdown files - ensures ipynb priority when paired file exists",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""Example: %(prog)s --pattern "*.md" --exclude-dirs drafts
Example: %(prog)s --paths docs --verbose
Example: %(prog)s --fix        # Interactive fix mode
Example: %(prog)s --fix-all    # Automatic fix mode
Default directory: current directory
Default pattern: *.md""",
        )
        parser.add_argument(
            "--paths",
            nargs="*",
            help="Paths to Markdown files or directories to check (default: current directory).",
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
        parser.add_argument(
            "--fix",
            action="store_true",
            default=False,
            help="Interactive fix mode - ask for confirmation before fixing each file.",
        )
        parser.add_argument(
            "--fix-all",
            action="store_true",
            default=False,
            help="Automatic fix mode - fix all errors without prompts.",
        )
        return parser

    def get_git_root_dir(self) -> Optional[Path]:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            return Path(result.stdout.strip()).resolve()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    def run(self, argv: Optional[List[str]] = None) -> None:
        """
        Execute logic.
        :param argv: Optional list of strings. If None, uses sys.argv[1:].
        """
        args = self.parser.parse_args(argv)
        verbose = args.verbose
        pattern = args.pattern
        fix_mode = args.fix
        fix_all_mode = args.fix_all

        root_dir = self.get_git_root_dir()
        if root_dir is None:
            root_dir = Path(".").resolve()
            if verbose:
                print(
                    "Warning: Not in a Git repository. Using current directory as root."
                )
        else:
            print(f"Using Git root as project root: {root_dir.name}")

        files = []
        file_finder = FileFinder(args.exclude_dirs, args.exclude_files, verbose)

        is_current_dir = False
        if args.paths:
            input_paths = args.paths
        else:
            is_current_dir = True
            input_paths = [str(Path.cwd())]

        for p in input_paths:
            path_obj = Path(p)
            if path_obj.is_absolute():
                resolved = path_obj.resolve()
            else:
                resolved = (Path.cwd() / path_obj).resolve()

            if resolved.is_file():
                # CRITICAL: Always check exclusions for explicit file arguments.
                # Prevents processing of files in external research repos when passed directly.
                if is_excluded(str(resolved)):
                    if verbose:
                        print(f"  EXCLUDING (by directory rule): {resolved}")
                    continue
                files.append(resolved)
            elif resolved.is_dir():
                files.extend(file_finder.find(resolved, pattern))
            else:
                print(f"Warning: Path does not exist: {resolved}", file=sys.stderr)

        if not files:
            print(f"No files matching '{pattern}' found!")
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
        link_format_validator = LinkFormatValidator(
            root_dir=root_dir,
            verbose=verbose,
            exclude_link_strings=list(BROKEN_LINKS_EXCLUDE_LINK_STRINGS),
        )

        # Collect all issues by file
        issues_by_file: Dict[Path, List[dict]] = {}

        for file in files:
            if verbose:
                print(f"\nChecking file: {file}")
            links = link_extractor.extract(file)
            file_issues = []
            for link, line_no in links:
                issue = link_format_validator.find_format_issue(link, file, line_no)
                if issue:
                    file_issues.append(issue)
            if file_issues:
                issues_by_file[file] = file_issues

        # No issues found
        if not issues_by_file:
            print("\n✅ All link formats are correct! (Note: format only - use check_broken_links.py to verify targets exist)")
            sys.exit(0)

        total_issues = sum(len(issues) for issues in issues_by_file.values())

        # Handle fix modes
        if fix_all_mode:
            # Automatic fix mode - no prompts
            fixer = LinkFixer(verbose=verbose)
            fixed_count = 0
            for file, issues in issues_by_file.items():
                count = fixer.fix_links_in_file(file, issues)
                fixed_count += count
            Reporter.report_fixes(fixed_count, total_issues)
        elif fix_mode:
            # Interactive fix mode - ask per file
            fixer = LinkFixer(verbose=verbose)
            fixed_count = 0
            skipped_count = 0
            try:
                for file, issues in issues_by_file.items():
                    try:
                        rel_file = file.relative_to(root_dir)
                    except ValueError:
                        rel_file = file

                    print(f"\nFile: {rel_file}")
                    for issue in issues:
                        print(f"  Line {issue['line']}: {issue['link']} → {issue['suggested']}")

                    response = input("Fix this file? [y/n/q] (q=quit): ").strip().lower()
                    if response == "y":
                        count = fixer.fix_links_in_file(file, issues)
                        fixed_count += count
                        print(f"  ✓ Fixed {count} link(s)")
                    elif response == "q":
                        skipped_count += len(issues)
                        # Count remaining files
                        remaining = list(issues_by_file.keys())
                        idx = remaining.index(file)
                        for remaining_file in remaining[idx + 1 :]:
                            skipped_count += len(issues_by_file[remaining_file])
                        break
                    else:
                        skipped_count += len(issues)
                        print("  ✗ Skipped")
            except (KeyboardInterrupt, EOFError):
                print("\n\nInterrupted.")

            Reporter.report_fixes(fixed_count, total_issues, skipped_count)
        else:
            # Check-only mode (original behavior)
            with tempfile.NamedTemporaryFile(
                delete=False, mode="w", encoding="utf-8"
            ) as tf:
                temp_path = Path(tf.name)
                for file, issues in issues_by_file.items():
                    for issue in issues:
                        with open(temp_path, "a", encoding="utf-8") as f:
                            f.write(issue["error_msg"])

                Reporter.report(temp_path, True)


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
                myst_includes = [
                    m[1:] if m.startswith(" ") and not m.startswith("  ") else m
                    for m in re.findall(r"```\{include\}([^`\n]+)", line)
                    if m.strip()
                ]
                for link in myst_includes:
                    matches.append((link, i))

            if self.verbose:
                if matches:
                    print(f"  Links found in {file}: {matches}")
                else:
                    print(f"  No links found for {file}")

            return matches
        except UnicodeDecodeError:
            print(f"Warning: Cannot decode file {file}. Skipping.", file=sys.stderr)
            return []


class LinkFormatValidator:
    """Validates link format - checks if .md links should be .ipynb instead."""

    def __init__(
        self,
        root_dir: Path,
        verbose: bool = False,
        exclude_link_strings: Optional[List[str]] = None,
    ):
        self.root_dir = root_dir.resolve()
        self.verbose = verbose
        self.exclude_link_strings = (
            set(exclude_link_strings) if exclude_link_strings else set()
        )

    def is_absolute_url(self, link: str) -> bool:
        """Check if link is an absolute HTTP/HTTPS URL."""
        return bool(re.match(r"^https?://", link))

    def get_path_from_link(self, link: str) -> str:
        """Remove fragment from link."""
        return link.split("#")[0]

    def resolve_target_path(self, link_path_str: str, source_file: Path) -> Path:
        """Resolve relative or absolute (project-root-relative) paths."""
        link_path = Path(link_path_str)

        if link_path.is_absolute():
            path_str_cleaned = str(link_path).lstrip("/")
            return (self.root_dir / path_str_cleaned).resolve()
        else:
            return (source_file.parent / link_path).resolve()

    def find_format_issue(
        self, link: str, source_file: Path, line_no: int
    ) -> Optional[dict]:
        """
        Find format issue - check if .md link should be .ipynb.
        Returns dict with issue info if found, None if valid/skipped.
        """
        if self.is_absolute_url(link):
            if self.verbose:
                print(f"  SKIP External URL: {link}")
            return None

        link_path = self.get_path_from_link(link)
        if not link_path:
            return None

        # Skip internal fragments without path separators or dots
        if "/" not in link_path and "." not in link_path:
            if self.verbose:
                print(f"  SKIP Internal Fragment/Variable: {link}")
            return None

        # Check for excluded link strings
        if any(exclude_str in link_path for exclude_str in self.exclude_link_strings):
            if self.verbose:
                print(f"  SKIP Excluded Link String: {link}")
            return None

        # Only check .md links
        if not link_path.endswith(".md"):
            if self.verbose:
                print(f"  OK (not .md): {link}")
            return None

        target_path = self.resolve_target_path(link_path, source_file)

        # Check if paired .ipynb exists
        ipynb_path = target_path.with_suffix(".ipynb")
        if ipynb_path.exists():
            try:
                rel_source = source_file.relative_to(self.root_dir)
            except ValueError:
                rel_source = source_file

            suggested_link = link.replace(".md", ".ipynb")
            error_msg = (
                f"LINK FORMAT ERROR: File '{rel_source}:{line_no}' links to '{link}' "
                f"but paired .ipynb exists.\n"
                f"  Suggested fix: Change to '{suggested_link}'\n"
            )
            return {
                "link": link,
                "suggested": suggested_link,
                "line": line_no,
                "source": source_file,
                "error_msg": error_msg,
            }
        elif self.verbose:
            print(f"  OK (no .ipynb pair): {link}")

        return None

    def validate_link_format(
        self, link: str, source_file: Path, line_no: int
    ) -> Optional[str]:
        """
        Validate link format - check if .md link should be .ipynb.
        Returns error message if format issue found, None if valid/skipped.
        """
        issue = self.find_format_issue(link, source_file, line_no)
        return issue["error_msg"] if issue else None


class LinkFixer:
    """Fixes .md links to .ipynb in source files."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def fix_links_in_file(self, source_file: Path, issues: List[dict]) -> int:
        """
        Apply all fixes to a file.
        Returns count of fixes applied.
        """
        try:
            content = source_file.read_text(encoding="utf-8")
            lines = content.splitlines(keepends=True)

            fixes_applied = 0
            for issue in issues:
                line_idx = issue["line"] - 1  # Convert to 0-indexed
                if 0 <= line_idx < len(lines):
                    old_link = issue["link"]
                    new_link = issue["suggested"]
                    if old_link in lines[line_idx]:
                        lines[line_idx] = lines[line_idx].replace(old_link, new_link)
                        fixes_applied += 1
                        if self.verbose:
                            print(f"  Fixed line {issue['line']}: {old_link} → {new_link}")

            # Write back
            new_content = "".join(lines)
            source_file.write_text(new_content, encoding="utf-8")

            return fixes_applied
        except (OSError, UnicodeDecodeError) as e:
            print(f"Error fixing file {source_file}: {e}", file=sys.stderr)
            return 0


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

        for file in search_dir.rglob(pattern):
            if not file.is_file():
                if self.verbose:
                    print(f"  SKIPPING (not a file): {file}")
                continue

            if file.name in self.exclude_files:
                if self.verbose:
                    print(f"  EXCLUDING (by file name): {file}")
                continue

            try:
                relative_path = file.relative_to(search_dir)
            except ValueError:
                filtered_files.append(file)
                continue

            is_excluded_by_dir = False

            if ".ipynb_checkpoints" in relative_path.parts:
                is_excluded_by_dir = True

            if not is_excluded_by_dir:
                for part in relative_path.parts:
                    if part in self.exclude_dirs:
                        is_excluded_by_dir = True
                        break

            if not is_excluded_by_dir:
                current_check_path = relative_path
                while current_check_path != Path("."):
                    if str(current_check_path) in self.exclude_dirs:
                        is_excluded_by_dir = True
                        break
                    current_check_path = current_check_path.parent

            if is_excluded_by_dir:
                if self.verbose:
                    print(f"  EXCLUDING (by directory rule): {file}")
                continue

            filtered_files.append(file)

        return filtered_files


class Reporter:
    """Handles result reporting and exit behavior."""

    @staticmethod
    def report(temp_file: Path, errors_found: bool) -> None:
        if errors_found:
            try:
                with open(temp_file, "r", encoding="utf-8") as f:
                    report_content = f.read()
            except FileNotFoundError:
                print("Error: Temporary report file not found.", file=sys.stderr)
                sys.exit(1)

            count = sum(
                1 for line in report_content.splitlines() if "LINK FORMAT ERROR" in line
            )
            print(f"\n❌ {count} Link format errors found:")
            print(report_content, end="")
            sys.exit(1)
        else:
            print("\n✅ All link formats are correct! (Note: format only - use check_broken_links.py to verify targets exist)")
            sys.exit(0)

    @staticmethod
    def report_fixes(fixed_count: int, total_count: int, skipped_count: int = 0) -> None:
        if fixed_count == total_count:
            print(f"\n✅ Fixed all {fixed_count} link format errors.")
            sys.exit(0)
        elif fixed_count > 0:
            print(f"\n✓ Fixed {fixed_count}/{total_count} link format errors.")
            if skipped_count > 0:
                print(f"  Skipped: {skipped_count}")
            sys.exit(0)
        else:
            print(f"\n❌ No fixes applied. {total_count} errors remain.")
            sys.exit(1)


if __name__ == "__main__":
    main()
