#!/usr/bin/env python3
"""
Config-Driven Frontmatter Validator.

Validates YAML frontmatter in governed markdown files against the hub+spoke
config chain defined in .vadocs/. Enforces ADR-26042 (Common Frontmatter
Standard): block composition, field presence, format, and allowed values.

STRUCTURAL SPECIFICATION (S-S-o-T):
----------------------------------
Governed files must follow one of two structural patterns based on their pairing:

1. The Dual-Block Pattern (For Jupytext-Paired Files):
   Required for any .md file that has a paired .ipynb file.
   Merging these blocks breaks Jupytext synchronization and the validation pipeline.

   Structure:
   ---
   # Block 1: Jupytext/Kernel Metadata
   jupytext:
     text_representation:
       extension: .md
       ...
   kernelspec:
     name: python3
     ...
   ---

   ---
   # Block 2: Project Identity, Discovery, and Lifecycle
   title: "Document Title"
   authors:
     - name: Vadim Rudakov
       email: rudakow.wadim@gmail.com
   date: "2026-05-01"
   description: "Elevator pitch"
   tags: [tag1, tag2]
   options:
     type: guide  # Mandatory: determines the validation spoke config
     birth: "2026-01-01"
     version: 1.0.0
   ---

2. The Single-Block Pattern (For Standard Governed Files):
   Used for files without a .ipynb pair (e.g., most ADRs, configs, guides).

   Structure:
   ---
   title: "Document Title"
   authors:
     - name: Vadim Rudakov
       email: rudakow.wadim@gmail.com
   date: "2026-05-01"
   description: "Elevator pitch"
   tags: [tag1, tag2]
   options:
     type: adr
     ...
   ---

Maintenance Rules:
-------------------
- date: Must be updated to today's date on every modification.
- options.version: Must be incremented according to SemVer:
    - Patch (1.0.0 -> 1.0.1): Simple edits, typos, or minor corrections.
    - Minor (1.0.0 -> 1.1.0): New functionality or content additions.
    - Major (1.0.0 -> 2.0.0): Significant architectural or decision changes.

Validation Scope:
    - ALL frontmatter validation: field presence, format, allowed values
    - Hub-level rules (blocks, field registry, tags, date format)
    - Spoke-level rules (type-specific required fields, statuses, severity)
    - Token size accuracy: Validates that 'options.token_size' reflects actual
      file content. This acts as a quality gate, ensuring that developers run
      the utility 'update_token_counts.py' before committing changes.
      NOTE: This script is read-only and does NOT automatically modify files;
      automatic updates are the responsibility of the fixer utility.

Does NOT own:
    - Structural validation (sections, section order) — domain scripts
    - Naming patterns (filename format, ID format) — domain scripts
    - Index generation — check_adr.py
    - Auto-fix (status_corrections) — check_adr.py
    - --fix mode — deferred to Phase 1.15

Public interface:
    main() — CLI entry point (--format)
    parse_frontmatter() — extract YAML frontmatter from file content
    resolve_type() — read options.type from parsed frontmatter
    load_config_chain() — load hub + optional spoke config
    validate_frontmatter() — validate a file's frontmatter (reads file)
    validate_parsed_frontmatter() — validate already-parsed frontmatter dict
    scan_paths() — resolve input paths to file list

Dependencies:
    - .vadocs/conf.json (hub — shared vocabulary, blocks, types, tags)
    - .vadocs/types/<type>.conf.json (spoke — type-specific rules)
    - yaml (frontmatter parsing only — config is JSON)
    - tools/scripts/paths.py (config discovery, VALIDATION_EXCLUDE_DIRS)
    - tools/scripts/git.py (detect_repo_root)

Exit codes:
    0: All validated files pass (warnings may still be printed)
    1: One or more validation errors found

Design evidence:
    - A-26015: Frontmatter Validator Architecture (Approach C, WRC 0.90)
    - S-26014: DevOps Consultant Assessment (SVA analysis, scope boundary)
"""

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import tiktoken
import yaml

from tools.scripts.git import detect_repo_root
from tools.scripts.paths import VALIDATION_EXCLUDE_DIRS, get_config_path

logger = logging.getLogger(__name__)


# ======================
# Data Classes
# ======================


