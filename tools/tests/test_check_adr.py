"""
Test suite for check_adr.py - ADR Index synchronization validator.

Tests are organized following the behavior-based testing principle:
- Test what the code does, not how it does it
- Use semantic assertions rather than exact string matching
- Parameterize inputs for varied scenarios
"""

import runpy
import subprocess
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

import pytest
import tools.scripts.check_adr as _module


# ======================
# Test Fixtures & Helpers
# ======================


@dataclass
class AdrTestEnv:
    """Test environment with isolated ADR directory structure."""

    adr_dir: Path
    root: Path
    index_path: Path = None


def get_valid_frontmatter(doc_type: str, **overrides) -> dict:
    """Generate a minimal valid frontmatter dict based on current config.

    Ensures that all fields required by the hub and spoke configs are present
    with valid default values, then applies overrides.

    This follows the 'Dynamic Data' rule in testing_standards.md.
    """
    from tools.scripts.check_frontmatter import load_config_chain, REPO_ROOT, FIELD_REGISTRY

    hub, spoke = load_config_chain(REPO_ROOT, doc_type)

    # Determine required fields (merge hub blocks + hub type required + spoke required)
    blocks = hub.get("blocks", {})
    type_def = hub.get("types", {}).get(doc_type, {})
    required = set()

    for block_name in type_def.get("blocks", []):
        required.update(blocks.get(block_name, []))
    required.update(type_def.get("required", []))

    if spoke:
        required.update(spoke.get("required_fields", []))
        required.update(spoke.get("common_required_fields", []))

    # Populate with minimal valid defaults
    fm = {"options": {"type": doc_type}}
    defaults = {
        "title": "Default Title",
        "date": "2024-01-01",
        "status": "proposed",
        "description": "Default description",
        "tags": ["architecture"],
        "authors": [{"name": "Test Author", "email": "test@example.com"}],
        "version": "1.0.0",
        "birth": "2024-01-01",
    }

    for field in required:
        if field in ("type", "options.type"):
            continue
        
        # Clean field name for lookup (remove 'options.' prefix if present)
        clean_field = field.replace("options.", "")
        
        # Determine if field should be under options.* (non-myst_native)
        # SSoT: FIELD_REGISTRY in check_frontmatter.py
        is_native = FIELD_REGISTRY.get(clean_field, {}).get("myst_native", True)
        
        val = defaults.get(clean_field, "default_value")
        if not is_native:
            fm["options"][clean_field] = val
        else:
            fm[clean_field] = val

    # Apply overrides
    for key, value in overrides.items():
        clean_key = key.replace("options.", "")
        is_native = FIELD_REGISTRY.get(clean_key, {}).get("myst_native", True)
        if not is_native:
            fm["options"][clean_key] = value
        else:
            fm[clean_key] = value

    return fm


def create_adr_file(directory: Path, number: int, title: str, slug: str | None = None) -> Path:
    """Create an ADR file with given number and title.

    Creates a full ADR file with YAML frontmatter and all required sections
    from the module's REQUIRED_SECTIONS (loaded from config).

    Args:
        directory: Directory to create file in
        number: ADR number (e.g., 26001)
        title: ADR title for the header
        slug: Optional slug for filename (derived from title if not provided)

    Returns:
        Path to created file
    """
    if slug is None:
        # Generate slug from title: lowercase, replace spaces with underscores, truncate
        slug = title.lower().replace(" ", "_").replace("-", "_")[:40]

    # Use create_adr_file_full with default sections from config
    return create_adr_file_full(
        directory=directory,
        number=number,
        title=title,
        slug=slug,
        status="accepted",
        include_subsections=True,
    )


def create_adr_file_with_frontmatter(
    directory: Path,
    number: int,
    title: str,
    slug: str,
    status: str = "proposed",
    tags: list[str] | None = None,
    frontmatter_title: str | None = None,
    description: str | None = None,
) -> Path:
    """Create an ADR file with YAML frontmatter (new format)."""
    filename = f"adr_{number}_{slug}.md"
    filepath = directory / filename

    # Build body first to calculate tokens
    import tools.scripts.check_adr as check_adr_mod
    sections = check_adr_mod.REQUIRED_SECTIONS

    body_lines = [
        "",
        f"# ADR-{number}: {title}",
        "",
    ]
    for section in sections:
        body_lines.append(f"## {section}")
        body_lines.append("")
        if section == "Status":
            body_lines.append(status)
            body_lines.append("")
        else:
            body_lines.append("Some content.")
            body_lines.append("")
    body = "\n".join(body_lines)

    # Generate valid frontmatter based on current config (SSoT)
    from tools.scripts.check_frontmatter import calculate_tokens
    fm = get_valid_frontmatter(
        "adr",
        title=frontmatter_title if frontmatter_title is not None else title,
        status=status,
        tags=tags,
        description=description,
    )
    
    # Dynamically calculate token size for the final content
    # We'll estimate it based on the body + estimated frontmatter size
    # To be precise, we'll dump YAML first
    import yaml
    temp_yaml = yaml.dump(fm, sort_keys=False)
    full_content_preview = f"---\n{temp_yaml}\n---\n{body}"
    fm["options"]["token_size"] = calculate_tokens(full_content_preview)

    frontmatter_yaml = yaml.dump(fm, sort_keys=False)
    frontmatter_lines = ["---", frontmatter_yaml.strip(), "---"]

    filepath.write_text("\n".join(frontmatter_lines) + body, encoding="utf-8")
    return filepath


def create_adr_config(path: Path) -> None:
    """Copy real ADR config to test directory.

    Sources from the production adr.conf.json (Single Source of Truth)
    to avoid maintaining a duplicate hardcoded config in tests.

    Args:
        path: Path to write config file
    """
    import shutil

    real_config = Path(__file__).resolve().parent.parent.parent / ".vadocs" / "types" / "adr.conf.json"
    shutil.copy2(real_config, path)


def create_hub_config(path: Path) -> None:
    """Copy real hub config to test directory.

    Sources from the production conf.json (Single Source of Truth)
    for shared vocabulary (tags, date_format).

    Args:
        path: Path to write config file
    """
    import shutil

    real_config = Path(__file__).resolve().parent.parent.parent / ".vadocs" / "conf.json"
    shutil.copy2(real_config, path)


def create_legacy_adr_file(
    directory: Path,
    number: int,
    title: str,
    slug: str,
    status: str = "Accepted",
    sections: list[str] | None = None,
) -> Path:
    """Create a legacy ADR file without YAML frontmatter (old format).

    Args:
        directory: Directory to create file in
        number: ADR number (e.g., 26001)
        title: ADR title for the header
        slug: Slug for filename
        status: ADR status in old markdown format
        sections: Optional list of section names to include

    Returns:
        Path to created file
    """
    filename = f"adr_{number}_{slug}.md"
    filepath = directory / filename

    content_lines = [
        f"# ADR-{number}: {title}",
        "",
        "## Status",
        "",
        status,
        "",
    ]

    if sections is None:
        sections = ["Context", "Decision", "Consequences", "Alternatives", "References", "Participants"]

    for section in sections:
        content_lines.append(f"## {section}")
        content_lines.append("")
        content_lines.append(f"Content for {section.lower()} section.")
        content_lines.append("")

    filepath.write_text("\n".join(content_lines), encoding="utf-8")
    return filepath


def create_adr_file_with_sync_status(
    directory: Path,
    number: int,
    title: str,
    slug: str,
    fm_status: str | None = "proposed",
    body_status: str | None = "proposed",
) -> Path:
    """Create an ADR file with optionally mismatched status in frontmatter and body.

    Args:
        directory: Directory to create file in
        number: ADR number
        title: ADR title
        slug: Slug for filename
        fm_status: Status in YAML frontmatter (None means omit)
        body_status: Status in ## Status section (None means omit)

    Returns:
        Path to created file
    """
    filename = f"adr_{number}_{slug}.md"
    filepath = directory / filename

    # Generate valid frontmatter based on current config (SSoT)
    fm = get_valid_frontmatter(
        "adr",
        title=title,
        status=fm_status if fm_status is not None else "proposed",
    )
    if fm_status is None:
        # If fm_status is None, we explicitly remove it to test missing status
        if "status" in fm:
            del fm["status"]

    # Convert dict to YAML block
    import yaml
    frontmatter_yaml = yaml.dump(fm, sort_keys=False)
    fm_lines = ["---", frontmatter_yaml.strip(), "---"]

    # Build body
    body_lines = [
        "",
        f"# ADR-{number}: {title}",
        "",
        "## Status",
        "",
        body_status if body_status is not None else "",
        "",
    ]
    # Add minimal sections to be a "full" ADR
    body_lines.append("## Context\n\nSome context.\n")

    filepath.write_text("\n".join(fm_lines + body_lines), encoding="utf-8")
    return filepath


def create_adr_file_full(
    directory: Path,
    number: int,
    title: str,
    slug: str,
    status: str = "proposed",
    tags: list[str] | None = None,
    frontmatter_title: str | None = None,
    date: str = "2024-01-15",
    adr_id: str | None = None,
    sections: list[str] | None = None,
    include_subsections: bool = False,
    superseded_by: str | None = None,
) -> Path:
    """Create an ADR file with full YAML frontmatter and optional sections.

    Args:
        directory: Directory to create file in
        number: ADR number (e.g., 26016)
        title: ADR title for the header
        slug: Slug for filename
        status: ADR status
        tags: Optional list of tags
        frontmatter_title: Optional title in frontmatter (defaults to title param)
        date: Date in YYYY-MM-DD format
        adr_id: Optional ADR ID (defaults to number)
        sections: Optional list of section names to include. If None, uses
                  REQUIRED_SECTIONS from the module (loaded from config).
        include_subsections: Whether to include recommended subsections
        superseded_by: Optional ADR reference (e.g., "ADR-26023") for superseded ADRs

    Returns:
        Path to created file
    """
    filename = f"adr_{number}_{slug}.md"
    filepath = directory / filename

    # Generate valid frontmatter based on current config (SSoT)
    fm = get_valid_frontmatter(
        "adr",
        title=frontmatter_title if frontmatter_title is not None else title,
        status=status,
        tags=tags,
        date=date,
        superseded_by=superseded_by,
    )
    # Ensure ID is present for the ADR structure
    fm["id"] = adr_id if adr_id is not None else str(number)

    import yaml
    frontmatter_yaml = yaml.dump(fm, sort_keys=False)
    fm_lines = ["---", frontmatter_yaml.strip(), "---"]

    content_lines = fm_lines + [
        "",
        f"# ADR-{number}: {title}",
        "",
    ]

    if sections is None:
        # Import here to get the monkeypatched value from the test fixture
        import tools.scripts.check_adr as module
        sections = module.REQUIRED_SECTIONS

    for section in sections:
        content_lines.append(f"## {section}")
        content_lines.append("")
        if section == "Status":
            content_lines.append(status)
            content_lines.append("")
        else:
            content_lines.append("Content.")
            content_lines.append("")

    filepath.write_text("\n".join(content_lines), encoding="utf-8")
    return filepath


def create_index(path: Path, entries: list[tuple[int, str, str]]) -> None:
    """Write an ADR index file at path with given entries.

    Entries: list of (number, title, link)
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# ADR Index\n", "\n## **Proposed**\n", "\n:::{glossary}\n"]
    for number, title, link in entries:
        lines.append(f"ADR-{number}\n")
        lines.append(f": [{title}]({link})\n")
        lines.append("\n")
    lines.append(":::\n")
    path.write_text("".join(lines), encoding="utf-8")


def create_empty_index(path: Path) -> None:
    """Helper to create an empty index file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# ADR Index\n", encoding="utf-8")


def create_md_file_with_term_refs(directory: Path, filename: str, content: str) -> Path:
    """Write a markdown file with the given content."""
    directory.mkdir(parents=True, exist_ok=True)
    filepath = directory / filename
    filepath.write_text(content, encoding="utf-8")
    return filepath


