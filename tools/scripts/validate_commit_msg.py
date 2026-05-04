#!/usr/bin/env python3
"""Validate commit message format against ADR-26024 structured body convention.

Pre-commit hook (stage: commit-msg) that enforces:
1. Conventional Commits subject format: type[(scope)][!]: description
2. Structured body with at least one changelog bullet (- Verb: target — desc)
3. ArchTag presence for refactor/perf types and breaking changes (Tier 3)

Usage:
    # As pre-commit hook (automatic — git passes the file path)
    uv run --active tools/scripts/validate_commit_msg.py .git/COMMIT_EDITMSG

    # Manual validation
    uv run tools/scripts/validate_commit_msg.py path/to/commit_msg_file

Exit codes:
    0 — valid commit message
    1 — validation failure (errors printed to stderr)
"""

import argparse
import re
import sys
import tomllib
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration loaded from pyproject.toml [tool.commit-convention]
#
# The rules (valid types, ArchTag requirements) are defined in:
#   tools/docs/git/01_production_git_workflow_standards.md
# and configured in:
#   pyproject.toml [tool.commit-convention]
#
# See: architecture/adr/adr_26029_pyproject_toml_as_tool_config_hub.md
# ---------------------------------------------------------------------------

_PYPROJECT = Path(__file__).resolve().parents[2] / "pyproject.toml"


def _load_commit_convention() -> dict:
    with open(_PYPROJECT, "rb") as f:
        return tomllib.load(f)["tool"]["commit-convention"]


_CONFIG = _load_commit_convention()
VALID_TYPES = frozenset(_CONFIG["valid-types"])
ARCHTAG_REQUIRED_TYPES = frozenset(_CONFIG["archtag-required-types"])
ARCHTAG_VALID_VALUES = _CONFIG.get("archtag-valid-values", [])

# Regex for CC subject: type[(scope)][!]: description
# Groups: type, scope (optional), breaking (optional), desc
_SUBJECT_RE = re.compile(
    r"^(?P<type>[a-z]+)"          # type (lowercase alpha)
    r"(?:\((?P<scope>[^)]+)\))?"  # optional (scope)
    r"(?P<breaking>!)?"           # optional ! for breaking
    r":\s+"                       # colon + at least one space
    r"(?P<desc>.+)$"              # non-empty description
)

# Bullet line: optional whitespace + '- ' + content (main bullet)
_BULLET_RE = re.compile(r"^\s*- .+")

# Sub-bullet line: 4+ spaces + '—' (em-dash) + content
_SUB_BULLET_RE = re.compile(r"^    — .+")

# ArchTag line: ArchTag:TAG-NAME (no space after colon)
_ARCHTAG_RE = re.compile(r"^ArchTag:\S+")


# ---------------------------------------------------------------------------
# Main entry point (top-down design)
# ---------------------------------------------------------------------------


def main():
    cli = ValidateCommitMsgCLI()
    cli.run()


# ---------------------------------------------------------------------------
# Validation functions — each returns list[str] of error messages
# ---------------------------------------------------------------------------


def validate_subject(subject: str) -> list[str]:
    """Validate CC subject format: type[(scope)][!]: description."""
    errors = []
    if not subject.strip():
        errors.append("Subject line is empty")
        return errors

    match = _SUBJECT_RE.match(subject)
    if not match:
        errors.append(
            f"Subject does not match Conventional Commits format: "
            f"type[(scope)][!]: description — got: {subject!r}"
        )
        return errors

    commit_type = match.group("type")
    if commit_type not in VALID_TYPES:
        errors.append(
            f"Unknown commit type '{commit_type}'. "
            f"Valid types: {', '.join(sorted(VALID_TYPES))}"
        )

    return errors


def validate_body(body_lines: list[str]) -> list[str]:
    """Validate that body contains at least one changelog bullet.

    A bullet is a line matching ^\\s*- .+ that is NOT an ArchTag.
    Sub-bullets (indented with '—') are allowed as continuations.

    Format:
        - Updated: file-path
            — detail line 1
            — detail line 2
    """
    bullets = [
        line for line in body_lines
        if _BULLET_RE.match(line)
        and not _ARCHTAG_RE.match(line.strip())
    ]

    if not bullets:
        return ["Body must contain at least one changelog bullet (- Verb: target — description)"]

    # Validate sub-bullets: must follow a main bullet, not precede one
    sub_errors = []
    for i, line in enumerate(body_lines):
        if _SUB_BULLET_RE.match(line):
            # Check if there's a main bullet before this sub-bullet
            has_prior_bullet = any(
                _BULLET_RE.match(body_lines[j])
                for j in range(i)
            )
            if not has_prior_bullet:
                sub_errors.append(
                    f"Sub-bullet without main bullet (line {i + 1}): {line.strip()!r}"
                )

    return sub_errors


