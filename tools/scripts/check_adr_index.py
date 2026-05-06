#!/usr/bin/env python3
"""
ADR Index Synchronizer.

This script ensures that the ADR index (architecture/adr_index.md) is synchronized
with the ADR files in architecture/adr/ and validates project-wide MyST term
references to these ADRs.
"""

import argparse
import logging
import re
import subprocess
import sys
from pathlib import Path

from tools.scripts import adr_utils
from tools.scripts.adr_utils import (
    AdrFile,
    IndexEntry,
    ValidationError,
    ADR_DIR,
    INDEX_PATH,
    SECTION_ORDER,
    STATUS_SECTIONS,
    DEFAULT_STATUS,
    PRIMARY_TAG_SECTIONING,
    TERM_SEPARATOR,
    BROKEN_TERM_PATTERN,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# ======================
# Core Logic
# ======================

def validate_sync(
    adr_files: list[AdrFile], index_entries: list[IndexEntry]
) -> list[ValidationError]:
    """Validate that ADR files and index entries are synchronized.

    Args:
        adr_files: List of discovered ADR files
        index_entries: List of parsed index entries

    Returns:
        List of ValidationError objects describing any issues found.
    """
    errors: list[ValidationError] = []

    # Build lookup maps
    files_by_number: dict[int, list[AdrFile]] = {}
    for f in adr_files:
        files_by_number.setdefault(f.number, []).append(f)

    entries_by_number: dict[int, IndexEntry] = {}
    for e in index_entries:
        entries_by_number[e.number] = e

    # Check for duplicate ADR numbers
    for number, files in files_by_number.items():
        if len(files) > 1:
            filenames = ", ".join(f.path.name for f in files)
            errors.append(
                ValidationError(
                    number=number,
                    error_type="duplicate_number",
                    message=f"ADR {number} has multiple files: {filenames}",
                )
            )

    # Check for ADRs missing from index
    for number, files in files_by_number.items():
        if number not in entries_by_number:
            file = files[0]
            errors.append(
                ValidationError(
                    number=number,
                    error_type="missing_in_index",
                    message=f"ADR {number} ({file.path.name}) not in index",
                )
            )

    # Check for orphan entries (in index but no file)
    for number, entry in entries_by_number.items():
        if number not in files_by_number:
            errors.append(
                ValidationError(
                    number=number,
                    error_type="orphan_in_index",
                    message=f"ADR {number} in index but file not found",
                )
            )

    # Check for wrong links and title mismatches
    for number, entry in entries_by_number.items():
        if number in files_by_number:
            file = files_by_number[number][0]
            expected_link = f"/architecture/adr/{file.path.name}"
            if entry.link != expected_link:
                errors.append(
                    ValidationError(
                        number=number,
                        error_type="wrong_link",
                        message=f"ADR {number} has wrong link: {entry.link} (expected {expected_link})",
                    )
                )

            # Title mismatch: index title vs file frontmatter title
            if file.frontmatter and file.frontmatter.get("title") != entry.title:
                errors.append(
                    ValidationError(
                        number=number,
                        error_type="title_mismatch",
                        message=f"ADR {number} title mismatch: index='{entry.title}', frontmatter='{file.frontmatter['title']}'",
                    )
                )

    # Check for correct section placement (SSoT: STATUS_SECTIONS in adr_utils)
    for number, entry in entries_by_number.items():
        if number in files_by_number:
            file = files_by_number[number][0]
            effective_status = file.status if file.status else DEFAULT_STATUS
            expected_section = STATUS_SECTIONS.get(effective_status, STATUS_SECTIONS[DEFAULT_STATUS])

            if entry.section != expected_section:
                errors.append(
                    ValidationError(
                        number=number,
                        error_type="wrong_section",
                        message=f"ADR {number} is in section '{entry.section}', but its status '{effective_status}' requires '{expected_section}'",
                    )
                )

    # Check for ordering (within each section for partitioned index)
    if index_entries and not PRIMARY_TAG_SECTIONING:
        sections_seen = []
        current_section = None
        current_numbers = []

        for entry in index_entries:
            if entry.section != current_section:
                if current_numbers and current_numbers != sorted(current_numbers):
                    errors.append(
                        ValidationError(
                            number=0,
                            error_type="wrong_order",
                            message=f"Index entries in section '{current_section}' are not in numerical order",
                        )
                    )
                current_section = entry.section
                current_numbers = [entry.number]
                if current_section:
                    sections_seen.append(current_section)
            else:
                current_numbers.append(entry.number)

        # Check final section
        if current_numbers and current_numbers != sorted(current_numbers):
            section_msg = f" in section '{current_section}'" if current_section else ""
            errors.append(
                ValidationError(
                    number=0,
                    error_type="wrong_order",
                    message=f"Index entries{section_msg} are not in numerical order",
                )
            )

    return errors


def _get_primary_tag(adr: AdrFile) -> str:
    """Extract primary tag (first tag) from ADR frontmatter."""
    if adr.frontmatter:
        tags = adr.frontmatter.get("tags", [])
        if isinstance(tags, list) and tags:
            return tags[0]
        if isinstance(tags, str) and tags:
            return tags
    return "untagged"


def _format_entry(adr: AdrFile) -> list[str]:
    """Format a single ADR entry for the index glossary block."""
    title = adr.title
    link = f"/architecture/adr/{adr.path.name}"

    annotation = ""
    if adr.frontmatter and adr.frontmatter.get("superseded_by"):
        successor = adr.frontmatter["superseded_by"]
        annotation = f" — superseded by {{term}}`{successor}`"

    entry_lines = [f"ADR-{adr.number}\n"]
    entry_lines.append(f": [{title}]({link}){annotation}\n")

    if adr.frontmatter:
        description = adr.frontmatter.get("description")
        if description:
            entry_lines.append("\n")
            entry_lines.append(f"  {description}\n")

    entry_lines.append("\n")
    return entry_lines


def fix_index() -> list[str]:
    """Fix the index file by regenerating it from ADR files."""
    adr_files = adr_utils.get_adr_files()
    changes: list[str] = []

    existing_titles: dict[int, str] = {}
    try:
        for entry in adr_utils.parse_index():
            existing_titles[entry.number] = entry.title
    except FileNotFoundError:
        pass

    sections: dict[str, list[AdrFile]] = {section: [] for section in SECTION_ORDER}
    for adr in adr_files:
        effective_status = adr.status if adr.status else DEFAULT_STATUS
        section = STATUS_SECTIONS.get(effective_status, STATUS_SECTIONS[DEFAULT_STATUS])
        sections[section].append(adr)

    seen_numbers: dict[int, list[str]] = {}
    for adr in adr_files:
        status = adr.status if adr.status else DEFAULT_STATUS
        tag = _get_primary_tag(adr)
        location = f"{status}/{tag}"
        if adr.number not in seen_numbers:
            seen_numbers[adr.number] = []
        seen_numbers[adr.number].append(location)

    for number, locations in seen_numbers.items():
        if len(locations) > 1:
            logger.warning(
                f"ADR-{number} appears in multiple index locations: {', '.join(locations)}"
            )

    lines = ["# ADR Index\n"]

    for section_name in SECTION_ORDER:
        section_adrs = sections.get(section_name, [])
        if not section_adrs:
            continue

        lines.append(f"\n## **{section_name}**\n")

        if PRIMARY_TAG_SECTIONING:
            tag_groups: dict[str, list[AdrFile]] = {}
            for adr in section_adrs:
                tag = _get_primary_tag(adr)
                tag_groups.setdefault(tag, []).append(adr)

            for tag in sorted(tag_groups):
                lines.append(f"\n### {tag}\n")
                lines.append("\n:::{glossary}\n")

                for adr in sorted(tag_groups[tag], key=lambda x: x.number):
                    lines.extend(_format_entry(adr))
                    if adr.number not in existing_titles:
                        changes.append(f"Added ADR {adr.number}: {adr.title}")

                lines.append(":::\n")
        else:
            lines.append("\n:::{glossary}\n")
            for adr in sorted(section_adrs, key=lambda x: x.number):
                lines.extend(_format_entry(adr))
                if adr.number not in existing_titles:
                    changes.append(f"Added ADR {adr.number}: {adr.title}")
            lines.append(":::\n")

    current_numbers = {f.number for f in adr_files}
    for number in existing_titles:
        if number not in current_numbers:
            changes.append(f"Removed orphan entry ADR {number}")

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text("".join(lines), encoding="utf-8")

    return changes


def get_all_md_files(root: Path) -> list[Path]:
    """Find all markdown files in the repository, excluding SSoT dirs."""
    from tools.scripts.paths import VALIDATION_EXCLUDE_DIRS
    md_files = []
    for filepath in root.rglob("*.md"):
        if any(excluded in filepath.parts for excluded in VALIDATION_EXCLUDE_DIRS):
            continue
        md_files.append(filepath)
    return sorted(md_files)


def find_broken_term_references(files: list[Path]) -> list[adr_utils.BrokenTermReference]:
    """Scan files for broken MyST term references."""
    broken_refs = []
    for filepath in files:
        try:
            content = filepath.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        for line_num, line in enumerate(content.splitlines(), start=1):
            for match in BROKEN_TERM_PATTERN.finditer(line):
                adr_number = int(match.group(1))
                broken_refs.append(
                    adr_utils.BrokenTermReference(
                        file_path=filepath,
                        line_number=line_num,
                        adr_number=adr_number,
                        original=match.group(0),
                    )
                )
    return broken_refs


def validate_term_references(files: list[Path]) -> list[ValidationError]:
    """Validate MyST term references in files."""
    broken_refs = find_broken_term_references(files)
    errors = []
    for ref in broken_refs:
        errors.append(
            ValidationError(
                number=ref.adr_number,
                error_type="broken_term_reference",
                message=(
                    f"{ref.file_path}:{ref.line_number}: "
                    f"'{ref.original}' should be '{ref.suggested_fix}'"
                ),
            )
        )
    return errors


def fix_term_references(files: list[Path]) -> list[Path]:
    """Fix broken term references in files."""
    modified_files = []
    for filepath in files:
        try:
            content = filepath.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        new_content = BROKEN_TERM_PATTERN.sub(
            rf"{{term}}`ADR{TERM_SEPARATOR}\1`", content
        )

        if new_content != content:
            filepath.write_text(new_content, encoding="utf-8")
            modified_files.append(filepath)
    return modified_files


def get_staged_adr_files() -> list[Path]:
    """Get list of staged ADR files from git."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            check=True,
            capture_output=True,
            text=True,
        )
        staged_files = result.stdout.strip().split("\n")
        return [
            Path(f)
            for f in staged_files
            if f.startswith("architecture/adr/adr_") and f.endswith(".md")
        ]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


# ======================
# CLI
# ======================

def main(argv: list[str] | None = None) -> int:
    """Main entry point for ADR Index Synchronizer."""
    parser = argparse.ArgumentParser(
        description="Synchronize ADR index and validate term references",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed output",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically regenerate the ADR index",
    )
    parser.add_argument(
        "--check-staged",
        action="store_true",
        help="Only check staged ADR files (for pre-commit)",
    )
    parser.add_argument(
        "--check-terms",
        action="store_true",
        help="Validate {term}`ADR-XXXXX` references in all .md files",
    )
    parser.add_argument(
        "--fix-terms",
        action="store_true",
        help="Fix broken term references",
    )

    args = parser.parse_args(argv)

    if args.verbose:
        logger.info("Checking ADR index synchronization...")

    # Handle --fix-terms mode
    if args.fix_terms:
        repo_root = ADR_DIR.parent.parent
        md_files = get_all_md_files(repo_root)
        modified = fix_term_references(md_files)
        if modified:
            logger.info(f"Fixed term references in {len(modified)} file(s):")
            for filepath in modified:
                logger.info(f"  - {filepath}")
        else:
            logger.info("No broken term references found.")
        return 0

    # Handle --check-terms mode
    if args.check_terms:
        repo_root = ADR_DIR.parent.parent
        md_files = get_all_md_files(repo_root)
        errors = validate_term_references(md_files)
        if errors:
            logger.error(f"Found {len(errors)} broken term reference(s):")
            for error in errors:
                logger.error(f"  - {error.message}")
            return 1
        logger.info("All term references are valid.")
        return 0

    # Handle fix mode (Regenerate Index)
    if args.fix:
        changes = fix_index()
        if changes:
            logger.info(f"Updated {INDEX_PATH}:")
            for change in changes:
                logger.info(f"  - {change}")
        else:
            logger.info("Index is already in sync.")
        return 0

    # Handle check-staged mode
    if args.check_staged:
        staged = get_staged_adr_files()
        if not staged:
            if args.verbose:
                logger.info("No staged ADR files to check.")
            return 0
        if args.verbose:
            logger.info(f"Checking {len(staged)} staged ADR files...")

    # Standard validation
    adr_files = adr_utils.get_adr_files()
    try:
        index_entries = adr_utils.parse_index()
    except FileNotFoundError:
        if adr_files:
            logger.error(f"Error: Index file not found at {INDEX_PATH}")
            return 1
        return 0

    errors = validate_sync(adr_files, index_entries)
    if errors:
        logger.error(f"{INDEX_PATH} is out of sync with ADR files:")
        for error in errors:
            logger.error(f"  - {error.message}")
        logger.info("Run with --fix to update the index automatically.")
        return 1

    if args.verbose:
        logger.info("All ADRs are synchronized with the index.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