@pytest.fixture
def adr_env(tmp_path, monkeypatch):
    """Create isolated ADR environment with configurable state."""
    adr_dir = tmp_path / "architecture" / "adr"
    adr_dir.mkdir(parents=True)

    # Create .vadocs/ structure mirroring production layout
    vadocs_dir = tmp_path / ".vadocs"
    types_dir = vadocs_dir / "types"
    types_dir.mkdir(parents=True)

    # Create dummy pyproject.toml for SSoT path resolution
    pyproject_content = '[tool.vadocs]\nconfig_dir = ".vadocs"\n'
    (tmp_path / "pyproject.toml").write_text(pyproject_content, encoding="utf-8")

    hub_config_path = vadocs_dir / "conf.json"
    spoke_config_path = types_dir / "adr.conf.json"

    # Create hub config (tags, date_format)
    create_hub_config(hub_config_path)

    # Create spoke config — rewrite parent_config to point to test hub
    create_adr_config(spoke_config_path)
    import json
    spoke = json.loads(spoke_config_path.read_text(encoding="utf-8"))
    spoke["parent_config"] = str(hub_config_path)
    spoke_config_path.write_text(json.dumps(spoke), encoding="utf-8")

    # Create the template file (should be excluded)
    template = adr_dir / "adr_template.md"
    template.write_text("# ADR Template\n\nUse this as a template.\n", encoding="utf-8")

    # Monkeypatch to use test directories
    monkeypatch.setattr("tools.scripts.git.detect_repo_root", lambda: tmp_path)
    monkeypatch.setattr("tools.scripts.adr_utils.ADR_DIR", adr_dir)
    monkeypatch.setattr("tools.scripts.check_adr_index.INDEX_PATH", tmp_path / "architecture" / "adr_index.md")

    # Force reload config with test paths
    import tools.scripts.adr_utils as utils
    import tools.scripts.check_adr as module
    
    # Reset lazy cache
    utils._config_cache = None
    config = utils.load_adr_config()
    
    # Sync constants across both modules
    for key, val in utils.get_adr_constants().items():
        if key != "ADR_DIR" and key != "INDEX_PATH":
            monkeypatch.setattr(module, key, val)
            monkeypatch.setattr(utils, key, val)
    
    # Explicitly sync paths
    monkeypatch.setattr(module, "ADR_DIR", adr_dir)
    monkeypatch.setattr(utils, "ADR_DIR", adr_dir)
    idx_path = tmp_path / "architecture" / "adr_index.md"
    monkeypatch.setattr(utils, "INDEX_PATH", idx_path)

    return AdrTestEnv(adr_dir=adr_dir, root=tmp_path, index_path=idx_path)


# ======================
# Unit Tests: ADR File Discovery
# ======================
# ======================
# Unit Tests: ADR File Discovery
# ======================


class TestGetAdrFiles:
    """Tests for ADR file discovery functionality."""

    def test_discovers_adr_files(self, adr_env):
        """Should find all ADR files in the directory."""
        from tools.scripts.adr_utils import get_adr_files

        create_adr_file(adr_env.adr_dir, 26001, "Test ADR", "test_adr")
        create_adr_file(adr_env.adr_dir, 26002, "Another ADR", "another_adr")

        files = get_adr_files()

        assert len(files) == 2
        numbers = {f.number for f in files}
        assert numbers == {26001, 26002}

    def test_excludes_template_file(self, adr_env):
        """Template file should not be included in results."""
        from tools.scripts.adr_utils import get_adr_files

        create_adr_file(adr_env.adr_dir, 26001, "Test ADR", "test_adr")
        # Template already created by fixture

        files = get_adr_files()

        filenames = {f.path.name for f in files}
        assert "adr_template.md" not in filenames

    def test_returns_sorted_by_number(self, adr_env):
        """ADR files should be sorted by number ascending."""
        from tools.scripts.adr_utils import get_adr_files

        # Create in reverse order
        create_adr_file(adr_env.adr_dir, 26003, "Third", "third")
        create_adr_file(adr_env.adr_dir, 26001, "First", "first")
        create_adr_file(adr_env.adr_dir, 26002, "Second", "second")

        files = get_adr_files()

        numbers = [f.number for f in files]
        assert numbers == [26001, 26002, 26003]

    def test_empty_directory_returns_empty_list(self, adr_env):
        """Empty ADR directory should return empty list."""
        from tools.scripts.adr_utils import get_adr_files

        # Only template exists (created by fixture)
        files = get_adr_files()

        assert files == []

    def test_parses_title_from_header(self, adr_env):
        """Should extract title from ADR header line."""
        from tools.scripts.adr_utils import get_adr_files

        create_adr_file(adr_env.adr_dir, 26001, "Use of Python for Scripts", "python_scripts")

        files = get_adr_files()

        assert len(files) == 1
        assert files[0].title == "Use of Python for Scripts"

    def test_handles_file_without_valid_header(self, adr_env):
        """File without valid ADR header should be skipped with warning."""
        from tools.scripts.adr_utils import get_adr_files

        # Create a file with wrong header format
        bad_file = adr_env.adr_dir / "adr_26001_bad.md"
        bad_file.write_text("# Not a valid ADR header\n\nContent here.\n", encoding="utf-8")

        # Also create a valid file
        create_adr_file(adr_env.adr_dir, 26002, "Valid ADR", "valid")

        files = get_adr_files()

        # Only the valid file should be returned
        assert len(files) == 1
        assert files[0].number == 26002

    def test_nonexistent_adr_directory(self, tmp_path, monkeypatch):
        """Should return empty list if ADR directory doesn't exist."""
        from tools.scripts.adr_utils import get_adr_files

        nonexistent = tmp_path / "nonexistent" / "adr"
        monkeypatch.setattr("tools.scripts.adr_utils.ADR_DIR", nonexistent)

        files = get_adr_files()

        assert files == []


# ======================
# Unit Tests: Frontmatter Options Support
# ======================


class TestFrontmatterParsingBug:
    """Reproduce the leading newline frontmatter parsing bug."""

    def test_adr_with_leading_newline_now_parses_correctly(self, adr_env):
        """Should verify that frontmatter parsing now succeeds even with a leading newline.

        The parser should ignore leading whitespace and correctly extract the frontmatter.
        """
        from tools.scripts.adr_utils import get_adr_files

        # Create ADR with leading newline
        adr_file_path = adr_env.adr_dir / "adr_26000_bug.md"
        content = "\n---\ntitle: Bug Test\nstatus: proposed\nid: 26000\ntags: [bug]\n---\n\n# ADR-26000: Bug Test\n\n## Context\nContent."
        adr_file_path.write_text(content, encoding="utf-8")

        # Use get_adr_files to load the file into an AdrFile object
        files = get_adr_files()
        adr_file = next(f for f in files if f.number == 26000)

        # Now, adr_file.frontmatter should NOT be None
        assert adr_file.frontmatter is not None, "Frontmatter should have been parsed despite leading newline."
        assert adr_file.frontmatter["title"] == "Bug Test"


# ======================
# Unit Tests: Conditional Fields
# ======================


class TestConditionalFieldsNamespace:
    """Contract: Conditional fields (e.g. superseded_by) must be detected 
    regardless of whether they are at top level or under options.*
    """

    def test_detects_superseded_by_in_options_block(self, adr_env):
        """ADR with status 'superseded' and 'superseded_by' in options block should pass."""
        # Create an ADR file with conditional field in options block
        adr_path = create_adr_file_full(
            directory=adr_env.adr_dir,
            number=26006,
            title="Test Superseded ADR",
            slug="test_superseded",
            status="superseded",
            superseded_by="ADR-26027",
        )
        
        # Use get_adr_files to load as AdrFile
        from tools.scripts.adr_utils import get_adr_files
        adr_file = next(f for f in get_adr_files() if f.number == 26006)
        
        # Validate conditional fields
        errors = _module.validate_conditional_fields(adr_file)
        
        # Should be no errors
        missing_fields = [e for e in errors if e.error_type == "missing_conditional_field"]
        assert not missing_fields, f"Expected no missing fields, but found: {missing_fields}"

    def test_rejects_missing_superseded_by_in_both_locations(self, adr_env):
        """ADR with status 'superseded' but no 'superseded_by' anywhere should fail."""
        # Create ADR with status superseded but explicitly omit superseded_by
        # we can do this by creating it with status='superseded' and superseded_by=None
        adr_path = create_adr_file_full(
            directory=adr_env.adr_dir,
            number=26007,
            title="Missing Ref ADR",
            slug="missing_ref",
            status="superseded",
            superseded_by=None,
        )
        
        from tools.scripts.adr_utils import get_adr_files
        adr_file = next(f for f in get_adr_files() if f.number == 26007)
        
        errors = _module.validate_conditional_fields(adr_file)
        
        # Should have a missing_conditional_field error
        assert any(e.error_type == "missing_conditional_field" for e in errors)


# ======================
# Unit Tests: Auto-Fix
# ======================


# ======================
# Integration Tests: CLI
# ======================


class TestCli:
    """Integration tests for command-line interface."""

    def test_check_staged_with_no_staged_files(self, adr_env, capsys):
        """Check-staged with no staged ADR files should pass."""
        from tools.scripts.check_adr import main

        with patch("tools.scripts.adr_utils.get_staged_adr_files", return_value=[]):
            exit_code = main(["--check-staged"])

        assert exit_code == 0

    def test_main_entry_point(self, adr_env, monkeypatch):
        """Cover the __main__ block."""
        monkeypatch.setattr("sys.argv", ["check_adr.py", "--help"])

        with pytest.raises(SystemExit) as exc_info:
            runpy.run_path("tools/scripts/check_adr.py", run_name="__main__")

        assert exc_info.value.code == 0

    def test_fix_with_errors_remaining(self, adr_env, caplog):
        """Fix should fail if unfixable errors remain (e.g., duplicates)."""
        import logging
        caplog.set_level(logging.ERROR)
        from tools.scripts.check_adr import main
    
        # Create duplicate ADR numbers (can't be auto-fixed)
        create_adr_file(adr_env.adr_dir, 26001, "First Version", "first_version")
        dup_file = adr_env.adr_dir / "adr_26001_duplicate.md"
        dup_file.write_text("# ADR-26001: Duplicate\n\n## Status\n\nAccepted\n", encoding="utf-8")
    
        exit_code = main(["--fix"])
    
        # Should fail because duplicates can't be auto-fixed
        assert exit_code == 1
        assert caplog.text  # Should explain why fix failed
    def test_check_staged_verbose_with_staged_files(self, adr_env, caplog):
        """Check-staged with verbose should produce output when files are staged."""
        import logging
        caplog.set_level(logging.INFO)
        from tools.scripts.check_adr import main
    
        with patch("tools.scripts.adr_utils.get_staged_adr_files") as mock_staged:
            mock_staged.return_value = [Path("architecture/adr/adr_26001_first_feature.md")]
            exit_code = main(["--check-staged", "--verbose"])
    
        assert exit_code == 0
        assert caplog.text  # Verbose should produce output

    def test_check_staged_verbose_no_staged_files(self, adr_env, caplog):
        """Check-staged with verbose and no staged files should produce output."""
        import logging
        caplog.set_level(logging.INFO)
        from tools.scripts.check_adr import main
    
        with patch("tools.scripts.adr_utils.get_staged_adr_files") as mock_staged:
            mock_staged.return_value = []
            exit_code = main(["--check-staged", "--verbose"])
    
        assert exit_code == 0
        assert caplog.text  # Verbose should produce output


# ======================
# Edge Cases
# ======================


class TestGetStagedAdrFiles:
    """Tests for git staged file detection."""

    def test_returns_staged_adr_files(self, adr_env):
        """Should return list of staged ADR files."""
        from tools.scripts.adr_utils import get_staged_adr_files

        staged_output = "architecture/adr/adr_26001_test.md\narchitecture/adr/adr_26002_other.md\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = staged_output
            files = get_staged_adr_files()

        assert len(files) == 2
        assert files[0] == Path("architecture/adr/adr_26001_test.md")

    def test_filters_non_adr_files(self, adr_env):
        """Should only return ADR files, not other staged files."""
        from tools.scripts.adr_utils import get_staged_adr_files

        staged_output = "README.md\narchitecture/adr/adr_26001_test.md\narchitecture/adr_index.md\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = staged_output
            files = get_staged_adr_files()

        assert len(files) == 1
        assert "adr_26001" in str(files[0])

    def test_handles_git_error(self, adr_env):
        """Should return empty list on git error."""
        from tools.scripts.adr_utils import get_staged_adr_files

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git")
            files = get_staged_adr_files()

        assert files == []

    def test_handles_git_not_found(self, adr_env):
        """Should return empty list if git is not installed."""
        from tools.scripts.adr_utils import get_staged_adr_files

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            files = get_staged_adr_files()

        assert files == []


# ======================
# Unit Tests: Status Extraction
# ======================