@dataclass
class FrontmatterError:
    """Represents a frontmatter validation error or warning.

    error_type taxonomy (used by main() to separate blocking vs non-blocking):
        "missing_frontmatter" — file has governed extension but no YAML frontmatter present (blocking)
        "missing_field"      — required field absent (blocking)
        "invalid_format"     — field present but wrong format, e.g. bad date (blocking)
        "invalid_value"      — field value not in allowed set, e.g. unknown tag (blocking)
        "unknown_type"       — options.type not in conf.json types registry (blocking)
        "missing_type"       — frontmatter present but options.type absent (blocking)
        "namespace_warning"  — non-myst_native field at top level instead of options.* (non-blocking)

    main() treats "namespace_warning" as stderr-only; all others cause exit 1.
    """

    file_path: Path
    error_type: str  # see taxonomy above
    field: str | None  # which field failed (None for file-level errors)
    message: str  # agent-friendly: what's wrong + what would fix it
    config_source: str  # which config defines the rule, e.g. ".vadocs/conf.json → blocks.identity"


# ======================
# Configuration
# ======================

# Matches YAML frontmatter between --- fences at the start of a file.
# Same regex used in check_adr.py and check_evidence.py — will be consolidated
# in Phase 2 when domain scripts delegate to this module.
# We use a non-greedy match for the content and ensure the closing delimiter
# is followed by a newline to confirm it's on its own line.
FRONTMATTER_PATTERN = re.compile(r"^---\s*\n([\s\S]*?)---\s*\n", re.DOTALL)
DEFAULT_TOKEN_ENCODING = "cl100k_base"

# Config cache — keyed by doc_type string (or None for hub-only).
# Populated on first load_config_chain() call per type, cleared in tests
# via monkeypatch. Avoids re-reading JSON + re-parsing pyproject.toml per file.
_config_cache: dict[str | None, tuple[dict, dict | None]] = {}

# ---------------------------------------------------------------------------
# Module-level constants — loaded once at import time, monkeypatched in tests.
#
# These are derived from .vadocs/conf.json (the hub config). They provide
# fast lookup during validation without re-reading the config per file.
# The hub defines the complete type system (ADR-26042): field registry,
# block composition, type registry, tag vocabulary, date format.
# ---------------------------------------------------------------------------
REPO_ROOT: Path = detect_repo_root()
HUB_CONFIG_PATH: Path = get_config_path(REPO_ROOT)
HUB_CONFIG_REL: str = str(HUB_CONFIG_PATH.relative_to(REPO_ROOT))
HUB_CONFIG: dict = json.loads(HUB_CONFIG_PATH.read_text(encoding="utf-8"))

# Tags in hub are dict with descriptions — extract keys for validation set
VALID_TAGS: set[str] = set(HUB_CONFIG.get("tags", {}).keys())
# 10 types defined: 9 content + 1 service (see conf.json "types" registry)
VALID_TYPES: set[str] = set(HUB_CONFIG.get("types", {}).keys())
DATE_FORMAT_PATTERN: str = HUB_CONFIG.get("date_format", r"^\d{4}-\d{2}-\d{2}$")
# field_registry maps field names → {description, maintenance, myst_native}
FIELD_REGISTRY: dict = HUB_CONFIG.get("field_registry", {})
# blocks maps block names → list of field names (e.g. identity → [title, type, authors])
BLOCKS: dict = HUB_CONFIG.get("blocks", {})
# types maps type names → {blocks, required, optional}
TYPES: dict = HUB_CONFIG.get("types", {})


