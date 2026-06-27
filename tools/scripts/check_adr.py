#!/usr/bin/env python3
"""
ADR Structural Validator.

This script enforces the domain-specific structural contract for Architectural
Decision Records (ADRs). It complements generic frontmatter validation
(delegated to check_frontmatter.py) by focusing on ADR-specific requirements.

Core Responsibilities:
    1. Body Structure: Validates required, allowed, and conditional markdown
       sections (## Header) based on the ADR status.
    2. Status Synchronization: Ensures the 'status' declared in YAML frontmatter
       matches the '## Status' section in the markdown body.
    3. Promotion Gates: Enforces quality criteria for ADRs transitioning to
       'accepted' (e.g., minimum number of Alternatives, non-empty Participants).

This script performs a full scan of all ADR files in the repository to prevent
documentation drift, ensuring that updates to governance rules are applied
consistently across all records, regardless of whether they were recently modified.

Note: Generic frontmatter validation (field presence, date format, tag
vocabulary) is handled by tools/scripts/check_frontmatter.py.

Exit codes:
    0: All ADRs pass domain validation
    1: Domain structural errors found
"""

import argparse
import logging
import re
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

from tools.scripts import check_frontmatter
from tools.scripts.git import detect_repo_root
from tools.scripts import adr_utils
from tools.scripts.adr_utils import (
    AdrFile,
    IndexEntry,
    ValidationError,
    ADR_DIR,
    INDEX_PATH,
    EXCLUDED_FILES,
    VALID_STATUSES,
    STATUS_SECTIONS,
    DEFAULT_STATUS,
    SECTION_ORDER,
    STATUS_CORRECTIONS,
    REQUIRED_SECTIONS,
    ALLOWED_SECTIONS,
    CONDITIONAL_SECTIONS,
    CONDITIONAL_FIELDS,
    MIN_CONDITIONAL_SECTION_WORDS,
    PRIMARY_TAG_SECTIONING,
    get_adr_files,
    get_staged_adr_files,
    parse_adr_file,
)

# ======================
# Configuration
# ======================

# Regex patterns
ADR_HEADER_PATTERN = re.compile(r"^#\s+ADR-(\d+):\s+(.+)$", re.MULTILINE)
STATUS_SECTION_PATTERN = re.compile(r"^##\s+Status\s*\n+\s*(\w+)", re.MULTILINE)
SECTION_HEADER_PATTERN = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
CODE_FENCE_PATTERN = re.compile(r"```.*?```", re.DOTALL)

# ======================
# Core Logic
# ======================

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

def validate_index_sync(
    adr_files: list[AdrFile], index_entries: list[adr_utils.IndexEntry]
) -> list[ValidationError]:
    """Validate that ADR files and index entries are synchronized."""
    errors: list[ValidationError] = []

    files_by_number: dict[int, list[AdrFile]] = {}
    for f in adr_files:
        files_by_number.setdefault(f.number, []).append(f)

    entries_by_number: dict[int, adr_utils.IndexEntry] = {}
    for e in index_entries:
        entries_by_number[e.number] = e

    for number, files in files_by_number.items():
        if len(files) > 1:
            filenames = ", ".join(f.path.name for f in files)
            errors.append(ValidationError(number, "duplicate_number", f"ADR {number} has multiple files: {filenames}"))

        if number not in entries_by_number:
            file = files[0]
            errors.append(ValidationError(number, "missing_in_index", f"ADR {number} ({file.path.name}) not in index"))

    for number, entry in entries_by_number.items():
        if number not in files_by_number:
            errors.append(ValidationError(number, "orphan_in_index", f"ADR {number} in index but file not found"))
        else:
            file = files_by_number[number][0]
            expected_link = f"/architecture/adr/{file.path.name}"
            if entry.link != expected_link:
                errors.append(ValidationError(number, "wrong_link", f"ADR {number} has wrong link: {entry.link} (expected {expected_link})"))

            if file.frontmatter and file.frontmatter.get("title") != entry.title:
                errors.append(ValidationError(number, "title_mismatch", f"ADR {number} title mismatch: index='{entry.title}', frontmatter='{file.frontmatter['title']}'"))

            effective_status = file.status if file.status else DEFAULT_STATUS
            expected_section = STATUS_SECTIONS.get(effective_status, STATUS_SECTIONS[DEFAULT_STATUS])
            if entry.section != expected_section:
                errors.append(ValidationError(number, "wrong_section", f"ADR {number} is in section '{entry.section}', but its status '{effective_status}' requires '{expected_section}'"))

    return errors

