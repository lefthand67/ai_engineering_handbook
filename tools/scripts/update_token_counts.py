#!/usr/bin/env python3
"""
Token Size Automation Utility.

Automates the calculation and update of the 'options.token_size' field in
YAML frontmatter for governed files. This eliminates manual entry errors
and prevents pre-commit hook failures caused by outdated token counts.

RATIONALE:
    LLM context window management requires accurate token counts of the
    actual artifacts being loaded. Using 'tiktoken' with the 'cl100k_base'
    encoding provides the industry standard for modern production-grade
    LLMs (GPT-4, etc.).

CONTRACT:
    - The utility only processes files with a valid YAML frontmatter block
      delimited by '---' at the start of the file.
    - Token counting is performed on the FULL file content (frontmatter + body),
      as this represents the actual bytes transferred to the LLM.
    - The 'options' field must be a dictionary. If it is missing or is a
      scalar, it is corrected to a dictionary to allow token_size insertion.
    - File body and '---' delimiters are preserved exactly.
    - YAML is dumped with 'default_flow_style=False' and 'sort_keys=False'
      to maintain human readability and avoid unstable diffs.
    - Malformed YAML is handled gracefully; the file is skipped without
      crashing the script.

Dependencies:
    - tiktoken (for accurate tokenization)
    - PyYAML (for frontmatter manipulation)
    - tools/scripts/git.py (to detect repository root)
    - tools/scripts/paths.py (to respect excluded directories)
"""

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import Any

import tiktoken
import yaml

from tools.scripts.git import detect_repo_root
from tools.scripts.paths import VALIDATION_EXCLUDE_DIRS, is_excluded

# Setup logging
logger = logging.getLogger(__name__)

# Matches YAML frontmatter blocks delimited by --- fences at the start of a file.
# We use a non-greedy match for the content and ensure the closing delimiter
# is followed by a newline to confirm it's on its own line.
FRONTMATTER_PATTERN = re.compile(r"^---\s*\n([\s\S]*?)---\s*\n", re.DOTALL | re.MULTILINE)

# The field name used for token size in frontmatter.
# Defined as a constant to facilitate renaming and maintain consistency.
TOKEN_SIZE_FIELD = "token_size"

# ======================
# Main
# ======================

def main(argv: list[str] | None = None) -> int:
    """CLI entry point for token count automation.

    Args:
        argv: Command line arguments.

    Returns:
        0 on success, 1 on critical failure.
    """
    parser = argparse.ArgumentParser(
        description="Automate token_size updates in YAML frontmatter."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Files or directories to update. Defaults to repo root.",
    )
    parser.add_argument(
        "--format",
        dest="fmt",
        choices=["md", "ipynb"],
        default="md",
        help="File extension to scan for (default: md).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log the changes that would be made without actually writing to disk.",
    )
    parser.add_argument(
        "--log-level",
        dest="log_level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO).",
    )
    args = parser.parse_args(argv)

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(levelname)s: %(message)s",
        stream=sys.stdout
    )

    # Resolve root and input paths
    repo_root = detect_repo_root()
    input_paths = [Path(p) for p in args.paths] if args.paths else [repo_root]
    files = scan_paths(input_paths, fmt=args.fmt)

    # Load governed extensions from hub config to filter files.
    # This ensures we only touch files intended to be governed.
    try:
        from tools.scripts.paths import get_config_path
        hub_path = get_config_path(repo_root)
        import json
        hub_config = json.loads(hub_path.read_text(encoding="utf-8"))
        governed_exts = hub_config.get("governed_extensions", [])
    except Exception as e:
        logger.error(f"Failed to load governance config: {e}")
        return 1

    updated_count = 0
    skipped_count = 0

    for file_path in files:
        if file_path.suffix not in governed_exts:
            continue

        if update_file_tokens(file_path, dry_run=args.dry_run):
            logger.info(f"Updated {file_path}")
            updated_count += 1
        else:
            skipped_count += 1
    logger.info(f"Finished. Updated: {updated_count}, Skipped: {skipped_count}")
    return 0

# ======================
# Core Logic
# ======================

def update_token_counts(root: Path, paths: list[Path], dry_run: bool = False) -> None:
    """Wrapper for updating multiple files.

    Args:
        root: The repository root (used for config discovery).
        paths: Input files or directories to update.
        dry_run: If True, log changes without writing to disk.
    """
    # Resolve input paths to actual files
    files = scan_paths(paths)

    for file_path in files:
        update_file_tokens(file_path, dry_run=dry_run)