class TestExtractStatus:
    """Tests for status extraction from ADR files."""

    def test_extracts_status_from_yaml_frontmatter(self, adr_env):
        """Should extract status from YAML frontmatter."""
        from tools.scripts.adr_utils import extract_status

        content = """---
title: Test ADR
status: accepted
---

# ADR-26001: Test ADR
"""
        result = extract_status(content)

        assert result == "accepted"

    def test_extracts_status_from_markdown_section(self, adr_env):
        """Should extract status from ## Status section (old format)."""
        from tools.scripts.adr_utils import extract_status

        content = """# ADR-26001: Test ADR

## Status

Accepted

## Context

Some context.
"""
        result = extract_status(content)

        assert result == "accepted"

    def test_yaml_frontmatter_takes_priority(self, adr_env):
        """When both formats exist, YAML frontmatter should take priority."""
        from tools.scripts.adr_utils import extract_status

        content = """---
title: Test ADR
status: proposed
---

# ADR-26001: Test ADR

## Status

Accepted
"""
        result = extract_status(content)

        assert result == "proposed"

    def test_returns_none_when_no_status(self, adr_env):
        """Should return None when no status is found in either format."""
        from tools.scripts.adr_utils import extract_status

        content = """# ADR-26001: Test ADR

## Context

No status section here.
"""
        result = extract_status(content)

        assert result is None

    def test_normalizes_status_to_lowercase(self, adr_env):
        """Status should be normalized to lowercase."""
        from tools.scripts.adr_utils import extract_status

        content = """# ADR-26001: Test ADR

## Status

ACCEPTED

## Context
"""
        result = extract_status(content)

        assert result == "accepted"


# ======================
# Unit Tests: Mixed Format Coexistence
# ======================


class TestMixedFormatCoexistence:
    """Tests for handling both old (markdown) and new (YAML) ADR formats."""

    def test_discovers_both_formats(self, adr_env):
        """Should discover ADR files in both old and new formats."""
        from tools.scripts.adr_utils import get_adr_files

        # Old format (markdown Status section)
        create_adr_file(adr_env.adr_dir, 26001, "Old Format ADR", "old_format")
        # New format (YAML frontmatter)
        create_adr_file_with_frontmatter(adr_env.adr_dir, 26002, "New Format ADR", "new_format", status="accepted")

        files = get_adr_files()

        assert len(files) == 2
        numbers = {f.number for f in files}
        assert numbers == {26001, 26002}

    def test_validates_both_formats(self, adr_env):
        """Validation should work for both old and new formats."""
        from tools.scripts.adr_utils import get_adr_files
        from tools.scripts.adr_utils import parse_index
        from tools.scripts.check_adr_index import validate_sync

        # Old format (legacy, will have missing field/section errors)
        create_legacy_adr_file(adr_env.adr_dir, 26001, "Old Format", "old_format")
        # New format (complete)
        create_adr_file_full(adr_env.adr_dir, 26002, "New Format", "new_format", status="accepted")

        create_index(
            adr_env.index_path,
            [
                (26001, "Old Format", "/architecture/adr/adr_26001_old_format.md"),
                (26002, "New Format", "/architecture/adr/adr_26002_new_format.md"),
            ],
        )

        adr_files = get_adr_files()
        index_entries = parse_index()
        errors = validate_sync(adr_files, index_entries)

        # Should have no index sync errors (missing_in_index, orphan_in_index, etc.)
        # Format errors (missing_field, missing_section) are expected for legacy files
        sync_error_types = {"missing_in_index", "orphan_in_index", "wrong_link", "wrong_order", "duplicate_number"}
        sync_errors = [e for e in errors if e.error_type in sync_error_types]
        assert sync_errors == []


# ======================
# Unit Tests: Title Mismatch Handling
# ======================


# ======================
# Unit Tests: Status Fix
# ======================


class TestFixInvalidStatus:
    """Tests for fixing invalid statuses in ADR files."""

    def test_fix_with_suggested_correction_accepted(self, adr_env, monkeypatch):
        """Should fix status when user accepts suggested correction."""
        from tools.scripts.check_adr import fix_invalid_status
        from tools.scripts.adr_utils import get_adr_files
        from tools.scripts.check_frontmatter import parse_frontmatter

        # Create ADR with typo in status (prposed -> proposed)
        create_adr_file_with_frontmatter(
            adr_env.adr_dir, 26001, "Test ADR", "test_adr", status="prposed"
        )

        adr_files = get_adr_files()
        adr_file = adr_files[0]

        # Simulate user accepting suggested fix (empty input = yes)
        monkeypatch.setattr("builtins.input", lambda _: "")

        result = fix_invalid_status(adr_file)

        assert result is True
        content = adr_file.path.read_text(encoding="utf-8")
        from tools.scripts.adr_utils import extract_status
        assert extract_status(content) == "proposed"

    def test_fix_with_custom_status(self, adr_env, monkeypatch):
        """Should fix status when user provides custom valid status."""
        from tools.scripts.check_adr import fix_invalid_status
        from tools.scripts.adr_utils import get_adr_files
        from tools.scripts.check_frontmatter import parse_frontmatter

        create_adr_file_with_frontmatter(
            adr_env.adr_dir, 26001, "Test ADR", "test_adr", status="prposed"
        )

        adr_files = get_adr_files()
        adr_file = adr_files[0]

        # Simulate user typing custom status
        monkeypatch.setattr("builtins.input", lambda _: "accepted")

        result = fix_invalid_status(adr_file)

        assert result is True
        content = adr_file.path.read_text(encoding="utf-8")
        from tools.scripts.adr_utils import extract_status
        assert extract_status(content) == "accepted"

    def test_fix_rejected_by_user(self, adr_env, monkeypatch):
        """Should return False when user rejects the fix."""
        from tools.scripts.check_adr import fix_invalid_status
        from tools.scripts.adr_utils import get_adr_files

        create_adr_file_with_frontmatter(
            adr_env.adr_dir, 26001, "Test ADR", "test_adr", status="prposed"
        )

        adr_files = get_adr_files()
        adr_file = adr_files[0]

        # Simulate user rejecting
        monkeypatch.setattr("builtins.input", lambda _: "n")

        result = fix_invalid_status(adr_file)

        assert result is False

    def test_fix_unknown_typo_with_manual_input(self, adr_env, monkeypatch):
        """Should prompt for manual input when typo is not in corrections list."""
        from tools.scripts.check_adr import fix_invalid_status
        from tools.scripts.adr_utils import get_adr_files
        from tools.scripts.check_frontmatter import parse_frontmatter

        create_adr_file_with_frontmatter(
            adr_env.adr_dir, 26001, "Test ADR", "test_adr", status="unknownstatus"
        )

        adr_files = get_adr_files()
        adr_file = adr_files[0]

        # Simulate user typing valid status
        monkeypatch.setattr("builtins.input", lambda _: "rejected")

        result = fix_invalid_status(adr_file)

        assert result is True
        content = adr_file.path.read_text(encoding="utf-8")
        from tools.scripts.adr_utils import extract_status, VALID_STATUSES
        assert extract_status(content) != "prposed"
        assert extract_status(content) in VALID_STATUSES

    def test_fix_skipped_when_empty_input(self, adr_env, monkeypatch):
        """Should skip fix when user provides empty input for unknown typo."""
        from tools.scripts.check_adr import fix_invalid_status
        from tools.scripts.adr_utils import get_adr_files

        create_adr_file_with_frontmatter(
            adr_env.adr_dir, 26001, "Test ADR", "test_adr", status="unknownstatus"
        )

        adr_files = get_adr_files()
        adr_file = adr_files[0]

        # Simulate user skipping (empty input for unknown typo)
        monkeypatch.setattr("builtins.input", lambda _: "")

        result = fix_invalid_status(adr_file)

        assert result is False

    def test_fix_invalid_custom_status_rejected(self, adr_env, monkeypatch):
        """Should reject when user provides invalid custom status."""
        from tools.scripts.check_adr import fix_invalid_status
        from tools.scripts.adr_utils import get_adr_files

        create_adr_file_with_frontmatter(
            adr_env.adr_dir, 26001, "Test ADR", "test_adr", status="prposed"
        )

        adr_files = get_adr_files()
        adr_file = adr_files[0]

        # Simulate user typing invalid status
        monkeypatch.setattr("builtins.input", lambda _: "notavalidstatus")

        result = fix_invalid_status(adr_file)

        assert result is False

    def test_fix_valid_status_returns_true(self, adr_env):
        """Should return True immediately for valid status (no-op)."""
        from tools.scripts.check_adr import fix_invalid_status
        from tools.scripts.adr_utils import get_adr_files

        create_adr_file_with_frontmatter(
            adr_env.adr_dir, 26001, "Test ADR", "test_adr", status="accepted"
        )

        adr_files = get_adr_files()
        adr_file = adr_files[0]

        result = fix_invalid_status(adr_file)

        assert result is True

    def test_fix_old_format_markdown_status(self, adr_env, monkeypatch):
        """Should fix status in old markdown format (no YAML frontmatter)."""
        from tools.scripts.adr_utils import extract_status
        from tools.scripts.check_adr import fix_invalid_status
        from tools.scripts.adr_utils import get_adr_files

        # Create old-format ADR with typo in status section
        filepath = adr_env.adr_dir / "adr_26001_old_format.md"
        content = """# ADR-26001: Old Format ADR

## Status

Prposed

## Context

Some context.
"""
        filepath.write_text(content, encoding="utf-8")

        adr_files = get_adr_files()
        adr_file = adr_files[0]

        # Simulate user accepting suggested fix
        monkeypatch.setattr("builtins.input", lambda _: "")

        result = fix_invalid_status(adr_file)

        assert result is True
        # Verify the markdown status section was updated
        new_content = filepath.read_text(encoding="utf-8")
        new_status = extract_status(new_content)
        assert new_status == "proposed"


class TestTitleMismatchHandling:
    """Tests for detecting and fixing title mismatches between header and frontmatter."""

    def test_detects_title_mismatch(self, adr_env):
        """Should detect when frontmatter title differs from header title."""
        from tools.scripts.adr_utils import get_adr_files
        from tools.scripts.adr_utils import parse_index
        from tools.scripts.check_adr_index import validate_sync

        # Create ADR with mismatched titles
        create_adr_file_with_frontmatter(
            adr_env.adr_dir,
            26001,
            "Header Title",
            "test_adr",
            status="accepted",
            frontmatter_title="Different Frontmatter Title",
        )
        create_index(
            adr_env.index_path,
            [(26001, "Header Title", "/architecture/adr/adr_26001_test_adr.md")],
        )

        adr_files = get_adr_files()
        index_entries = parse_index()
        errors = validate_sync(adr_files, index_entries)

        assert any(e.error_type == "title_mismatch" for e in errors)

    def test_fix_title_mismatch_updates_frontmatter(self, adr_env, monkeypatch):
        """Fix should update frontmatter title to match header when user confirms."""
        from tools.scripts.check_adr import fix_title_mismatch
        from tools.scripts.adr_utils import get_adr_files
        from tools.scripts.check_frontmatter import parse_frontmatter

        create_adr_file_with_frontmatter(
            adr_env.adr_dir,
            26001,
            "Header Title",
            "test_adr",
            status="accepted",
            frontmatter_title="Wrong Title",
        )

        adr_files = get_adr_files()
        adr_file = adr_files[0]

        # Simulate user confirming the fix
        monkeypatch.setattr("builtins.input", lambda _: "y")

        result = fix_title_mismatch(adr_file)

        assert result is True
        # Verify the file was updated by parsing the frontmatter
        content = adr_file.path.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(content)
        assert frontmatter is not None
        assert frontmatter.get("title") == "Header Title"

    def test_fix_title_mismatch_rejected_returns_false(self, adr_env, monkeypatch):
        """Fix should return False when user rejects the fix."""
        from tools.scripts.check_adr import fix_title_mismatch
        from tools.scripts.adr_utils import get_adr_files
        from tools.scripts.check_frontmatter import parse_frontmatter

        create_adr_file_with_frontmatter(
            adr_env.adr_dir,
            26001,
            "Header Title",
            "test_adr",
            status="accepted",
            frontmatter_title="Wrong Title",
        )

        adr_files = get_adr_files()
        adr_file = adr_files[0]

        # Simulate user rejecting the fix
        monkeypatch.setattr("builtins.input", lambda _: "n")

        result = fix_title_mismatch(adr_file)

        assert result is False
        # Verify the file was NOT updated by parsing the frontmatter
        content = adr_file.path.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(content)
        assert frontmatter is not None
        assert frontmatter.get("title") == "Wrong Title"


# ======================
# Unit Tests: Partitioned Index
# ======================