# ======================
# Main
# ======================


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Parse args, scan, validate, report, return exit code.

    When no args provided, resolves to [repo_root] for full-repo scan.

    Exit codes:
        0 — all files pass (warnings may still be printed to stderr)
        1 — one or more validation errors found

    Output:
        stdout — error report, one line per error with file:field:source format
        stderr — warnings (missing type, namespace) for agent visibility
    """
    # -- Argument parsing ------------------------------------------------
    parser = argparse.ArgumentParser(
        description="Validate frontmatter against .vadocs/ config chain (ADR-26042). Refer to the module docstring (accessible via --help) for the structural Dual-Block specification.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Files or directories to validate. Defaults to repo root.",
    )
    parser.add_argument(
        "--format",
        dest="fmt",
        choices=["md", "ipynb"],
        default="md",
        help="File extension to scan for in directories (default: md).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging for validation process.",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format='%(levelname)s: %(message)s'
    )

    # -- Resolve input paths ---------------------------------------------
    # Empty paths → scan from repo root (monkeypatched in tests)
    input_paths = [Path(p) for p in args.paths] if args.paths else [REPO_ROOT]
    files = scan_paths(input_paths, REPO_ROOT, fmt=args.fmt)

    # Load governance scope and exclusions from hub config
    governed_exts = HUB_CONFIG.get("governed_extensions", [])
    excludes = HUB_CONFIG.get("governance_excludes", {})
    exclude_dirs = excludes.get("dirs", [])
    exclude_files = excludes.get("files", [])

    # -- Validate each file -----------------------------------------------
    # NOTE: This loop intentionally does NOT call validate_frontmatter() directly.
    # validate_frontmatter() silently returns [] for files with no type — but
    # main() needs to print a WARNING for those files so agents see them.
    # The parse → resolve_type → validate_parsed pipeline is split here to
    # insert the warning step. Do not refactor to validate_frontmatter() without
    # preserving the warning behavior.
    all_errors: list[FrontmatterError] = []
    for file_path in files:
        logger.debug(f"Processing file: {file_path}")
        # Skip explicitly excluded files or directories
        if any(part in exclude_dirs for part in file_path.parts) or file_path.name in exclude_files:
            logger.debug(f"Skipping excluded file: {file_path}")
            continue

        content = file_path.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(content, file_path=file_path)

        # Files without frontmatter are checked against governed extensions.
        # If a file has a governed extension but no frontmatter, it's a blocking error.
        # Non-governed files (e.g. plain scripts) are silently skipped.
        if frontmatter is None:
            if file_path.suffix in governed_exts:
                all_errors.append(
                    FrontmatterError(
                        file_path=file_path,
                        error_type="missing_frontmatter",
                        field=None,
                        message="file has governed extension but no YAML frontmatter present — all governed files must have frontmatter to be subject to validation",
                        config_source=f"{HUB_CONFIG_REL} → governed_extensions",
                    )
                )
            continue

        # Files with frontmatter but no options.type: this is now a blocking error.
        # All governed files MUST declare their type to be subject to validation.
        # Without a type, the correct spoke config cannot be loaded and type-specific
        # rules cannot be enforced — this is a validation gap that must be closed.
        doc_type = resolve_type(frontmatter)
        if doc_type is None:
            logger.debug(f"Missing type for {file_path}: parsed frontmatter was {frontmatter}")
            all_errors.append(
                FrontmatterError(
                    file_path=file_path,
                    error_type="missing_type",
                    field="options.type",
                    message="frontmatter present but missing required 'options.type' — type determines which validation rules apply and is required for governance",
                    config_source=f"{HUB_CONFIG_REL} → field_registry.type",
                )
            )
            continue

        errors = validate_parsed_frontmatter(frontmatter, file_path, REPO_ROOT, content=content)
        all_errors.extend(errors)

    # -- Report errors to stdout ------------------------------------------
    for e in all_errors:
        # Format: file_path:field — message [config_source]
        # Agent-friendly: file path for navigation, field for quick fix,
        # config_source for rule lookup.
        field_part = f":{e.field}" if e.field else ""
        logger.error(f"{e.file_path}{field_part} — {e.message} [{e.config_source}]")

    if all_errors:
        logger.info(f"{'-'*80}")
        logger.info("DIAGNOSTIC TIP: If the error above seems misleading (e.g., 'missing type' "
                    "when the field is present), there may be a YAML syntax error in the "
                    "frontmatter block. Run the following command for detailed debug logs:")
        logger.info(f"  uv run python -m tools.scripts.check_frontmatter <file_path> -v")
        logger.info(f"{'-'*80}")

    # -- Exit code: 0 if no real errors, 1 otherwise ----------------------
    return 1 if all_errors else 0


# ======================
# Scanning
# ======================


def scan_paths(
    paths: list[Path], repo_root: Path, fmt: str = "md"
) -> list[Path]:
    """Resolve input paths to file list.

    Files are returned as-is. Directories are walked recursively,
    filtered by format extension and VALIDATION_EXCLUDE_DIRS.
    The fmt parameter controls which extension to glob for when scanning
    directories ('md' or 'ipynb'). Ignored for explicit file paths.
    """
    extension = f".{fmt}"
    files: list[Path] = []

    for path in paths:
        if path.is_file():
            # CRITICAL: Always check exclusions for explicit file arguments.
            # Prevents processing of files in external research repos when passed directly.
            if any(part in VALIDATION_EXCLUDE_DIRS for part in path.parts):
                continue
            files.append(path)
        elif path.is_dir():
            for child in sorted(path.rglob(f"*{extension}")):
                # Skip files inside excluded directories
                if any(part in VALIDATION_EXCLUDE_DIRS for part in child.parts):
                    continue
                files.append(child)

    return files


# ======================
# Validation — public
# ======================


def validate_frontmatter(
    file_path: Path, repo_root: Path
) -> list[FrontmatterError]:
    """Validate a single file's frontmatter against hub + spoke rules.

    Orchestrates: read file -> parse -> resolve type -> load configs -> check.
    Returns empty list if valid or if file is not governed.
    """
    content = file_path.read_text(encoding="utf-8")
    frontmatter = parse_frontmatter(content, file_path=file_path)
    if frontmatter is None:
        # If file has a governed extension but no frontmatter, it's a blocking error.
        governed_exts = HUB_CONFIG.get("governed_extensions", [])
        if file_path.suffix in governed_exts:
            return [
                FrontmatterError(
                    file_path=file_path,
                    error_type="missing_frontmatter",
                    field=None,
                    message="file has governed extension but no YAML frontmatter present — all governed files must have frontmatter to be subject to validation",
                    config_source=f"{HUB_CONFIG_REL} → governed_extensions",
                )
            ]
        return []
    return validate_parsed_frontmatter(frontmatter, file_path, repo_root, content=content)


def validate_parsed_frontmatter(
    frontmatter: dict, file_path: Path, repo_root: Path, content: str | None = None
) -> list[FrontmatterError]:
    """Validate already-parsed frontmatter dict against hub + spoke rules.

    For use by domain scripts (check_adr.py, check_evidence.py) that have
    already parsed frontmatter for their own structural validation. This
    avoids double-parsing during the migration period where both the domain
    script and check_frontmatter.py run on the same files.

    Returns [FrontmatterError] for files with frontmatter but no options.type —
    all governed files must declare their type to be validated. The type
    determines which spoke config is loaded, which required fields apply, and
    which status/severity values are allowed. Without a type, validation
    cannot proceed meaningfully.
    """
    # Step 1: Determine document type from options.type field.
    # Files without options.type are not governed — this is now a blocking error.
    # Every file with frontmatter MUST declare its type so that:
    #   1. The correct spoke config (.vadocs/types/<type>.conf.json) is loaded
    #   2. Type-specific required fields, statuses, and rules are enforced
    #   3. The file is subject to governance — no silent bypasses
    # Without a type, schema validation cannot proceed meaningfully.
    doc_type = resolve_type(frontmatter)
    if doc_type is None:
        return [
            FrontmatterError(
                file_path=file_path,
                error_type="missing_type",
                field="options.type",
                message=f"frontmatter present but missing required 'options.type' — type determines which validation rules apply. To fix: add 'options:\\n  type: <type>' to the frontmatter (valid types: {', '.join(sorted(VALID_TYPES))})",
                config_source=".vadocs/conf.json → field_registry.type",
            )
        ]

    # Step 2: Reject unknown types early — all 10 valid types are in conf.json.
    if doc_type not in VALID_TYPES:
        return [
            FrontmatterError(
                file_path=file_path,
                error_type="unknown_type",
                field="options.type",
                message=f"unknown type '{doc_type}', expected one of {sorted(VALID_TYPES)}. To fix: check for typos in 'options.type'",
                config_source=f"{HUB_CONFIG_REL} → types",
            )
        ]

    # Step 3: Load the config chain for this type.
    # Hub config is always loaded. Spoke config loaded only for types that have
    # a .conf.json in .vadocs/types/ (currently: adr, evidence). Types without
    # a spoke config (tutorial, guide, etc.) are validated against hub rules only.
    hub, spoke = load_config_chain(repo_root, doc_type)

    # Step 4: Compute the full required field set from three sources (union merge).
    # See _get_required_fields docstring for the merge semantics (ADR-26042).
    required = _get_required_fields(doc_type, hub, spoke)
    errors: list[FrontmatterError] = []

    # Step 5: Check required field presence (at top level OR under options.*).
    for field in required:
        if not _field_present(frontmatter, field):
            block_source = _find_field_block(field, doc_type, hub)
            errors.append(
                FrontmatterError(
                    file_path=file_path,
                    error_type="missing_field",
                    field=field,
                    message=f"missing required field '{field}' — To fix: add '{field}: <value>' to the frontmatter (or under options.* if not MyST-native)",
                    config_source=block_source,
                )
            )

    # Step 6: Validate values of present fields (dates, tags, status, authors).
    for field in required:
        value = _get_field_value(frontmatter, field)
        if value is None:
            continue
        error = _validate_field_value(field, value, file_path, hub, spoke, content=content)
        if error is not None:
            errors.append(error)

    # Step 7: Check options.* namespace compliance (warnings only until Phase 1.15).
    errors.extend(_check_options_namespace(frontmatter, file_path, hub))

    # Step 8: Reject governed fields in non-governed blocks.
    if content is not None:
        errors.extend(_check_governed_field_placement(content, file_path, hub))

    return errors


# ======================
# Validation — internal
# ======================


def calculate_tokens(text: str) -> int:
    """Calculate token count using the project's default encoding."""
    encoding = tiktoken.get_encoding(DEFAULT_TOKEN_ENCODING)
    return len(encoding.encode(text, disallowed_special=()))


