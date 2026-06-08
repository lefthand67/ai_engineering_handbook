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
    ValidationError,
    ADR_DIR,
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
            adr_files = get_adr_files() # Refresh

    all_numbers = {adr.number for adr in adr_files}
    total_errors = 0
    for adr in adr_files:
        if args.verbose:
            logger.info(f"Checking ADR {adr.number}...")

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
            errors.append(ValidationError(adr.number, e.error_type, f"Frontmatter: {e.message}"))

        if errors:
            total_errors += len(errors)
            for e in errors:
                logger.error(f"ADR {e.number} [{e.error_type}]: {e.message}")

    # Promotion gate ( warnings don't fail the build)
    for adr in adr_files:
        errs, warns = validate_promotion_gate(adr)
        total_errors += len(errs)
        for e in errs: logger.error(f"ADR {e.number} [gate_error]: {e.message}")
        for w in warns: logger.warning(f"ADR {w.number} [gate_warning]: {w.message}")

    return 1 if total_errors > 0 else 0

if __name__ == "__main__":
    sys.exit(main())