class TestPartitionedIndex:
    """Tests for state-partitioned index generation."""

    def test_groups_adrs_by_status(self, adr_env):
        """Fix should group ADRs by status into different sections."""
        from tools.scripts.adr_utils import STATUS_SECTIONS
        from tools.scripts.adr_utils import parse_index
        from tools.scripts.check_adr_index import fix_index

        # Create ADRs with different statuses
        create_adr_file_with_frontmatter(adr_env.adr_dir, 26001, "Accepted ADR", "accepted_adr", status="accepted")
        create_adr_file_with_frontmatter(adr_env.adr_dir, 26002, "Proposed ADR", "proposed_adr", status="proposed")
        create_adr_file_with_frontmatter(adr_env.adr_dir, 26003, "Rejected ADR", "rejected_adr", status="rejected")

        fix_index()

        entries = parse_index()

        # Check that entries are grouped according to STATUS_SECTIONS mapping
        accepted_entry = next(e for e in entries if e.number == 26001)
        proposed_entry = next(e for e in entries if e.number == 26002)
        rejected_entry = next(e for e in entries if e.number == 26003)

        # Use the module's own mapping to verify section assignment
        assert accepted_entry.section == STATUS_SECTIONS["accepted"]
        assert proposed_entry.section == STATUS_SECTIONS["proposed"]
        assert rejected_entry.section == STATUS_SECTIONS["rejected"]

    def test_adrs_with_same_status_grouped_together(self, adr_env):
        """ADRs with the same status should appear in the same section."""
        from tools.scripts.adr_utils import parse_index
        from tools.scripts.check_adr_index import fix_index

        # Create multiple ADRs with same status
        create_adr_file_with_frontmatter(adr_env.adr_dir, 26001, "First Accepted", "first", status="accepted")
        create_adr_file_with_frontmatter(adr_env.adr_dir, 26002, "Second Accepted", "second", status="accepted")
        create_adr_file_with_frontmatter(adr_env.adr_dir, 26003, "Third Accepted", "third", status="accepted")

        fix_index()

        entries = parse_index()

        # All entries should be in the same section
        sections = {e.section for e in entries}
        assert len(sections) == 1

    def test_numerical_order_within_sections(self, adr_env):
        """ADRs should be in numerical order within each section."""
        from tools.scripts.adr_utils import parse_index
        from tools.scripts.check_adr_index import fix_index

        # Create ADRs in non-sequential order
        create_adr_file_with_frontmatter(adr_env.adr_dir, 26003, "Third Accepted", "third", status="accepted")
        create_adr_file_with_frontmatter(adr_env.adr_dir, 26001, "First Accepted", "first", status="accepted")
        create_adr_file_with_frontmatter(adr_env.adr_dir, 26002, "Second Accepted", "second", status="accepted")

        fix_index()

        entries = parse_index()
        # Get entries from any section (they're all in same section)
        section = entries[0].section
        numbers = [e.number for e in entries if e.section == section]

        assert numbers == sorted(numbers)

    def test_default_section_for_no_status(self, adr_env):
        """ADRs without explicit status should be treated as proposed."""
        from tools.scripts.adr_utils import STATUS_SECTIONS
        from tools.scripts.adr_utils import parse_index
        from tools.scripts.check_adr_index import fix_index

        # Create old-format ADR without explicit status
        filepath = adr_env.adr_dir / "adr_26001_no_status.md"
        content = """# ADR-26001: No Status ADR

## Context

Some context without a status section.
"""
        filepath.write_text(content, encoding="utf-8")

        fix_index()

        entries = parse_index()
        entry = next(e for e in entries if e.number == 26001)

        # Should be in the same section as "proposed" ADRs
        assert entry.section == STATUS_SECTIONS["proposed"]

    def test_validates_section_placement(self, adr_env):
        """Should detect ADRs placed in a section that doesn't match their status."""
        from tools.scripts.adr_utils import STATUS_SECTIONS, get_adr_files
        from tools.scripts.adr_utils import parse_index
        from tools.scripts.check_adr_index import validate_sync

        # Create accepted ADR
        create_adr_file_with_frontmatter(adr_env.adr_dir, 26001, "Accepted ADR", "accepted_adr", status="accepted")

        # Get the section name for "proposed" (different from "accepted")
        wrong_section = STATUS_SECTIONS["proposed"]

        # Create index with ADR in wrong section
        content = f"""# ADR Index

## {wrong_section}

:::{{glossary}}
ADR-26001
: [Accepted ADR](/architecture/adr/adr_26001_accepted_adr.md)
:::
"""
        adr_env.index_path.write_text(content, encoding="utf-8")

        adr_files = get_adr_files()
        index_entries = parse_index()
        errors = validate_sync(adr_files, index_entries)

        # Should have an error (type doesn't matter, just that it's detected)
        assert len(errors) > 0
        # At least one error should mention the ADR number
        assert any(e.number == 26001 for e in errors)


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_adr_number_in_header_differs_from_filename(self, adr_env):
        """Header number should be authoritative over filename number."""
        from tools.scripts.adr_utils import get_adr_files

        # Create file with mismatched numbers
        filepath = adr_env.adr_dir / "adr_26001_test.md"
        filepath.write_text("# ADR-26002: Different Number\n\n## Status\n\nAccepted\n", encoding="utf-8")

        files = get_adr_files()

        # Should use header number (26002), not filename number (26001)
        assert len(files) == 1
        assert files[0].number == 26002

    def test_title_with_special_characters(self, adr_env):
        """Titles with special characters should be handled correctly."""
        from tools.scripts.adr_utils import get_adr_files

        create_adr_file(adr_env.adr_dir, 26001, "Use: Python & OOP (v2.0)", "python_oop")

        files = get_adr_files()

        assert len(files) == 1
        assert "Python & OOP" in files[0].title

    def test_index_with_extra_whitespace(self, adr_env):
        """Index with extra whitespace should be parsed correctly."""
        from tools.scripts.adr_utils import parse_index

        # Write index with extra blank lines
        content = """# ADR Index

:::{glossary}
ADR-26001
: [First ADR](/architecture/adr/adr_26001_first.md)


ADR-26002
: [Second ADR](/architecture/adr/adr_26002_second.md)
:::
"""
        adr_env.index_path.write_text(content, encoding="utf-8")

        entries = parse_index()

        assert len(entries) == 2

    def test_link_with_relative_path(self, adr_env):
        """Index entry with relative path should be detected as wrong."""
        from tools.scripts.adr_utils import get_adr_files
        from tools.scripts.adr_utils import parse_index
        from tools.scripts.check_adr_index import validate_sync

        create_adr_file(adr_env.adr_dir, 26001, "Test", "test")

        # Create index with relative path
        create_index(
            adr_env.index_path,
            [(26001, "Test", "adr/adr_26001_test.md")],  # Relative, not absolute
        )

        adr_files = get_adr_files()
        index_entries = parse_index()

        errors = validate_sync(adr_files, index_entries)

        # Should detect wrong link format
        assert any(e.error_type == "wrong_link" for e in errors)

    def test_empty_adr_directory_and_empty_index(self, adr_env):
        """Both empty directory and empty index should result in no errors."""
        from tools.scripts.adr_utils import get_adr_files
        from tools.scripts.adr_utils import parse_index
        from tools.scripts.check_adr_index import validate_sync

        create_empty_index(adr_env.index_path)

        adr_files = get_adr_files()
        index_entries = parse_index()

        errors = validate_sync(adr_files, index_entries)

        assert errors == []


# ======================
# Unit Tests: Tag Validation
# ======================


class TestValidateTags:
    """Tests for tag validation."""

    def test_all_valid_tags_pass(self, adr_env):
        """ADR with all valid tags should pass validation."""
        from tools.scripts.adr_utils import get_adr_files
        from tools.scripts.check_adr import validate_tags

        create_adr_file_full(
            adr_env.adr_dir,
            26001,
            "Valid Tags ADR",
            "valid_tags",
            tags=["architecture", "documentation"],
        )

        adr_files = get_adr_files()
        errors = validate_tags(adr_files[0])

        assert not any(e.error_type == "invalid_tag" for e in errors)

    def test_invalid_tag_produces_error(self, adr_env):
        """ADR with invalid tag should produce error."""
        from tools.scripts.adr_utils import get_adr_files
        from tools.scripts.check_adr import validate_tags

        create_adr_file_full(
            adr_env.adr_dir,
            26001,
            "Invalid Tag ADR",
            "invalid_tag",
            tags=["architecture", "nonexistent_tag"],
        )

        adr_files = get_adr_files()
        errors = validate_tags(adr_files[0])

        assert any(e.error_type == "invalid_tag" for e in errors)

    def test_empty_tags_list_produces_error(self, adr_env):
        """ADR with empty tags list should produce error."""
        from tools.scripts.adr_utils import get_adr_files
        from tools.scripts.check_adr import validate_tags

        create_adr_file_full(
            adr_env.adr_dir,
            26001,
            "Empty Tags ADR",
            "empty_tags",
            tags=[],
        )

        adr_files = get_adr_files()
        errors = validate_tags(adr_files[0])

        # Empty tags should produce an error (tags is required and must have at least one)
        assert any(e.error_type == "empty_tags" or (e.error_type == "invalid_tag" and "empty" in e.message.lower()) for e in errors)

    def test_mixed_valid_invalid_tags(self, adr_env):
        """ADR with mix of valid and invalid tags should produce error for invalid ones."""
        from tools.scripts.adr_utils import get_adr_files
        from tools.scripts.check_adr import validate_tags

        create_adr_file_full(
            adr_env.adr_dir,
            26001,
            "Mixed Tags ADR",
            "mixed_tags",
            tags=["architecture", "bad_tag", "documentation"],
        )

        adr_files = get_adr_files()
        errors = validate_tags(adr_files[0])

        invalid_tag_errors = [e for e in errors if e.error_type == "invalid_tag"]
        assert len(invalid_tag_errors) >= 1
        assert any("bad_tag" in e.message for e in invalid_tag_errors)


# ======================
# Unit Tests: Section Validation
# ======================


class TestValidateSections:
    """Tests for required section validation."""

    def test_all_required_sections_present_passes(self, adr_env):
        """ADR with all required sections should pass validation."""
        from tools.scripts.adr_utils import get_adr_files
        from tools.scripts.check_adr import validate_sections

        create_adr_file_full(
            adr_env.adr_dir,
            26001,
            "Complete Sections ADR",
            "complete_sections",
        )

        adr_files = get_adr_files()
        errors = validate_sections(adr_files[0])

        assert not any(e.error_type == "missing_section" for e in errors)

    def test_missing_required_section_produces_error(self, adr_env):
        """ADR missing required section should produce error."""
        from tools.scripts.adr_utils import get_adr_files
        from tools.scripts.check_adr import validate_sections

        create_adr_file_full(
            adr_env.adr_dir,
            26001,
            "Incomplete Sections ADR",
            "incomplete_sections",
            sections=["Context", "Decision", "Consequences"],  # Missing Alternatives, References, Participants
        )

        adr_files = get_adr_files()
        errors = validate_sections(adr_files[0])

        missing_section_errors = [e for e in errors if e.error_type == "missing_section"]
        assert len(missing_section_errors) >= 1

    def test_partial_sections_reports_all_missing(self, adr_env):
        """Should report all missing sections, not just the first one."""
        from tools.scripts.adr_utils import get_adr_files
        from tools.scripts.check_adr import validate_sections

        create_adr_file_full(
            adr_env.adr_dir,
            26001,
            "Partial Sections ADR",
            "partial_sections",
            sections=["Context", "Decision"],  # Missing many sections
        )

        adr_files = get_adr_files()
        errors = validate_sections(adr_files[0])

        missing_section_errors = [e for e in errors if e.error_type == "missing_section"]
        # Should have errors for Consequences, Alternatives, References, Participants
        assert len(missing_section_errors) >= 4

    def test_subsections_warning_not_error(self, adr_env):
        """Missing recommended subsections should not produce errors (only warnings)."""
        from tools.scripts.adr_utils import get_adr_files
        from tools.scripts.check_adr import validate_sections

        create_adr_file_full(
            adr_env.adr_dir,
            26001,
            "No Subsections ADR",
            "no_subsections",
            sections=["Context", "Decision", "Consequences", "Alternatives", "References", "Participants"],
            include_subsections=False,  # Don't include Positive/Negative subsections
        )

        adr_files = get_adr_files()
        errors = validate_sections(adr_files[0])

        # Should not fail on missing subsections (they're recommended, not required)
        assert not any(e.error_type == "missing_subsection" for e in errors)

    def test_section_case_sensitivity(self, adr_env):
        """Section validation should be case-sensitive."""
        from tools.scripts.adr_utils import get_adr_files
        from tools.scripts.check_adr import validate_sections

        # Create ADR with lowercase section names
        filepath = adr_env.adr_dir / "adr_26001_lowercase.md"
        content = """---
id: 26001
title: Lowercase Sections ADR
date: 2024-01-15
status: proposed
tags: [architecture]
---

# ADR-26001: Lowercase Sections ADR

## context

Content.

## decision

Content.

## consequences

Content.

## alternatives

Content.

## references

Content.

## participants

Content.
"""
        filepath.write_text(content, encoding="utf-8")

        adr_files = get_adr_files()
        errors = validate_sections(adr_files[0])

        # Lowercase sections should not match required sections (case-sensitive)
        missing_section_errors = [e for e in errors if e.error_type == "missing_section"]
        assert len(missing_section_errors) >= 1


