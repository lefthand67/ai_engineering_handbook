#!/usr/bin/env python3
"""
Shared utilities for ADR (Architectural Decision Record) validation and indexing.

This module provides the Single Source of Truth (SSoT) for ADR domain models,
configuration loading, and common discovery patterns.
"""

import json
import logging
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# ======================
# Configuration
# ======================

_config_cache: dict[str, Any] | None = None

def load_adr_config() -> dict[str, Any]:
    """Load ADR configuration from JSON file (SSoT).

    Returns:
        Configuration dictionary.
    """
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    from tools.scripts.git import detect_repo_root
    from tools.scripts.paths import get_config_path

    config_path = get_config_path(detect_repo_root(), "adr")
    if not config_path.exists():
        raise FileNotFoundError(f"ADR config not found: {config_path}")

    with open(config_path, encoding="utf-8") as f:
        _config_cache = json.load(f)
    
    return _config_cache
def _build_status_sections(config: dict) -> dict[str, str]:
    """Build status-to-section mapping from config."""
    mapping = {}
    for section_name, statuses in config.get("sections", {}).items():
        for status in statuses:
            mapping[status] = section_name
    return mapping

def _build_status_corrections(config: dict) -> dict[str, str]:
    """Build typo-to-correct-status mapping from config."""
    mapping = {}
    for correct_status, typos in config.get("status_corrections", {}).items():
        for typo in typos:
            mapping[typo.lower()] = correct_status
    return mapping

def get_adr_constants():
    """
    Return ADR constants derived from the current config.
    This function is used to resolve constants dynamically,
    enabling test monkeypatching of the repo root.
    """
    config = load_adr_config()
    from tools.scripts.git import detect_repo_root
    root = detect_repo_root()

    return {
        "VALID_STATUSES": set(config.get("statuses", [])),
        "STATUS_SECTIONS": _build_status_sections(config),
        "DEFAULT_STATUS": config.get("default_status", "proposed"),
        "SECTION_ORDER": list(config.get("sections", {}).keys()),
        "STATUS_CORRECTIONS": _build_status_corrections(config),
        "REQUIRED_SECTIONS": config.get("required_sections", []),
        "ALLOWED_SECTIONS": set(config.get("allowed_sections", [])),
        "CONDITIONAL_SECTIONS": config.get("conditional_sections", {}),
        "CONDITIONAL_FIELDS": config.get("conditional_fields", {}),
        "MIN_CONDITIONAL_SECTION_WORDS": config.get("min_conditional_section_words", 3),
        "PRIMARY_TAG_SECTIONING": config.get("primary_tag_sectioning", False),
        "ADR_DIR": root / "architecture" / "adr",
        "INDEX_PATH": root / "architecture" / "adr_index.md",
    }

# Load config and build derived constants
_config = load_adr_config()
VALID_STATUSES: set[str] = set(_config.get("statuses", []))
STATUS_SECTIONS: dict[str, str] = _build_status_sections(_config)
DEFAULT_STATUS: str = _config.get("default_status", "proposed")
SECTION_ORDER: list[str] = list(_config.get("sections", {}).keys())
STATUS_CORRECTIONS: dict[str, str] = _build_status_corrections(_config)
REQUIRED_SECTIONS: list[str] = _config.get("required_sections", [])
ALLOWED_SECTIONS: set[str] = set(_config.get("allowed_sections", []))
CONDITIONAL_SECTIONS: dict[str, list[str]] = _config.get("conditional_sections", {})
CONDITIONAL_FIELDS: dict[str, dict] = _config.get("conditional_fields", {})
MIN_CONDITIONAL_SECTION_WORDS: int = _config.get("min_conditional_section_words", 3)
PRIMARY_TAG_SECTIONING: bool = _config.get("primary_tag_sectioning", False)

# Term reference configuration (SSoT: adr.conf.json)
_term_config = _config.get("term_reference", {})
TERM_SEPARATOR: str = _term_config.get("separator", "-")
BROKEN_TERM_PATTERN: re.Pattern = re.compile(
    _term_config.get("broken_pattern", r"\{term\}`ADR (\d+)`")
)

# Paths - Resolved dynamically to maintain SSoT
from tools.scripts.git import detect_repo_root
ROOT = detect_repo_root()
ADR_DIR = ROOT / "architecture" / "adr"
INDEX_PATH = ROOT / "architecture" / "adr_index.md"
EXCLUDED_FILES = {"adr_template.md"}

# Regex for index parsing
INDEX_ENTRY_PATTERN = re.compile(
    r"^ADR-(\d+)\s*\n:\s*\[([^\]]+)\]\(([^)]+)\)",
    re.MULTILINE,
)
GLOSSARY_BLOCK_PATTERN = re.compile(r":::\{glossary\}(.*?):::", re.DOTALL)
SECTION_HEADER_PATTERN = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)