def _field_present(frontmatter: dict, field: str) -> bool:
    """Check if a field exists at top level or under options.*

    Pre-migration compatibility: non-myst_native fields like id, status are
    currently at top level in existing files. After Phase 1.15 they move to
    options.*. This function checks both locations so validation works in
    both the pre- and post-migration state.
    """
    if field in frontmatter:
        return True
    options = frontmatter.get("options", {})
    if isinstance(options, dict):
        # Check both the full field name and the name without 'options.' prefix
        if field in options or field.replace("options.", "") in options:
            return True
    return False


def _get_field_value(frontmatter: dict, field: str) -> Any:
    """Get field value, checking top level first, then options.*

    Top level takes precedence — if a field exists at both levels (shouldn't
    happen in well-formed files), the top-level value is used for validation.
    """
    if field in frontmatter:
        return frontmatter[field]
    options = frontmatter.get("options", {})
    if isinstance(options, dict) and field in options:
        return options[field]
    return None


def _find_field_block(field: str, doc_type: str, hub_config: dict) -> str:
    """Determine which config source requires this field.

    Used for agent-friendly error messages — tells the agent exactly which
    config file and key defines the requirement so it can look up the rule.
    Search order: hub blocks → hub types.required → spoke required_fields.
    """
    blocks = hub_config.get("blocks", {})
    for block_name, block_fields in blocks.items():
        if field in block_fields:
            return f"{HUB_CONFIG_REL} → blocks.{block_name}"
    types = hub_config.get("types", {})
    type_def = types.get(doc_type, {})
    if field in type_def.get("required", []):
        return f"{HUB_CONFIG_REL} → types.{doc_type}.required"
    return f".vadocs/types/{doc_type}.conf.json → required_fields"