# ======================
# Unit Tests: Legacy ADR Migration
# ======================


class TestMigrateLegacyAdr:
    """Tests for legacy ADR migration functionality."""

    def test_migrate_adds_frontmatter(self, adr_env):
        """Migration should add YAML frontmatter to legacy file."""
        from tools.scripts.check_adr import migrate_legacy_adr
        from tools.scripts.adr_utils import get_adr_files
        from tools.scripts.check_frontmatter import parse_frontmatter

        filepath = create_legacy_adr_file(adr_env.adr_dir, 26001, "Legacy ADR", "legacy_adr")

        result = migrate_legacy_adr(filepath)

        assert result is True
        content = filepath.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(content)
        assert frontmatter is not None
        assert "title" in frontmatter
        assert "status" in frontmatter

    def test_migrate_preserves_content(self, adr_env):
        """Migration should preserve the document body unchanged."""
        from tools.scripts.check_adr import migrate_legacy_adr

        filepath = create_legacy_adr_file(
            adr_env.adr_dir,
            26001,
            "Legacy ADR",
            "legacy_adr",
            sections=["Context", "Decision"],
        )
        original_body = "## Context\n"  # Part of the original content

        result = migrate_legacy_adr(filepath)

        assert result is True
        content = filepath.read_text(encoding="utf-8")
        assert original_body in content

    def test_migrate_extracts_status(self, adr_env):
        """Migration should extract status from ## Status section."""
        from tools.scripts.check_adr import migrate_legacy_adr
        from tools.scripts.adr_utils import get_adr_files
        from tools.scripts.check_frontmatter import parse_frontmatter

        filepath = create_legacy_adr_file(
            adr_env.adr_dir,
            26001,
            "Legacy ADR",
            "legacy_adr",
            status="Accepted",  # Status in markdown section
        )

        result = migrate_legacy_adr(filepath)

        assert result is True
        content = filepath.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(content)
        assert frontmatter is not None
        assert frontmatter.get("status") == "accepted"

    def test_migrate_skips_files_with_frontmatter(self, adr_env):
        """Migration should skip files that already have YAML frontmatter."""
        from tools.scripts.check_adr import migrate_legacy_adr
        from tools.scripts.adr_utils import get_adr_files
        from tools.scripts.check_frontmatter import parse_frontmatter

        # Create file with existing frontmatter
        filepath = create_adr_file_full(
            adr_env.adr_dir,
            26001,
            "Already Migrated",
            "already_migrated",
            status="proposed",
        )
        original_content = filepath.read_text(encoding="utf-8")

        result = migrate_legacy_adr(filepath)

        # Should return False (no changes made) or True (idempotent)
        # Either way, content should be unchanged
        new_content = filepath.read_text(encoding="utf-8")
        assert new_content == original_content

    def test_migrate_with_invalid_status_typo(self, adr_env):
        """Migration should correct status typos using corrections map."""
        from tools.scripts.check_adr import migrate_legacy_adr
        from tools.scripts.adr_utils import get_adr_files
        from tools.scripts.check_frontmatter import parse_frontmatter

        filepath = create_legacy_adr_file(
            adr_env.adr_dir,
            26001,
            "Legacy ADR",
            "legacy_adr",
            status="Prposed",  # Typo that should be corrected
        )

        result = migrate_legacy_adr(filepath)

        assert result is True
        content = filepath.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(content)
        assert frontmatter is not None
        assert frontmatter.get("status") == "proposed"  # Corrected

    def test_migrate_with_unknown_status_uses_default(self, adr_env):
        """Migration should use default status for unknown status values."""
        from tools.scripts.adr_utils import DEFAULT_STATUS
        from tools.scripts.check_adr import migrate_legacy_adr
        from tools.scripts.adr_utils import get_adr_files
        from tools.scripts.check_frontmatter import parse_frontmatter

        filepath = create_legacy_adr_file(
            adr_env.adr_dir,
            26001,
            "Legacy ADR",
            "legacy_adr",
            status="UnknownStatus",  # Not in corrections map
        )

        result = migrate_legacy_adr(filepath)

        assert result is True
        content = filepath.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(content)
        assert frontmatter is not None
        assert frontmatter.get("status") == DEFAULT_STATUS

    def test_migrate_without_status_section(self, adr_env):
        """Migration should use default status when no Status section exists."""
        from tools.scripts.adr_utils import DEFAULT_STATUS
        from tools.scripts.check_adr import migrate_legacy_adr
        from tools.scripts.adr_utils import get_adr_files
        from tools.scripts.check_frontmatter import parse_frontmatter

        # Create file without Status section
        filepath = adr_env.adr_dir / "adr_26001_no_status.md"
        content = """# ADR-26001: No Status ADR

## Context

Some context.
"""
        filepath.write_text(content, encoding="utf-8")

        result = migrate_legacy_adr(filepath)

        assert result is True
        new_content = filepath.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(new_content)
        assert frontmatter is not None
        assert frontmatter.get("status") == DEFAULT_STATUS

    def test_migrate_skips_file_without_valid_header(self, adr_env):
        """Migration should skip files without valid ADR header."""
        from tools.scripts.check_adr import migrate_legacy_adr

        # Create file without valid header
        filepath = adr_env.adr_dir / "adr_26001_invalid.md"
        content = """# Not an ADR header

Some content.
"""
        filepath.write_text(content, encoding="utf-8")

        result = migrate_legacy_adr(filepath)

        assert result is False  # Can't migrate without valid header


# ======================
# Unit Tests: CLI Migration Mode
# ======================


class TestCliMigrateMode:
    """Tests for --migrate CLI mode."""

    def test_migrate_mode_migrates_legacy_files(self, adr_env, capsys):
        """--migrate should add frontmatter to legacy ADR files."""
        from tools.scripts.check_adr import main
        from tools.scripts.check_frontmatter import parse_frontmatter

        filepath = create_legacy_adr_file(adr_env.adr_dir, 26001, "Legacy ADR", "legacy_adr")

        exit_code = main(["--migrate"])

        assert exit_code == 0
        # Semantic check: Verify file now has frontmatter
        content = filepath.read_text(encoding="utf-8")
        assert parse_frontmatter(content) is not None

    def test_migrate_mode_no_legacy_files(self, adr_env, caplog):
        """--migrate with no legacy files should report nothing to migrate."""
        import logging
        caplog.set_level(logging.INFO)
        from tools.scripts.check_adr import main
    
        # Create only files with frontmatter
        create_adr_file_full(adr_env.adr_dir, 26001, "Modern ADR", "modern_adr")
    
        exit_code = main(["--migrate"])
    
        assert exit_code == 0
        assert caplog.text  # Should produce some output informing the user

    def test_migrate_mode_verbose(self, adr_env, caplog):
        """--migrate --verbose should show detailed output."""
        import logging
        caplog.set_level(logging.INFO)
        from tools.scripts.check_adr import main
    
        create_legacy_adr_file(adr_env.adr_dir, 26001, "Legacy ADR", "legacy_adr")
    
        exit_code = main(["--migrate", "--verbose"])
    
        assert exit_code == 0
        assert caplog.text  # Verbose should produce output

# ======================
# Unit Tests: Tag Edge Cases
# ======================


class TestTagEdgeCases:
    """Tests for tag validation edge cases."""

    def test_single_tag_as_string(self, adr_env):
        """Single tag provided as string (not list) should be handled."""
        from tools.scripts.adr_utils import get_adr_files
        from tools.scripts.adr_utils import parse_index
        from tools.scripts.check_adr_index import validate_sync

        # Create ADR with single tag as string in YAML
        filepath = adr_env.adr_dir / "adr_26001_single_tag.md"
        content = """---
id: 26001
title: Single Tag ADR
date: 2024-01-15
status: proposed
tags: architecture
---

# ADR-26001: Single Tag ADR

## Context

Content.

## Decision

Content.

## Consequences

Content.

## Alternatives

Content.

## References

Content.

## Participants

Content.
"""
        filepath.write_text(content, encoding="utf-8")
        create_index(
            adr_env.index_path,
            [(26001, "Single Tag ADR", "/architecture/adr/adr_26001_single_tag.md")],
        )

        adr_files = get_adr_files()
        index_entries = parse_index()
        errors = validate_sync(adr_files, index_entries)

        # Should not produce invalid_tag error for valid single tag
        assert not any(e.error_type == "invalid_tag" for e in errors)


# ======================
# Unit Tests: Fix Mode Edge Cases
# ======================


class TestFixModeEdgeCases:
    """Tests for --fix mode edge cases."""

    def test_fix_with_invalid_status(self, adr_env, monkeypatch, capsys):
        """--fix should prompt to fix invalid status."""
        from tools.scripts.check_adr import main
        from tools.scripts.check_frontmatter import parse_frontmatter

        # Create ADR with invalid status
        filepath = create_adr_file_with_frontmatter(
            adr_env.adr_dir, 26001, "Invalid Status ADR", "invalid_status", status="prposed"
        )

        # Simulate user accepting the fix
        monkeypatch.setattr("builtins.input", lambda _: "")

        exit_code = main(["--fix"])

        # Semantic check: Verify status was corrected in the file
        content = filepath.read_text(encoding="utf-8")
        from tools.scripts.adr_utils import extract_status, VALID_STATUSES
        assert extract_status(content) != "prposed"
        assert extract_status(content) in VALID_STATUSES

    def test_fix_with_title_mismatch(self, adr_env, monkeypatch, capsys):
        """--fix should prompt to fix title mismatch."""
        from tools.scripts.check_adr import main

        # Create ADR with mismatched titles
        filepath = create_adr_file_with_frontmatter(
            adr_env.adr_dir,
            26001,
            "Header Title",
            "mismatch",
            status="accepted",
            frontmatter_title="Different Title",
        )
        create_index(
            adr_env.index_path,
            [(26001, "Header Title", "/architecture/adr/adr_26001_mismatch.md")],
        )

        # Simulate user accepting the fix
        monkeypatch.setattr("builtins.input", lambda _: "y")

        exit_code = main(["--fix"])

        # Semantic check: Verify titles are now synchronized
        content = filepath.read_text(encoding="utf-8")
        from tools.scripts.check_frontmatter import parse_frontmatter
        fm = parse_frontmatter(content)
        assert fm is not None
        assert fm.get("title") == "Header Title"


class TestSectionValidationEdgeCases:
    """Tests for section validation edge cases."""

    def test_adr_file_with_no_content(self, adr_env):
        """Should handle AdrFile with content=None."""
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_sections

        adr_file = AdrFile(
            path=adr_env.adr_dir / "test.md",
            number=26001,
            title="Test",
            content=None,  # No content
        )

        errors = validate_sections(adr_file)

        assert errors == []  # Should return empty list, not crash


# ======================
# Unit Tests: Promotion Gate Validation (ADR-26025)
# ======================
#
# ADR-26025 formalizes that `status: proposed` ADRs serve as RFCs.
# The "promotion gate" prevents an ADR from being accepted without
# sufficient analysis. validate_promotion_gate() returns (errors, warnings):
#
#   - accepted ADRs: errors if ## Alternatives < 2 entries or ## Participants empty
#   - proposed ADRs: warnings (not errors) if ## Alternatives is empty
#
# Tests assert on error_type strings (structured contract) and exit codes,
# never on human-readable messages — messages may change without breaking contracts.
#
# Entry detection patterns (all found in real ADRs in this repo):
#   "- **Name**: ..."   → dash bullet + bold  (ADR-26016)
#   "* **Name**: ..."   → asterisk bullet + bold  (ADR-26001, 26002, 26023)
#   "### Name"          → subheading per alternative  (ADR-26013, 26014)
#   "1. **Name**: ..."  → numbered list


from tools.scripts.check_frontmatter import calculate_tokens


def _make_adr_content(
    number: int,
    status: str,
    alternatives_body: str = "",
    participants_body: str = "",
    references_body: str = "",
) -> str:
    """Build minimal ADR content string for promotion gate tests.

    Args:
        number: ADR number.
        status: ADR status (proposed, accepted, etc.).
        alternatives_body: Raw text under ## Alternatives.
        participants_body: Raw text under ## Participants.
        references_body: Raw text under ## References.

    Returns:
        Full ADR content string with all required sections.
    """
    # 1. Generate base frontmatter
    fm = get_valid_frontmatter(
        "adr",
        title="Test",
        status=status,
    )
    if "options" not in fm:
        fm["options"] = {}
    fm["options"]["id"] = str(number)

    # 2. Define the body
    body = (
        f"# ADR-{number}: Test\n\n"
        f"## Date\n\n2024-01-01\n\n"
        f"## Status\n\n{status}\n\n"
        f"## Context\n\nSome context.\n\n"
        f"## Decision\n\nSome decision.\n\n"
        f"## Consequences\n\nSome consequences.\n\n"
        f"## Alternatives\n\n{alternatives_body}\n\n"
        f"## References\n\n{references_body}\n\n"
        f"## Participants\n\n{participants_body}\n"
    )

    # 3. Calculate tokens for the combined content to be precise
    # We use a dummy token_size first to get a close estimate
    fm["options"]["token_size"] = 0
    import yaml
    fm_yaml = yaml.dump(fm, sort_keys=False)
    full_content_estimate = f"--- \n{fm_yaml.strip()}\n---\n\n{body}"
    actual_tokens = calculate_tokens(full_content_estimate)

    # 4. Update with actual token count
    fm["options"]["token_size"] = actual_tokens
    fm_yaml = yaml.dump(fm, sort_keys=False)

    return f"--- \n{fm_yaml.strip()}\n---\n\n{body}"