def fix_index() -> list[str]:
    """Fix the index file by regenerating it from ADR files."""
    adr_files = adr_utils.get_adr_files()
    changes: list[str] = []

    # Detect and warn about duplicate ADR numbers
    files_by_number: dict[int, list[AdrFile]] = {}
    for adr in adr_files:
        files_by_number.setdefault(adr.number, []).append(adr)

    for number, files in files_by_number.items():
        if len(files) > 1:
            statuses = ", ".join([f"status={f.status}" for f in files])
            logger.warning(f"ADR-{number} appears in multiple index locations: {statuses}")

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

    for number in existing_titles:
        if number not in {f.number for f in adr_files}:
            changes.append(f"Removed orphan entry ADR {number}")

    adr_utils.INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    adr_utils.INDEX_PATH.write_text("".join(lines), encoding="utf-8")
    return changes

def find_broken_term_references(files: list[Path]) -> list[adr_utils.BrokenTermReference]:
    """Scan files for broken MyST term references."""
    broken_refs = []
    for filepath in files:
        try:
            content = filepath.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for line_num, line in enumerate(content.splitlines(), start=1):
            for match in adr_utils.BROKEN_TERM_PATTERN.finditer(line):
                adr_number = int(match.group(1))
                broken_refs.append(adr_utils.BrokenTermReference(
                    file_path=filepath, line_number=line_num, adr_number=adr_number,
                    original_text=match.group(0), suggested_fix=f"{{term}}`ADR{adr_utils.TERM_SEPARATOR}{adr_number}`"
                ))
    return broken_refs

def validate_term_references(files: list[Path]) -> list[ValidationError]:
    """Validate MyST term references in files."""
    broken_refs = find_broken_term_references(files)
    return [ValidationError(ref.adr_number, "broken_term_reference", f"{ref.file_path}:{ref.line_number}: '{ref.original_text}' should be '{ref.suggested_fix}'") for ref in broken_refs]

def fix_term_references(files: list[Path]) -> list[Path]:
    """Fix broken term references in files."""
    modified_files = []
    for filepath in files:
        try:
            content = filepath.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        new_content = adr_utils.BROKEN_TERM_PATTERN.sub(rf"{{term}}`ADR{adr_utils.TERM_SEPARATOR}\1`", content)
        if new_content != content:
            filepath.write_text(new_content, encoding="utf-8")
            modified_files.append(filepath)
    return modified_files