def _get_required_fields(
    doc_type: str, hub_config: dict, spoke_config: dict | None
) -> set[str]:
    """Merge hub block fields + hub types.required + spoke required_fields.

    Three sources, union merge (additive inheritance per ADR-26042):
    1. Hub blocks — expand field names for this type's block list
    2. Hub types.<type>.required — type-specific fields from hub
    3. Spoke required_fields — operational required fields from spoke config
    """
    blocks = hub_config.get("blocks", {})
    types = hub_config.get("types", {})
    type_def = types.get(doc_type, {})

    required: set[str] = set()

    # 1. Expand block composition
    for block_name in type_def.get("blocks", []):
        required.update(blocks.get(block_name, []))

    # 2. Hub type-specific required
    required.update(type_def.get("required", []))

    # 3. Spoke required_fields (and common_required_fields for sub-types)
    if spoke_config is not None:
        required.update(spoke_config.get("required_fields", []))
        required.update(spoke_config.get("common_required_fields", []))

    return required


def _validate_field_value(
    field: str,
    value: Any,
    file_path: Path,
    hub_config: dict,
    spoke_config: dict | None,
    content: str | None = None,
) -> FrontmatterError | None:
    """Check a single field's value against config rules.

    Dispatches to field-specific validation based on field name.
    Returns None if the value is valid, or a FrontmatterError describing
    exactly what's wrong, what was expected, and which config defines the rule.

    Validation rules come from two sources:
    - Hub config: date_format regex, tag vocabulary, authors format, field_registry
    - Spoke config: allowed statuses, severity values (type-specific)
    """
    # Token size accuracy check
    if field == "token_size":
        if content is None:
            return None  # Cannot validate accuracy without content

        # Check if the file extension is excluded from token_size validation via hub config.
        # This prevents conflicts between .md and .ipynb pairs.
        token_exclusions = HUB_CONFIG.get("token_size_exclusions", [])
        if file_path.suffix in token_exclusions:
            return None

        try:
            token_val = int(value)
        except (ValueError, TypeError):
            return FrontmatterError(
                file_path=file_path,
                error_type="invalid_format",
                field="token_size",
                message=f"token_size must be an integer, got '{value}'",
                config_source=f"{HUB_CONFIG_REL} → field_registry.token_size",
            )

        actual_count = calculate_tokens(content)

        # Contract: We allow a small margin (10 tokens) to account for minor
        # tokenizer version differences or insignificant whitespace changes
        # that don't impact context budgeting, while still catching
        # outdated values that need synchronization.
        if abs(token_val - actual_count) > 10:
            return FrontmatterError(
                file_path=file_path,
                error_type="invalid_value",
                field="token_size",
                message=f"declared token_size '{value}' differs from actual count '{actual_count}' — To fix: run 'uv run tools/scripts/update_token_counts.py {file_path}' and commit again",
                config_source=f"{HUB_CONFIG_REL} → field_registry.token_size",
            )

    # Date format validation (date, birth) — regex from hub config
    if field in ("date", "birth"):
        date_pattern = hub_config.get("date_format", r"^\d{4}-\d{2}-\d{2}$")
        # yaml.safe_load converts dates to datetime.date — stringify for regex
        str_value = str(value)
        if not re.match(date_pattern, str_value):
            return FrontmatterError(
                file_path=file_path,
                error_type="invalid_format",
                field=field,
                message=f"field '{field}' has value '{str_value}', expected format YYYY-MM-DD. To fix: ensure the date is quoted in YAML (e.g., date: \"2026-01-01\") to prevent automatic type conversion",
                config_source=f"{HUB_CONFIG_REL} → date_format",
            )

    # Tags validation — each tag must exist in hub vocabulary (.vadocs/conf.json → tags)
    if field == "tags":
        valid_tags = set(hub_config.get("tags", {}).keys())
        if isinstance(value, list):
            invalid = [t for t in value if t not in valid_tags]
            if invalid:
                return FrontmatterError(
                    file_path=file_path,
                    error_type="invalid_value",
                    field="tags",
                    message=f"unknown tags {invalid}, expected from {sorted(valid_tags)}",
                    config_source=f"{HUB_CONFIG_REL} → tags",
                )

    # Status validation — allowed values defined per doc type in spoke config.
    # ADR: proposed/accepted/rejected/superseded/deprecated
    # Evidence: active/absorbed/superseded (analyses), active/resolved/superseded (retros)
    if field == "status" and spoke_config is not None:
        allowed = spoke_config.get("statuses", [])
        if allowed and value not in allowed:
            return FrontmatterError(
                file_path=file_path,
                error_type="invalid_value",
                field="status",
                message=f"field 'status' has value '{value}', expected one of {allowed}",
                config_source=f".vadocs/types/{spoke_config.get('parent_config', '?')!s} → statuses",
            )

    # Severity validation — only applies to evidence retrospectives.
    # The evidence spoke config nests severity under artifact_types.retrospective,
    # not at the top level. This is a quirk of the evidence config structure.
    # NOTE: Currently unreachable because load_config_chain("retrospective")
    # finds no .vadocs/types/retrospective.conf.json — severity rules are inside
    # evidence.conf.json. check_evidence.py handles severity validation today.
    # Will become reachable when spoke config resolution maps sub-types to
    # their parent spoke (Phase 2 config chain enhancement).
    if field == "severity" and spoke_config is not None:  # pragma: no cover
        allowed = spoke_config.get("severity", [])
        if not allowed and "artifact_types" in spoke_config:
            for at in spoke_config["artifact_types"].values():
                if "severity" in at:
                    allowed = at["severity"]
                    break
        if allowed and value not in allowed:
            return FrontmatterError(
                file_path=file_path,
                error_type="invalid_value",
                field="severity",
                message=f"field 'severity' has value '{value}', expected one of {allowed}",
                config_source=".vadocs/types/evidence.conf.json → severity",
            )

    # Authors format — MyST spec requires list of {name, email} objects.
    # Ecosystem minimum (conf.json → field_registry.authors): both name and
    # email required for every author entry.
    if field == "authors":
        if not isinstance(value, list):
            return FrontmatterError(
                file_path=file_path,
                error_type="invalid_format",
                field="authors",
                message=f"field 'authors' must be a list of {{name, email}} objects, got {type(value).__name__}",
                config_source=f"{HUB_CONFIG_REL} → field_registry.authors",
            )
        for i, author in enumerate(value):
            if not isinstance(author, dict):
                return FrontmatterError(
                    file_path=file_path,
                    error_type="invalid_format",
                    field="authors",
                    message=f"author[{i}] must be a {{name, email}} object, got {type(author).__name__}",
                    config_source=f"{HUB_CONFIG_REL} → field_registry.authors",
                )
            if "name" not in author or "email" not in author:
                missing = [k for k in ("name", "email") if k not in author]
                return FrontmatterError(
                    file_path=file_path,
                    error_type="invalid_format",
                    field="authors",
                    message=f"author[{i}] missing required keys: {missing}",
                    config_source=f"{HUB_CONFIG_REL} → field_registry.authors",
                )

    return None