class TestPromotionGateAlternatives:
    """Contract: accepted ADRs MUST have ≥2 entries in ## Alternatives.

    An 'entry' is a line starting with '- **' or a numbered item (e.g. '1.').
    Proposed ADRs get a warning (not error) if empty.

    Boundary: 0 → error, 1 → error, 2 → pass. Status determines severity.
    """

    # --- accepted: hard errors ---

    def test_accepted_with_zero_alternatives_fails(self, adr_env):
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_promotion_gate

        content = _make_adr_content(26099, "accepted", alternatives_body="")
        adr = AdrFile(path=adr_env.adr_dir / "test.md", number=26099, title="Test",
                      status="accepted", content=content)
        errors, _warnings = validate_promotion_gate(adr)
        assert len(errors) > 0
        assert any(e.error_type == "insufficient_alternatives" for e in errors)

    def test_accepted_with_one_alternative_fails(self, adr_env):
        # 1 < 2, still below the gate threshold
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_promotion_gate

        alt = "- **Option A**: Rejected. Some reason."
        content = _make_adr_content(26099, "accepted", alternatives_body=alt)
        adr = AdrFile(path=adr_env.adr_dir / "test.md", number=26099, title="Test",
                      status="accepted", content=content)
        errors, _warnings = validate_promotion_gate(adr)
        assert len(errors) > 0
        assert any(e.error_type == "insufficient_alternatives" for e in errors)

    def test_accepted_with_two_alternatives_passes(self, adr_env):
        # Exactly at the boundary — should pass
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_promotion_gate

        alt = (
            "- **Option A**: Rejected. Some reason.\n"
            "- **Option B**: Rejected. Another reason."
        )
        content = _make_adr_content(26099, "accepted", alternatives_body=alt)
        adr = AdrFile(path=adr_env.adr_dir / "test.md", number=26099, title="Test",
                      status="accepted", content=content)
        errors, _warnings = validate_promotion_gate(adr)
        assert not any(e.error_type == "insufficient_alternatives" for e in errors)

    def test_accepted_with_numbered_alternatives_passes(self, adr_env):
        # Numbered list format ("1. **...") is a valid alternative entry
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_promotion_gate

        alt = (
            "1. **Option A**: Rejected.\n"
            "2. **Option B**: Rejected."
        )
        content = _make_adr_content(26099, "accepted", alternatives_body=alt)
        adr = AdrFile(path=adr_env.adr_dir / "test.md", number=26099, title="Test",
                      status="accepted", content=content)
        errors, _warnings = validate_promotion_gate(adr)
        assert not any(e.error_type == "insufficient_alternatives" for e in errors)

    def test_accepted_with_asterisk_bullet_alternatives_passes(self, adr_env):
        # Asterisk bullet format ("* **...") used by ADR-26001, 26002, 26023
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_promotion_gate

        alt = (
            "* **Shell/Bash:** Rejected due to poor testability.\n"
            "* **Functional Python:** Rejected because shared state."
        )
        content = _make_adr_content(26099, "accepted", alternatives_body=alt)
        adr = AdrFile(path=adr_env.adr_dir / "test.md", number=26099, title="Test",
                      status="accepted", content=content)
        errors, _warnings = validate_promotion_gate(adr)
        assert not any(e.error_type == "insufficient_alternatives" for e in errors)

    def test_accepted_with_subheading_alternatives_passes(self, adr_env):
        # Subheading format ("### Name (Rejected)") used by ADR-26013, 26014
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_promotion_gate

        alt = (
            "### Persistent Artifact Storage (Rejected)\n\n"
            "Some analysis paragraph.\n\n"
            "### YAML as Source of Truth (Rejected)\n\n"
            "Another analysis paragraph."
        )
        content = _make_adr_content(26099, "accepted", alternatives_body=alt)
        adr = AdrFile(path=adr_env.adr_dir / "test.md", number=26099, title="Test",
                      status="accepted", content=content)
        errors, _warnings = validate_promotion_gate(adr)
        assert not any(e.error_type == "insufficient_alternatives" for e in errors)

    # --- proposed: soft warnings ---

    def test_proposed_with_empty_alternatives_warns(self, adr_env):
        # Proposed ADRs are still in RFC phase — no hard failure, just a nudge
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_promotion_gate

        content = _make_adr_content(26099, "proposed", alternatives_body="")
        adr = AdrFile(path=adr_env.adr_dir / "test.md", number=26099, title="Test",
                      status="proposed", content=content)
        errors, warnings = validate_promotion_gate(adr)
        assert len(errors) == 0
        assert len(warnings) > 0

    def test_proposed_with_alternatives_no_warning(self, adr_env):
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_promotion_gate

        alt = "- **Option A**: Rejected.\n- **Option B**: Rejected."
        content = _make_adr_content(26099, "proposed", alternatives_body=alt)
        adr = AdrFile(path=adr_env.adr_dir / "test.md", number=26099, title="Test",
                      status="proposed", content=content)
        errors, warnings = validate_promotion_gate(adr)
        assert len(errors) == 0
        assert len(warnings) == 0


class TestPromotionGateParticipants:
    """Contract: accepted ADRs MUST have non-empty ## Participants.

    'Non-empty' means the section body has any non-whitespace text.
    Proposed ADRs are exempt — the Participants section may be empty
    while the ADR is still in RFC phase.
    """

    def test_accepted_with_empty_participants_fails(self, adr_env):
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_promotion_gate

        # Alternatives pass the gate so the only error is empty participants
        alt = "- **A**: Rejected.\n- **B**: Rejected."
        content = _make_adr_content(26099, "accepted", alternatives_body=alt, participants_body="")
        adr = AdrFile(path=adr_env.adr_dir / "test.md", number=26099, title="Test",
                      status="accepted", content=content)
        errors, _warnings = validate_promotion_gate(adr)
        assert any(e.error_type == "empty_participants" for e in errors)

    def test_accepted_with_participants_passes(self, adr_env):
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_promotion_gate

        alt = "- **A**: Rejected.\n- **B**: Rejected."
        participants = "1. Test Author\n2. Test Reviewer"
        content = _make_adr_content(26099, "accepted", alternatives_body=alt,
                                     participants_body=participants)
        adr = AdrFile(path=adr_env.adr_dir / "test.md", number=26099, title="Test",
                      status="accepted", content=content)
        errors, _warnings = validate_promotion_gate(adr)
        assert not any(e.error_type == "empty_participants" for e in errors)

    def test_proposed_with_empty_participants_no_error(self, adr_env):
        # Proposed ADRs are exempt from the participants requirement
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_promotion_gate

        content = _make_adr_content(26099, "proposed", participants_body="")
        adr = AdrFile(path=adr_env.adr_dir / "test.md", number=26099, title="Test",
                      status="proposed", content=content)
        errors, _warnings = validate_promotion_gate(adr)
        assert not any(e.error_type == "empty_participants" for e in errors)


class TestPromotionGateCLIIntegration:
    """Contract: promotion gate feeds into main() exit code.

    - Gate errors (accepted ADR failing criteria) → exit 1
    - Gate warnings (proposed ADR missing alternatives) → exit 0
    - Gate pass (all criteria met) → exit 0

    These tests use create_adr_file_full + create_index to set up
    a synced environment, so only the promotion gate determines the exit code.
    Tests assert solely on exit codes — never on output text.
    """

    def test_accepted_adr_failing_gate_causes_exit_1(self, adr_env):
        """Synced but under-analyzed accepted ADR → exit 1."""
        from tools.scripts.check_adr import main

        # Write ADR content directly — no dependency on helper placeholder strings.
        # This accepted ADR has no "- **" entries and empty participants.
        content = _make_adr_content(
            26090, "accepted",
            alternatives_body="No real alternatives analyzed.",
            participants_body="",
        )
        filepath = adr_env.adr_dir / "adr_26090_gate_fail_test.md"
        filepath.write_text(content, encoding="utf-8")

        create_index(
            adr_env.index_path,
            [(26090, "Gate Fail Test", "/architecture/adr/adr_26090_gate_fail_test.md")],
        )

        assert main([]) == 1

    def test_proposed_adr_with_empty_alternatives_still_exits_0(self, adr_env):
        """Synced proposed ADR with no alternatives → warnings only, exit 0."""
        from tools.scripts.check_adr import main

        # Write directly — proposed with empty alternatives should only warn.
        content = _make_adr_content(
            26091, "proposed",
            alternatives_body="",
            participants_body="",
        )
        filepath = adr_env.adr_dir / "adr_26091_proposed_warning_test.md"
        filepath.write_text(content, encoding="utf-8")

        create_index(
            adr_env.index_path,
            [(26091, "Proposed Warning Test", "/architecture/adr/adr_26091_proposed_warning_test.md")],
        )

        assert main([]) == 0


# ======================
# Duplicate Section Detection Tests
# ======================


class TestDuplicateSections:
    """Contract: validate_sections() must detect duplicate ## headers.

    A section name appearing more than once produces a 'duplicate_section' error.
    The set-based approach silently collapsed duplicates — this catches them.
    """

    def test_duplicate_section_produces_error(self, adr_env):
        """ADR with two ## Participants headers should produce duplicate_section error."""
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_sections

        content = (
            "---\nid: 26099\ntitle: Test\ndate: 2026-01-01\n"
            "status: proposed\ntags: [architecture]\nsuperseded_by: null\n---\n\n"
            "# ADR-26099: Test\n\n"
            "## Context\n\nSome context.\n\n"
            "## Decision\n\nSome decision.\n\n"
            "## Consequences\n\nSome consequences.\n\n"
            "## Alternatives\n\nSome alternatives.\n\n"
            "## References\n\nSome references.\n\n"
            "## Participants\n\n"
            "## Participants\n\n1. Test Author\n"
        )
        adr = AdrFile(
            path=adr_env.adr_dir / "test.md",
            number=26099,
            title="Test",
            content=content,
        )
        errors = validate_sections(adr)
        assert any(e.error_type == "duplicate_section" for e in errors)

    def test_no_duplicates_passes(self, adr_env):
        """ADR with unique sections should not produce duplicate_section error."""
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_sections

        content = _make_adr_content(26099, "proposed", participants_body="1. Author")
        adr = AdrFile(
            path=adr_env.adr_dir / "test.md",
            number=26099,
            title="Test",
            content=content,
        )
        errors = validate_sections(adr)
        assert not any(e.error_type == "duplicate_section" for e in errors)

    def test_three_duplicates_produce_single_error(self, adr_env):
        """Three ## Participants headers should produce exactly one duplicate_section error."""
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_sections

        content = (
            "---\nid: 26099\ntitle: Test\ndate: 2026-01-01\n"
            "status: proposed\ntags: [architecture]\nsuperseded_by: null\n---\n\n"
            "# ADR-26099: Test\n\n"
            "## Context\n\nSome context.\n\n"
            "## Decision\n\nSome decision.\n\n"
            "## Consequences\n\nSome consequences.\n\n"
            "## Alternatives\n\nSome alternatives.\n\n"
            "## References\n\nSome references.\n\n"
            "## Participants\n\n"
            "## Participants\n\n1. Author\n"
            "## Participants\n\n2. Another Author\n"
        )
        adr = AdrFile(
            path=adr_env.adr_dir / "test.md",
            number=26099,
            title="Test",
            content=content,
        )
        errors = validate_sections(adr)
        dup_errors = [e for e in errors if e.error_type == "duplicate_section"]
        # One error per duplicated section name, not per occurrence
        assert len(dup_errors) == 1