def validate_sections(adr_file: AdrFile) -> list[ValidationError]:
    """Check required/allowed sections and conditional section rules."""
    errors = []
    if adr_file.content is None:
        return errors

    content_without_fences = CODE_FENCE_PATTERN.sub("", adr_file.content)
    section_counts: dict[str, int] = {}
    for match in SECTION_HEADER_PATTERN.finditer(content_without_fences):
        name = match.group(1)
        section_counts[name] = section_counts.get(name, 0) + 1

    for name, count in section_counts.items():
        if count > 1:
            errors.append(
                ValidationError(
                    number=adr_file.number,
                    error_type="duplicate_section",
                    message=f"ADR {adr_file.number} has duplicate section: '## {name}' ({count} occurrences)",
                )
            )

    found_sections = set(section_counts)
    for required_section in REQUIRED_SECTIONS:
        if required_section not in found_sections:
            errors.append(
                ValidationError(
                    number=adr_file.number,
                    error_type="missing_section",
                    message=f"ADR {adr_file.number} missing required section: '## {required_section}'",
                )
            )

    if ALLOWED_SECTIONS:
        unexpected = found_sections - ALLOWED_SECTIONS
        for section in sorted(unexpected):
            errors.append(
                ValidationError(
                    number=adr_file.number,
                    error_type="unexpected_section",
                    message=f"ADR {adr_file.number} has unexpected section: '## {section}' (not in allowed_sections)",
                )
            )

    if CONDITIONAL_SECTIONS:
        allowed_statuses: dict[str, set[str]] = {}
        for status, sections in CONDITIONAL_SECTIONS.items():
            for section in sections:
                allowed_statuses.setdefault(section, set()).add(status)

        effective_status = adr_file.status or ""
        for section_name, valid_statuses in allowed_statuses.items():
            if section_name in found_sections and effective_status not in valid_statuses:
                errors.append(
                    ValidationError(
                        number=adr_file.number,
                        error_type="conditional_section_violation",
                        message=(
                            f"ADR {adr_file.number} has '## {section_name}' but status is "
                            f"'{effective_status}' (only allowed for: {', '.join(sorted(valid_statuses))})"
                        ),
                    )
                )

        for status, required_section_names in CONDITIONAL_SECTIONS.items():
            if effective_status == status:
                for section_name in required_section_names:
                    if section_name not in found_sections:
                        errors.append(
                            ValidationError(
                                number=adr_file.number,
                                error_type="missing_conditional_section",
                                message=(
                                    f"ADR {adr_file.number} has status '{effective_status}' "
                                    f"but is missing required section: '## {section_name}'"
                                ),
                            )
                        )
    return errors

def validate_tags(adr_file: AdrFile) -> list[ValidationError]:
    """Delegate tag validation to check_frontmatter and enforce non-empty tags."""
    errors = []
    fm_errs = check_frontmatter.validate_parsed_frontmatter(
        adr_file.frontmatter or {}, adr_file.path, detect_repo_root(), content=adr_file.content
    )
    for e in fm_errs:
        # Tag errors are reported as 'invalid_value' (unknown tag) or 'missing_field' (absent)
        if e.error_type in ("invalid_value", "missing_field") and e.field == "tags":
            errors.append(ValidationError(adr_file.number, "invalid_tag", e.message))

    # Domain rule: Tags must not be an empty list
    tags = adr_file.frontmatter.get("tags") if adr_file.frontmatter else None
    if isinstance(tags, list) and not tags:
        errors.append(ValidationError(adr_file.number, "empty_tags", f"ADR {adr_file.number} tags list is empty"))
    return errors

def validate_conditional_fields(adr_file: AdrFile, all_adr_numbers: set[int] | None = None) -> list[ValidationError]:
    """Check status-dependent frontmatter fields."""
    errors = []
    if not adr_file.frontmatter or not adr_file.status:
        return errors

    field_rules = CONDITIONAL_FIELDS.get(adr_file.status, {})
    for field_name, rules in field_rules.items():
        # Check both top-level and options block (per ADR-26042)
        value = adr_file.frontmatter.get(field_name)
        if value is None:
            options = adr_file.frontmatter.get("options")
            if isinstance(options, dict):
                value = options.get(field_name)

        if rules.get("required") and not value:
            errors.append(
                ValidationError(
                    number=adr_file.number,
                    error_type="missing_conditional_field",
                    message=f"ADR {adr_file.number} has status '{adr_file.status}' but '{field_name}' is missing",
                )
            )
            continue
        if not value:
            continue
        if rules.get("type") == "adr_reference":
            ref_match = re.match(r"^ADR-(\d+)$", str(value))
            if not ref_match:
                errors.append(
                    ValidationError(
                        number=adr_file.number,
                        error_type="invalid_field_type",
                        message=f"ADR {adr_file.number} field '{field_name}' must be 'ADR-NNNNN', got: {value}",
                    )
                )
                continue
            ref_number = int(ref_match.group(1))
            if all_adr_numbers is not None and ref_number not in all_adr_numbers:
                errors.append(
                    ValidationError(
                        number=adr_file.number,
                        error_type="invalid_field_reference",
                        message=f"ADR {adr_file.number} field '{field_name}' references non-existent ADR {ref_number}",
                    )
                )
    return errors

