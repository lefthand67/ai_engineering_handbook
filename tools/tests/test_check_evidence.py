#!/usr/bin/env python3
"""
Test suite for check_evidence.py - Evidence artifact validator.

Tests are organized following the behavior-based testing principle:
- Test what the code does, not how it does it
- Use semantic assertions rather than exact string matching
- Parametrize from config, not hardcoded lists (SSoT-driven)

Test classes and their contracts:
- TestConfigLoading: Config loads from .vadocs/types/evidence.conf.json, resolves parent_config tags
- TestValidateNaming: Filenames match regex patterns from config per artifact type
- TestValidateFrontmatter: Required fields present, valid statuses/severity/tags per type
- TestValidateSections: Required sections present, no unexpected sections
- TestDetectOrphanedSources: Sources with null extracted_into flagged past threshold
- TestDiscoverArtifacts: Scans correct directories, returns sorted artifacts
- TestCli: Exit codes 0 (valid) / 1 (errors), --verbose and --check-staged flags
"""

import json
import shutil
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

import tools.scripts.check_evidence as _module


def _recent_date() -> str:
    """Return an ISO date 5 days ago — always within the orphan threshold."""
    return (date.today() - timedelta(days=5)).isoformat()


# ======================
# Config-driven constants (SSoT)
# ======================
# All paths resolve from convention: .vadocs/types/evidence.conf.json → parent_config.
# No pyproject.toml indirection — .vadocs/ directory IS the convention.

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Convention-based config path
_EVIDENCE_CONFIG_REL = ".vadocs/types/evidence.conf.json"
_EVIDENCE_CONFIG_PATH = _REPO_ROOT / _EVIDENCE_CONFIG_REL

# Evidence config → parent_config relative path → parent config
with open(_EVIDENCE_CONFIG_PATH, encoding="utf-8") as _f:
    _EVIDENCE_CONFIG = json.load(_f)
_PARENT_CONFIG_REL = _EVIDENCE_CONFIG["parent_config"]
_PARENT_CONFIG_PATH = _REPO_ROOT / _PARENT_CONFIG_REL
with open(_PARENT_CONFIG_PATH, encoding="utf-8") as _f:
    _PARENT_CONFIG = json.load(_f)

# Derived constants — all from config, nothing hardcoded
_ARTIFACT_TYPES = _EVIDENCE_CONFIG["artifact_types"]
_NAMING_PATTERNS = _EVIDENCE_CONFIG["naming_patterns"]
_LIFECYCLE = _EVIDENCE_CONFIG["lifecycle"]
_COMMON_REQUIRED_FIELDS = _EVIDENCE_CONFIG["common_required_fields"]
_DATE_FORMAT = _PARENT_CONFIG.get("date_format", r"^\d{4}-\d{2}-\d{2}$")
# Tags in hub are dict with descriptions — extract keys for validation
_tags_raw = _PARENT_CONFIG["tags"]
_VALID_TAGS = list(_tags_raw.keys()) if isinstance(_tags_raw, dict) else _tags_raw

# Default values for common fields, keyed by field name.
# "id" and "date" need type-aware formatting; handled in _build_valid_frontmatter.
_COMMON_FIELD_DEFAULTS = {
    field: f"Test {field.capitalize()}" for field in _COMMON_REQUIRED_FIELDS
}


# ======================
# Test Fixtures & Helpers
# ======================


@dataclass
class EvidenceTestEnv:
    """Test environment with isolated evidence directory structure."""

    evidence_dir: Path
    root: Path

    def dir_for(self, artifact_type: str) -> Path:
        """Return the directory for a given artifact type, from config."""
        dirname = _ARTIFACT_TYPES[artifact_type]["directory_name"]
        return self.evidence_dir / dirname


def _resolve_field_default(field: str, type_config: dict) -> object:
    """Resolve a valid default value for a required field by searching config structure.

    Resolution order (no field names are hardcoded):
    1. Direct key match in type_config (e.g., "severity" → type_config["severity"][0])
    2. Pluralized key match (e.g., "status" → type_config["statuses"][0])
    3. Key match in parent config (e.g., "tags" → [parent_config["tags"][0]])
    4. Free-text fallback for fields with no validation list
    """
    # 1. Direct key match (e.g., severity → type_config["severity"])
    if field in type_config and isinstance(type_config[field], list) and type_config[field]:
        return type_config[field][0]

    # 2. Pluralized key match (e.g., status → type_config["statuses"])
    for suffix in ("s", "es"):
        plural = field + suffix
        if plural in type_config and isinstance(type_config[plural], list) and type_config[plural]:
            return type_config[plural][0]

    # 3. Parent config match (e.g., tags → parent_config["tags"])
    if field in _PARENT_CONFIG:
        val = _PARENT_CONFIG[field]
        if isinstance(val, dict) and val:
            # Hub tags are dict with descriptions — return first key
            return [next(iter(val))]
        if isinstance(val, list) and val:
            return [val[0]]

    # 4. Free-text fallback
    return f"test-{field}-value"