class TestFixDuplicateSections:
    """Contract: fix_duplicate_sections() merges duplicate ## headers.

    Keeps the first header, concatenates all bodies (preserving order).
    Returns True if any file was modified.
    """

    def test_merges_two_duplicate_sections(self, adr_env):
        """Two ## Participants should merge into one with combined body."""
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import fix_duplicate_sections

        content = (
            "---\nid: 26099\ntitle: Test\ndate: 2026-01-01\n"
            "status: accepted\ntags: [architecture]\nsuperseded_by: null\n---\n\n"
            "# ADR-26099: Test\n\n"
            "## Context\n\nSome context.\n\n"
            "## Decision\n\nSome decision.\n\n"
            "## Consequences\n\nSome consequences.\n\n"
            "## Alternatives\n\n"
            "- **Option A**: Rejected.\n"
            "- **Option B**: Rejected.\n\n"
            "## References\n\nSome references.\n\n"
            "## Participants\n\n"
            "## Participants\n\n1. Test Author\n"
        )
        filepath = adr_env.adr_dir / "adr_26099_test.md"
        filepath.write_text(content, encoding="utf-8")

        adr = AdrFile(
            path=filepath,
            number=26099,
            title="Test",
            status="accepted",
            content=content,
        )

        with patch("builtins.input", return_value="y"):
            modified = fix_duplicate_sections([adr])
        assert modified is True

        result = filepath.read_text(encoding="utf-8")
        # Should have exactly one ## Participants
        assert result.count("## Participants") == 1
        # The merged body should contain the actual content
        assert "1. Test Author" in result

    def test_no_duplicates_returns_false(self, adr_env):
        """When no duplicates exist, should return False (no changes)."""
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import fix_duplicate_sections

        content = _make_adr_content(26099, "proposed", participants_body="1. Author")
        filepath = adr_env.adr_dir / "adr_26099_test.md"
        filepath.write_text(content, encoding="utf-8")

        adr = AdrFile(
            path=filepath,
            number=26099,
            title="Test",
            status="proposed",
            content=content,
        )

        modified = fix_duplicate_sections([adr])
        assert modified is False

    def test_merges_preserves_body_content(self, adr_env):
        """Merged section should contain content from all duplicate bodies."""
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import fix_duplicate_sections

        content = (
            "---\nid: 26099\ntitle: Test\ndate: 2026-01-01\n"
            "status: accepted\ntags: [architecture]\nsuperseded_by: null\n---\n\n"
            "# ADR-26099: Test\n\n"
            "## Context\n\nSome context.\n\n"
            "## Decision\n\nSome decision.\n\n"
            "## Consequences\n\nSome consequences.\n\n"
            "## Alternatives\n\n"
            "- **Option A**: Rejected.\n"
            "- **Option B**: Rejected.\n\n"
            "## References\n\nSome references.\n\n"
            "## Participants\n\nFirst body content.\n\n"
            "## Participants\n\n1. Test Author\n"
        )
        filepath = adr_env.adr_dir / "adr_26099_test.md"
        filepath.write_text(content, encoding="utf-8")

        adr = AdrFile(
            path=filepath,
            number=26099,
            title="Test",
            status="accepted",
            content=content,
        )

        with patch("builtins.input", return_value="y"):
            fix_duplicate_sections([adr])

        result = filepath.read_text(encoding="utf-8")
        assert result.count("## Participants") == 1
        assert "First body content." in result
        assert "1. Test Author" in result

    def test_rejected_merge_returns_false(self, adr_env):
        """User rejecting merge should return False and not modify file."""
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import fix_duplicate_sections

        content = (
            "---\nid: 26099\ntitle: Test\ndate: 2026-01-01\n"
            "status: accepted\ntags: [architecture]\nsuperseded_by: null\n---\n\n"
            "# ADR-26099: Test\n\n"
            "## Context\n\nSome context.\n\n"
            "## Decision\n\nSome decision.\n\n"
            "## Consequences\n\nSome consequences.\n\n"
            "## Alternatives\n\n"
            "- **Option A**: Rejected.\n"
            "- **Option B**: Rejected.\n\n"
            "## References\n\nSome references.\n\n"
            "## Participants\n\n"
            "## Participants\n\n1. Test Author\n"
        )
        filepath = adr_env.adr_dir / "adr_26099_test.md"
        filepath.write_text(content, encoding="utf-8")

        adr = AdrFile(
            path=filepath,
            number=26099,
            title="Test",
            status="accepted",
            content=content,
        )

        with patch("builtins.input", return_value="n"):
            modified = fix_duplicate_sections([adr])
        assert modified is False

        # File should be unchanged
        result = filepath.read_text(encoding="utf-8")
        assert result.count("## Participants") == 2


class TestPromotionGateInFixMode:
    """Contract: --fix mode must run promotion gate validation.

    Previously, --fix exited at line 1313 before reaching the promotion
    gate block (line 1357). This caused pre-commit (--fix) to pass while
    CI (--verbose) failed on the same ADR.
    """

    def test_fix_mode_returns_exit_1_for_empty_participants(self, adr_env):
        """--fix mode should fail when accepted ADR has empty ## Participants."""
        from tools.scripts.check_adr import main

        content = _make_adr_content(
            26090, "accepted",
            alternatives_body=(
                "- **Option A**: Rejected.\n"
                "- **Option B**: Rejected."
            ),
            participants_body="",
        )
        filepath = adr_env.adr_dir / "adr_26090_gate_fix_test.md"
        filepath.write_text(content, encoding="utf-8")

        create_index(
            adr_env.index_path,
            [(26090, "Gate Fix Test", "/architecture/adr/adr_26090_gate_fix_test.md")],
        )

        assert main(["--fix"]) == 1

    def test_fix_mode_returns_exit_0_when_gate_passes(self, adr_env):
        """--fix mode should succeed when accepted ADR passes promotion gate."""
        from tools.scripts.check_adr import main

        content = _make_adr_content(
            26090, "accepted",
            alternatives_body=(
                "- **Option A**: Rejected.\n"
                "- **Option B**: Rejected."
            ),
            participants_body="1. Test Author",
        )
        filepath = adr_env.adr_dir / "adr_26090_gate_pass_test.md"
        filepath.write_text(content, encoding="utf-8")

        create_index(
            adr_env.index_path,
            [(26090, "Gate Pass Test", "/architecture/adr/adr_26090_gate_pass_test.md")],
        )

        assert main(["--fix"]) == 0

    def test_accepted_adr_passing_gate_exits_0(self, adr_env):
        """Synced accepted ADR with ≥2 alternatives + participants → exit 0."""
        from tools.scripts.check_adr import main

        # Write directly — this accepted ADR satisfies all gate criteria.
        content = _make_adr_content(
            26092, "accepted",
            alternatives_body=(
                "- **Option A**: Rejected. Reason.\n"
                "- **Option B**: Rejected. Reason."
            ),
            participants_body="1. Author A\n2. Author B",
        )
        filepath = adr_env.adr_dir / "adr_26092_gate_pass_test.md"
        filepath.write_text(content, encoding="utf-8")

        create_index(
            adr_env.index_path,
            [(26092, "Gate Pass Test", "/architecture/adr/adr_26092_gate_pass_test.md")],
        )

        assert main([]) == 0


# ======================
# Section Whitelist Validation
# ======================


class TestSectionWhitelist:
    """Contract: validate_sections() must reject sections not in allowed_sections.

    Allowed sections are defined in adr_config.yaml as the Single Source of Truth.
    Any ## header not in that list should produce an 'unexpected_section' error.
    """

    def test_unexpected_section_produces_error(self, adr_env):
        """ADR with a ## section not in allowed_sections should fail."""
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_sections

        content = """---
id: 26050
title: Test Unexpected Section
date: 2024-01-15
status: proposed
tags: [architecture]
---

# ADR-26050: Test Unexpected Section

## Date
2024-01-15

## Status
proposed

## Context
Some context.

## Decision
Some decision.

## Consequences
Some consequences.

## CustomBogusSection
This should be flagged.

## Alternatives
Some alternatives.

## References
Some references.

## Participants
1. Author
"""
        adr = AdrFile(
            path=adr_env.adr_dir / "adr_26050_test.md",
            number=26050,
            title="Test Unexpected Section",
            status="proposed",
            content=content,
        )

        errors = validate_sections(adr)
        unexpected_errors = [e for e in errors if e.error_type == "unexpected_section"]
        assert len(unexpected_errors) == 1
        assert 26050 == unexpected_errors[0].number

    def test_all_allowed_sections_pass(self, adr_env):
        """ADR with only allowed sections should produce no unexpected_section errors."""
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_sections

        content = """---
id: 26051
title: All Allowed Sections
date: 2024-01-15
status: proposed
tags: [architecture]
---

# ADR-26051: All Allowed Sections

## Title
All Allowed Sections

## Date
2024-01-15

## Status
proposed

## Context
Some context.

## Decision
Some decision.

## Consequences
Some consequences.

## Alternatives
Some alternatives.

## References
Some references.

## Participants
1. Author
"""
        adr = AdrFile(
            path=adr_env.adr_dir / "adr_26051_test.md",
            number=26051,
            title="All Allowed Sections",
            status="proposed",
            content=content,
        )

        errors = validate_sections(adr)
        unexpected_errors = [e for e in errors if e.error_type == "unexpected_section"]
        assert len(unexpected_errors) == 0


class TestConditionalSections:
    """Contract: conditional sections are only allowed for specific statuses.

    ## Rejection Rationale is only valid in ADRs with status: rejected.
    """

    def test_rejection_rationale_in_proposed_adr_produces_error(self, adr_env):
        """## Rejection Rationale in a proposed ADR should fail."""
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_sections

        content = """---
id: 26052
title: Wrong Rationale
date: 2024-01-15
status: proposed
tags: [architecture]
---

# ADR-26052: Wrong Rationale

## Date
2024-01-15

## Status
proposed

## Rejection Rationale
Should not be here in a proposed ADR.

## Context
Some context.

## Decision
Some decision.

## Consequences
Some consequences.

## Alternatives
Some alternatives.

## References
Some references.

## Participants
1. Author
"""
        adr = AdrFile(
            path=adr_env.adr_dir / "adr_26052_test.md",
            number=26052,
            title="Wrong Rationale",
            status="proposed",
            content=content,
        )

        errors = validate_sections(adr)
        conditional_errors = [e for e in errors if e.error_type == "conditional_section_violation"]
        assert len(conditional_errors) == 1
        assert 26052 == conditional_errors[0].number

    def test_rejection_rationale_in_rejected_adr_passes(self, adr_env):
        """## Rejection Rationale in a rejected ADR should pass."""
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_sections

        content = """---
id: 26053
title: Proper Rejection
date: 2024-01-15
status: rejected
tags: [architecture]
---

# ADR-26053: Proper Rejection

## Date
2024-01-15

## Status
rejected

## Rejection Rationale
Valid rationale for rejection.

## Context
Some context.

## Decision
Some decision.

## Consequences
Some consequences.

## Alternatives
Some alternatives.

## References
Some references.

## Participants
1. Author
"""
        adr = AdrFile(
            path=adr_env.adr_dir / "adr_26053_test.md",
            number=26053,
            title="Proper Rejection",
            status="rejected",
            content=content,
        )

        errors = validate_sections(adr)
        conditional_errors = [e for e in errors if e.error_type == "conditional_section_violation"]
        assert len(conditional_errors) == 0


class TestCodeFencedSectionsIgnored:
    """Contract: ## headers inside fenced code blocks must not be treated as sections.

    The regex ^## with re.MULTILINE matches inside code fences. The parser
    must strip code blocks before extracting section headers.
    """

    def test_section_inside_code_block_is_ignored(self, adr_env):
        """## headers inside ```markdown fences should not be counted as sections."""
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_sections

        content = '''---
id: 26054
title: Code Block Sections
date: 2024-01-15
status: proposed
tags: [architecture]
---

# ADR-26054: Code Block Sections

## Date
2024-01-15

## Status
proposed

## Context
Some context.

## Decision

Example of what an ARCHITECTURE.md looks like:

```markdown
## Governing ADRs (in hub)
- ADR-001: Example

## Implementation ADRs (in this repo)
- ADR-002: Example
```

## Consequences
Some consequences.

## Alternatives
Some alternatives.

## References
Some references.

## Participants
1. Author
'''
        adr = AdrFile(
            path=adr_env.adr_dir / "adr_26054_test.md",
            number=26054,
            title="Code Block Sections",
            status="proposed",
            content=content,
        )

        errors = validate_sections(adr)
        unexpected_errors = [e for e in errors if e.error_type == "unexpected_section"]
        assert len(unexpected_errors) == 0


# ======================
# Two-Level Index (Status × Primary Tag)
# ======================


# Helper: minimal ADR content for conditional section/field tests
def _adr_content(number, title, status, extra_sections="", superseded_by="null"):
    """Build minimal valid ADR content with optional extra sections."""
    return f"""---
id: {number}
title: {title}
date: 2024-01-15
status: {status}
tags: [architecture]
superseded_by: {superseded_by}
---

# ADR-{number}: {title}

## Date
2024-01-15

## Status
{status}

{extra_sections}## Context
Some context.

## Decision
Some decision.

## Consequences
Some consequences.

## Alternatives
- **Option A**: First alternative.
- **Option B**: Second alternative.

## References
Some references.

## Participants
1. Author
"""


