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
        "broken_dual_block"     — missing separator fence between jupytext and project blocks (blocking)
        "invalid_field"      — field present but not defined in hub registry (blocking)
        "invalid_namespace"  — non-myst_native field at top level instead of options.* (blocking)
        "invalid_order"      — fields present in non-canonical sequence (blocking)

    all error_types cause exit 1.
    """,

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
        
        # Skip files based on:
        # 1. Hub-defined governance exclusions (conf.json)
        # 2. Centralized validation exclusions (paths.py -> includes external repos)
        hub_excludes = HUB_CONFIG.get("governance_excludes", {})
        exclude_dirs = hub_excludes.get("dirs", [])
        exclude_files = hub_excludes.get("files", [])
        
        if any(part in exclude_dirs for part in file_path.parts) or \
           file_path.name in exclude_files or \
           any(excl in str(file_path) for excl in VALIDATION_EXCLUDE_DIRS):
            logger.debug(f"Skipping excluded file: {file_path}")
            continue

        content = file_path.read_text(encoding="utf-8")
        frontmatter, block_count, anomalies = parse_frontmatter(content, file_path=file_path)

        # Structural anomalies detected during parsing (e.g. broken Dual-Block pattern, YAML syntax errors)
        # These must be checked first, as they can occur even if frontmatter is None (asymmetric fences).
        for anomaly in anomalies:
            if anomaly == "broken_dual_block":
                all_errors.append(
                    FrontmatterError(
                        file_path=file_path,
                        error_type="broken_dual_block",
                        field=None,
                        message="Broken Dual-Block pattern: The project metadata block starts without an opening '---' fence. To fix: add '--- \\n ---' between the Jupytext block and the project metadata",
                        config_source=f"{HUB_CONFIG_REL} → structural_spec",
                    )
                )
            elif anomaly == "invalid_yaml":
                all_errors.append(
                    FrontmatterError(
                        file_path=file_path,
                        error_type="invalid_yaml",
                        field=None,
                        message="YAML syntax error in frontmatter block — the file is corrupted and cannot be validated. To fix: check for indentation errors or missing colons in the YAML frontmatter",
                        config_source=f"{HUB_CONFIG_REL} → structural_spec",
                    )
                )

        # Files without frontmatter are checked against governed extensions.
        # If a file has a governed extension but no frontmatter, it's a blocking error.
        # Non-governed files (e.g. plain scripts) are silently skipped.
        if frontmatter is None:
            # If we already found a structural anomaly (like asymmetric fences), 
            # we don't also report it as 'missing' to avoid redundant/confusing errors.
            if not anomalies:
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

        # Files with frontmatter but no options.type: this is now a blocking error.
        # All governed files MUST declare their type to be subject to validation.
        # Without a type, the correct spoke config cannot be loaded and type-specific
        # rules cannot be enforced — this is a validation gap that must be closed.
        doc_type = resolve_type(frontmatter)
        if doc_type is None:
            logger.debug(f"Missing type for {file_path}: parsed frontmatter was {frontmatter}")
            type_field = _get_type_field_name()
            all_errors.append(
                FrontmatterError(
                    file_path=file_path,
                    error_type="missing_type",
                    field=f"options.{type_field}",
                    message=f"frontmatter present but missing required 'options.{type_field}' — type determines which validation rules apply and is required for governance. To fix: add 'options:\\n  {type_field}: <type>' to the frontmatter. If the file has a paired .ipynb, use the Dual-Block pattern (separate jupytext block from project metadata with --- \\n ---) to avoid synchronization stripping",
                    config_source=f"{HUB_CONFIG_REL} → field_registry.{type_field}",
                )
            )
            continue

        errors = validate_parsed_frontmatter(frontmatter, file_path, REPO_ROOT, content=content, block_count=block_count)
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
    frontmatter, block_count, anomalies = parse_frontmatter(content, file_path=file_path)
    logger.debug(f"Validating {file_path}: frontmatter={frontmatter}, blocks={block_count}, anomalies={anomalies}")

    # 1. Prioritize structural anomalies (including YAML syntax errors)
    # This ensures that corrupted frontmatter is reported as a syntax error
    # rather than a 'missing' frontmatter error.
    errors = []
    for anomaly in anomalies:
        if anomaly == "invalid_yaml":
            errors.append(
                FrontmatterError(
                    file_path=file_path,
                    error_type="invalid_yaml",
                    field=None,
                    message="Frontmatter contains invalid YAML syntax. To fix: check for missing colons, incorrect indentation, or unquoted special characters in strings.",
                    config_source=f"{HUB_CONFIG_REL} → structural_spec",
                )
            )
        elif anomaly == "broken_dual_block":
            errors.append(
                FrontmatterError(
                    file_path=file_path,
                    error_type="broken_dual_block",
                    field=None,
                    message="Broken Dual-Block pattern: The project metadata block starts without an opening '---' fence. To fix: add '--- \\n ---' between the Jupytext block and the project metadata",
                    config_source=f"{HUB_CONFIG_REL} → structural_spec",
                )
            )

    if errors:
        return errors

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

    errors.extend(validate_parsed_frontmatter(frontmatter, file_path, repo_root, content=content, block_count=block_count))
    return errors


def _check_key_order(frontmatter: dict, file_path: Path) -> list[FrontmatterError]:
    """Enforce the canonical sequence of top-level YAML keys (ADR-26042).

    Canonical order: id > title > authors > date > description > tags > status > superseded_by > options.
    Only fields present in the frontmatter are checked for relative order.
    """
    canonical_order = [
        "id", "title", "authors", "date", "description", "tags", "status", "superseded_by", "options"
    ]
    # Extract only keys that are part of the canonical set, preserving current order
    present_canonical_keys = [k for k in frontmatter.keys() if k in canonical_order]

    # Check if the extracted keys match their relative order in the canonical list
    # We can do this by comparing the index of each key in the canonical list
    indices = [canonical_order.index(k) for k in present_canonical_keys]

    if indices != sorted(indices):
        # Identify the first pair that is out of order for a better error message
        for i in range(len(present_canonical_keys) - 1):
            k1, k2 = present_canonical_keys[i], present_canonical_keys[i+1]
            if canonical_order.index(k1) > canonical_order.index(k2):
                return [
                    FrontmatterError(
                        file_path=file_path,
                        error_type="invalid_order",
                        field=None,
                        message=f"Fields present in non-canonical sequence: '{k1}' appears before '{k2}'. "
                                f"Canonical order is: {', '.join(canonical_order)}",
                        config_source=f"{HUB_CONFIG_REL} → structural_spec",
                    )
                ]
    return []


def validate_parsed_frontmatter(
    frontmatter: dict,
    file_path: Path,
    repo_root: Path,
    content: str | None = None,
    block_count: int = 1,
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
    errors: list[FrontmatterError] = []

    # Step 0: Enforce Dual-Block pattern if Jupytext metadata is present.
    # If 'jupytext' is found in the merged frontmatter but only one block was parsed,
    # the governance metadata has been merged into the Jupytext block.
    if "jupytext" in frontmatter and block_count < 2:
        errors.append(
            FrontmatterError(
                file_path=file_path,
                error_type="merged_blocks",
                field=None,
                message="Jupytext metadata and project governance metadata are merged into a single block — this violates the Dual-Block pattern and will cause data loss during Jupytext sync. To fix: separate the jupytext block from the project metadata with '--- \\n ---'",
                config_source=f"{HUB_CONFIG_REL} → structural_spec",
            )
        )

    # Enforce canonical key order (id > title > authors > ...)
    errors.extend(_check_key_order(frontmatter, file_path))

    # Step 1: Determine document type from the configured type field.
    # Files without this field are not governed — this is now a blocking error.
    # Every file with frontmatter MUST declare its type so that:
    #   1. The correct spoke config (.vadocs/types/<type>.conf.json) is loaded
    #   2. Type-specific required fields, statuses, and rules are enforced
    #   3. The file is subject to governance — no silent bypasses
    # Without a type, schema validation cannot proceed meaningfully.
    doc_type = resolve_type(frontmatter)
    if doc_type is None:
        type_field = _get_type_field_name()
        errors.append(
            FrontmatterError(
                file_path=file_path,
                error_type="missing_type",
                field=f"options.{type_field}",
                message=f"frontmatter present but missing required 'options.{type_field}' — type determines which validation rules apply. To fix: add 'options:\\n  {type_field}: <type>' to the frontmatter (valid types: {', '.join(sorted(VALID_TYPES))}). If the file has a paired .ipynb, use the Dual-Block pattern (separate jupytext block from project metadata with --- \\n ---) to avoid synchronization stripping",
                config_source=f"{HUB_CONFIG_REL} → field_registry.{type_field}",
            )
        )
        return errors

    # Step 2: Reject unknown types early — all 10 valid types are in conf.json.
    if doc_type not in VALID_TYPES:
        type_field = _get_type_field_name()
        return [
            FrontmatterError(
                file_path=file_path,
                error_type="unknown_type",
                field=f"options.{type_field}",
                message=f"unknown type '{doc_type}', expected one of {sorted(VALID_TYPES)}. To fix: check for typos in 'options.{type_field}'",
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

    # Step 6: Validate values of all present governed fields.
    # We validate any field present in the frontmatter that is defined in the hub registry,
    # regardless of whether it is marked as 'required' for this specific doc type.
    # This ensures that optional fields (like 'id' in guides) still follow global format rules.
    all_present_fields = set()
    for k in frontmatter:
        all_present_fields.add(k)
    options = frontmatter.get("options")
    if isinstance(options, dict):
        for k in options:
            all_present_fields.add(k)

    allowed = _get_allowed_fields(doc_type, hub, spoke)
    for field in all_present_fields:
        # Only validate fields that are governed (defined in hub registry)
        if field not in hub.get("field_registry", {}):
            continue
        
        if field not in allowed:
            errors.append(
                FrontmatterError(
                    file_path=file_path,
                    error_type="invalid_field",
                    field=field,
                    message=f"governed field '{field}' is not permitted for type '{doc_type}' — To fix: remove it or add it to the allow-list in the config",
                    config_source=f"{HUB_CONFIG_REL} → types.{doc_type}",
                )
            )
            continue

        value = _get_field_value(frontmatter, field)
        if value is None:
            continue
        error = _validate_field_value(field, value, file_path, hub, spoke, doc_type, content=content)
        if error is not None:
            errors.append(error)

    # Step 7: Check options.* namespace compliance (warnings only until Phase 1.15).
    errors.extend(_check_options_namespace(frontmatter, file_path, hub, doc_type))

    # Step 8: Unknown field detection ( forbid anything not in registry/infra )
    errors.extend(_check_unknown_fields(frontmatter, file_path, hub))

    # Step 9: Reject governed fields in non-governed blocks.
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

def _get_allowed_fields(
    doc_type: str, hub_config: dict, spoke_config: dict | None
) -> set[str]:
    """Compute the union of all permitted fields for this document type.

    Permitted fields include:
    1. Fields from all blocks assigned to this type in the hub.
    2. Fields explicitly marked as 'required' or 'optional' in the hub type def.
    3. Fields explicitly marked as 'required' or 'optional' in the spoke config.
    """
    blocks = hub_config.get("blocks", {})
    types = hub_config.get("types", {})
    type_def = types.get(doc_type, {})

    allowed: set[str] = set()

    # 1. Expand block composition
    for block_name in type_def.get("blocks", []):
        allowed.update(blocks.get(block_name, []))

    # 2. Hub type-specific requirements/optionals
    allowed.update(type_def.get("required", []))
    allowed.update(type_def.get("optional", []))

    # 3. Spoke requirements/optionals
    if spoke_config is not None:
        allowed.update(spoke_config.get("required_fields", []))
        allowed.update(spoke_config.get("optional_fields", []))
        allowed.update(spoke_config.get("common_required_fields", []))
        allowed.update(spoke_config.get("common_optional_fields", []))

    return allowed

def _validate_field_value(
    field: str,
    value: Any,
    file_path: Path,
    hub_config: dict,
    spoke_config: dict | None,
    doc_type: str,
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
    # ID prefix validation (ADR-26042 / S-S-o-T)
    if field == "id":
        str_id = str(value)
        type_def = hub_config.get("types", {}).get(doc_type, {})
        expected_prefix = type_def.get("prefix")

        # 1. Type has a defined prefix (e.g., ADR, A, S, R)
        if expected_prefix:
            if expected_prefix == "ADR":
                # Special rule for ADRs: allow 'ADR-123' or '123'
                if not re.match(r"^(ADR-)?\d+$", str_id):
                    return FrontmatterError(
                        file_path=file_path,
                        error_type="invalid_format",
                        field="id",
                        message=f"ADR ID '{str_id}' is invalid; expected 'ADR-NNN' or 'NNN' — To fix: change ID to follow 'ADR-NNN' or 'NNN' format",
                        config_source=f"{HUB_CONFIG_REL} → types.adr.prefix",
                    )
            else:
                # Standard prefix rule: must be 'PREFIX-NNN'
                pattern = rf"^{expected_prefix}-\d+$"
                if not re.match(pattern, str_id):
                    return FrontmatterError(
                        file_path=file_path,
                        error_type="invalid_format",
                        field="id",
                        message=f"ID '{str_id}' must start with '{expected_prefix}-NNN' for type '{doc_type}' — To fix: change ID to start with '{expected_prefix}-' followed by digits",
                        config_source=f"{HUB_CONFIG_REL} → types.{doc_type}.prefix",
                    )

        # 2. Type has no prefix (prefix is null), but ID uses a reserved one
        else:
            reserved = {
                t: def_.get("prefix") 
                for t, def_ in hub_config.get("types", {}).items() 
                if def_.get("prefix")
            }
            for res_type, res_pref in reserved.items():
                if str_id.startswith(f"{res_pref}-"):
                    return FrontmatterError(
                        file_path=file_path,
                        error_type="invalid_value",
                        field="id",
                        message=f"ID '{str_id}' uses a reserved prefix '{res_pref}-' (associated with the '{res_type}' type) forbidden for type '{doc_type}' — To fix: remove the reserved prefix from the ID",
                        config_source=f"{HUB_CONFIG_REL} → types.{res_type}.prefix",
                    )

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


def _check_unknown_fields(
    frontmatter: dict, file_path: Path, hub_config: dict
) -> list[FrontmatterError]:
    """Forbid any fields not defined in the hub registry or permitted infra-list.

    Checks both the top-level keys and the 'options' block.
    - Top-level: Must be in FIELD_REGISTRY (myst_native=true) or ALLOWED_INFRA_KEYS.
    - options.*: Must be in FIELD_REGISTRY.

    Returns [FrontmatterError] with error_type='invalid_field'.
    """
    errors: list[FrontmatterError] = []
    field_registry = hub_config.get("field_registry", {})
    # Permitted infrastructure keys that can exist at top level but aren't governed
    allowed_infra_keys = {"options", "jupytext", "kernelspec"}

    # 1. Check top-level keys
    for key in frontmatter:
        if key in allowed_infra_keys:
            continue
        
        if key not in field_registry:
            # Field is completely unknown to the SSoT
            # Use common_mistakes from config for dynamic suggestions
            common_mistakes = hub_config.get("common_mistakes", {})
            suggestion = "remove it"
            if key in common_mistakes:
                suggestion = f"replace it with the registered '{common_mistakes[key]}' field"

            errors.append(
                FrontmatterError(
                    file_path=file_path,
                    error_type="invalid_field",
                    field=key,
                    message=f"field '{key}' is not defined in the hub registry — unknown fields are forbidden — To fix: {suggestion}",
                    config_source=f"{HUB_CONFIG_REL} → field_registry",
                )
            )

    # 2. Check keys inside 'options'
    options = frontmatter.get("options")
    if isinstance(options, dict):
        for key in options:
            if key not in field_registry:
                errors.append(
                    FrontmatterError(
                        file_path=file_path,
                        error_type="invalid_field",
                        field=f"options.{key}",
                        message=f"field 'options.{key}' is not defined in the hub registry — unknown fields are forbidden",
                        config_source=f"{HUB_CONFIG_REL} → field_registry",
                    )
                )
            elif field_registry[key].get("myst_native", False):
                # Reserved MyST-native keys (like 'id') MUST NOT be in options
                errors.append(
                    FrontmatterError(
                        file_path=file_path,
                        error_type="invalid_namespace",
                        field=f"options.{key}",
                        message=f"reserved MyST-native field '{key}' found in options block — it must reside at the top level",
                        config_source=f"{HUB_CONFIG_REL} → field_registry",
                    )
                )

    return errors


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
    frontmatter: dict, file_path: Path, hub_config: dict, doc_type: str | None = None
) -> list[FrontmatterError]:
    """Enforce that non-myst_native fields reside under options.* and
    myst_native fields reside at the top level.

    ADR-26042 says: MyST-native fields (title, authors, date, description,
    tags) live at top level; all others belong under options.*. The hub config
    field_registry has a myst_native boolean per field.

    Exception (ADR-26042): 'status' and 'superseded_by' are permitted at the top
    level specifically for 'adr' type documents.

    Returns invalid_namespace (blocking error) to ensure clean top-level
    frontmatter and avoid MyST reserved key conflicts.
    """
    errors: list[FrontmatterError] = []
    field_registry = hub_config.get("field_registry", {})
    adr_top_level_exceptions = {"status", "superseded_by"}
    logger.debug(f"Checking namespace for {file_path}")

    # 1. Check top-level keys: Forbid non-native fields here
    for key in frontmatter:
        if key == "options":
            continue
        if key in field_registry:
            native = field_registry[key].get("myst_native", False)
            logger.debug(f"Field '{key}' native status: {native}")
            if not native:
                # Check for ADR exception
                if doc_type == "adr" and key in adr_top_level_exceptions:
                    continue

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

    # 2. Check options block: Forbid native fields here (prevents reserved key conflicts)
    options = frontmatter.get("options")
    if isinstance(options, dict):
        for opt_key in options:
            if opt_key in field_registry and field_registry[opt_key].get("myst_native", False):
                logger.debug(f"Found MyST-native field inside options: {opt_key}")
                errors.append(
                    FrontmatterError(
                        file_path=file_path,
                        error_type="invalid_namespace",
                        field=f"options.{opt_key}",
                        message=f"field '{opt_key}' is MyST-native and must reside at the top level, not under 'options'. To fix: move the field out of the 'options' block",
                        config_source=".vadocs/conf.json → field_registry",
                    )
                )

    return errors


# ======================
# Parsing
# ======================


def parse_frontmatter(content: str, file_path: Path | None = None) -> tuple[dict | None, int, list[str]]:
    """Extract YAML frontmatter from markdown or notebook content.

    Supports multiple frontmatter blocks at the start of the file (e.g. Jupytext
    metadata followed by governed document frontmatter). Merges all consecutive
    YAML blocks found at the start of the file into a single dictionary.

    Returns (merged_dict, block_count, anomalies), or (None, 0, []) if no frontmatter found.
    """
    # .ipynb files store frontmatter in the first markdown cell's source.
    if file_path is not None and file_path.suffix == ".ipynb":
        try:
            notebook = json.loads(content)
        except (json.JSONDecodeError, ValueError):
            return None, 0, []
        cells = notebook.get("cells", [])
        if not cells or cells[0].get("cell_type") != "markdown":
            return None, 0, []
        source = cells[0].get("source", [])
        content = "".join(source) if isinstance(source, list) else source

    blocks = []
    anomalies = []
    current_pos = 0
    
    # Use split to find all blocks between fences. Fences must be on their own line.
    parts = re.split(r"^[ \t]*---\s*$", content, flags=re.MULTILINE)
    logger.debug(f"SPLIT PARTS: {repr(parts)}")
    
    # Case 1: The file starts with a fence (Standard behavior)
    # We strip leading whitespace to allow for leading newlines before the first fence.
    if parts[0].strip() == "":
        # Collect the first block
        if len(parts) > 1:
            first_block_text = parts[1].strip("\n")
            blocks.append(first_block_text)

            # Determine if this is a Jupytext-only block (expects a second governance block)
            # or a full governance block (single-block file).
            try:
                first_block_data = yaml.safe_load(first_block_text)
                is_jupytext_only = (
                    isinstance(first_block_data, dict) and
                    "jupytext" in first_block_data and
                    "title" not in first_block_data
                )
            except yaml.YAMLError:
                is_jupytext_only = False

            if is_jupytext_only:
                # Collect the second block ONLY if the gap between first and second is empty
                if len(parts) > 3 and not parts[2].strip():
                    blocks.append(parts[3].strip("\n"))
                elif len(parts) > 2 and parts[2].strip():
                    # BROKEN DUAL-BLOCK: Jupytext block found, but metadata exists
                    # without an opening fence.
                    blocks.append(parts[2].strip("\n"))
                    anomalies.append("broken_dual_block")
    # Case 2: The file does NOT start with a fence but HAS one or more fences (Asymmetric)
    elif len(parts) > 1:
        # Found a closing fence without a preceding opening fence.
        # This is structural corruption.
        anomalies.append("broken_dual_block")
        return None, 0, anomalies
    # Case 3: No fences present at all
    else:
        return None, 0, []

    # We only support up to 2 blocks (Jupytext + Project) at the start.
    # Anything after that is treated as body content.

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
                anomalies.append("invalid_yaml")
        except yaml.YAMLError as e:
            logger.warning(f"YAML syntax error in block {i} of {file_id}: {e}")
            anomalies.append("invalid_yaml")
            continue

    return (merged_data if has_valid_block else None), len(blocks), anomalies

def _get_type_field_name() -> str:
    """Resolve the field name used for document type from the hub config.

    CONTRACT:
    1. The validator identifies the document type via a field in the 'options' block.
    2. To avoid hardcoding 'type', this function looks at HUB_CONFIG['blocks']['identity'].
    3. It returns the first field in that list that is NOT 'title' or 'authors'.
    4. ASSUMPTION: 'title' and 'authors' are stable identity fields; any other
       identity field is the document type discriminator.
    5. FALLBACK: Defaults to 'type' if the identity block is empty or only contains
       stable fields.

    Returns:
        The resolved field name (e.g., 'type' or 'doc_type').
    """
    identity_fields = HUB_CONFIG.get("blocks", {}).get("identity", [])
    for field in identity_fields:
        if field not in {"title", "authors"}:
            return field
    return "type"

def resolve_type(frontmatter: dict) -> str | None:
    """Read the document type field from parsed frontmatter dynamically.

    CONTRACT:
    1. This is the primary 'switch' for Hub-and-Spoke validation.
    2. The field name is resolved dynamically via _get_type_field_name() to ensure
       consistency with HUB_CONFIG.
    3. If the resolved field is missing from 'options', returns None.
    4. A return value of None marks the file as 'ungoverned' or 'missing type',
       which is a blocking error for all files with frontmatter.

    Args:
        frontmatter: The parsed YAML dictionary.

    Returns:
        The type string (e.g., 'adr', 'guide') or None if not found.
    """
    logger.debug(f"Resolving type from frontmatter: {frontmatter}")
    type_field = _get_type_field_name()
    options = frontmatter.get("options")
    if not isinstance(options, dict):
        logger.debug("Field 'options' is missing or not a dictionary")
        return None
    doc_type = options.get(type_field)
    if doc_type is None:
        logger.debug(f"Field 'options.{type_field}' is missing")
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