def _build_valid_frontmatter(artifact_type: str, **overrides) -> dict:
    """Build a valid frontmatter dict for any artifact type, fully config-driven.

    Common fields come from evidence.conf.json common_required_fields.
    Type-specific fields resolved via _resolve_field_default heuristic.
    Individual fields can be overridden via kwargs for negative testing.
    """
    type_config = _ARTIFACT_TYPES[artifact_type]
    prefix = type_config["id_prefix"]

    # Common required fields
    fm = dict(_COMMON_FIELD_DEFAULTS)
    # id and date need structured values, not plain strings
    fm["id"] = f"{prefix}-26001"
    fm["date"] = "2026-02-26"

    # Type-specific required fields — resolved dynamically from config
    for field in type_config["required_fields"]:
        fm[field] = _resolve_field_default(field, type_config)

    fm.update(overrides)
    return fm


def _build_valid_filename(artifact_type: str, artifact_id: str | None = None, slug: str = "test_slug") -> str:
    """Build a valid filename for a given artifact type from config prefix."""
    prefix = _ARTIFACT_TYPES[artifact_type]["id_prefix"]
    if artifact_id is None:
        artifact_id = f"{prefix}-26001"
    return f"{artifact_id}_{slug}.md"


def create_artifact_file(
    directory: Path,
    artifact_type: str,
    artifact_id: str | None = None,
    slug: str = "test_artifact",
    frontmatter_overrides: dict | None = None,
    sections: list[str] | None = None,
    extra_content: str = "",
) -> Path:
    """Create an evidence artifact file with valid frontmatter and sections.

    Builds valid-by-default content from config. Override specific fields
    or sections as needed for negative testing.

    Args:
        directory: Directory to create file in
        artifact_type: Type key from config (e.g., "analysis")
        artifact_id: Explicit ID (default: derived from config prefix)
        slug: Filename slug
        frontmatter_overrides: Dict of fields to override in frontmatter
        sections: List of section headers (default: required_sections from config)
        extra_content: Extra markdown to append after sections

    Returns:
        Path to created file
    """
    type_config = _ARTIFACT_TYPES[artifact_type]
    prefix = type_config["id_prefix"]
    if artifact_id is None:
        artifact_id = f"{prefix}-26001"

    fm = _build_valid_frontmatter(artifact_type, id=artifact_id)
    if frontmatter_overrides:
        fm.update(frontmatter_overrides)

    if sections is None:
        sections = list(type_config.get("required_sections", []))

    filename = f"{artifact_id}_{slug}.md"
    filepath = directory / filename

    # Build YAML frontmatter
    fm_lines = ["---"]
    for key, value in fm.items():
        if isinstance(value, list):
            fm_lines.append(f"{key}: [{', '.join(str(v) for v in value)}]")
        elif value is None:
            fm_lines.append(f"{key}: null")
        else:
            fm_lines.append(f"{key}: {value}")
    fm_lines.append("---")

    # Build body
    body_lines = [
        "",
        f"# {artifact_id}: {fm.get('title', 'Test')}",
        "",
    ]
    for section in sections:
        body_lines.append(f"## {section}")
        body_lines.append("")
        body_lines.append(f"Content for {section.lower()} section.")
        body_lines.append("")

    if extra_content:
        body_lines.append(extra_content)

    content = "\n".join(fm_lines + body_lines)
    filepath.write_text(content, encoding="utf-8")
    return filepath


def create_evidence_config(path: Path) -> None:
    """Copy real evidence config to test directory (SSoT)."""
    shutil.copy2(_EVIDENCE_CONFIG_PATH, path)


def create_hub_config(path: Path) -> None:
    """Copy real hub config to test directory (SSoT)."""
    shutil.copy2(_PARENT_CONFIG_PATH, path)