class TestConditionalSectionsMissing:
    """Contract: when a status requires a conditional section, its absence is an error.

    This is the inverse of TestConditionalSections which tests that conditional
    sections are rejected for wrong statuses. Here we test that they are
    required for the right statuses.
    """

    def test_rejected_adr_without_rejection_rationale_fails(self, adr_env):
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_sections

        content = _adr_content(26060, "Missing Rationale", "rejected")
        adr = AdrFile(
            path=adr_env.adr_dir / "adr_26060_test.md",
            number=26060, title="Missing Rationale",
            status="rejected", content=content,
        )
        errors = validate_sections(adr)
        missing = [e for e in errors if e.error_type == "missing_conditional_section"]
        assert any(e.number == 26060 for e in missing)

    def test_superseded_adr_without_supersession_rationale_fails(self, adr_env):
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_sections

        content = _adr_content(26061, "Missing Supersession", "superseded",
                               superseded_by="ADR-26099")
        adr = AdrFile(
            path=adr_env.adr_dir / "adr_26061_test.md",
            number=26061, title="Missing Supersession",
            status="superseded", content=content,
        )
        errors = validate_sections(adr)
        missing = [e for e in errors if e.error_type == "missing_conditional_section"]
        assert any(e.number == 26061 for e in missing)

    def test_superseded_adr_with_supersession_rationale_passes(self, adr_env):
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_sections

        extra = "## Supersession Rationale\nReplaced by a better approach.\n\n"
        content = _adr_content(26062, "Proper Supersession", "superseded",
                               extra_sections=extra, superseded_by="ADR-26099")
        adr = AdrFile(
            path=adr_env.adr_dir / "adr_26062_test.md",
            number=26062, title="Proper Supersession",
            status="superseded", content=content,
        )
        errors = validate_sections(adr)
        conditional = [e for e in errors
                       if e.error_type in ("missing_conditional_section",
                                           "conditional_section_violation")]
        assert conditional == []

    def test_deprecated_adr_without_deprecation_rationale_fails(self, adr_env):
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_sections

        content = _adr_content(26063, "Missing Deprecation", "deprecated")
        adr = AdrFile(
            path=adr_env.adr_dir / "adr_26063_test.md",
            number=26063, title="Missing Deprecation",
            status="deprecated", content=content,
        )
        errors = validate_sections(adr)
        missing = [e for e in errors if e.error_type == "missing_conditional_section"]
        assert any(e.number == 26063 for e in missing)

    def test_proposed_adr_without_conditional_sections_passes(self, adr_env):
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_sections

        content = _adr_content(26064, "Plain Proposed", "proposed")
        adr = AdrFile(
            path=adr_env.adr_dir / "adr_26064_test.md",
            number=26064, title="Plain Proposed",
            status="proposed", content=content,
        )
        errors = validate_sections(adr)
        conditional = [e for e in errors
                       if e.error_type in ("missing_conditional_section",
                                           "conditional_section_violation")]
        assert conditional == []


class TestValidateConditionalFields:
    """Contract: status-dependent frontmatter fields must be present and valid.

    When status is 'superseded', superseded_by must be a non-null
    'ADR-NNNNN' string referencing an existing ADR.
    """

    def test_superseded_with_null_superseded_by_fails(self, adr_env):
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_conditional_fields

        adr = AdrFile(
            path=adr_env.adr_dir / "adr_26070_test.md",
            number=26070, title="Null Successor",
            status="superseded",
            frontmatter={"id": 26070, "title": "Null Successor",
                         "date": "2024-01-15", "status": "superseded",
                         "tags": ["architecture"], "superseded_by": None},
        )
        errors = validate_conditional_fields(adr)
        assert any(e.error_type == "missing_conditional_field" for e in errors)

    def test_superseded_with_valid_superseded_by_passes(self, adr_env):
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_conditional_fields

        adr = AdrFile(
            path=adr_env.adr_dir / "adr_26071_test.md",
            number=26071, title="Valid Successor",
            status="superseded",
            frontmatter={"id": 26071, "title": "Valid Successor",
                         "date": "2024-01-15", "status": "superseded",
                         "tags": ["architecture"], "superseded_by": "ADR-26099"},
        )
        errors = validate_conditional_fields(adr, all_adr_numbers={26071, 26099})
        assert errors == []

    def test_superseded_with_nonexistent_successor_fails(self, adr_env):
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_conditional_fields

        adr = AdrFile(
            path=adr_env.adr_dir / "adr_26072_test.md",
            number=26072, title="Ghost Successor",
            status="superseded",
            frontmatter={"id": 26072, "title": "Ghost Successor",
                         "date": "2024-01-15", "status": "superseded",
                         "tags": ["architecture"], "superseded_by": "ADR-99999"},
        )
        errors = validate_conditional_fields(adr, all_adr_numbers={26072})
        assert any(e.error_type == "invalid_field_reference" for e in errors)

    def test_accepted_adr_ignores_superseded_by(self, adr_env):
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_conditional_fields

        adr = AdrFile(
            path=adr_env.adr_dir / "adr_26073_test.md",
            number=26073, title="Normal Accepted",
            status="accepted",
            frontmatter={"id": 26073, "title": "Normal Accepted",
                         "date": "2024-01-15", "status": "accepted",
                         "tags": ["architecture"], "superseded_by": None},
        )
        errors = validate_conditional_fields(adr)
        assert errors == []

    def test_superseded_by_must_be_adr_reference_format(self, adr_env):
        """Bare integers are rejected — must use 'ADR-NNNNN' string format."""
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_conditional_fields

        adr = AdrFile(
            path=adr_env.adr_dir / "adr_26074_test.md",
            number=26074, title="Bare Integer",
            status="superseded",
            frontmatter={"id": 26074, "title": "Bare Integer",
                         "date": "2024-01-15", "status": "superseded",
                         "tags": ["architecture"], "superseded_by": 26099},
        )
        errors = validate_conditional_fields(adr)
        assert any(e.error_type == "invalid_field_type" for e in errors)


class TestConditionalSectionContent:
    """Contract: conditional sections must have meaningful content.

    Minimum word count is config-driven (min_conditional_section_words).
    """

    def test_empty_conditional_section_fails(self, adr_env):
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_conditional_section_content

        extra = "## Rejection Rationale\n\n"
        content = _adr_content(26080, "Empty Rationale", "rejected",
                               extra_sections=extra)
        adr = AdrFile(
            path=adr_env.adr_dir / "adr_26080_test.md",
            number=26080, title="Empty Rationale",
            status="rejected", content=content,
        )
        errors = validate_conditional_section_content(adr)
        assert any(e.error_type == "empty_conditional_section" for e in errors)

    def test_whitespace_only_conditional_section_fails(self, adr_env):
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_conditional_section_content

        extra = "## Rejection Rationale\n   \n   \n\n"
        content = _adr_content(26081, "Whitespace Rationale", "rejected",
                               extra_sections=extra)
        adr = AdrFile(
            path=adr_env.adr_dir / "adr_26081_test.md",
            number=26081, title="Whitespace Rationale",
            status="rejected", content=content,
        )
        errors = validate_conditional_section_content(adr)
        assert any(e.error_type == "empty_conditional_section" for e in errors)

    def test_below_minimum_word_count_fails(self, adr_env):
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_conditional_section_content

        extra = "## Rejection Rationale\nTBD\n\n"
        content = _adr_content(26082, "TBD Rationale", "rejected",
                               extra_sections=extra)
        adr = AdrFile(
            path=adr_env.adr_dir / "adr_26082_test.md",
            number=26082, title="TBD Rationale",
            status="rejected", content=content,
        )
        errors = validate_conditional_section_content(adr)
        assert any(e.error_type == "empty_conditional_section" for e in errors)

    def test_substantive_content_passes(self, adr_env):
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_conditional_section_content

        extra = "## Rejection Rationale\nThis approach was rejected because it conflicts with principles.\n\n"
        content = _adr_content(26083, "Good Rationale", "rejected",
                               extra_sections=extra)
        adr = AdrFile(
            path=adr_env.adr_dir / "adr_26083_test.md",
            number=26083, title="Good Rationale",
            status="rejected", content=content,
        )
        errors = validate_conditional_section_content(adr)
        assert errors == []

    def test_empty_supersession_rationale_fails(self, adr_env):
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr import validate_conditional_section_content

        extra = "## Supersession Rationale\n\n"
        content = _adr_content(26084, "Empty Supersession", "superseded",
                               extra_sections=extra, superseded_by="ADR-26099")
        adr = AdrFile(
            path=adr_env.adr_dir / "adr_26084_test.md",
            number=26084, title="Empty Supersession",
            status="superseded", content=content,
        )
        errors = validate_conditional_section_content(adr)
        assert any(e.error_type == "empty_conditional_section" for e in errors)


# ======================
# Tests: fix_index() Duplicate Detection
# ======================


class TestFixIndexDuplicateDetection:
    """Contract: fix_index() warns when same ADR number appears in multiple index locations.

    Non-brittle design:
    - Uses unique high ADR numbers (269XX) to avoid conflicts with real ADRs
    - Asserts on error_type and location patterns, not exact message strings
    - Self-contained test data, no dependency on external config state
    - Mocks INDEX_PATH to avoid corrupting real index file
    """

    def test_duplicate_adr_prints_warning(self, tmp_path, caplog, monkeypatch):
        """Same ADR number in different status/tag combinations produces warning."""
        import logging
        caplog.set_level(logging.WARNING)
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr_index import fix_index, INDEX_PATH
    
        # Use high ADR numbers to avoid conflicts with real ADRs
        test_number = 26999
    
        # Mock get_adr_files to return two ADRs with same number but different status
        def mock_get_adr_files():
            return [
                AdrFile(
                    path=tmp_path / f"adr_{test_number}_test1.md",
                    number=test_number,
                    title="Test ADR",
                    status="accepted",
                    frontmatter={
                        "id": test_number,
                        "title": "Test ADR",
                        "status": "accepted",
                        "tags": ["governance"],
                        "date": "2026-01-01"
                    }
                ),
                AdrFile(
                    path=tmp_path / f"adr_{test_number}_test2.md",
                    number=test_number,
                    title="Test ADR Duplicate",
                    status="rejected",
                    frontmatter={
                        "id": test_number,
                        "title": "Test ADR Duplicate",
                        "status": "rejected",
                        "tags": ["governance"],
                        "date": "2026-01-01"
                    }
                )
            ]
    
        # Mock INDEX_PATH to write to temp file instead of real index
        temp_index = tmp_path / "test_adr_index.md"
        monkeypatch.setattr("tools.scripts.check_adr_index.INDEX_PATH", temp_index)
        monkeypatch.setattr("tools.scripts.adr_utils.get_adr_files", mock_get_adr_files)
    
        # Call fix_index
        fix_index()
    
        # Check warning was logged (semantic assertion on pattern, not exact string)
        assert f"ADR-{test_number}" in caplog.text
        assert "multiple index locations" in caplog.text
        # Verify both locations are mentioned (order-independent)
        assert any("accepted" in line for line in caplog.text.split('\n'))
        assert any("rejected" in line for line in caplog.text.split('\n'))

    def test_no_duplicate_no_warning(self, tmp_path, capsys, monkeypatch):
        """Unique ADR numbers produce no warnings."""
        from tools.scripts.adr_utils import AdrFile
        from tools.scripts.check_adr_index import fix_index, INDEX_PATH

        def mock_get_adr_files():
            return [
                AdrFile(
                    path=tmp_path / "adr_26997_test1.md",
                    number=26997,
                    title="Test ADR 1",
                    status="accepted",
                    frontmatter={
                        "id": 26997,
                        "title": "Test ADR 1",
                        "status": "accepted",
                        "tags": ["governance"],
                        "date": "2026-01-01"
                    }
                ),
                AdrFile(
                    path=tmp_path / "adr_26998_test2.md",
                    number=26998,
                    title="Test ADR 2",
                    status="rejected",
                    frontmatter={
                        "id": 26998,
                        "title": "Test ADR 2",
                        "status": "rejected",
                        "tags": ["governance"],
                        "date": "2026-01-01"
                    }
                )
            ]

        # Mock INDEX_PATH to write to temp file instead of real index
        temp_index = tmp_path / "test_adr_index.md"
        monkeypatch.setattr("tools.scripts.check_adr_index.INDEX_PATH", temp_index)
        monkeypatch.setattr("tools.scripts.check_adr.get_adr_files", mock_get_adr_files)

        # Call fix_index
        fix_index()

        # Check no duplicate warning was printed
        captured = capsys.readouterr()
        assert "multiple index locations" not in captured.err