def validate_conditional_section_content(adr_file: AdrFile) -> list[ValidationError]:
    """Check that conditional sections have meaningful content."""
    errors = []
    if not adr_file.content or not adr_file.status:
        return errors
    section_names = CONDITIONAL_SECTIONS.get(adr_file.status, [])
    for section_name in section_names:
        body = _extract_section_body(adr_file.content, section_name)
        word_count = len(body.split()) if body else 0
        if word_count < MIN_CONDITIONAL_SECTION_WORDS:
            errors.append(
                ValidationError(
                    number=adr_file.number,
                    error_type="empty_conditional_section",
                    message=f"ADR {adr_file.number} section '## {section_name}' is too short ({word_count} words)",
                )
            )
    return errors

def _extract_section_body(content: str, section_name: str) -> str:
    """Extract the body text of a named ## section."""
    pattern = re.compile(
        rf"^##\s+{re.escape(section_name)}\s*$\n(.*?)(?=^##\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(content)
    return match.group(1).strip() if match else ""

def validate_promotion_gate(adr_file: AdrFile) -> tuple[list[ValidationError], list[ValidationError]]:
    """Validate promotion gate criteria (ADR-26025)."""
    errors, warnings = [], []
    if adr_file.content is None or adr_file.status is None:
        return errors, warnings
    alt_body = _extract_section_body(adr_file.content, "Alternatives")
    part_body = _extract_section_body(adr_file.content, "Participants")
    alt_count = len(re.findall(r"^(?:[-*]\s+\*\*|\d+\.\s+|###\s+)", alt_body, re.MULTILINE))
    if adr_file.status == "accepted":
        if alt_count < 2:
            errors.append(ValidationError(adr_file.number, "insufficient_alternatives", f"ADR {adr_file.number} accepted but has <2 alternatives"))
        if not part_body:
            errors.append(ValidationError(adr_file.number, "empty_participants", f"ADR {adr_file.number} accepted but empty Participants"))
    elif adr_file.status == "proposed" and alt_count == 0:
        warnings.append(ValidationError(adr_file.number, "no_alternatives_proposed", f"ADR {adr_file.number} proposed with no alternatives"))
    return errors, warnings

# ======================
# Fix Functions
# ======================

def fix_invalid_status(adr_file: AdrFile) -> bool:
    """Fix invalid status by suggesting correction."""
    if adr_file.status is None or adr_file.status in VALID_STATUSES:
        return True
    invalid_status = adr_file.status.lower()
    suggested = STATUS_CORRECTIONS.get(invalid_status)
    logger.error(f"ADR {adr_file.number} has invalid status: '{adr_file.status}'")
    if suggested:
        logger.info(f"Suggested: '{invalid_status}' -> '{suggested}'")
        response = input(f"Apply fix '{suggested}'? [Y/n/custom]: ").strip().lower()
        new_status = suggested if response in ("", "y") else (response if response != "n" else None)
    else:
        new_status = input(f"Enter correct status (or Enter to skip): ").strip().lower() or None
    if not new_status or new_status not in VALID_STATUSES:
        return False
    content = adr_file.path.read_text(encoding="utf-8")
    fm, *rest = check_frontmatter.parse_frontmatter(content)
    if fm:
        # Use a regex that captures leading whitespace to preserve indentation
        # This handles both top-level (no indent) and options block (indented)
        status_pattern = re.compile(r"^(\s*)status:\s*.+$", re.MULTILINE)

        def replace_status(m):
            # m.group(1) captures the exact indentation used in the file
            # m.group(0) is the entire '  status: value' line
            indent = m.group(1)
            # We replace the entire line matching the pattern within the frontmatter block
            fm_content = m.group(1)
            updated_fm = status_pattern.sub(f"\\1status: {new_status}", fm_content)
            return f"---\n{updated_fm}\n---\n"

        # However, FRONTMATTER_PATTERN.sub's callback receives the match for the WHOLE block.
        # We need to substitute the status line within that block.
        def block_replacer(m):
            block_content = m.group(1)
            updated_block = status_pattern.sub(f"\\1status: {new_status}", block_content)
            return f"---\n{updated_block}\n---\n"

        new_content = check_frontmatter.FRONTMATTER_PATTERN.sub(block_replacer, content)
    else:
        new_content = STATUS_SECTION_PATTERN.sub(f"## Status\n\n{new_status.capitalize()}", content)
    adr_file.path.write_text(new_content, encoding="utf-8")
    adr_file.status = new_status
    return True

def fix_title_mismatch(adr_file: AdrFile) -> bool:
    """Fix title mismatch by updating frontmatter to match header."""
    if adr_file.frontmatter_title is None or adr_file.frontmatter_title == adr_file.title:
        return True
    logger.error(f"ADR {adr_file.number} title mismatch: Header '{adr_file.title}' vs FM '{adr_file.frontmatter_title}'")
    if input("Update frontmatter to match header? [y/N]: ").strip().lower() != "y":
        return False
    content = adr_file.path.read_text(encoding="utf-8")
    def replace_title(m):
        updated = re.sub(r"^title:\s*.+$", f"title: {adr_file.title}", m.group(1), flags=re.MULTILINE)
        return f"---\n{updated}\n---\n"
    adr_file.path.write_text(check_frontmatter.FRONTMATTER_PATTERN.sub(replace_title, content), encoding="utf-8")
    return True

def fix_duplicate_sections(adr_files: list[AdrFile]) -> bool:
    """Merge duplicate ## section headers in ADR files."""
    any_modified = False
    for adr in adr_files:
        if adr.content is None: continue
        section_counts = {}
        for match in SECTION_HEADER_PATTERN.finditer(adr.content):
            name = match.group(1)
            section_counts[name] = section_counts.get(name, 0) + 1
        duplicates = {name for name, count in section_counts.items() if count > 1}
        if not duplicates: continue
        content = adr.content
        for section_name in duplicates:
            pattern = re.compile(rf"^##\s+{re.escape(section_name)}\s*$\n(.*?)(?=^##\s|\Z)", re.MULTILINE | re.DOTALL)
            matches = list(pattern.finditer(content))
            if len(matches) <= 1: continue
            bodies = [m.group(1).strip() for m in matches]
            merged_body = "\n\n".join(b for b in bodies if b)
            if input(f"Merge {len(matches)} '## {section_name}' in ADR {adr.number}? [Y/n]: ").strip().lower() not in ("", "y"):
                continue
            for m in reversed(matches[1:]):
                content = content[:m.start()] + content[m.end():]
            first = pattern.search(content)
            if first:
                content = content[:first.start()] + f"## {section_name}\n\n{merged_body}\n\n" + content[first.end():]
        if content != adr.content:
            adr.path.write_text(content, encoding="utf-8")
            any_modified = True
    return any_modified

def migrate_legacy_adr(filepath: Path) -> bool:
    """Add YAML frontmatter to legacy ADR file without it."""
    content = filepath.read_text(encoding="utf-8")
    if check_frontmatter.parse_frontmatter(content)[0] is not None:
        return False
    header_match = ADR_HEADER_PATTERN.search(content)
    if not header_match: return False
    number, title = int(header_match.group(1)), header_match.group(2).strip()
    status_match = STATUS_SECTION_PATTERN.search(content)
    status = status_match.group(1).lower() if status_match else DEFAULT_STATUS
    if status not in VALID_STATUSES:
        status = STATUS_CORRECTIONS.get(status, DEFAULT_STATUS)
    import datetime
    date_str = datetime.datetime.fromtimestamp(filepath.stat().st_mtime).strftime("%Y-%m-%d")
    fm = f"---\nid: {number}\ntitle: {title}\ndate: {date_str}\nstatus: {status}\ntags: [architecture]\nsuperseded_by: null\n---\n\n"
    filepath.write_text(fm + content, encoding="utf-8")
    return True

# ======================
# CLI
# ======================

def main(argv: list[str] | None = None) -> int:
    """Main entry point for structural validation."""
    parser = argparse.ArgumentParser(description="Validate ADR structural contract")
    parser.add_argument(
        "paths",
        nargs="*",
        help="Files or directories to validate. Defaults to ADR directory.",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Detailed output")
    parser.add_argument("--fix", action="store_true", help="Fix structural issues (status, titles, sections)")
    parser.add_argument("--migrate", action="store_true", help="Migrate legacy ADRs to frontmatter")
    args = parser.parse_args(argv)

    if args.migrate:
        migrated = 0
        for f in ADR_DIR.glob("adr_*.md"):
            if f.name not in EXCLUDED_FILES and migrate_legacy_adr(f):
                migrated += 1
        logger.info(f"Migrated {migrated} ADR files.")
        return 0

    # Identify staged files for dual-mode validation (ADR-26042)
    staged_files_set = {Path(p).resolve() for p in args.paths} if args.paths else set()

    # Resolve files to validate
    if args.paths:
        # If paths provided, scan those specifically
        input_paths = [Path(p) for p in args.paths]
        adr_files = []
        for p in input_paths:
            if p.is_dir():
                for f in p.glob("adr_*.md"):
                    adr = parse_adr_file(f)
                    if adr: adr_files.append(adr)
            elif p.is_file():
                adr = parse_adr_file(p)
                if adr: adr_files.append(adr)
    else:
        # Default: full repo scan
        adr_files = get_adr_files()

    if not adr_files:
        if args.verbose: logger.info("No ADR files found to check.")
        return 0

    if args.fix:
        modified = []
        for adr in adr_files:
            if fix_invalid_status(adr): modified.append(adr.path.name)
            if fix_title_mismatch(adr): modified.append(adr.path.name)
        if fix_duplicate_sections(adr_files):
            modified.append("multiple_files")
        if modified:
            logger.info(f"Fixed structural issues in {len(set(modified))} files.")
            # Refresh files list after fix
            if args.paths:
                adr_files = []
                for p in [Path(path) for path in args.paths]:
                    if p.is_dir():
                        for f in p.glob("adr_*.md"):
                            adr = parse_adr_file(f)
                            if adr: adr_files.append(adr)
                    elif p.is_file():
                        adr = parse_adr_file(p)
                        if adr: adr_files.append(adr)
            else:
                adr_files = get_adr_files()

    all_numbers = {adr.number for adr in adr_files}
    blocking_errors = 0
    all_errors: list[ValidationError] = []

    for adr in adr_files:
        if args.verbose:
            logger.info(f"Checking ADR {adr.number}...")

        # Determine if this file is blocking (staged)
        is_blocking = adr.path.resolve() in staged_files_set

        errors = []
        errors.extend(validate_sections(adr))
        errors.extend(validate_conditional_fields(adr, all_numbers))
        errors.extend(validate_conditional_section_content(adr))

        # Status sync check
        if adr.status and adr.body_status and adr.status != adr.body_status:
            errors.append(ValidationError(adr.number, "status_mismatch", f"Frontmatter '{adr.status}' vs Body '{adr.body_status}'"))

        # Generic frontmatter delegation
        fm_errs = check_frontmatter.validate_frontmatter(adr.path, detect_repo_root())
        for e in fm_errs:
            # Preserve the is_blocking status from check_frontmatter or the staged set
            # frontmatter.validate_frontmatter is a global scan, so we override with local staged status
            errors.append(ValidationError(adr.number, e.error_type, f"Frontmatter: {e.message}", is_blocking=is_blocking))

        if errors:
            for e in errors:
                e.is_blocking = is_blocking
                mode = "[BLOCKING]" if e.is_blocking else "[LEGACY]"
                logger.error(f"{mode} ADR {e.number} [{e.error_type}]: {e.message}")
                if e.is_blocking:
                    blocking_errors += 1
            all_errors.extend(errors)

    # Promotion gate ( warnings don't fail the build)
    for adr in adr_files:
        is_blocking = adr.path.resolve() in staged_files_set
        errs, warns = validate_promotion_gate(adr)
        for e in errs:
            e.is_blocking = is_blocking
            mode = "[BLOCKING]" if e.is_blocking else "[LEGACY]"
            logger.error(f"{mode} ADR {e.number} [gate_error]: {e.message}")
            if e.is_blocking:
                blocking_errors += 1
        for w in warns:
            logger.warning(f"ADR {w.number} [gate_warning]: {w.message}")

    return 1 if blocking_errors > 0 else 0
if __name__ == "__main__":
    sys.exit(main())