def _check_governed_field_placement(
    content: str, file_path: Path, hub_config: dict
) -> list[FrontmatterError]:
    """Enforce that governed fields reside exclusively in the governed block.

    Governed fields (non-myst_native) must reside exclusively in the governed
    block (the one containing 'options.type'). If a governed field appears in
    any other block, it's a placement error (blocking).

    Example: 'token_size' appearing in the Jupytext block instead of the
    governed block.
    """
    errors: list[FrontmatterError] = []
    field_registry = hub_config.get("field_registry", {})
    governed_fields = {f for f, meta in field_registry.items() if not meta.get("myst_native", True)}

    # Find all YAML blocks at the start of the file
    blocks_data: list[dict] = []
    current_pos = 0
    while True:
        match = re.search(
            r"^\s*---\s*\n(.*?)\n---\s*\n",
            content[current_pos:],
            re.DOTALL | re.MULTILINE,
        )
        if not match:
            break

        block_text = match.group(1)
        current_pos += match.end()

        try:
            data = yaml.safe_load(block_text)
            if isinstance(data, dict):
                blocks_data.append(data)
        except yaml.YAMLError:
            pass

        if not re.match(r"^\s*---", content[current_pos:], re.MULTILINE):
            break

    if not blocks_data:
        return []

    # Identify the governed block (the one with options.type)
    governed_block_idx: int | None = None
    for idx, data in enumerate(blocks_data):
        options = data.get("options")
        if isinstance(options, dict) and "type" in options:
            governed_block_idx = idx
            break

    # If no governed block is found, any governed field is misplaced
    # (though main() already flags missing_type, we still check for leakages)
    for idx, data in enumerate(blocks_data):
        if idx == governed_block_idx:
            continue

        # Check top-level keys
        for key in data:
            if key in governed_fields:
                errors.append(
                    FrontmatterError(
                        file_path=file_path,
                        error_type="misplaced_field",
                        field=key,
                        message=f"governed field '{key}' is misplaced in a non-governed block — it must reside exclusively in the governed block (the one with options.type)",
                        config_source=f"{HUB_CONFIG_REL} → field_registry",
                    )
                )

        # Check keys inside 'options'
        options = data.get("options")
        if isinstance(options, dict):
            for key in options:
                if key in governed_fields:
                    errors.append(
                        FrontmatterError(
                            file_path=file_path,
                            error_type="misplaced_field",
                            field=key,
                            message=f"governed field '{key}' is misplaced in a non-governed block — it must reside exclusively in the governed block (the one with options.type)",
                            config_source=f"{HUB_CONFIG_REL} → field_registry",
                        )
                    )

    return errors


