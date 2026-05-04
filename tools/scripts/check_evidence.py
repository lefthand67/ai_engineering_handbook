#!/usr/bin/env python3
"""
Evidence Artifact Validator.

Validates evidence artifacts (analyses, retrospectives, sources) in
architecture/evidence/ against the schema defined in .vadocs/types/evidence.conf.json.

Scope: validates naming, frontmatter, and sections of evidence artifacts.
Does NOT modify files — read-only validation with exit codes.

Validation Strategy:
    The script employs a hybrid validation strategy to balance performance
    with collection-level integrity:
    1. Targeted Validation (--check-staged): Naming, frontmatter, and sections
       are validated only for files currently staged in Git. This prevents
       legacy errors in unstaged files from blocking commits.
    2. Global Validation: Orphan source detection (detect_orphaned_sources)
       is performed across the entire evidence collection regardless of
       staged status, as it requires full context to detect unextracted sources.

    This internal handling of staged files (vs. relying on pre-commit's
    pass_filenames) ensures that global integrity checks are not bypassed.

Public interface:
    main() — CLI entry point (--verbose, --check-staged)
    validate_naming(), validate_frontmatter(), validate_sections() — pure validators
    discover_artifacts() — scans evidence directories
    detect_orphaned_sources() — warns about unextracted sources

Dependencies:
    - .vadocs/types/evidence.conf.json (evidence rules)
    - .vadocs/conf.json (shared tags, date_format via parent_config pointer)
    - yaml (frontmatter parsing only — config is JSON)

Exit codes:
    0: All artifacts are valid
    1: Validation errors found
"""

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import yaml

from tools.scripts.git import detect_repo_root, get_staged_files
from tools.scripts.paths import get_config_path

logger = logging.getLogger(__name__)

# ======================
# Data Classes
# ======================


@dataclass
class EvidenceArtifact:
    """Represents an evidence artifact on disk."""

    path: Path
    artifact_id: str
    artifact_type: str
    frontmatter: dict | None = None
    content: str | None = None


@dataclass
class ValidationError:
    """Represents a validation error.

    Mimics FrontmatterError for consistency and agent actionability.
    """

    file_path: Path
    error_type: str
    message: str
    field: str | None = None
    config_source: str = "evidence.conf.json"


# ======================
# Configuration
# ======================

FRONTMATTER_PATTERN = re.compile(r"^\s*---\s*\n(.*?)\n---\s*(\n|$)", re.DOTALL)
SECTION_HEADER_PATTERN = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
CODE_FENCE_PATTERN = re.compile(r"```.*?```", re.DOTALL)