def calculate_tokens(text: str) -> int:
    """Calculate token count using cl100k_base encoding.

    Returns:
        The number of tokens in the provided text.
    """
    # cl100k_base is the standard for current production-grade LLMs.
    encoding = tiktoken.get_encoding("cl100k_base")
    # We disable disallowed_special to allow encoding of tokens like '<|fim_prefix|>'
    # which may appear as literal text in documentation.
    return len(encoding.encode(text, disallowed_special=()))

def update_file_tokens(file_path: Path, dry_run: bool = False) -> bool:
    """Update the token_size field in a file's governed frontmatter block.

    Args:
        file_path: Path to the file to update.
        dry_run: If True, log changes but do not write to disk.

    Returns:
        True if the file was updated (or would be updated in dry run),
        False if it was skipped.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        matches = list(FRONTMATTER_PATTERN.finditer(content))
        if not matches:
            logger.debug(f"[{file_path.name}] No frontmatter blocks found.")
            return False

        logger.debug(f"[{file_path.name}] Found frontmatter")
        new_size = calculate_tokens(content)
        changed = False
        result_content = content

        # 1. Try to find an existing governed block (containing 'options.type')
        governed_match = None
        for match in matches:
            fm_text = match.group(1)
            try:
                fm_data = yaml.safe_load(fm_text)
                if isinstance(fm_data, dict):
                    options = fm_data.get("options")
                    if isinstance(options, dict) and "type" in options:
                        governed_match = match
                        break
            except yaml.YAMLError:
                continue

        # 2. Fallback: if no block with options.type exists but there's only one block, treat it as governed
        if governed_match is None and len(matches) == 1:
            governed_match = matches[0]
            logger.debug(f"[{file_path.name}] No governed block found, treating single block as governed")

        if governed_match is None:
            logger.debug(f"[{file_path.name}] No governed block identified among multiple blocks.")
            return False

        # Now update the identified governed block
        match = governed_match
        fm_text = match.group(1)
        try:
            fm_data = yaml.safe_load(fm_text)
        except yaml.YAMLError:
            logger.error(f"[{file_path.name}] Malformed YAML in governed block: {fm_text}")
            return False

        if fm_data is None:
            fm_data = {}
        elif not isinstance(fm_data, dict):
            logger.error(f"[{file_path.name}] Governed block is not a dictionary.")
            return False

        logger.debug(f"[{file_path.name}] Found governed frontmatter block")

        # 1. Structural correction: Ensure token_size is NOT at the root
        if TOKEN_SIZE_FIELD in fm_data:
            logger.debug(f"[{file_path.name}] Removing root-level '{TOKEN_SIZE_FIELD}'")
            del fm_data[TOKEN_SIZE_FIELD]
            changed = True

        # 2. Structural correction: Ensure 'options' is a dictionary
        if "options" not in fm_data or not isinstance(fm_data["options"], dict):
            logger.debug(f"[{file_path.name}] Correcting 'options' to be a dictionary")
            fm_data["options"] = {}
            changed = True

        # 3. Update token_size inside options
        current_size = fm_data["options"].get(TOKEN_SIZE_FIELD)
        if current_size != new_size:
            logger.debug(f"[{file_path.name}] Updating options.{TOKEN_SIZE_FIELD}: {current_size} -> {new_size}")
            fm_data["options"][TOKEN_SIZE_FIELD] = new_size
            changed = True

        if not changed:
            return False

        # Dump YAML back to text, maintaining readability and avoiding sorting
        new_fm_text = yaml.dump(
            fm_data,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True
        ).strip()

        # Replace only this block in the content
        start, end = match.span()
        result_content = content[:start] + f"---\n{new_fm_text}\n---\n" + content[end:]

        if dry_run:
            logger.info(f"[{file_path.name}] Dry run: would have updated governed frontmatter")
            return True

        file_path.write_text(result_content, encoding="utf-8")
        return True
    except Exception as e:
        logger.error(f"Unexpected error updating {file_path}: {e}", exc_info=True)
        return False

# ======================
# Discovery
# ======================

def scan_paths(paths: list[Path], fmt: str = "md") -> list[Path]:
    """Resolve input paths to a list of files matching the format.

    Args:
        paths: Input files or directories.
        fmt: File extension to filter for.

    Returns:
        List of absolute Paths to candidates.
    """
    extension = f".{fmt}"
    files: list[Path] = []

    for path in paths:
        if path.is_file():
            # CRITICAL: Always check exclusions for explicit file arguments.
            # Prevents modification of files in external research repos when passed directly.
            if is_excluded(str(path)):
                logger.debug(f"[{path.name}] Excluded by validation rules")
                continue
            files.append(path)
        elif path.is_dir():
            for child in sorted(path.rglob(f"*{extension}")):
                if is_excluded(str(child)):
                    logger.debug(f"[{child.name}] Excluded by validation rules")
                    continue
                files.append(child)

    return files

if __name__ == "__main__":
    sys.exit(main())