def _check_options_namespace(
    frontmatter: dict, file_path: Path, hub_config: dict
) -> list[FrontmatterError]:
    """Enforce that non-myst_native fields reside under options.*

    ADR-26042 says: MyST-native fields (title, authors, date, description,
    tags) live at top level; all others belong under options.*. The hub config
    field_registry has a myst_native boolean per field.

    Returns invalid_namespace (blocking error) to ensure clean top-level
    frontmatter.
    """
    errors: list[FrontmatterError] = []
    field_registry = hub_config.get("field_registry", {})
    logger.debug(f"Checking namespace for {file_path}")
    logger.debug(f"Frontmatter keys: {list(frontmatter.keys())}")
    logger.debug(f"Field registry keys: {list(field_registry.keys())}")

    for key in frontmatter:
        if key == "options":
            continue
        if key in field_registry and not field_registry[key].get("myst_native", False):
            logger.debug(f"Found non-myst_native field at top level: {key}")
            errors.append(
                FrontmatterError(
                    file_path=file_path,
                    error_type="invalid_namespace",
                    field=key,
                    message=f"field '{key}' is not MyST-native and must be under options.*. To fix: move the field into the 'options' block",
                    config_source=".vadocs/conf.json → field_registry",
                )
            )

    return errors


# ======================
# Parsing
# ======================


def parse_frontmatter(content: str, file_path: Path | None = None) -> dict | None:
    """Extract YAML frontmatter from markdown or notebook content.

    Supports multiple frontmatter blocks at the start of the file (e.g. Jupytext
    metadata followed by governed document frontmatter). Merges all consecutive
    YAML blocks found at the start of the file into a single dictionary.

    Returns parsed dict, or None if no frontmatter found.
    """
    # .ipynb files store frontmatter in the first markdown cell's source.
    if file_path is not None and file_path.suffix == ".ipynb":
        try:
            notebook = json.loads(content)
        except (json.JSONDecodeError, ValueError):
            return None
        cells = notebook.get("cells", [])
        if not cells or cells[0].get("cell_type") != "markdown":
            return None
        source = cells[0].get("source", [])
        content = "".join(source) if isinstance(source, list) else source

    blocks = []
    current_pos = 0
    # Use split to find all blocks between fences. Fences must be on their own line.
    # If the file starts with a fence, parts[0] is empty, and parts[1, 3, ...] are the blocks.
    if content.strip().startswith("---"):
        parts = re.split(r"^\s*---\s*$", content, flags=re.MULTILINE)
        # The first part must be empty for the file to start with a fence.
        if not parts[0].strip():
            blocks = []
            # Collect the first block
            if len(parts) > 1:
                blocks.append(parts[1].strip("\n"))
                # Collect the second block ONLY if the gap between first and second is empty
                # (Dual-Block Pattern: Block 1 -> fence -> Block 2)
                if len(parts) > 3 and not parts[2].strip():
                    blocks.append(parts[3].strip("\n"))
            # We only support up to 2 blocks (Jupytext + Project) at the start.
            # Anything after that is treated as body content.


    if not blocks:
        return None

    # Parser Transparency: log discovered blocks for debuggability
    file_id = str(file_path) if file_path else "content"
    logger.debug(f"Found {len(blocks)} YAML blocks in {file_id}")
    for i, block in enumerate(blocks):
        logger.debug(f"Block {i} content:\n---\n{block}\n---")

    merged_data: dict = {}
    has_valid_block = False

    for i, block_text in enumerate(blocks):
        try:
            data = yaml.safe_load(block_text)
            if data is None:
                logger.warning(f"YAML block {i} in {file_id} is empty or contains only whitespace")
                continue
            if isinstance(data, dict):
                merged_data.update(data)
                has_valid_block = True
            else:
                logger.warning(f"YAML block {i} in {file_id} is not a dictionary (got {type(data).__name__})")
        except yaml.YAMLError as e:
            logger.warning(f"YAML syntax error in block {i} of {file_id}: {e}")
            continue

    return merged_data if has_valid_block else None