def load_evidence_config(config_path: Path) -> dict:
    """Load evidence configuration from JSON file.

    Args:
        config_path: Path to evidence.conf.json.

    Returns:
        Configuration dictionary.

    Raises:
        FileNotFoundError: If config file doesn't exist.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Evidence config not found: {config_path}")

    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def load_parent_config(evidence_config: dict, repo_root: Path) -> dict:
    """Load parent config (shared tags, date_format) via parent_config pointer.

    Args:
        evidence_config: Loaded evidence configuration.
        repo_root: Repository root directory.

    Returns:
        Parent configuration dictionary (.vadocs/conf.json).

    Raises:
        FileNotFoundError: If parent config file doesn't exist.
    """
    parent_rel = evidence_config.get("parent_config", "")
    parent_path = Path(parent_rel)

    # Support both relative-to-repo-root and absolute paths (tests use absolute)
    if not parent_path.is_absolute():
        parent_path = repo_root / parent_path

    if not parent_path.exists():
        raise FileNotFoundError(f"Parent config not found: {parent_path}")

    with open(parent_path, encoding="utf-8") as f:
        return json.load(f)


# Module-level placeholders — initialized in main()
REPO_ROOT: Path = Path("")
EVIDENCE_CONFIG_PATH: Path = Path("")
EVIDENCE_CONFIG: dict = {}
_parent_config: dict = {}
VALID_TAGS: set[str] = set()
ARTIFACT_TYPES: dict = {}
NAMING_PATTERNS: dict = {}
LIFECYCLE: dict = {}
COMMON_REQUIRED_FIELDS: list[str] = []
EVIDENCE_DIR: Path = Path("")
DATE_FORMAT_PATTERN: str = ""

def setup_config():
    """Initialize global configuration based on current repo root.
    Does not overwrite if config is already populated (allows test monkeypatching).
    """
    global REPO_ROOT, EVIDENCE_CONFIG_PATH, EVIDENCE_CONFIG, _parent_config, VALID_TAGS, ARTIFACT_TYPES, NAMING_PATTERNS, LIFECYCLE, COMMON_REQUIRED_FIELDS, EVIDENCE_DIR, DATE_FORMAT_PATTERN

    if REPO_ROOT == Path(""):
        REPO_ROOT = detect_repo_root()
    
    # If config is already loaded (monkeypatched in tests), skip filesystem loading
    if EVIDENCE_CONFIG:
        return

    EVIDENCE_CONFIG_PATH = get_config_path(REPO_ROOT, "evidence")
    EVIDENCE_CONFIG = load_evidence_config(EVIDENCE_CONFIG_PATH)
    _parent_config = load_parent_config(EVIDENCE_CONFIG, REPO_ROOT)

    _tags_raw = _parent_config.get("tags", {})
    VALID_TAGS = set(_tags_raw.keys()) if isinstance(_tags_raw, dict) else set(_tags_raw)
    ARTIFACT_TYPES = EVIDENCE_CONFIG.get("artifact_types", {})
    NAMING_PATTERNS = EVIDENCE_CONFIG.get("naming_patterns", {})
    LIFECYCLE = EVIDENCE_CONFIG.get("lifecycle", {})
    COMMON_REQUIRED_FIELDS = EVIDENCE_CONFIG.get("common_required_fields", [])
    EVIDENCE_DIR = REPO_ROOT / EVIDENCE_CONFIG.get("evidence_dir", "architecture/evidence")
    DATE_FORMAT_PATTERN = _parent_config.get("date_format", r"^\d{4}-\d{2}-\d{2}$")


# ======================
# Main
# ======================


def main() -> None:
    """Validate all evidence artifacts. Exit 0 if valid, 1 if errors found."""
    parser = argparse.ArgumentParser(description="Validate evidence artifacts.")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--check-staged", action="store_true", help="Only validate staged files")
    args = parser.parse_args()

    setup_config()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format='%(levelname)s: %(message)s'
    )
    logger.setLevel(logging.DEBUG if args.verbose else logging.WARNING)

    all_errors: list[ValidationError] = []
    all_warnings: list[ValidationError] = []
    artifact_count = 0

    staged_files = get_staged_files() if args.check_staged else None

    for artifact_type in ARTIFACT_TYPES:
        artifacts = discover_artifacts(artifact_type)

        for artifact in artifacts:
            rel_path = str(artifact.path.relative_to(REPO_ROOT)) if REPO_ROOT != Path("") else str(artifact.path)
            rel_path = Path(rel_path).as_posix()

            if staged_files is not None:
                staged_files_normalized = [Path(p).as_posix() for p in staged_files] if staged_files else []

                if rel_path not in staged_files_normalized:
                    logger.debug(f"Skipping {rel_path}: not in staged_files {staged_files_normalized}")
                    continue

            artifact_count += 1
            logger.debug(f"Validating {artifact.artifact_id} ({artifact_type}) - path: {rel_path}")

            if args.verbose:
                logger.debug(f"Validating {artifact.artifact_id} ({artifact_type})")

            all_errors.extend(validate_naming(artifact.path, artifact.path.name, artifact_type))

            all_errors.extend(validate_frontmatter(artifact.path, artifact.frontmatter or {}, artifact_type))

            if artifact.content:
                sections = _extract_sections(artifact.content)
                section_errors = validate_sections(artifact.path, sections, artifact_type)
                all_errors.extend(section_errors)

    # Orphaned source detection
    source_type = next((k for k, v in ARTIFACT_TYPES.items() if not v.get("statuses")), None)
    if source_type:
        sources_dir = EVIDENCE_DIR / ARTIFACT_TYPES[source_type]["directory_name"]
        # Convert orphan warnings to ValidationError for consistent reporting
        for warn in detect_orphaned_sources(sources_dir):
            # Orphan detection currently returns ValidationError-like objects but with artifact_id.
            # Let's fix detect_orphaned_sources to return proper ValidationErrors.
            all_warnings.append(warn)

    # Report
    if args.verbose or all_errors or all_warnings:
        logger.info(f"Evidence validation: {artifact_count} artifacts checked")

    if all_warnings:
        for w in all_warnings:
            # Warnings are reported to stderr via logger.warning
            path_part = f"{w.file_path}" if hasattr(w, 'file_path') else f"ID:{w.artifact_id}"
            logger.warning(f"{path_part} — {w.message} [orphan_warning]")

    if all_errors:
        for e in all_errors:
            field_part = f":{e.field}" if e.field else ""
            # Format: file_path:field [error_type] — message [config_source]
            logger.error(f"{e.file_path}{field_part} [{e.error_type}] — {e.message} [{e.config_source}]")

        logger.info(f"{'-'*80}")
        logger.info("DIAGNOSTIC TIP: If you see 'Missing required field' but the field is present, "
                    "check for YAML syntax errors in the frontmatter block.")
        logger.info(f"{'-'*80}")
        sys.exit(1)

    if args.verbose:
        logger.info("All artifacts valid.")

    sys.exit(0)


# ======================
# Validation
# ======================


def validate_naming(filepath: Path, filename: str, artifact_type: str) -> list[ValidationError]:
    """Validate filename against naming pattern from config.

    Args:
        filepath: Absolute path to the file.
        filename: Filename (with .md extension).
        artifact_type: Artifact type key from config.

    Returns:
        List of validation errors (empty if valid).
    """
    errors = []
    pattern_str = NAMING_PATTERNS.get(artifact_type)

    if pattern_str is None:
        errors.append(ValidationError(
            file_path=filepath,
            error_type="naming",
            message=f"No naming pattern defined for type '{artifact_type}'",
            config_source=f"{EVIDENCE_CONFIG_PATH.name} → naming_patterns",
        ))
        return errors

    stem = filename.removesuffix(".md") if filename.endswith(".md") else filename

    if not re.compile(pattern_str).match(stem):
        errors.append(ValidationError(
            file_path=filepath,
            error_type="naming",
            message=f"Filename '{filename}' does not match pattern: {pattern_str}",
            config_source=f"{EVIDENCE_CONFIG_PATH.name} → naming_patterns",
        ))

    return errors


def _get_field(frontmatter: dict, field: str) -> Any:
    """Get field value from top level or options block.

    Ensures compatibility with Common Frontmatter Standard (ADR-26042)
    where non-native fields are moved to the 'options' namespace.
    """
    if field in frontmatter:
        return frontmatter[field]
    options = frontmatter.get("options", {})
    if isinstance(options, dict) and field in options:
        return options[field]
    return None


def validate_frontmatter(filepath: Path, frontmatter: dict, artifact_type: str) -> list[ValidationError]:
    """Validate frontmatter fields against config requirements.

    Checks common required fields, type-specific required fields,
    valid statuses/severity/tags, and date format.

    Args:
        filepath: Absolute path to the file.
        frontmatter: Parsed YAML frontmatter dict.
        artifact_type: Artifact type key from config.

    Returns:
        List of validation errors (empty if valid).
    """
    errors = []
    type_config = ARTIFACT_TYPES.get(artifact_type, {})

    # Common required fields
    for field_name in COMMON_REQUIRED_FIELDS:
        if _get_field(frontmatter, field_name) is None:
            errors.append(ValidationError(
                file_path=filepath,
                error_type="frontmatter",
                field=field_name,
                message=f"Missing required field: {field_name}",
                config_source=f"{EVIDENCE_CONFIG_PATH.name} → common_required_fields",
            ))

    # Type-specific required fields
    for field_name in type_config.get("required_fields", []):
        if _get_field(frontmatter, field_name) is None:
            errors.append(ValidationError(
                file_path=filepath,
                error_type="frontmatter",
                field=field_name,
                message=f"Missing required field: {field_name}",
                config_source=f"{EVIDENCE_CONFIG_PATH.name} → artifact_types.{artifact_type}.required_fields",
            ))

    # Date format
    date_value = frontmatter.get("date")
    if date_value is not None:
        date_str = str(date_value)
        if not re.match(DATE_FORMAT_PATTERN, date_str):
            errors.append(ValidationError(
                file_path=filepath,
                error_type="frontmatter",
                field="date",
                message=f"Invalid date format: '{date_str}' (expected YYYY-MM-DD)",
                config_source=f"{_parent_config.get('date_format', 'conf.json')} → date_format",
            ))

    # Status (only for types with non-empty statuses list)
    valid_statuses = type_config.get("statuses", [])
    status_value = _get_field(frontmatter, "status")
    if valid_statuses and status_value is not None:
        if status_value not in valid_statuses:
            errors.append(ValidationError(
                file_path=filepath,
                error_type="frontmatter",
                field="status",
                message=f"Invalid status: '{status_value}' (valid: {valid_statuses})",
                config_source=f"{EVIDENCE_CONFIG_PATH.name} → artifact_types.{artifact_type}.statuses",
            ))

    # Severity (only for types with severity list)
    valid_severities = type_config.get("severity", [])
    severity_value = _get_field(frontmatter, "severity")
    if valid_severities and severity_value is not None:
        if severity_value not in valid_severities:
            errors.append(ValidationError(
                file_path=filepath,
                error_type="frontmatter",
                field="severity",
                message=f"Invalid severity: '{severity_value}' (valid: {valid_severities})",
                config_source=f"{EVIDENCE_CONFIG_PATH.name} → artifact_types.{artifact_type}.severity",
            ))

    # Tags (against parent config tags)
    if "tags" in frontmatter and isinstance(frontmatter["tags"], list):
        invalid_tags = [t for t in frontmatter["tags"] if t not in VALID_TAGS]
        if invalid_tags:
            errors.append(ValidationError(
                file_path=filepath,
                error_type="frontmatter",
                field="tags",
                message=f"Invalid tags: {invalid_tags} (valid: {sorted(VALID_TAGS)})",
                config_source=f"{_parent_config.get('tags', 'conf.json')} → tags",
            ))

    return errors


def validate_sections(filepath: Path, sections: list[str], artifact_type: str) -> list[ValidationError]:
    """Validate document sections against config requirements.

    Types with no required/optional sections accept anything (free-form).

    Args:
        filepath: Absolute path to the file.
        sections: List of ## section headers found in document.
        artifact_type: Artifact type key from config.

    Returns:
        List of validation errors (empty if valid).
    """
    errors = []
    type_config = ARTIFACT_TYPES.get(artifact_type, {})

    required_sections = type_config.get("required_sections", [])
    optional_sections = type_config.get("optional_sections", [])

    if not required_sections and not optional_sections:
        return errors

    allowed_sections = set(required_sections) | set(optional_sections)

    for section in required_sections:
        if section not in sections:
            errors.append(ValidationError(
                file_path=filepath,
                error_type="sections",
                field=section,
                message=f"Missing required section: '{section}'",
                config_source=f"{EVIDENCE_CONFIG_PATH.name} → artifact_types.{artifact_type}.required_sections",
            ))

    for section in sections:
        if section not in allowed_sections:
            errors.append(ValidationError(
                file_path=filepath,
                error_type="sections",
                field=section,
                message=f"Unexpected section: '{section}' (allowed: {sorted(allowed_sections)})",
                config_source=f"{EVIDENCE_CONFIG_PATH.name} → artifact_types.{artifact_type}.optional_sections",
            ))

    return errors


def detect_orphaned_sources(sources_dir: Path) -> list[ValidationError]:
    """Detect source files with null extracted_into older than threshold.

    Args:
        sources_dir: Path to evidence/sources/ directory.

    Returns:
        List of warning-level validation errors.
    """
    warnings = []
    orphan_days = LIFECYCLE.get("orphan_warning_days", 30)
    threshold = date.today() - timedelta(days=orphan_days)

    if not sources_dir.exists():
        return warnings

    for md_file in sorted(sources_dir.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        fm_match = FRONTMATTER_PATTERN.match(content)
        if not fm_match:
            continue

        try:
            fm = yaml.safe_load(fm_match.group(1))
        except yaml.YAMLError:
            continue
            
        if fm is None:
            continue

        if fm.get("extracted_into") is not None:
            continue

        date_str = str(fm.get("date", ""))
        try:
            source_date = date.fromisoformat(date_str)
        except (ValueError, TypeError):
            continue

        if source_date < threshold:
            warnings.append(ValidationError(
                file_path=md_file,
                error_type="orphan",
                message=f"Source has null extracted_into and is {(date.today() - source_date).days} days old",
                config_source=f"{EVIDENCE_CONFIG_PATH.name} → lifecycle.orphan_warning_days",
            ))

    return warnings


# ======================
# Discovery
# ======================


def discover_artifacts(artifact_type: str) -> list[EvidenceArtifact]:
    """Discover and parse evidence artifacts of a given type.

    Scans the type's directory (from config), filters by naming pattern,
    parses frontmatter, and returns sorted by ID.

    Args:
        artifact_type: Artifact type key from config.

    Returns:
        List of EvidenceArtifact sorted by artifact_id.
    """
    type_config = ARTIFACT_TYPES.get(artifact_type, {})
    directory_name = type_config.get("directory_name", "")

    target_dir = EVIDENCE_DIR / directory_name
    logger.debug(f"Scanning directory: {target_dir}")
    if not target_dir.exists():
        logger.debug(f"Directory {target_dir} does not exist")
        return []

    pattern_str = NAMING_PATTERNS.get(artifact_type)
    if pattern_str is None:
        return []

    pattern = re.compile(pattern_str)
    artifacts = []

    files_found = list(target_dir.glob("*.md"))
    logger.debug(f"Found {len(files_found)} .md files in {target_dir}")

    for md_file in files_found:
        stem = md_file.stem
        logger.debug(f"Checking file {md_file.name} (stem: {stem}) against pattern: {pattern_str}")
        if not pattern.match(stem):
            logger.debug(f"File {md_file.name} does not match pattern")
            continue

        content = md_file.read_text(encoding="utf-8")
        fm_match = FRONTMATTER_PATTERN.match(content)

        fm = None
        if fm_match:
            try:
                fm = yaml.safe_load(fm_match.group(1)) or {}
            except yaml.YAMLError:
                # Log the error but keep the artifact so validation can flag it
                logger.debug(f"Malformed YAML in {md_file.name}")

        artifact_id = fm.get("id", stem.split("_")[0] if "_" in stem else stem) if fm else (stem.split("_")[0] if "_" in stem else stem)
        artifacts.append(EvidenceArtifact(
            path=md_file,
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            frontmatter=fm,
            content=content,
        ))

    return sorted(artifacts, key=lambda a: str(a.artifact_id))


# ======================
# Helpers
# ======================


def _extract_sections(content: str) -> list[str]:
    """Extract ## section headers from markdown content, ignoring code fences."""
    stripped = CODE_FENCE_PATTERN.sub("", content)
    return SECTION_HEADER_PATTERN.findall(stripped)



if __name__ == "__main__":
    main()