@pytest.fixture
def evidence_env(tmp_path, monkeypatch):
    """Create isolated evidence environment with configurable state."""
    # Mirror .vadocs/ structure
    vadocs_dir = tmp_path / ".vadocs"
    types_dir = vadocs_dir / "types"
    types_dir.mkdir(parents=True)

    hub_config_path = vadocs_dir / "conf.json"
    spoke_config_path = types_dir / "evidence.conf.json"

    # Copy real configs
    create_hub_config(hub_config_path)
    create_evidence_config(spoke_config_path)

    # Rewrite parent_config to point to test hub (absolute path for test isolation)
    spoke = json.loads(spoke_config_path.read_text(encoding="utf-8"))
    spoke["parent_config"] = str(hub_config_path)
    spoke_config_path.write_text(json.dumps(spoke), encoding="utf-8")

    # Reload config with test paths
    config = _module.load_evidence_config(spoke_config_path)
    parent_config = _module.load_parent_config(config, tmp_path)

    # Create evidence artifact directories at evidence_dir from config
    evidence_rel = config.get("evidence_dir", "architecture/evidence")
    evidence_dir = tmp_path / evidence_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    for type_config in _ARTIFACT_TYPES.values():
        (evidence_dir / type_config["directory_name"]).mkdir(exist_ok=True)

    # Tags from hub are dict with descriptions — extract keys
    tags_raw = parent_config.get("tags", {})
    valid_tags = set(tags_raw.keys()) if isinstance(tags_raw, dict) else set(tags_raw)

    # Monkeypatch module-level constants
    monkeypatch.setattr(_module, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(_module, "EVIDENCE_CONFIG_PATH", spoke_config_path)
    monkeypatch.setattr(_module, "EVIDENCE_CONFIG", config)
    monkeypatch.setattr(_module, "EVIDENCE_DIR", evidence_dir)
    monkeypatch.setattr(_module, "VALID_TAGS", valid_tags)
    monkeypatch.setattr(_module, "ARTIFACT_TYPES", config.get("artifact_types", {}))
    monkeypatch.setattr(_module, "NAMING_PATTERNS", config.get("naming_patterns", {}))
    monkeypatch.setattr(_module, "LIFECYCLE", config.get("lifecycle", {}))
    monkeypatch.setattr(_module, "COMMON_REQUIRED_FIELDS", config.get("common_required_fields", []))
    monkeypatch.setattr(_module, "DATE_FORMAT_PATTERN", parent_config.get("date_format", r"^\d{4}-\d{2}-\d{2}$"))

    return EvidenceTestEnv(
        evidence_dir=evidence_dir,
        root=tmp_path,
    )


class TestErrorReporting:
    """Contract: Error reporting must be agent-actionable."""

    def test_error_reporting_format(self, evidence_env, caplog):
        """Contract: Errors must include file path and error type for agent actionability.
        Format: <path>: [<error_type>] <message> [<config_source>]
        """
        # Create an artifact and explicitly set a required field to None to trigger a failure
        artifact_type = "analysis"
        
        filename = _build_valid_filename(artifact_type, slug="format_test")
        filepath = evidence_env.dir_for(artifact_type) / filename
    
        # Use helper to create a file with an invalid frontmatter (missing status)
        create_artifact_file(
            evidence_env.dir_for(artifact_type),
            artifact_type=artifact_type,
            slug="format_test",
            frontmatter_overrides={"status": None}
        )
    
        # Run main()
        with patch("sys.argv", ["check_evidence.py", "--verbose"]):
            with pytest.raises(SystemExit) as e:
                _module.main()
            assert e.value.code == 1

        # Check that the error message contains the file path and the error type in brackets
        # We search in all log records
        error_messages = [record.getMessage() for record in caplog.records if record.levelname == "ERROR"]

        # Assert that at least one error contains the file path and the laveled error type
        assert any(str(filepath) in msg and "[frontmatter]" in msg for msg in error_messages), \
            f"Expected path and [frontmatter] in error messages: {error_messages}"


class TestConfigLoading:
    """Contract: Config loads from JSON, resolves parent_config for shared tags."""

    def test_loads_evidence_config(self, evidence_env):
        """Should load evidence config with artifact_types, naming_patterns, lifecycle."""
        config = _module.EVIDENCE_CONFIG

        assert "artifact_types" in config
        assert "naming_patterns" in config
        assert "lifecycle" in config

    def test_loads_parent_config_tags(self, evidence_env):
        """Should resolve parent_config and load shared tags from hub."""
        config = _module.EVIDENCE_CONFIG
        parent = _module.load_parent_config(config, evidence_env.root)

        assert "tags" in parent
        assert len(parent["tags"]) > 0

    def test_parent_config_tags_match_production(self, evidence_env):
        """Tags from parent config should match the real hub config."""
        config = _module.EVIDENCE_CONFIG
        parent = _module.load_parent_config(config, evidence_env.root)
        tags_raw = parent["tags"]
        loaded_tags = set(tags_raw.keys()) if isinstance(tags_raw, dict) else set(tags_raw)

        assert loaded_tags == set(_VALID_TAGS)

    def test_missing_config_raises_error(self, tmp_path):
        """Should raise FileNotFoundError when config file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            _module.load_evidence_config(tmp_path / "nonexistent.json")

    def test_missing_parent_config_raises_error(self, evidence_env):
        """Should raise FileNotFoundError when parent config doesn't exist."""
        config = dict(_module.EVIDENCE_CONFIG)
        config["parent_config"] = "nonexistent/config.json"

        with pytest.raises(FileNotFoundError):
            _module.load_parent_config(config, evidence_env.root)

    def test_all_artifact_types_present(self, evidence_env):
        """Should load all artifact types defined in config."""
        loaded_types = set(_module.ARTIFACT_TYPES.keys())

        assert loaded_types == set(_ARTIFACT_TYPES.keys())


# ======================
# Naming Convention Validation
# ======================


class TestValidateNaming:
    """Contract: Filenames must match regex patterns from config per artifact type."""

    @pytest.mark.parametrize("artifact_type", list(_NAMING_PATTERNS.keys()))
    def test_valid_name_per_type(self, evidence_env, artifact_type):
        """Valid filename (built from config) should pass for each type."""

        filename = _build_valid_filename(artifact_type)
        errors = _module.validate_naming(Path("fake/path"), filename, artifact_type)
        assert len(errors) == 0

    @pytest.mark.parametrize("artifact_type", list(_NAMING_PATTERNS.keys()))
    def test_uppercase_slug_rejected(self, evidence_env, artifact_type):
        """Uppercase characters in slug should fail naming validation."""

        prefix = _ARTIFACT_TYPES[artifact_type]["id_prefix"]
        filename = f"{prefix}-26001_UpperCase.md"
        errors = _module.validate_naming(Path("fake/path"), filename, artifact_type)
        assert len(errors) > 0

    @pytest.mark.parametrize("artifact_type", list(_NAMING_PATTERNS.keys()))
    def test_missing_dash_rejected(self, evidence_env, artifact_type):
        """Missing dash between prefix and number should fail."""

        prefix = _ARTIFACT_TYPES[artifact_type]["id_prefix"]
        filename = f"{prefix}26001_some_slug.md"
        errors = _module.validate_naming(Path("fake/path"), filename, artifact_type)
        assert len(errors) > 0

    @pytest.mark.parametrize("artifact_type", list(_NAMING_PATTERNS.keys()))
    def test_short_number_rejected(self, evidence_env, artifact_type):
        """Number with fewer than 5 digits should fail."""

        prefix = _ARTIFACT_TYPES[artifact_type]["id_prefix"]
        filename = f"{prefix}-2601_short.md"
        errors = _module.validate_naming(Path("fake/path"), filename, artifact_type)
        assert len(errors) > 0

    def test_wrong_prefix_rejected(self, evidence_env):
        """Wrong prefix letter for artifact type should fail."""

        # Use retrospective prefix for analysis type
        errors = _module.validate_naming(Path("fake/path"), "R-26001_wrong_prefix.md", "analysis")
        assert len(errors) > 0

# ======================
# Frontmatter Validation
# ======================


class TestValidateFrontmatter:
    """Contract: Required fields present and valid per artifact type."""

    @pytest.mark.parametrize("artifact_type", list(_ARTIFACT_TYPES.keys()))
    def test_valid_frontmatter_passes(self, evidence_env, artifact_type):
        """Valid frontmatter (built from config) should pass for each type."""

        fm = _build_valid_frontmatter(artifact_type)
        errors = _module.validate_frontmatter(Path("fake/path"), fm, artifact_type)
        assert len(errors) == 0

    @pytest.mark.parametrize("field", _COMMON_REQUIRED_FIELDS)
    def test_missing_common_field_detected(self, evidence_env, field):
        """Missing common field (id, title, date) should produce error."""

        # Use first type that has the simplest config
        first_type = list(_ARTIFACT_TYPES.keys())[0]
        fm = _build_valid_frontmatter(first_type)
        del fm[field]

        errors = _module.validate_frontmatter(Path("fake/path"), fm, first_type)
        assert len(errors) > 0

    @pytest.mark.parametrize(
        "artifact_type,field",
        [
            (atype, field)
            for atype, tcfg in _ARTIFACT_TYPES.items()
            for field in tcfg["required_fields"]
        ],
    )
    def test_missing_type_specific_field_detected(self, evidence_env, artifact_type, field):
        """Missing type-specific required field should produce error."""

        fm = _build_valid_frontmatter(artifact_type)
        del fm[field]

        errors = _module.validate_frontmatter(Path("fake/path"), fm, artifact_type)
        assert len(errors) > 0

    @pytest.mark.parametrize(
        "artifact_type,status",
        [
            (atype, status)
            for atype, tcfg in _ARTIFACT_TYPES.items()
            if tcfg["statuses"]
            for status in tcfg["statuses"]
        ],
    )
    def test_all_valid_statuses_accepted(self, evidence_env, artifact_type, status):
        """All statuses from config should be accepted."""

        fm = _build_valid_frontmatter(artifact_type, status=status)
        errors = _module.validate_frontmatter(Path("fake/path"), fm, artifact_type)
        assert len(errors) == 0

    @pytest.mark.parametrize(
        "artifact_type",
        [atype for atype, tcfg in _ARTIFACT_TYPES.items() if tcfg["statuses"]],
    )
    def test_invalid_status_detected(self, evidence_env, artifact_type):
        """Invalid status should produce error for types with status validation."""

        fm = _build_valid_frontmatter(artifact_type, status="bogus_nonexistent_status")
        errors = _module.validate_frontmatter(Path("fake/path"), fm, artifact_type)
        assert len(errors) > 0

    @pytest.mark.parametrize(
        "artifact_type",
        [atype for atype, tcfg in _ARTIFACT_TYPES.items() if not tcfg["statuses"]],
    )
    def test_no_status_validation_for_statusless_types(self, evidence_env, artifact_type):
        """Types with empty statuses list should not require or validate status."""

        fm = _build_valid_frontmatter(artifact_type)
        errors = _module.validate_frontmatter(Path("fake/path"), fm, artifact_type)
        assert len(errors) == 0

    @pytest.mark.parametrize(
        "artifact_type,severity",
        [
            (atype, sev)
            for atype, tcfg in _ARTIFACT_TYPES.items()
            if "severity" in tcfg
            for sev in tcfg["severity"]
        ],
    )
    def test_all_valid_severities_accepted(self, evidence_env, artifact_type, severity):
        """All severity levels from config should be accepted."""

        fm = _build_valid_frontmatter(artifact_type, severity=severity)
        errors = _module.validate_frontmatter(Path("fake/path"), fm, artifact_type)
        assert len(errors) == 0

    @pytest.mark.parametrize(
        "artifact_type",
        [atype for atype, tcfg in _ARTIFACT_TYPES.items() if "severity" in tcfg],
    )
    def test_invalid_severity_detected(self, evidence_env, artifact_type):
        """Invalid severity should produce error for types with severity validation."""

        fm = _build_valid_frontmatter(artifact_type, severity="catastrophic_nonexistent")
        errors = _module.validate_frontmatter(Path("fake/path"), fm, artifact_type)
        assert len(errors) > 0

    def test_invalid_tag_detected(self, evidence_env):
        """Tag not in parent config should produce error."""

        # Use any type that requires tags
        types_with_tags = [
            atype for atype, tcfg in _ARTIFACT_TYPES.items()
            if "tags" in tcfg["required_fields"]
        ]
        if not types_with_tags:
            pytest.skip("No artifact types require tags")

        artifact_type = types_with_tags[0]
        fm = _build_valid_frontmatter(artifact_type, tags=["nonexistent_invalid_tag_xyz"])
        errors = _module.validate_frontmatter(Path("fake/path"), fm, artifact_type)
        assert len(errors) > 0

    def test_invalid_date_format_detected(self, evidence_env):
        """Date not matching YYYY-MM-DD should produce error."""

        first_type = list(_ARTIFACT_TYPES.keys())[0]
        fm = _build_valid_frontmatter(first_type, date="26-02-2026")
        errors = _module.validate_frontmatter(Path("fake/path"), fm, first_type)
        assert len(errors) > 0


# ======================
# Section Validation
# ======================


class TestValidateSections:
    """Contract: Required sections present, no unexpected sections."""

    @pytest.mark.parametrize("artifact_type", list(_ARTIFACT_TYPES.keys()))
    def test_required_sections_pass(self, evidence_env, artifact_type):
        """Artifact with exactly the required sections should pass."""

        required = list(_ARTIFACT_TYPES[artifact_type].get("required_sections", []))
        errors = _module.validate_sections(Path("fake/path"), required, artifact_type)
        assert len(errors) == 0

    @pytest.mark.parametrize("artifact_type", list(_ARTIFACT_TYPES.keys()))
    def test_required_plus_optional_pass(self, evidence_env, artifact_type):
        """Artifact with required + optional sections should pass."""

        type_config = _ARTIFACT_TYPES[artifact_type]
        all_sections = (
            list(type_config.get("required_sections", []))
            + list(type_config.get("optional_sections", []))
        )
        errors = _module.validate_sections(Path("fake/path"), all_sections, artifact_type)
        assert len(errors) == 0

    @pytest.mark.parametrize(
        "artifact_type,missing_section",
        [
            (atype, section)
            for atype, tcfg in _ARTIFACT_TYPES.items()
            for section in tcfg.get("required_sections", [])
        ],
    )
    def test_missing_required_section_detected(self, evidence_env, artifact_type, missing_section):
        """Each missing required section should produce error."""

        required = list(_ARTIFACT_TYPES[artifact_type]["required_sections"])
        sections = [s for s in required if s != missing_section]
        errors = _module.validate_sections(Path("fake/path"), sections, artifact_type)
        assert len(errors) > 0

    @pytest.mark.parametrize(
        "artifact_type",
        [
            atype for atype, tcfg in _ARTIFACT_TYPES.items()
            if tcfg.get("required_sections") or tcfg.get("optional_sections")
        ],
    )
    def test_unexpected_section_detected(self, evidence_env, artifact_type):
        """Section not in required or optional should produce error."""

        required = list(_ARTIFACT_TYPES[artifact_type].get("required_sections", []))
        sections = required + ["Completely Unknown Section XYZ"]
        errors = _module.validate_sections(Path("fake/path"), sections, artifact_type)
        assert len(errors) > 0

    @pytest.mark.parametrize(
        "artifact_type",
        [
            atype for atype, tcfg in _ARTIFACT_TYPES.items()
            if not tcfg.get("required_sections") and not tcfg.get("optional_sections")
        ],
    )
    def test_no_section_validation_for_freeform_types(self, evidence_env, artifact_type):
        """Types with no required/optional sections should accept anything."""

        sections = ["Any Section I Want", "Another Random One"]
        errors = _module.validate_sections(Path("fake/path"), sections, artifact_type)
        assert len(errors) == 0


class TestDiscoverArtifacts:
    """Contract: Scans correct directories, returns sorted artifacts."""

    @pytest.mark.parametrize("artifact_type", list(_ARTIFACT_TYPES.keys()))
    def test_discovers_valid_artifacts(self, evidence_env, artifact_type):
        """Should discover all artifacts matching the naming pattern."""

        # Create 3 valid artifacts
        for i in range(3):
            create_artifact_file(
                evidence_env.dir_for(artifact_type),
                artifact_type=artifact_type,
                slug=f"test_{i}"
            )

        artifacts = _module.discover_artifacts(artifact_type)
        assert len(artifacts) == 3
        # Check sorted order (by artifact_id)
        assert artifacts[0].artifact_id <= artifacts[1].artifact_id <= artifacts[2].artifact_id

    @pytest.mark.parametrize("artifact_type", list(_ARTIFACT_TYPES.keys()))
    def test_ignores_invalid_names(self, evidence_env, artifact_type):
        """Should ignore files that don't match the naming pattern."""

        # Create one valid, one invalid
        create_artifact_file(evidence_env.dir_for(artifact_type), artifact_type=artifact_type, slug="valid")
        (evidence_env.dir_for(artifact_type) / "invalid_name.md").write_text("content")

        artifacts = _module.discover_artifacts(artifact_type)
        assert len(artifacts) == 1

    def test_handles_malformed_yaml(self, evidence_env):
        """Should discover artifacts even if their frontmatter is malformed YAML."""
    
        artifact_type = list(_ARTIFACT_TYPES.keys())[0]
        filepath = (evidence_env.dir_for(artifact_type) / "A-26001_malformed.md")
        filepath.write_text("---\nkey: : invalid yaml\n---\ncontent", encoding="utf-8")
    
        artifacts = _module.discover_artifacts(artifact_type)
        assert len(artifacts) == 1
        assert artifacts[0].frontmatter is None
    def test_handles_missing_frontmatter(self, evidence_env):
        """Should discover artifacts even if frontmatter block is missing."""
    
        artifact_type = list(_ARTIFACT_TYPES.keys())[0]
        filepath = (evidence_env.dir_for(artifact_type) / "A-26001_no_fm.md")
        filepath.write_text("# No Frontmatter Here", encoding="utf-8")
    
        artifacts = _module.discover_artifacts(artifact_type)
        assert len(artifacts) == 1
        assert artifacts[0].frontmatter is None

class TestDetectOrphanedSources:
    """Contract: Sources with null extracted_into flagged past threshold."""

    def test_flags_orphaned_sources(self, evidence_env):
        """Sources with null extracted_into and old date should be flagged."""

        source_type = next((k for k, v in _ARTIFACT_TYPES.items() if not v.get("statuses")), None)
        sources_dir = evidence_env.dir_for(source_type)

        # 1. Old orphan (should be flagged)
        old_date = (date.today() - timedelta(days=40)).isoformat()
        S1 = create_artifact_file(
            sources_dir,
            artifact_type=source_type,
            slug="old_orphan",
            frontmatter_overrides={"extracted_into": None, "date": old_date}
        )

        # 2. New orphan (should NOT be flagged)
        new_date = _recent_date()
        S2 = create_artifact_file(
            sources_dir,
            artifact_type=source_type,
            slug="new_orphan",
            frontmatter_overrides={"extracted_into": None, "date": new_date}
        )

        # 3. Extracted source (should NOT be flagged)
        S3 = create_artifact_file(
            sources_dir,
            artifact_type=source_type,
            slug="extracted",
            frontmatter_overrides={"extracted_into": "A-26001", "date": old_date}
        )

        warnings = _module.detect_orphaned_sources(sources_dir)
        assert len(warnings) == 1
        assert warnings[0].file_path == S1

    def test_empty_sources_dir_handled(self, evidence_env):
        """Should return empty list if sources directory is missing."""
        warnings = _module.detect_orphaned_sources(Path("nonexistent/dir"))
        assert warnings == []


class TestCli:
    """Contract: Exit codes 0 (valid) / 1 (errors), --verbose and --check-staged flags."""

    def test_exit_code_zero_for_valid(self, evidence_env):
        """Should exit 0 when all artifacts are valid."""

        # Create one valid artifact
        create_artifact_file(evidence_env.dir_for("analysis"), artifact_type="analysis")

        with patch("sys.argv", ["check_evidence.py"]):
            with pytest.raises(SystemExit) as e:
                _module.main()
            assert e.value.code == 0

    def test_exit_code_one_for_errors(self, evidence_env):
        """Should exit 1 when validation errors are found."""

        # Create one invalid artifact (missing required field)
        create_artifact_file(
            evidence_env.dir_for("analysis"),
            artifact_type="analysis",
            frontmatter_overrides={"status": None}
        )

        with patch("sys.argv", ["check_evidence.py"]):
            with pytest.raises(SystemExit) as e:
                _module.main()
            assert e.value.code == 1

    def test_verbose_output(self, evidence_env, caplog):
        """--verbose should trigger debug logging for each artifact."""

        create_artifact_file(evidence_env.dir_for("analysis"), artifact_type="analysis")

        with patch("sys.argv", ["check_evidence.py", "--verbose"]):
            with pytest.raises(SystemExit):
                _module.main()

        # Check for debug logs
        debug_logs = [record.getMessage() for record in caplog.records if record.levelname == "DEBUG"]
        assert any("Validating" in msg for msg in debug_logs)

    def test_check_staged_filter(self, evidence_env, monkeypatch):
        """--check-staged should only validate files returned by get_staged_files()."""

        # Create two artifacts
        A1 = create_artifact_file(evidence_env.dir_for("analysis"), artifact_type="analysis", slug="staged")
        A2 = create_artifact_file(evidence_env.dir_for("analysis"), artifact_type="analysis", slug="unstaged")

        # Mock get_staged_files to only return A1
        rel_path_A1 = str(A1.relative_to(evidence_env.root))
        monkeypatch.setattr("tools.scripts.git.get_staged_files", lambda: [rel_path_A1])

        # Make A2 invalid (so it would trigger exit 1 if checked)
        # We rewrite A2 to be invalid
        fm = _build_valid_frontmatter("analysis")
        del fm["status"]
        create_artifact_file(
            evidence_env.dir_for("analysis"),
            artifact_type="analysis",
            slug="unstaged",
            frontmatter_overrides=fm
        )

        # Run with --check-staged
        with patch("sys.argv", ["check_evidence.py", "--check-staged"]):
            with pytest.raises(SystemExit) as e:
                _module.main()
            # Should be 0 because only the valid A1 is checked
            assert e.value.code == 0

    def test_check_staged_with_errors(self, evidence_env, monkeypatch):
        """--check-staged should exit 1 if a staged file is invalid.
        
        Contract:
        - We monkeypatch 'get_staged_files' to simulate Git's staging area.
        - The 'evidence_env' fixture already provides correct config and REPO_ROOT.
        """
        A1 = create_artifact_file(
            evidence_env.dir_for("analysis"),
            artifact_type="analysis",
            slug="staged",
            frontmatter_overrides={"status": None}
        )
    
        rel_path_A1 = str(A1.relative_to(evidence_env.root))
        monkeypatch.setattr(_module, "get_staged_files", lambda: [rel_path_A1])
    
        with patch("sys.argv", ["check_evidence.py", "--check-staged", "--verbose"]):
            with pytest.raises(SystemExit) as e:
                _module.main()
            assert e.value.code == 1


class TestCoverageGaps:
    """Targeted tests to cover remaining missing lines in check_evidence.py."""

    def test_missing_evidence_config_raises(self, tmp_path):
        """Cover line 204: load_evidence_config raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            _module.load_evidence_config(tmp_path / "missing.json")

    def test_missing_parent_config_raises(self, tmp_path):
        """Cover lines 174-179, 211-214: load_parent_config raises FileNotFoundError."""
        # Case 1: Absolute path missing
        with pytest.raises(FileNotFoundError):
            _module.load_parent_config({"parent_config": "/tmp/no_hub.json"}, tmp_path)

        # Case 2: Relative path missing
        with pytest.raises(FileNotFoundError):
            _module.load_parent_config({"parent_config": "no_hub.json"}, tmp_path)

    def test_no_naming_pattern_handling(self, evidence_env, monkeypatch):
        """Cover lines 254-260 and 498: Handling of types with no naming pattern."""
        # Mock ARTIFACT_TYPES to include a type without a pattern
        mock_types = dict(_module.ARTIFACT_TYPES)
        mock_types["no_pattern_type"] = {"directory_name": "no_pattern", "id_prefix": "NP", "required_fields": []}
        monkeypatch.setattr(_module, "ARTIFACT_TYPES", mock_types)

        # Mock NAMING_PATTERNS to exclude this type
        mock_patterns = dict(_module.NAMING_PATTERNS)
        # Ensure "no_pattern_type" is NOT in mock_patterns
        monkeypatch.setattr(_module, "NAMING_PATTERNS", mock_patterns)

        # 1. Test validate_naming directly
        errors = _module.validate_naming(Path("fake"), "NP-26001_test.md", "no_pattern_type")
        assert len(errors) == 1
        assert "No naming pattern defined" in errors[0].message

        # 2. Test discover_artifacts
        (evidence_env.evidence_dir / "no_pattern").mkdir(exist_ok=True)
        (evidence_env.evidence_dir / "no_pattern" / "NP-26001_test.md").write_text("content")

        artifacts = _module.discover_artifacts("no_pattern_type")
        assert len(artifacts) == 0

    def test_frontmatter_validation_errors(self, evidence_env):
        """Cover lines 427, 433, 437-438, 441: Trigger all frontmatter validation failures."""
        first_type = list(_module.ARTIFACT_TYPES.keys())[0]
        type_config = _module.ARTIFACT_TYPES[first_type]

        # 1. Invalid date format
        fm_date = _build_valid_frontmatter(first_type, date="01-01-2026")
        errors = _module.validate_frontmatter(Path("fake"), fm_date, first_type)
        assert any("Invalid date format" in e.message for e in errors)

        # 2. Invalid status (if applicable)
        if type_config.get("statuses"):
            fm_status = _build_valid_frontmatter(first_type, status="bogus_status")
            errors = _module.validate_frontmatter(Path("fake"), fm_status, first_type)
            assert any("Invalid status" in e.message for e in errors)

        # 3. Invalid severity (if applicable)
        if "severity" in type_config:
            fm_sev = _build_valid_frontmatter(first_type, severity="bogus_severity")
            errors = _module.validate_frontmatter(Path("fake"), fm_sev, first_type)
            assert any("Invalid severity" in e.message for e in errors)

        # 4. Invalid tags
        fm_tags = _build_valid_frontmatter(first_type, tags=["nonexistent_tag"])
        errors = _module.validate_frontmatter(Path("fake"), fm_tags, first_type)
        assert any("Invalid tags" in e.message for e in errors)

    def test_sections_validation_errors(self, evidence_env):
        """Cover lines 449-450: Trigger missing required section error."""
        first_type = list(_module.ARTIFACT_TYPES.keys())[0]
        type_config = _module.ARTIFACT_TYPES[first_type]
        required = list(type_config.get("required_sections", []))

        if required:
            # Remove one required section
            missing_section = required[0]
            sections = [s for s in required if s != missing_section]
            errors = _module.validate_sections(Path("fake"), sections, first_type)
            assert any("Missing required section" in e.message for e in errors)

    def test_orphaned_sources_missing_dir(self, evidence_env):
        """Cover line 490: detect_orphaned_sources handles missing directory."""
        warnings = _module.detect_orphaned_sources(Path("nonexistent_dir_xyz"))
        assert warnings == []

    def test_main_entry_point(self, evidence_env, monkeypatch):
        """Cover line 536: if __name__ == '__main__': main()"""
        # This is hard to test as it's at the bottom of the module.
        # We can just call main() directly via the module.
        with patch("sys.argv", ["check_evidence.py"]):
            with pytest.raises(SystemExit):
                _module.main()