def resolve_type(frontmatter: dict) -> str | None:
    """Read options.type from parsed frontmatter.

    Returns type string, or None if not present.
    """
    logger.debug(f"Resolving type from frontmatter: {frontmatter}")
    options = frontmatter.get("options")
    if not isinstance(options, dict):
        logger.debug("Field 'options' is missing or not a dictionary")
        return None
    doc_type = options.get("type")
    if doc_type is None:
        logger.debug("Field 'options.type' is missing")
    return doc_type


# ======================
# Config Loading
# ======================


def load_config_chain(
    repo_root: Path, doc_type: str | None = None
) -> tuple[dict, dict | None]:
    """Load hub config and optional child config for a document type.

    Uses paths.get_config_path() for config discovery.
    Returns (hub_config, child_config_or_None).
    Configs are cached per doc_type after first load.

    Sub-type resolution (TD-005):
    When doc_type is a sub-type (e.g., "analysis", "retrospective", "source"),
    the parent config (evidence) is loaded, and the sub_type_rules are extracted
    from artifact_types.<sub_type>. The returned child_config contains the merged
    common rules + sub-type-specific rules.
    """
    if doc_type in _config_cache:
        return _config_cache[doc_type]

    # get_config_path reads pyproject.toml [tool.vadocs].config_dir each call.
    # We cache per doc_type so pyproject.toml is parsed at most once per type
    # per run, not once per file.
    hub_path = get_config_path(repo_root)
    hub = json.loads(hub_path.read_text(encoding="utf-8"))

    child_config = None
    if doc_type is not None:
        # Sub-type → parent config resolution (TD-005)
        # paths.get_config_path() already resolves sub-types to parent config
        child_path = get_config_path(repo_root, doc_type)
        if child_path.exists():
            child_config = json.loads(child_path.read_text(encoding="utf-8"))
            # Extract sub-type rules if this is a sub-type (TD-005)
            child_config = _resolve_subtype_rules(child_config, doc_type)

    _config_cache[doc_type] = (hub, child_config)
    return hub, child_config


def _resolve_subtype_rules(
    parent_config: dict, doc_type: str
) -> dict | None:
    """Extract sub-type rules from parent config's artifact_types (TD-005).

    For evidence sub-types (analysis, retrospective, source), the parent
    config contains artifact_types.<sub_type> with type-specific rules.
    This function merges common rules with sub-type-specific rules.

    Args:
        parent_config: Loaded parent config (e.g., evidence.conf.json)
        doc_type: The sub-type name (e.g., "analysis")

    Returns:
        Merged config with common_required_fields + sub-type required_fields,
        or None if doc_type is not a sub-type or has no artifact_types entry.
    """
    artifact_types = parent_config.get("artifact_types", {})
    if doc_type not in artifact_types:
        return parent_config  # Not a sub-type, return as-is

    sub_type_rules = artifact_types[doc_type]
    # Merge common + sub-type required fields
    common_fields = parent_config.get("common_required_fields", [])
    sub_type_fields = sub_type_rules.get("required_fields", [])
    merged_fields = list(common_fields) + list(sub_type_fields)

    # Return merged config
    result = dict(parent_config)
    result["common_required_fields"] = merged_fields
    result["artifact_type"] = doc_type  # Mark which sub-type we resolved
    return result


# ======================
# Entry Point
# ======================

if __name__ == "__main__":
    sys.exit(main())