# ======================
# Data Classes
# ======================

@dataclass
class AdrFile:
    """Represents an ADR file on disk."""
    path: Path
    number: int
    title: str
    status: str | None = None
    body_status: str | None = None
    frontmatter_title: str | None = None
    frontmatter: dict | None = None
    content: str | None = None

@dataclass
class IndexEntry:
    """Represents an entry in the ADR index."""
    number: int
    title: str
    link: str
    section: str | None = None

@dataclass
class ValidationError:
    """Represents a validation error."""
    number: int
    error_type: str
    message: str
    is_blocking: bool = True

@dataclass
class BrokenTermReference:
    """Represents a broken term reference in the documentation."""
    file_path: Path
    line_number: int
    adr_number: int
    original_text: str
    suggested_fix: str

# ======================
# Utilities
# ======================

def extract_body_status(content: str) -> str | None:
    """Extract status specifically from the markdown ## Status section."""
    # Note: STATUS_SECTION_PATTERN is defined in check_adr.py, but used here.
    # To avoid circularity, we define it here or import it.
    pattern = re.compile(r"^##\s+Status\s*\n+\s*(\w+)", re.MULTILINE)
    match = pattern.search(content)
    return match.group(1).lower() if match else None

def extract_status(content: str) -> str | None:
    """Extract status from ADR content (frontmatter priority)."""
    from tools.scripts import check_frontmatter
    frontmatter, *rest = check_frontmatter.parse_frontmatter(content)
    if frontmatter:
        # Check top-level first, then check under options
        status = frontmatter.get("status") or frontmatter.get("options", {}).get("status")
        if status:
            return str(status).lower()
    return extract_body_status(content)

def parse_adr_file(filepath: Path) -> AdrFile | None:
    """Parse a single ADR file into an AdrFile object. Returns None if not a valid ADR."""
    from tools.scripts import check_frontmatter
    try:
        content = filepath.read_text(encoding="utf-8")
        header_pattern = re.compile(r"^#\s+ADR-(\d+):\s+(.+)$", re.MULTILINE)
        match = header_pattern.search(content)
        if not match:
            return None

        number = int(match.group(1))
        title = match.group(2).strip()
        effective_status = extract_status(content)
        body_status = extract_body_status(content)
        frontmatter, *rest = check_frontmatter.parse_frontmatter(content)
        frontmatter_title = frontmatter.get("title") if frontmatter else None
        return AdrFile(
            path=filepath,
            number=number,
            title=title,
            status=effective_status,
            body_status=body_status,
            frontmatter_title=frontmatter_title,
            frontmatter=frontmatter,
            content=content,
        )
    except Exception as e:
        logger.warning(f"Failed to parse ADR file {filepath}: {e}")
        return None

def get_adr_files() -> list[AdrFile]:
    """Discover and parse all ADR files in the ADR directory."""
    adr_files = []
    if not ADR_DIR.exists():
        return []
    for filepath in ADR_DIR.glob("adr_*.md"):
        if filepath.name in EXCLUDED_FILES:
            continue
        adr = parse_adr_file(filepath)
        if adr:
            adr_files.append(adr)
    return sorted(adr_files, key=lambda x: x.number)

def parse_index() -> list[IndexEntry]:
    """Parse the ADR index file and extract all entries."""
    if not INDEX_PATH.exists():
        raise FileNotFoundError(f"Index file not found: {INDEX_PATH}")
    content = INDEX_PATH.read_text(encoding="utf-8")
    entries = []
    section_positions = []
    for match in SECTION_HEADER_PATTERN.finditer(content):
        name = match.group(1).strip("*")
        section_positions.append((match.start(), name))
    for glossary_match in GLOSSARY_BLOCK_PATTERN.finditer(content):
        glossary_start = glossary_match.start()
        glossary_content = glossary_match.group(1)
        current_section = None
        for pos, section_name in section_positions:
            if pos < glossary_start:
                current_section = section_name
            else:
                break
        for match in INDEX_ENTRY_PATTERN.finditer(glossary_content):
            number = int(match.group(1))
            title = match.group(2).strip()
            link = match.group(3).strip()
            entries.append(
                IndexEntry(number=number, title=title, link=link, section=current_section)
            )
    return entries

def get_staged_adr_files() -> list[AdrFile]:
    """Get list of staged ADR files from git and parse them into AdrFile objects."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            check=True,
            capture_output=True,
            text=True,
        )
        staged_files = result.stdout.strip().split("\n")
        paths = [
            ROOT / f
            for f in staged_files
            if f.startswith("architecture/adr/adr_") and f.endswith(".md")
        ]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

    adr_files = []
    for filepath in paths:
        if filepath.name in EXCLUDED_FILES:
            continue
        adr = parse_adr_file(filepath)
        if adr:
            adr_files.append(adr)

    return sorted(adr_files, key=lambda x: x.number)