def validate_archtag(
    commit_type: str,
    body_lines: list[str],
    breaking: bool = False,
) -> list[str]:
    """Validate ArchTag presence, position, and value for refactor/perf/breaking commits (Tier 3)."""
    needs_archtag = commit_type in ARCHTAG_REQUIRED_TYPES or breaking
    if not needs_archtag:
        return []

    # 1. Check for presence and position
    if not body_lines:
        return ["COMMIT_EDITMSG:body — ArchTag required for breaking change or refactor/perf type — body is empty [pyproject.toml]"]

    if not _ARCHTAG_RE.match(body_lines[0]):
        # Check if it exists elsewhere to provide a "Move it" hint
        if any(_ARCHTAG_RE.match(line) for line in body_lines[1:]):
            return ["COMMIT_EDITMSG:body — ArchTag Position: ArchTag found in body, but it MUST be the first line. Move it to the top. [pyproject.toml]"]

        reason = "breaking change" if breaking else f"'{commit_type}' type"
        valid_options = ", ".join(ARCHTAG_VALID_VALUES)
        return [f"COMMIT_EDITMSG:body — ArchTag required for {reason} — add 'ArchTag:VALUE' as the first line of the body. Valid options: {valid_options}. [pyproject.toml]"]

    # 2. Validate the value of the ArchTag found on the first line
    tag_line = body_lines[0]
    try:
        tag_value = tag_line.split(":", 1)[1].strip()
    except IndexError:
        return ["COMMIT_EDITMSG:body — Malformed ArchTag: Expected 'ArchTag:VALUE' on the first line. [pyproject.toml]"]

    if not any(re.match(pattern, tag_value) for pattern in ARCHTAG_VALID_VALUES):
        valid_options = ", ".join(ARCHTAG_VALID_VALUES)
        return [f"COMMIT_EDITMSG:body — Invalid ArchTag: '{tag_value}' is not recognized. Valid options: {valid_options}. If this is a new decision, create an ADR first. [pyproject.toml]"]

    return []


# ---------------------------------------------------------------------------
# Commit message parsing helper
# ---------------------------------------------------------------------------


def _parse_commit_message(text: str) -> tuple[str, list[str]]:
    """Split commit message into subject and body lines.

    Git commit message format:
        subject line
        <blank line>
        body line 1
        body line 2

    Returns (subject, body_lines). Body lines exclude the blank separator.
    """
    lines = text.strip().splitlines()
    if not lines:
        return "", []

    subject = lines[0].strip()

    # Find body start (after first blank line)
    body_start = None
    for i, line in enumerate(lines[1:], start=1):
        if not line.strip():
            body_start = i + 1
            break

    if body_start is None or body_start >= len(lines):
        return subject, []

    body_lines = [line for line in lines[body_start:] if line.strip()]
    return subject, body_lines


# ---------------------------------------------------------------------------
# CLI class
# ---------------------------------------------------------------------------


class ValidateCommitMsgCLI:
    """CLI for commit message validation."""

    def __init__(self):
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description="Validate commit message against ADR-26024 conventions",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""\
Examples:
    # Automatic (git commit-msg hook)
    validate_commit_msg.py .git/COMMIT_EDITMSG

    # Manual check
    validate_commit_msg.py path/to/msg_file
""",
        )
        parser.add_argument(
            "msg_file",
            help="Path to the commit message file (provided by git commit-msg hook)",
        )
        return parser

    def run(self, argv: list[str] | None = None) -> None:
        args = self.parser.parse_args(argv)
        msg_path = Path(args.msg_file)
        text = msg_path.read_text(encoding="utf-8")

        subject, body_lines = _parse_commit_message(text)

        # Collect all validation errors
        errors: list[str] = []

        # 1. Subject format
        errors.extend(validate_subject(subject))

        # 2. Body bullets
        errors.extend(validate_body(body_lines))

        # 3. ArchTag (only check if subject parsed successfully)
        match = _SUBJECT_RE.match(subject)
        if match:
            commit_type = match.group("type")
            breaking = bool(match.group("breaking"))
            errors.extend(validate_archtag(commit_type, body_lines, breaking))

        if errors:
            print("Commit message validation failed:", file=sys.stderr)
            for error in errors:
                print(f"  ✗ {error}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
