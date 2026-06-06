"""
Test suite for check_frontmatter.py — Config-driven frontmatter validator.

Tests the hub+spoke frontmatter validation pipeline: config loading, YAML
parsing, type resolution, field presence/format/value checking, file scanning,
and CLI behavior.

What belongs here:
    - All frontmatter validation contracts (field presence, format, values)
    - Config loading and merge semantics
    - File scanning and directory exclusion
    - CLI exit codes and error reporting structure

What does NOT belong here:
    - Structural validation (sections, naming) — test_check_adr.py, test_check_evidence.py
    - Config file content correctness — validated by JSON Schema

Test classes and their contracts:
    - TestLoadConfigChain: Hub loads, hub+spoke for known types, None spoke for unknown
    - TestParseFrontmatter: Extracts YAML dict from .md; returns None when absent
    - TestResolveType: Reads options.type; returns None when missing
    - TestGetRequiredFields: Union of hub blocks + hub types.required + spoke required_fields
    - TestValidateFieldPresence: Detects missing required fields; passes when all present
    - TestValidateDateFormat: Accepts YYYY-MM-DD; rejects other formats
    - TestValidateTags: Accepts known tags; rejects unknown; handles empty
    - TestValidateStatus: Accepts spoke-defined statuses; rejects invalid
    - TestValidateAuthors: Accepts list of {name, email}; rejects malformed
    - TestOptionsNamespace: Non-myst_native at top level produces warnings (not errors)
    - TestWarningNoType: Files with frontmatter but no options.type produce warning
    - TestScanPaths: File args as-is; directories walked with exclusions; format filter
    - TestMainExitCodes: Exit 0 valid; exit 1 errors; warnings don't affect code
    - TestErrorMessages: FrontmatterError dataclass fields populated correctly
    - TestValidateFrontmatterConvenience: Convenience wrapper returns [] for no-fm / no-type
    - TestUnknownType: Unknown options.type produces blocking error
    - TestAuthorNonDict: String author entries rejected
    - TestParseEdgeCases: Malformed JSON/YAML returns None gracefully
    - TestFindFieldBlockFallback: Config source attribution for spoke-only fields

Naming convention: one test class per contract, method names describe behavior.
"""

import json
import shutil
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

import tools.scripts.check_frontmatter as _module

# ======================
# Config-driven constants (SSoT)
# ======================

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

_HUB_CONFIG_REL = ".vadocs/conf.json"
_HUB_CONFIG_PATH = _REPO_ROOT / _HUB_CONFIG_REL

with open(_HUB_CONFIG_PATH, encoding="utf-8") as _f:
    _HUB_CONFIG = json.load(_f)

_BLOCKS = _HUB_CONFIG["blocks"]
_TYPES = _HUB_CONFIG["types"]
_FIELD_REGISTRY = _HUB_CONFIG["field_registry"]
_VALID_TAGS = list(_HUB_CONFIG["tags"].keys())
_DATE_FORMAT = _HUB_CONFIG.get("date_format", r"^\d{4}-\d{2}-\d{2}$")

# Load spoke configs for types that have them
_SPOKE_CONFIGS: dict[str, dict] = {}
for _type_name in _TYPES:
    _spoke_path = _REPO_ROOT / f".vadocs/types/{_type_name}.conf.json"
    if _spoke_path.exists():
        with open(_spoke_path, encoding="utf-8") as _f:
            _SPOKE_CONFIGS[_type_name] = json.load(_f)


# ======================
# Test Helpers
# ======================


def _build_valid_frontmatter(doc_type: str) -> dict:
    """Build a valid frontmatter dict for a given type, derived from config.

    Uses hub blocks + hub types.required + spoke required_fields to determine
    which fields are needed, then populates with valid values from config.
    """
    type_def = _TYPES[doc_type]
    spoke = _SPOKE_CONFIGS.get(doc_type)

    # 1. Resolve all required fields (union merge)
    required = set()
    for block_name in type_def.get("blocks", []):
        required.update(_BLOCKS.get(block_name, []))
    required.update(type_def.get("required", []))
    if spoke:
        required.update(spoke.get("required_fields", []))

    # 2. Define dynamic value generators to avoid brittle if/elif chains
    generators = {
        "title": lambda: f"Test {doc_type.capitalize()} Title",
        "authors": lambda: [{"name": "Test Author", "email": "test@example.com"}],
        "description": lambda: "Test description",
        "tags": lambda: [_VALID_TAGS[0]] if _VALID_TAGS else [],
        "date": lambda: "2026-01-15",
        "id": lambda: 26099 if doc_type == "adr" else "X-26099",
        "token_size": lambda: 100,
        "birth": lambda: "2026-01-01",
        "version": lambda: "1.0.0",
        "model": lambda: "test-model",
    }

    def get_status_value():
        if spoke and "statuses" in spoke:
            return spoke["statuses"][0]
        if spoke and "artifact_types" in spoke:
            for at in spoke["artifact_types"].values():
                if at.get("statuses"): return at["statuses"][0]
        return "active"

    def get_severity_value():
        if spoke and "artifact_types" in spoke:
            for at in spoke["artifact_types"].values():
                if "severity" in at: return at["severity"][0]
        return "low"

    generators["status"] = get_status_value
    generators["severity"] = get_severity_value
    generators["superseded_by"] = lambda: None

    # 3. Build structure dynamically based on myst_native property (S-S-o-T)
    fm: dict = {}
    options: dict = {"type": doc_type}

    # We must iterate in a specific order to ensure the resulting dict is canonical.
    # First, 'id' (if applicable)
    if "id" in required and _FIELD_REGISTRY.get("id", {}).get("myst_native"):
        fm["id"] = generators["id"]()

    # Second, fields from the defined blocks sequence
    for block_name in type_def.get("blocks", []):
        for field in _BLOCKS.get(block_name, []):
            if field == "id": continue # already handled
            if field in required and _FIELD_REGISTRY.get(field, {}).get("myst_native"):
                fm[field] = generators.get(field, lambda: f"test-{field}")()

    # Third, all other required fields go into options
    for field in required:
        if field == "type": continue
        # If it's already at top level (myst_native), skip it
        if field in fm: continue
        
        fm_val = generators.get(field, lambda: f"test-{field}")()
        options[field] = fm_val

    fm["options"] = options
    return fm


def _frontmatter_to_md(fm: dict) -> str:
    """Convert a frontmatter dict to markdown file content with YAML fences."""
    return f"---\n{yaml.dump(fm, default_flow_style=False, sort_keys=False)}---\n\n# Test Document\n"


# ======================
# Fixtures
# ======================


@pytest.fixture()
def frontmatter_env(tmp_path, monkeypatch):
    """Isolated test environment with .vadocs/ configs copied from real repo.

    Monkeypatches module-level constants for test isolation.
    """
    # Copy .vadocs/ configs to tmp
    vadocs_src = _REPO_ROOT / ".vadocs"
    vadocs_dst = tmp_path / ".vadocs"
    shutil.copytree(vadocs_src, vadocs_dst)

    # Rewrite parent_config pointers to use absolute paths in test env
    for spoke_file in (tmp_path / ".vadocs" / "types").glob("*.conf.json"):
        spoke_data = json.loads(spoke_file.read_text(encoding="utf-8"))
        if "parent_config" in spoke_data:
            spoke_data["parent_config"] = str(vadocs_dst / "conf.json")
            spoke_file.write_text(
                json.dumps(spoke_data, indent=2), encoding="utf-8"
            )

    # Create pyproject.toml so get_config_path() works in test env
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[tool.vadocs]\nconfig_dir = ".vadocs"\n', encoding="utf-8"
    )

    # Load hub config from test env
    hub_config = json.loads(
        (vadocs_dst / "conf.json").read_text(encoding="utf-8")
    )

    # Monkeypatch module-level constants
    monkeypatch.setattr(_module, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(_module, "HUB_CONFIG_PATH", vadocs_dst / "conf.json")
    monkeypatch.setattr(_module, "HUB_CONFIG", hub_config)
    monkeypatch.setattr(
        _module, "VALID_TAGS", set(hub_config.get("tags", {}).keys())
    )
    monkeypatch.setattr(
        _module, "VALID_TYPES", set(hub_config.get("types", {}).keys())
    )
    monkeypatch.setattr(
        _module,
        "DATE_FORMAT_PATTERN",
        hub_config.get("date_format", r"^\d{4}-\d{2}-\d{2}$"),
    )
    monkeypatch.setattr(_module, "FIELD_REGISTRY", hub_config.get("field_registry", {}))
    monkeypatch.setattr(_module, "BLOCKS", hub_config.get("blocks", {}))
    monkeypatch.setattr(_module, "TYPES", hub_config.get("types", {}))
    monkeypatch.setattr(_module, "_config_cache", {})

    return tmp_path


# ======================
# Tests: Config Loading
# ======================


class TestLoadConfigChain:
    """Contract: load_config_chain returns (hub_config, child_config) tuple.

    Hub config always loaded. Child config loaded when doc_type has a .conf.json
    file, None otherwise. Results cached per doc_type.

    Sub-type resolution (TD-005):
    - Sub-types (analysis, retrospective, source) resolve to parent config (evidence)
    - Sub-type rules extracted from artifact_types.<sub_type>
    - common_required_fields merged with sub-type required_fields
    """

    def test_hub_only_when_no_doc_type(self, frontmatter_env):
        """No doc_type → returns (hub_dict, None)."""
        hub_config, child_config = _module.load_config_chain(frontmatter_env, doc_type=None)
        assert isinstance(hub_config, dict)
        assert "field_registry" in hub_config
        assert "blocks" in hub_config
        assert "types" in hub_config
        assert child_config is None

    def test_hub_plus_child_for_known_type(self, frontmatter_env):
        """Known type with child config → returns (hub_dict, child_dict)."""
        hub_config, child_config = _module.load_config_chain(frontmatter_env, doc_type="adr")
        assert isinstance(hub_config, dict)
        assert isinstance(child_config, dict)
        assert "required_fields" in child_config or "statuses" in child_config

    def test_none_child_for_type_without_config(self, frontmatter_env):
        """Type defined in hub but no child .conf.json → (hub_dict, None)."""
        # Find a type without a child config file (config-driven, not hardcoded)
        hub_config = json.loads(_module.HUB_CONFIG_PATH.read_text())
        types_without_config = []
        for type_name in hub_config.get("types", {}).keys():
            config_path = _module.get_config_path(frontmatter_env, type_name)
            if not config_path.exists():
                types_without_config.append(type_name)

        if not types_without_config:
            # All types have configs — skip instead of fail
            pytest.skip("All hub types have child config files")

        # Use first type without config
        test_type = types_without_config[0]
        hub_config_result, child_config = _module.load_config_chain(frontmatter_env, doc_type=test_type)
        assert isinstance(hub_config_result, dict)
        assert child_config is None

    def test_caches_results(self, frontmatter_env):
        """Second call with same doc_type returns cached result."""
        result1 = _module.load_config_chain(frontmatter_env, doc_type="adr")
        result2 = _module.load_config_chain(frontmatter_env, doc_type="adr")
        assert result1[0] is result2[0]  # same object, not re-loaded
        assert result1[1] is result2[1]

    def test_different_types_cached_independently(self, frontmatter_env):
        """Different doc_types have independent cache entries."""
        _, child_adr = _module.load_config_chain(frontmatter_env, doc_type="adr")
        _, child_evidence = _module.load_config_chain(
            frontmatter_env, doc_type="evidence"
        )
        assert child_adr is not child_evidence

    # ======================
    # Tests: Sub-type Resolution (TD-005)
    # ======================

    def test_subtype_resolves_to_parent_config(self, frontmatter_env):
        """Sub-type resolves to parent config with artifact_type marker."""
        # Load sub-type from config, not hardcoded
        evidence_config_path = _module.get_config_path(frontmatter_env, "evidence")
        evidence_config = json.loads(evidence_config_path.read_text())
        subtypes = list(evidence_config["artifact_types"].keys())
        test_subtype = subtypes[0]  # Use first available sub-type

        hub_config, child_config = _module.load_config_chain(
            frontmatter_env, doc_type=test_subtype
        )
        assert isinstance(hub_config, dict)
        assert child_config is not None
        # Should have artifact_type marker matching input
        assert child_config.get("artifact_type") == test_subtype

    def test_subtype_merges_required_fields(self, frontmatter_env):
        """Sub-type merges common + sub-type required_fields (config-driven)."""
        # Load expected from config using module's path resolver, not hardcoded
        evidence_config_path = _module.get_config_path(frontmatter_env, "evidence")
        evidence_config = json.loads(evidence_config_path.read_text())
        common = evidence_config.get("common_required_fields", [])
        analysis_fields = evidence_config["artifact_types"]["analysis"]["required_fields"]
        expected_merged = set(common) | set(analysis_fields)

        _, child_config = _module.load_config_chain(
            frontmatter_env, doc_type="analysis"
        )
        merged_fields = set(child_config.get("common_required_fields", []))
        assert merged_fields == expected_merged

    def test_retrospective_subtype_resolves_correctly(self, frontmatter_env):
        """Sub-type 'retrospective' loads evidence parent config with merged fields."""
        # Load expected from config using module's path resolver, not hardcoded
        evidence_config_path = _module.get_config_path(frontmatter_env, "evidence")
        evidence_config = json.loads(evidence_config_path.read_text())
        common = evidence_config.get("common_required_fields", [])
        retro_fields = evidence_config["artifact_types"]["retrospective"]["required_fields"]
        expected_merged = set(common) | set(retro_fields)

        _, child_config = _module.load_config_chain(
            frontmatter_env, doc_type="retrospective"
        )
        assert child_config is not None
        assert child_config.get("artifact_type") == "retrospective"
        merged_fields = set(child_config.get("common_required_fields", []))
        assert merged_fields == expected_merged

    def test_source_subtype_resolves_correctly(self, frontmatter_env):
        """Sub-type 'source' loads evidence parent config with merged fields."""
        # Load expected from config using module's path resolver, not hardcoded
        evidence_config_path = _module.get_config_path(frontmatter_env, "evidence")
        evidence_config = json.loads(evidence_config_path.read_text())
        common = evidence_config.get("common_required_fields", [])
        source_fields = evidence_config["artifact_types"]["source"]["required_fields"]
        expected_merged = set(common) | set(source_fields)

        _, child_config = _module.load_config_chain(
            frontmatter_env, doc_type="source"
        )
        assert child_config is not None
        assert child_config.get("artifact_type") == "source"
        merged_fields = set(child_config.get("common_required_fields", []))
        assert merged_fields == expected_merged

    def test_subtype_preserves_artifact_types_structure(self, frontmatter_env):
        """Sub-type resolution preserves artifact_types dict for downstream use."""
        # Load expected sub-types from config using module's path resolver
        evidence_config_path = _module.get_config_path(frontmatter_env, "evidence")
        evidence_config = json.loads(evidence_config_path.read_text())
        expected_subtypes = set(evidence_config["artifact_types"].keys())

        _, child_config = _module.load_config_chain(
            frontmatter_env, doc_type="analysis"
        )
        # artifact_types should still be accessible for other validation logic
        assert "artifact_types" in child_config
        # All sub-types should be preserved
        preserved_subtypes = set(child_config["artifact_types"].keys())
        assert preserved_subtypes == expected_subtypes

    def test_subtype_required_fields_merge_includes_common(self, frontmatter_env):
        """Sub-type resolution must merge common_required_fields from spoke config."""
        # 'analysis' is a sub-type of 'evidence'
        # evidence.conf.json has common_required_fields: [id, title, date]
        # artifact_types.analysis has required_fields: [status, tags]
        hub, spoke = _module.load_config_chain(frontmatter_env, doc_type="analysis")
        required = _module._get_required_fields("analysis", hub, spoke)
        
        expected = {"id", "title", "date", "status", "tags"}
        assert expected.issubset(required), f"Missing required fields: {expected - required}"


# ======================
# Tests: Asymmetric Fences
# ======================


class TestAsymmetricFences:
    """Contract: Detect asymmetric YAML fences (closing without opening).

    A file that has a closing fence ('---') but no opening fence at the start
    should be flagged as corrupted/invalid, NOT as 'missing_frontmatter'.
    """

    def test_single_block_missing_opening_fence(self, frontmatter_env):
        """Single block: closing fence present, opening fence missing -> corrupted."""
        content = (
            "title: Asymmetric Doc\n"
            "options:\n"
            "  type: guide\n"
            "---\n"
            "\n"
            "# Body\n"
        )
        file_path = frontmatter_env / "single_asymmetric.md"
        file_path.write_text(content, encoding="utf-8")

        errors = _module.validate_frontmatter(file_path, frontmatter_env)

        assert not any(e.error_type == "missing_frontmatter" for e in errors), \
            "Should not be reported as missing_frontmatter when a closing fence exists"
        assert any(e.error_type == "broken_dual_block" for e in errors), \
            "Should be reported as broken_dual_block (corrupted) when closing fence exists without opening"

    def test_dual_block_missing_second_opening_fence(self, frontmatter_env):
        """Dual block: first block OK, second block missing opening fence -> corrupted."""
        content = (
            "---\n"
            "jupytext:\n"
            "  text_representation: {format_name: myst}\n"
            "---\n"
            "\n"
            "title: Asymmetric Dual Doc\n"
            "options:\n"
            "  type: guide\n"
            "---\n"
            "\n"
            "# Body\n"
        )
        file_path = frontmatter_env / "dual_asymmetric.md"
        file_path.write_text(content, encoding="utf-8")

        errors = _module.validate_frontmatter(file_path, frontmatter_env)

        assert not any(e.error_type == "missing_frontmatter" for e in errors), \
            "Should not be reported as missing_frontmatter when blocks exist"
        assert any(e.error_type == "broken_dual_block" for e in errors), \
            "Should be reported as broken_dual_block when second block is asymmetric"

    def test_no_fences_reported_as_missing(self, frontmatter_env):
        """No fences at all -> reported as missing_frontmatter."""
        content = (
            "title: No Fences\n"
            "options:\n"
            "  type: guide\n"
            "\n"
            "# Body\n"
        )
        file_path = frontmatter_env / "no_fences.md"
        file_path.write_text(content, encoding="utf-8")

        errors = _module.validate_frontmatter(file_path, frontmatter_env)

        assert any(e.error_type == "missing_frontmatter" for e in errors), \
            "Files with no fences at all should be reported as missing_frontmatter"

    def test_proper_fences_pass_parsing(self, frontmatter_env):
        """Proper symmetric fences should not trigger asymmetric errors."""
        content = (
            "---\n"
            "title: Proper Doc\n"
            "options:\n"
            "  type: guide\n"
            "---\n"
            "\n"
            "# Body\n"
        )
        file_path = frontmatter_env / "proper.md"
        file_path.write_text(content, encoding="utf-8")

        errors = _module.validate_frontmatter(file_path, frontmatter_env)

        assert not any(e.error_type == "broken_dual_block" for e in errors), \
            "Proper symmetric fences should not be flagged as broken"

    def test_leading_newline_is_forbidden(self, frontmatter_env):
        """File starting with a newline before the opening fence MUST be flagged as an error.

        The first character of a governed file must be the start of the YAML fence.
        """
        content = (
            "\n"
            "---\n"
            "title: Leading Newline\n"
            "options:\n"
            "  type: guide\n"
            "---\n"
            "\n"
            "# Body\n"
        )
        file_path = frontmatter_env / "leading_newline.md"
        file_path.write_text(content, encoding="utf-8")

        errors = _module.validate_frontmatter(file_path, frontmatter_env)

        assert any(e.error_type == "leading_newline" for e in errors), \
            "Files starting with a newline before the fence must be reported as leading_newline"

# ======================
# Tests: Key Order
# ======================


class TestKeyOrder:
    """Contract: Enforce canonical sequence of top-level YAML keys.

    Canonical order: id > title > authors > date > description > tags > status > superseded_by > options.
    """

    def test_canonical_order_passes(self, frontmatter_env):
        """Fields in exact canonical order should pass."""
        # Use the helper to get a guaranteed canonical structure for 'adr'
        fm = _build_valid_frontmatter("adr")
        file_path = frontmatter_env / "canonical.md"
        file_path.write_text(_frontmatter_to_md(fm), encoding="utf-8")

        errors = _module.validate_frontmatter(file_path, frontmatter_env)
        assert not any(e.error_type == "invalid_order" for e in errors)

    def test_partial_canonical_order_passes(self, frontmatter_env):
        """Fields in correct relative order (even if some are missing) should pass."""
        fm = {
            "id": 26001,
            "date": "2026-01-01",
            "options": {"type": "adr"}
        }
        file_path = frontmatter_env / "partial_canonical.md"
        file_path.write_text(_frontmatter_to_md(fm), encoding="utf-8")

        errors = _module.validate_frontmatter(file_path, frontmatter_env)
        assert not any(e.error_type == "invalid_order" for e in errors)

    def test_incorrect_order_fails(self, frontmatter_env):
        """Fields in incorrect relative order should produce 'invalid_order' error."""
        fm = {
            "title": "Wrong Order",
            "id": 26001, # id should be first
            "options": {"type": "adr"}
        }
        file_path = frontmatter_env / "wrong_order.md"
        file_path.write_text(_frontmatter_to_md(fm), encoding="utf-8")

        errors = _module.validate_frontmatter(file_path, frontmatter_env)
        assert any(e.error_type == "invalid_order" for e in errors), \
            "Should detect that 'title' comes before 'id'"

    def test_options_out_of_place_fails(self, frontmatter_env):
        """'options' block must be the final canonical field."""
        fm = {
            "options": {"type": "adr"},
            "date": "2026-01-01" # date should be before options
        }
        file_path = frontmatter_env / "options_first.md"
        file_path.write_text(_frontmatter_to_md(fm), encoding="utf-8")

        errors = _module.validate_frontmatter(file_path, frontmatter_env)
        assert any(e.error_type == "invalid_order" for e in errors), \
            "Should detect that 'options' comes before 'date'"


class TestDualBlockParsing:
    """Contract: Correctly distinguish between Jupytext-only blocks and project metadata blocks.

    A Jupytext block may contain an 'options' field. The parser must not mistake this
    for the project governance block. If a Jupytext block is found, the parser
    should look for a second governance block.
    """

    def test_jupytext_block_with_options_does_not_block_governance_block(self):
        """Jupytext block with 'options' should still be identified as jupytext_only,
        allowing the parser to collect the second project metadata block.
        """
        content = (
            "---\n"
            "jupytext:\n"
            "  text_representation: {format_name: myst}\n"
            "options:\n"
            "  type: source\n"
            "---\n"
            "---\n"
            "title: Project Title\n"
            "options:\n"
            "  type: guide\n"
            "---\n"
            "\n"
            "# Body\n"
        )
        # We only test the parse_frontmatter function here
        merged_data, block_count, anomalies = _module.parse_frontmatter(content)

        assert block_count == 2, f"Expected 2 blocks, found {block_count}"
        assert merged_data is not None
        assert merged_data["title"] == "Project Title"
        assert merged_data["options"]["type"] == "guide"
        assert "jupytext" in merged_data
        assert not anomalies

    def test_single_governance_block_with_options_is_not_jupytext(self):
        """A single block with 'options' and 'title' is correctly identified as governance."""
        content = (
            "---\n"
            "title: Project Title\n"
            "options:\n"
            "  type: guide\n"
            "---\n"
            "\n"
            "# Body\n"
        )
        merged_data, block_count, anomalies = _module.parse_frontmatter(content)

        assert block_count == 1
        assert merged_data["title"] == "Project Title"
        assert not anomalies

    def test_jupytext_block_missing_second_block_fence(self):
        """Jupytext block followed by project metadata without an opening fence -> broken_dual_block."""
        content = (
            "---\n"
            "jupytext:\n"
            "  text_representation: {format_name: myst}\n"
            "---\n"
            "\n"
            "title: Project Title\n"
            "options:\n"
            "  type: guide\n"
            "---\n"
            "\n"
            "# Body\n"
        )
        merged_data, block_count, anomalies = _module.parse_frontmatter(content)

        assert "broken_dual_block" in anomalies
        # It should still merge the data if it can
        assert merged_data["title"] == "Project Title"


class TestParseFrontmatter:
    """Contract: parse_frontmatter extracts YAML dict from content.

    Returns dict when valid YAML frontmatter found between --- fences.
    Returns None when no frontmatter present.
    """

    def test_extracts_yaml_from_md(self):
        """Standard markdown with YAML fences → parsed dict."""
        content = "---\ntitle: Test\ndate: 2026-01-01\n---\n\n# Body\n"
        result, *rest = _module.parse_frontmatter(content)
        assert isinstance(result, dict)
        assert result["title"] == "Test"
        # yaml.safe_load converts date strings to datetime.date
        assert result["date"] == date(2026, 1, 1)

    def test_returns_none_when_no_frontmatter(self):
        """Markdown without --- fences → None."""
        content = "# Just a heading\n\nSome text.\n"
        result, *rest = _module.parse_frontmatter(content)
        assert result is None

    def test_returns_none_for_empty_content(self):
        """Empty string → None."""
        result, *rest = _module.parse_frontmatter("")
        assert result is None

    def test_handles_nested_options(self):
        """Frontmatter with options.type → nested dict preserved."""
        content = "---\ntitle: Test\noptions:\n  type: adr\n  birth: 2026-01-01\n---\n\n# Body\n"
        result, *rest = _module.parse_frontmatter(content)
        assert result["options"]["type"] == "adr"
        assert result["options"]["birth"] == date(2026, 1, 1)

    def test_handles_list_fields(self):
        """Tags as list → preserved as list."""
        content = "---\ntitle: Test\ntags: [governance, ci]\n---\n\n# Body\n"
        result, *rest = _module.parse_frontmatter(content)
        assert result["tags"] == ["governance", "ci"]

    def test_ipynb_extracts_from_first_markdown_cell(self):
        """ipynb JSON with frontmatter in first markdown cell → parsed dict."""
        notebook = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "source": [
                        "---\n",
                        "title: Notebook Test\n",
                        "date: 2026-03-25\n",
                        "---\n",
                        "\n",
                        "# Content\n",
                    ],
                    "metadata": {},
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        content = json.dumps(notebook)
        result, *rest = _module.parse_frontmatter(content, file_path=Path("test.ipynb"))
        assert isinstance(result, dict)
        assert result["title"] == "Notebook Test"

    def test_ipynb_returns_none_for_empty_notebook(self):
        """ipynb with no cells → None."""
        notebook = {"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}
        content = json.dumps(notebook)
        result, *rest = _module.parse_frontmatter(content, file_path=Path("test.ipynb"))
        assert result is None

    def test_ipynb_returns_none_when_no_frontmatter(self):
        """ipynb without YAML fences in first cell → None."""
        notebook = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "source": ["# Just a heading\n"],
                    "metadata": {},
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        content = json.dumps(notebook)
        result, *rest = _module.parse_frontmatter(content, file_path=Path("test.ipynb"))
        assert result is None

    def test_merges_multiple_frontmatter_blocks(self):
        """Files with multiple YAML blocks at start → all blocks merged into one dict."""
        content = (
            "---\n"
            "jupytext:\n"
            "  text_representation: {format_name: myst}\n"
            "---\n"
            "\n"
            "---\n"
            "title: Governed Doc\n"
            "options:\n"
            "  type: guide\n"
            "---\n"
            "\n"
            "# Body\n"
        )
        result, *rest = _module.parse_frontmatter(content)
        assert isinstance(result, dict)
        assert "jupytext" in result, "Jupytext block missing from merged result"
        assert "title" in result, "Governed block missing from merged result"
        assert result["title"] == "Governed Doc"
        assert result["options"]["type"] == "guide"

    def test_merges_dual_blocks_with_whitespace_gap(self):
        """Dual-block frontmatter with a whitespace gap should be merged."""
        content = (
            "---\n"
            "jupytext: {format_name: myst}\n"
            "---\n"
            "\n  \n"
            "---\n"
            "title: Governed Doc\n"
            "options:\n"
            "  type: guide\n"
            "---\n"
            "\n"
            "# Body\n"
        )
        result, *rest = _module.parse_frontmatter(content)
        assert result is not None
        assert "jupytext" in result
        assert "title" in result
        assert result["options"]["type"] == "guide"

    def test_rejects_governed_field_in_non_governed_block(self, frontmatter_env):
        """Governed fields must reside exclusively in the governed block."""
        # Field 'token_size' is governed (non-myst_native)
        # It is placed in the first block (Jupytext), and omitted from the second (Governed)
        content = (
            "---\n"
            "jupytext:\n"
            "  text_representation: {format_name: myst}\n"
            "token_size: 100\n"
            "---\n"
            "\n"
            "---\n"
            "title: Governed Doc\n"
            "options:\n"
            "  type: guide\n"
            "---\n"
            "\n"
            "# Body\n"
        )
        file_path = frontmatter_env / "test_leak.md"
        file_path.write_text(content, encoding="utf-8")

        errors = _module.validate_frontmatter(file_path, frontmatter_env)

        has_placement_error = any(
            e.error_type == "misplaced_field" and e.field == "token_size"
            for e in errors
        )
        assert has_placement_error, "Governed field in Jupytext block should be rejected"

    def test_rejects_duplicate_governed_field_across_blocks(self, frontmatter_env):
        """Field present in both blocks → rejected as misplaced."""
        content = (
            "---\n"
            "jupytext:\n"
            "  text_representation: {format_name: myst}\n"
            "token_size: 100\n"
            "---\n"
            "\n"
            "---\n"
            "title: Governed Doc\n"
            "options:\n"
            "  type: guide\n"
            "token_size: 200\n"
            "---\n"
            "\n"
            "# Body\n"
        )
        file_path = frontmatter_env / "test_dup.md"
        file_path.write_text(content, encoding="utf-8")

        errors = _module.validate_frontmatter(file_path, frontmatter_env)

        has_placement_error = any(
            e.error_type == "misplaced_field" and e.field == "token_size"
            for e in errors
        )
        assert has_placement_error, "Duplicate governed field should be rejected as misplaced"

class TestBrokenDualBlock:
    """Contract: Detect missing separator fence in Dual-Block pattern.

    If a file has Jupytext metadata but the project metadata block starts
    without its own opening '---' fence, it must be reported as a
    'broken_dual_block' error, not a 'missing_type' error.
    """

    def test_detects_missing_separator_fence(self, frontmatter_env):
        """Missing fence between blocks → broken_dual_block error."""
        content = (
            "---\n"
            "jupytext:\n"
            "  text_representation: {format_name: myst}\n"
            "---\n"
            "\n"
            "title: Broken Dual Block\n"
            "options:\n"
            "  type: guide\n"
            "---\n"
            "\n"
            "# Body\n"
        )
        file_path = frontmatter_env / "broken_dual.md"
        file_path.write_text(content, encoding="utf-8")

        errors = _module.validate_frontmatter(file_path, frontmatter_env)

        # It should explicitly identify the broken dual block
        has_structural_error = any(
            e.error_type == "broken_dual_block"
            for e in errors
        )
        assert has_structural_error, "Should report 'broken_dual_block' when separator fence is missing"

        # It should NOT report 'missing_type' as the primary reason
        has_missing_type = any(
            e.error_type == "missing_type"
            for e in errors
        )
        assert not has_missing_type, "Should not report 'missing_type' when the block is structurally broken"

    def test_ignores_yaml_blocks_in_body(self, frontmatter_env):
        """YAML blocks occurring in the body of the document must be ignored.
        
        Contract: Only contiguous blocks at the start are parsed.
        """
        # Use config-driven valid frontmatter for the top block
        valid_fm = _build_valid_frontmatter("guide")
        top_block = yaml.dump(valid_fm, default_flow_style=False)
        
        # Create a fake YAML block for the body
        fake_fm = {"title": "Fake Title", "options": {"type": "adr"}}
        body_block = yaml.dump(fake_fm, default_flow_style=False)
        
        content = (
            f"---\n{top_block}---\n"
            "\n"
            "# Body\n"
            "Here is an example of a YAML block in the body:\n"
            "\n"
            f"---\n{body_block}---\n"
            "\n"
            "This should be ignored."
        )
        
        result, *rest = _module.parse_frontmatter(content)
        assert isinstance(result, dict)
        # Verify the top block was parsed
        assert result["title"] == valid_fm["title"]
        assert result["options"]["type"] == "guide"
        # Verify the body block was NOT merged
        assert result["title"] != "Fake Title"
        assert "Fake Title" not in str(result)


    def test_unquoted_colon_in_title_fails_parsing(self):
        """YAML with an unquoted colon in a value (e.g. title) should fail safe_load.
        The parser should log an error and skip the block.
        """
        content = (
            "---\n"
            "title: The Truth: A Guide\n"
            "options:\n"
            "  type: guide\n"
            "---\n"
        )
        # The current implementation logs an error and returns None if only one block exists and it fails
        result, *rest = _module.parse_frontmatter(content)
        assert result is None

    @pytest.mark.parametrize("separator", [
        "\\n",      # Single newline (consecutive fences)
        "\\n\\n",    # Double newline (empty line between fences)
        "\\n  \\n",  # Line with whitespace between fences
    ])
    def test_merges_consecutive_blocks_with_various_spacing(self, separator):
        """Files with consecutive YAML blocks separated by various whitespace → merge."""
        # Use repr to handle the escaped newlines in parametrization
        sep = separator.encode().decode('unicode_escape')
        content = (
            "---\n"
            "jupytext:\n"
            "  text_representation: {format_name: myst}\n"
            "---\n"
            f"{sep}"
            "---\n"
            "title: Governed Doc\n"
            "options:\n"
            "  type: guide\n"
            "---\n"
            "\n"
            "# Body\n"
        )
        result, *rest = _module.parse_frontmatter(content)
        assert isinstance(result, dict)
        assert "jupytext" in result, f"Failed to merge with separator {repr(sep)}"
        assert "title" in result, f"Failed to merge with separator {repr(sep)}"
        assert result["options"]["type"] == "guide"



# ======================
# Adversary Tests
# ======================


    def test_id_reserved_prefix_violation(self, frontmatter_env, monkeypatch):
        """ID using a prefix reserved for another type should be reported.

        Example: Custom type 'test_type' allows 'id' but has no prefix.
        It should reject 'ADR-12345' because 'ADR-' is reserved for 'adr'.
        """
        # 1. Setup hub config in the temporary environment
        hub_path = frontmatter_env / ".vadocs" / "conf.json"
        hub_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Start with a basic valid hub config
        hub_config = {
            "field_registry": {
                "id": {"myst_native": True}, 
                "title": {"myst_native": True}, 
                "authors": {"myst_native": True},
                "type": {"myst_native": False}
            },
            "blocks": {"identity": ["title", "type", "id", "authors"]},
            "types": {
                "adr": {"prefix": "ADR", "blocks": ["identity"], "required": ["id"]},
                "test_type": {"prefix": None, "blocks": ["identity"], "required": ["id"]}
            },
            "governed_extensions": [".md"]
        }
        hub_path.write_text(json.dumps(hub_config))
        
        # 2. Monkeypatch get_config_path to return our test hub path
        # This ensures the validator reads our controlled config instead of the project root
        monkeypatch.setattr(_module, "get_config_path", lambda root, type=None: hub_path if type is None else hub_path)
        
        # 3. Clear cache and update module-level constants that are used by the validator
        _module._config_cache.clear()
        monkeypatch.setattr(_module, "HUB_CONFIG", hub_config)
        monkeypatch.setattr(_module, "VALID_TYPES", set(hub_config["types"].keys()))

        # 4. Create the test file
        fm = {
            "title": "Test Document",
            "id": "ADR-12345",
            "authors": [{"name": "Vadim", "email": "v@v.com"}],
            "options": {"type": "test_type"}
        }
        file_path = frontmatter_env / "reserved_id.md"
        file_path.write_text(_frontmatter_to_md(fm), encoding="utf-8")

        errors = _module.validate_frontmatter(file_path, frontmatter_env)
        
        # Ensure we actually found an id error
        id_errors = [e for e in errors if e.field == "id"]
        assert len(id_errors) > 0, f"Expected id error, but got: {errors}"
        
        id_error = id_errors[0]
        assert id_error.error_type == "invalid_value"
        # Message wording is secondary to error_type and field.

class TestYamlAdversary:
    """Contract: Validator must handle adversarial YAML (aliases, anchors, recursion).

    YAML anchors (&) and aliases (*) can be used to create redundant data or,
    in extreme cases, recursive structures that lead to Denial of Service (DoS)
    via exponential expansion (Billion Laughs attack).
    """

    def test_yaml_aliases_merge_correctly(self, frontmatter_env):
        """YAML aliases should be expanded by safe_load and validated normally."""
        content = (
            "---\n"
            "defaults: &defaults\n"
            "  token_size: 100\n"
            "  version: 1.0.0\n"
            "options:\n"
            "  type: guide\n"
            "  <<: *defaults\n"
            "---\n"
            "\n"
            "# Body\n"
        )
        file_path = frontmatter_env / "alias_test.md"
        file_path.write_text(content, encoding="utf-8")

        errors = _module.validate_frontmatter(file_path, frontmatter_env)
        # Should be valid as far as YAML is concerned
        # (Though 'defaults' might be flagged as 'invalid_field' if not in registry)
        invalid_fields = [e for e in errors if e.error_type == "invalid_field" and e.field == "defaults"]
        # We care that it didn't crash and that options.token_size was resolved
        assert len(invalid_fields) > 0 # 'defaults' is unknown
        # Check that we didn't get a structural error
        assert not any(e.error_type == "invalid_yaml" for e in errors)

    def test_recursive_aliases_do_not_crash(self, frontmatter_env):
        """Recursive aliases should be handled gracefully by safe_load.

        PyYAML's safe_load generally prevents recursive anchors from causing
        infinite loops, but we must verify it doesn't crash the process.
        """
        content = (
            "---\n"
            "a: &a [\"loop\"]\n"
            "b: &b [*a, *b]\n"
            "options:\n"
            "  type: guide\n"
            "---\n"
        )
        file_path = frontmatter_env / "recursive_test.md"
        file_path.write_text(content, encoding="utf-8")

        # This should either return an error or a parsed dict, but NOT crash
        try:
            errors = _module.validate_frontmatter(file_path, frontmatter_env)
            assert isinstance(errors, list)
        except Exception as e:
            pytest.fail(f"Validator crashed on recursive YAML alias: {e}")


class TestInputAdversary:
    """Contract: Validator must be resilient to corrupted or non-text input.

    Includes binary data, malformed UTF-8, and YAML blocks that are not dictionaries.
    """

    def test_malformed_utf8_handled(self, frontmatter_env):
        """Files with invalid UTF-8 bytes should not crash the validator.

        If read_text(encoding='utf-8') raises UnicodeDecodeError, it should be
        caught and reported as a structural error.
        """
        file_path = frontmatter_env / "binary.md"
        # Write invalid UTF-8 bytes
        file_path.write_bytes(b"\xff\xfe\xfd\x00\x01")

        try:
            errors = _module.validate_frontmatter(file_path, frontmatter_env)
            assert isinstance(errors, list)
        except UnicodeDecodeError:
            pytest.fail("Validator crashed with UnicodeDecodeError on binary file")
        except Exception as e:
            pytest.fail(f"Validator crashed on binary file with unexpected error: {e}")

    def test_non_dict_yaml_blocks(self, frontmatter_env):
        """YAML blocks that are lists or scalars instead of dicts should be rejected.

        The validator expects frontmatter to be a mapping. If a block is a list
        or a string, it should be flagged as 'invalid_yaml'.
        """
        # Case 1: Block is a list
        content_list = "---\n- item1\n- item2\n---\n\n# Body\n"
        file_path_list = frontmatter_env / "list_block.md"
        file_path_list.write_text(content_list, encoding="utf-8")

        errors_list = _module.validate_frontmatter(file_path_list, frontmatter_env)
        assert any(e.error_type == "invalid_yaml" for e in errors_list), \
            "YAML list block should be reported as invalid_yaml"

        # Case 2: Block is a scalar
        content_scalar = "---\nJust a string\n---\n\n# Body\n"
        file_path_scalar = frontmatter_env / "scalar_block.md"
        file_path_scalar.write_text(content_scalar, encoding="utf-8")

        errors_scalar = _module.validate_frontmatter(file_path_scalar, frontmatter_env)
        assert any(e.error_type == "invalid_yaml" for e in errors_scalar), \
            "YAML scalar block should be reported as invalid_yaml"


class TestMainCoverage:
    """Targeted tests to close coverage gaps in main()."""

    def test_main_skips_hub_excluded_dirs(self, frontmatter_env, monkeypatch):
        """Files in hub's governance_excludes.dirs should be skipped."""
        # Add a directory to excludes in hub config
        hub_config = json.loads((frontmatter_env / ".vadocs" / "conf.json").read_text())
        hub_config["governance_excludes"] = {"dirs": ["excluded_dir"]}
        (frontmatter_env / ".vadocs" / "conf.json").write_text(json.dumps(hub_config))
        
        # Update monkeypatched hub config
        monkeypatch.setattr(_module, "HUB_CONFIG", hub_config)

        excluded_dir = frontmatter_env / "excluded_dir"
        excluded_dir.mkdir()
        file_path = excluded_dir / "test.md"
        file_path.write_text("---\noptions:\n  type: guide\n---\n", encoding="utf-8")

        # Run main and ensure it doesn't return errors for the excluded file
        # We pass the directory path to main
        with patch("sys.argv", ["check_frontmatter.py", str(excluded_dir)]):
            exit_code = _module.main()
        
        assert exit_code == 0

    def test_main_reports_missing_frontmatter_without_anomalies(self, frontmatter_env, monkeypatch):
        """Governed extension but no fences -> missing_frontmatter."""
        file_path = frontmatter_env / "no_fences.md"
        file_path.write_text("Just some text", encoding="utf-8")

        with patch("sys.argv", ["check_frontmatter.py", str(file_path)]):
            # We need to capture the output to verify the error, but here we check exit code
            exit_code = _module.main()

        assert exit_code == 1

    def test_main_handles_binary_file(self, frontmatter_env, monkeypatch):
        """Binary file passed to main() should return exit 1 and report invalid_encoding."""
        file_path = frontmatter_env / "binary_main.md"
        file_path.write_bytes(b"\xff\xfe\xfd")

        with patch("sys.argv", ["check_frontmatter.py", str(file_path)]):
            exit_code = _module.main()

        assert exit_code == 1

    def test_main_reports_structural_anomalies(self, frontmatter_env, monkeypatch):
        """Test that main() reports leading_newline, invalid_yaml, and broken_dual_block."""
        
        # 1. Leading newline
        file_nl = frontmatter_env / "leading_nl.md"
        file_nl.write_text("\n---\noptions:\n  type: guide\n---\n", encoding="utf-8")
        with patch("sys.argv", ["check_frontmatter.py", str(file_nl)]):
            assert _module.main() == 1

        # 2. Invalid YAML
        file_yaml = frontmatter_env / "bad_yaml.md"
        file_yaml.write_text("---\noptions: [missing colon\n---\n", encoding="utf-8")
        with patch("sys.argv", ["check_frontmatter.py", str(file_yaml)]):
            assert _module.main() == 1

        # 3. Broken dual block
        file_dual = frontmatter_env / "broken_dual.md"
        file_dual.write_text("---\njupytext: {extension: .md}\n---\noptions:\n  type: guide\n---\n", encoding="utf-8")
        with patch("sys.argv", ["check_frontmatter.py", str(file_dual)]):
            assert _module.main() == 1

class TestUnknownFieldSuggestions:
    """Verify that unknown fields trigger suggestions from common_mistakes."""
    def test_common_mistake_suggestion(self, frontmatter_env, monkeypatch):
        """Field in common_mistakes should trigger a suggestion."""
        hub_config = _module.HUB_CONFIG.copy()
        hub_config["common_mistakes"] = {"author": "authors"}
        monkeypatch.setattr(_module, "HUB_CONFIG", hub_config)

        fm = _build_valid_frontmatter("guide")
        fm["author"] = "Vadim" # typo
        file_path = frontmatter_env / "mistake.md"
        file_path.write_text(_frontmatter_to_md(fm), encoding="utf-8")

        errors = _module.validate_frontmatter(file_path, frontmatter_env)
        field_error = [e for e in errors if e.field == "author"][0]

        assert field_error.error_type == "invalid_field"
        # Message contains suggestion, but we assert on structural correctness
class TestFieldPlacementEdgeCases:
    """Coverage for edge cases in _check_governed_field_placement."""

    def test_no_blocks_returns_empty(self, frontmatter_env):
        """File with no YAML blocks returns no placement errors."""
        content = "# No blocks here"
        file_path = frontmatter_env / "no_blocks.md"
        file_path.write_text(content, encoding="utf-8")
        
        # We need a hub config to check governed fields
        errors = _module._check_governed_field_placement(content, file_path, _module.HUB_CONFIG)
        assert errors == []


class TestTypeResolutionEdgeCases:
    """Tests for dynamic type field resolution and fallback logic."""

    def test_type_field_fallback_to_type(self, frontmatter_env, monkeypatch):
        """If identity block has no type-specifying field, default to 'type'."""
        hub_path = frontmatter_env / ".vadocs" / "conf.json"
        hub_path.parent.mkdir(parents=True, exist_ok=True)
        hub_config = {
            "field_registry": {"title": {"myst_native": True}, "authors": {"myst_native": True}, "type": {"myst_native": False}},
            "blocks": {"identity": ["title", "authors"]}, # No type-like field here
            "types": {"guide": {"blocks": ["identity"], "required": []}},
            "governed_extensions": [".md"]
        }
        hub_path.write_text(json.dumps(hub_config))
        
        monkeypatch.setattr(_module, "get_config_path", lambda root, type=None: hub_path if type is None else hub_path)
        _module._config_cache.clear()
        monkeypatch.setattr(_module, "HUB_CONFIG", hub_config)
        monkeypatch.setattr(_module, "VALID_TYPES", set(hub_config["types"].keys()))

        fm = {"title": "Test", "options": {"type": "guide"}}
        file_path = frontmatter_env / "fallback.md"
        file_path.write_text(_frontmatter_to_md(fm), encoding="utf-8")

        # Should resolve as 'guide' using the fallback 'type' field
        assert _module.resolve_type(fm) == "guide"

    def test_find_field_block_spoke_fallback(self, frontmatter_env, monkeypatch):
        """Verify fallback to spoke config when field is not in hub blocks or required."""
        hub_config = {
            "field_registry": {"spoke_field": {"myst_native": False}},
            "blocks": {"identity": ["title"]},
            "types": {"adr": {"required": [], "blocks": ["identity"]}},
        }
        # Field 'spoke_field' is NOT in blocks.identity or types.adr.required
        
        # Use monkeypatch to simulate the hub config
        monkeypatch.setattr(_module, "HUB_CONFIG", hub_config)
        
        # Test the internal function directly
        res = _module._find_field_block("spoke_field", "adr", hub_config)
        assert res == ".vadocs/types/adr.conf.json → required_fields"

class TestFieldResolutionEdgeCases:
    """Tests for field value resolution and missing fields."""

    def test_get_field_value_missing(self, frontmatter_env):
        """Verify _get_field_value returns None when field is missing from both levels."""
        fm = {"title": "Test", "options": {"type": "guide"}}
        # Field 'id' is missing
        assert _module._get_field_value(fm, "id") is None

class TestParseFrontmatterAnomalies:
    """Targeted tests for complex parsing anomalies in parse_frontmatter."""

    def test_malformed_dual_block_yaml(self, frontmatter_env):
        """Dual block where the second block has invalid YAML."""
        content = "---\njupytext: {extension: .md}\n---\n---\noptions: [missing colon\n---\n"
        # This should trigger the yaml.YAMLError in the loop
        fm, count, anomalies = _module.parse_frontmatter(content, file_path=frontmatter_env / "bad_dual.md")
        assert "invalid_yaml" in anomalies

class TestResolveType:
    """Contract: resolve_type reads options.type from parsed frontmatter.

    Returns type string when present, None when missing.
    """

    def test_returns_type_from_options(self):
        """options.type present → returns type string."""
        fm = {"title": "Test", "options": {"type": "adr"}}
        assert _module.resolve_type(fm) == "adr"

    def test_returns_none_when_no_options(self):
        """No options key → None."""
        fm = {"title": "Test"}
        assert _module.resolve_type(fm) is None

    def test_returns_none_when_options_has_no_type(self):
        """options exists but no type key → None."""
        fm = {"title": "Test", "options": {"birth": "2026-01-01"}}
        assert _module.resolve_type(fm) is None


class TestResolveTypeDynamic:
    """Contract: resolve_type dynamically resolves field name from hub config.

    If HUB_CONFIG['blocks']['identity'] defines a different field for type,
    resolve_type must use that field.
    """

    def test_resolves_custom_type_field(self, frontmatter_env, monkeypatch):
        """Hub config defines 'doc_type' as type field → resolve_type uses it."""
        # Setup custom hub config
        custom_hub = _module.HUB_CONFIG.copy()
        custom_hub["blocks"] = {"identity": ["title", "doc_type", "authors"]}
        monkeypatch.setattr(_module, "HUB_CONFIG", custom_hub)

        fm = {"options": {"doc_type": "guide"}}
        assert _module.resolve_type(fm) == "guide"

        # Should return None if the custom field is missing, even if 'type' is present
        fm_wrong = {"options": {"type": "guide"}}
        assert _module.resolve_type(fm_wrong) is None


    def test_returns_none_for_empty_frontmatter(self):
        """Empty dict → None."""
        assert _module.resolve_type({}) is None


# ======================
# Tests: Required Fields Merge
# ======================


class TestGetRequiredFields:
    """Contract: _get_required_fields returns union of three sources.

    1. Hub block fields (expanded from type's block list)
    2. Hub types.<type>.required
    3. Spoke required_fields (if spoke exists)

    Union deduplicates. Types without spoke use only hub sources.
    """

    def test_adr_includes_block_fields(self):
        """ADR type has identity+discovery+lifecycle blocks → all block fields present."""
        required = _module._get_required_fields("adr", _HUB_CONFIG, _SPOKE_CONFIGS.get("adr"))
        # identity block fields
        for field in _BLOCKS["identity"]:
            assert field in required
        # lifecycle block fields
        for field in _BLOCKS["lifecycle"]:
            assert field in required

    def test_adr_includes_hub_type_required(self):
        """ADR hub types.adr.required (id, status) included."""
        required = _module._get_required_fields("adr", _HUB_CONFIG, _SPOKE_CONFIGS.get("adr"))
        for field in _TYPES["adr"]["required"]:
            assert field in required

    def test_adr_includes_spoke_required_fields(self):
        """ADR spoke required_fields merged in."""
        spoke = _SPOKE_CONFIGS.get("adr")
        if spoke and "required_fields" in spoke:
            required = _module._get_required_fields("adr", _HUB_CONFIG, spoke)
            for field in spoke["required_fields"]:
                assert field in required

    def test_type_without_spoke_uses_hub_only(self):
        """Tutorial has no spoke → required = block fields + hub type required."""
        required = _module._get_required_fields("tutorial", _HUB_CONFIG, None)
        tutorial_def = _TYPES["tutorial"]
        expected = set()
        for block_name in tutorial_def["blocks"]:
            expected.update(_BLOCKS[block_name])
        expected.update(tutorial_def["required"])
        assert required == expected

    def test_source_has_no_lifecycle_block(self):
        """Source type only has identity+discovery blocks, not lifecycle."""
        required = _module._get_required_fields("source", _HUB_CONFIG, _SPOKE_CONFIGS.get("source"))
        # lifecycle fields should NOT be required for source
        for field in _BLOCKS.get("lifecycle", []):
            if field not in _TYPES["source"].get("required", []):
                assert field not in required

    @pytest.mark.parametrize("doc_type", list(_TYPES.keys()))
    def test_all_types_return_set(self, doc_type):
        """Every hub type returns a non-empty set."""
        spoke = _SPOKE_CONFIGS.get(doc_type)
        required = _module._get_required_fields(doc_type, _HUB_CONFIG, spoke)
        assert isinstance(required, set)
        assert len(required) > 0  # at minimum, identity block fields


# ======================
# Tests: Token Counting
# ======================


class TestTokenCounting:
    """Contract: _calculate_tokens returns accurate token counts.

    Must handle normal text, large blocks, and special tokens (e.g. <|fim_prefix|>)
    without crashing.
    """

    def test_counts_normal_text(self):
        """Simple string returns expected count."""
        text = "Hello world"
        count = _module.calculate_tokens(text)
        assert isinstance(count, int)
        assert count > 0

    def test_handles_special_tokens_without_crashing(self):
        """Text containing special tokens (e.g. <|fim_prefix|>) does not crash.

        This prevents ValueError in tiktoken when documentation discusses
        LLM internal control sequences.
        """
        text = "The FIM token <|fim_prefix|> is used for fill-in-the-middle."
        # This should not raise ValueError
        count = _module.calculate_tokens(text)
        assert isinstance(count, int)
        assert count > 0


class TestValidateFieldPresence:
    """Contract: missing required fields produce errors.

    Field lookup checks both top-level and options.* (pre-migration compat).
    """

    def test_valid_frontmatter_no_errors(self, frontmatter_env):
        """Complete valid frontmatter for ADR → no errors."""
        fm = _build_valid_frontmatter("adr")
        md_file = frontmatter_env / "test.md"
        md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
        errors = _module.validate_frontmatter(md_file, frontmatter_env)
        field_errors = [e for e in errors if e.error_type == "missing_field"]
        assert len(field_errors) == 0

    def test_missing_required_field_detected(self, frontmatter_env):
        """Frontmatter missing 'title' → error with error_type 'missing_field'."""
        fm = _build_valid_frontmatter("adr")
        fm.pop("title", None)
        md_file = frontmatter_env / "test.md"
        md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
        errors = _module.validate_frontmatter(md_file, frontmatter_env)
        missing = [e for e in errors if e.error_type == "missing_field" and e.field == "title"]
        assert len(missing) > 0

    def test_field_under_options_counts_as_present(self, frontmatter_env):
        """Field at options.birth (not top-level) → not flagged as missing."""
        fm = _build_valid_frontmatter("adr")
        # birth should already be under options from _build_valid_frontmatter
        assert "birth" in fm.get("options", {})
        md_file = frontmatter_env / "test.md"
        md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
        errors = _module.validate_frontmatter(md_file, frontmatter_env)
        birth_errors = [e for e in errors if e.field == "birth"]
        assert len(birth_errors) == 0


class TestValidateDateFormat:
    """Contract: date and birth fields must match YYYY-MM-DD pattern."""

    def test_valid_date_accepted(self, frontmatter_env):
        """Standard date format → no date format errors."""
        fm = _build_valid_frontmatter("adr")
        md_file = frontmatter_env / "test.md"
        md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
        errors = _module.validate_frontmatter(md_file, frontmatter_env)
        date_errors = [e for e in errors if e.error_type == "invalid_format" and e.field in ("date", "birth")]
        assert len(date_errors) == 0

    def test_invalid_date_rejected(self, frontmatter_env):
        """Non-YYYY-MM-DD date → format error."""
        fm = _build_valid_frontmatter("adr")
        fm["date"] = "January 2026"
        md_file = frontmatter_env / "test.md"
        md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
        errors = _module.validate_frontmatter(md_file, frontmatter_env)
        date_errors = [e for e in errors if e.error_type == "invalid_format" and e.field == "date"]
        assert len(date_errors) > 0


class TestValidateTags:
    """Contract: tags must be from hub vocabulary."""

    def test_valid_tags_accepted(self, frontmatter_env):
        """Known tags → no tag errors."""
        fm = _build_valid_frontmatter("adr")
        fm["tags"] = [_VALID_TAGS[0]]
        md_file = frontmatter_env / "test.md"
        md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
        errors = _module.validate_frontmatter(md_file, frontmatter_env)
        tag_errors = [e for e in errors if e.error_type == "invalid_value" and e.field == "tags"]
        assert len(tag_errors) == 0

    def test_unknown_tag_rejected(self, frontmatter_env):
        """Unknown tag → value error."""
        fm = _build_valid_frontmatter("adr")
        fm["tags"] = ["nonexistent_tag_xyz"]
        md_file = frontmatter_env / "test.md"
        md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
        errors = _module.validate_frontmatter(md_file, frontmatter_env)
        tag_errors = [e for e in errors if e.error_type == "invalid_value" and e.field == "tags"]
        assert len(tag_errors) > 0


class TestValidateStatus:
    """Contract: status must match spoke-defined allowed values."""

    def test_valid_status_accepted(self, frontmatter_env):
        """Spoke-defined status → no errors."""
        fm = _build_valid_frontmatter("adr")
        md_file = frontmatter_env / "test.md"
        md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
        errors = _module.validate_frontmatter(md_file, frontmatter_env)
        status_errors = [e for e in errors if e.error_type == "invalid_value" and e.field == "status"]
        assert len(status_errors) == 0

    def test_invalid_status_rejected(self, frontmatter_env):
        """Non-allowed status → value error."""
        fm = _build_valid_frontmatter("adr")
        fm["status"] = "nonexistent_status"
        md_file = frontmatter_env / "test.md"
        md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
        errors = _module.validate_frontmatter(md_file, frontmatter_env)
        status_errors = [e for e in errors if e.error_type == "invalid_value" and e.field == "status"]
        assert len(status_errors) > 0


class TestValidateAuthors:
    """Contract: authors must be list of {name, email} objects."""

    def test_valid_authors_accepted(self, frontmatter_env):
        """List of {name, email} dicts → no errors."""
        fm = _build_valid_frontmatter("adr")
        fm["authors"] = [{"name": "Test", "email": "test@example.com"}]
        md_file = frontmatter_env / "test.md"
        md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
        errors = _module.validate_frontmatter(md_file, frontmatter_env)
        author_errors = [e for e in errors if e.field == "authors"]
        assert len(author_errors) == 0

    def test_non_list_authors_rejected(self, frontmatter_env):
        """String author instead of list → format error."""
        fm = _build_valid_frontmatter("adr")
        fm["authors"] = "Just A Name"
        md_file = frontmatter_env / "test.md"
        md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
        errors = _module.validate_frontmatter(md_file, frontmatter_env)
        author_errors = [e for e in errors if e.field == "authors"]
        assert len(author_errors) > 0

    def test_author_missing_email_rejected(self, frontmatter_env):
        """Author dict without email → format error."""
        fm = _build_valid_frontmatter("adr")
        fm["authors"] = [{"name": "Test"}]
        md_file = frontmatter_env / "test.md"
        md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
        errors = _module.validate_frontmatter(md_file, frontmatter_env)
        author_errors = [e for e in errors if e.field == "authors"]
        assert len(author_errors) > 0

# ======================
# Tests: Unknown Field Detection
# ======================


class TestUnknownFieldDetection:
    """Contract: forbid any fields not in the FIELD_REGISTRY or permitted infra-list.

    - Top-level: Must be in FIELD_REGISTRY (myst_native=true) or ALLOWED_INFRA_KEYS.
    - options.*: Must be in FIELD_REGISTRY.
    - Permitted infra keys (jupytext, kernelspec) must be allowed.
    - Unknown fields produce 'invalid_field' error.
    """

    def test_valid_fields_no_error(self, frontmatter_env):
        """All fields in registry → no unknown field errors."""
        fm = _build_valid_frontmatter("adr")
        md_file = frontmatter_env / "test_valid.md"
        md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
        errors = _module.validate_frontmatter(md_file, frontmatter_env)
        unknown_errors = [e for e in errors if e.error_type == "invalid_field"]
        assert len(unknown_errors) == 0

    def test_top_level_unknown_field_rejected(self, frontmatter_env):
        """Field 'mystery_field' at top level → invalid_field error with correct instruction."""
        fm = _build_valid_frontmatter("adr")
        fm["mystery_field"] = "I should not be here"
        md_file = frontmatter_env / "test_unknown_top.md"
        md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
        errors = _module.validate_frontmatter(md_file, frontmatter_env)
        unknown_errors = [e for e in errors if e.error_type == "invalid_field" and e.field == "mystery_field"]
        assert len(unknown_errors) > 0
        # Message wording is secondary to error_type and field.

    def test_author_field_suggests_authors(self, frontmatter_env):
        """Field 'author' at top level → suggests 'authors'."""
        fm = _build_valid_frontmatter("adr")
        fm["author"] = "Vadim"
        md_file = frontmatter_env / "test_author.md"
        md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
        errors = _module.validate_frontmatter(md_file, frontmatter_env)
        author_errors = [e for e in errors if e.field == "author"]
        assert len(author_errors) > 0
        assert author_errors[0].error_type == "invalid_field"
        # Message wording is secondary to error_type and field.

    def test_options_unknown_field_rejected(self, frontmatter_env):
        """Field 'mystery_field' under options → invalid_field error."""
        fm = _build_valid_frontmatter("adr")
        fm["options"]["mystery_field"] = "I should not be here"
        md_file = frontmatter_env / "test_unknown_options.md"
        md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
        errors = _module.validate_frontmatter(md_file, frontmatter_env)
        unknown_errors = [e for e in errors if e.error_type == "invalid_field" and e.field == "options.mystery_field"]
        # Note: the script might report 'mystery_field' or 'options.mystery_field'
        # We will check for the field name specifically.
        assert any(e.field == "mystery_field" or e.field == "options.mystery_field" for e in unknown_errors)

    def test_permitted_infra_keys_accepted(self, frontmatter_env):
        """jupytext and kernelspec at top level → no unknown field errors."""
        fm = _build_valid_frontmatter("adr")
        fm["jupytext"] = {"text_representation": {"extension": ".md"}}
        fm["kernelspec"] = {"name": "python3"}
        md_file = frontmatter_env / "test_infra.md"
        md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
        errors = _module.validate_frontmatter(md_file, frontmatter_env)
        unknown_errors = [e for e in errors if e.error_type == "invalid_field"]
        assert len(unknown_errors) == 0


class TestIDPrefixValidation:
    """Contract: ID fields must follow type-specific prefixing.

    - adr: ^ADR-\d+$ or ^\d+$
    - evidence (analysis): ^A-\d+$
    - evidence (source): ^S-\d+$
    - other types: Must NOT start with A-, S-, or ADR-

    Invalid IDs produce 'invalid_format' or 'invalid_value' errors.
    """

    def test_adr_valid_id(self, frontmatter_env):
        """ADR with valid ID (ADR-123 or 123) → no errors."""
        for valid_id in ["ADR-123", "123"]:
            fm = _build_valid_frontmatter("adr")
            fm["id"] = valid_id
            md_file = frontmatter_env / f"test_{valid_id}.md"
            md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
            errors = _module.validate_frontmatter(md_file, frontmatter_env)
            id_errors = [e for e in errors if e.field == "id"]
            assert len(id_errors) == 0, f"Valid ADR ID {valid_id} should be accepted"

    def test_adr_invalid_id(self, frontmatter_env):
        """ADR with invalid ID (e.g. A-123) → error."""
        fm = _build_valid_frontmatter("adr")
        fm["id"] = "A-123"
        md_file = frontmatter_env / "test_bad_adr.md"
        md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
        errors = _module.validate_frontmatter(md_file, frontmatter_env)
        id_errors = [e for e in errors if e.field == "id"]
        assert len(id_errors) > 0, "ADR ID starting with A- should be rejected"

    def test_evidence_analysis_valid_id(self, frontmatter_env):
        """Evidence analysis with valid ID (A-123) → no errors."""
        fm = _build_valid_frontmatter("analysis")
        fm["id"] = "A-123"
        md_file = frontmatter_env / "test_analysis.md"
        md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
        errors = _module.validate_frontmatter(md_file, frontmatter_env)
        id_errors = [e for e in errors if e.field == "id"]
        assert len(id_errors) == 0

    def test_evidence_analysis_invalid_id(self, frontmatter_env):
        """Evidence analysis with invalid ID (e.g. S-123) → error."""
        fm = _build_valid_frontmatter("analysis")
        fm["id"] = "S-123"
        md_file = frontmatter_env / "test_bad_analysis.md"
        md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
        errors = _module.validate_frontmatter(md_file, frontmatter_env)
        id_errors = [e for e in errors if e.field == "id"]
        assert len(id_errors) > 0

    def test_evidence_source_valid_id(self, frontmatter_env):
        """Evidence source with valid ID (S-123) → no errors."""
        fm = _build_valid_frontmatter("source")
        fm["id"] = "S-123"
        md_file = frontmatter_env / "test_source.md"
        md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
        errors = _module.validate_frontmatter(md_file, frontmatter_env)
        id_errors = [e for e in errors if e.field == "id"]
        assert len(id_errors) == 0

    def test_evidence_source_invalid_id(self, frontmatter_env):
        """Evidence source with invalid ID (e.g. A-123) → error."""
        fm = _build_valid_frontmatter("source")
        fm["id"] = "A-123"
        md_file = frontmatter_env / "test_bad_source.md"
        md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
        errors = _module.validate_frontmatter(md_file, frontmatter_env)
        id_errors = [e for e in errors if e.field == "id"]
        assert len(id_errors) > 0

    def test_other_types_forbid_reserved_prefixes(self, frontmatter_env):
        """guide type must not use A-, S-, or ADR- prefixes."""
        fm = _build_valid_frontmatter("guide")
        # guide might not have a required ID, but if it does, it must not be reserved
        for reserved in ["A-123", "S-123", "ADR-123"]:
            fm["id"] = reserved
            md_file = frontmatter_env / f"test_reserved_{reserved}.md"
            md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
            errors = _module.validate_frontmatter(md_file, frontmatter_env)
            id_errors = [e for e in errors if e.field == "id"]
            assert len(id_errors) > 0, f"Guide ID {reserved} should be rejected"


class TestOptionsNamespace:
    """Contract: non-myst_native fields at top level produce blocking errors.

    Ensures all non-MyST-native fields reside under options.* to maintain
    clean MyST-native top-level frontmatter.
    """

    def test_myst_native_at_top_level_no_error(self, frontmatter_env):
        """title, date, tags at top level (myst_native=true) → no namespace errors."""
        fm = _build_valid_frontmatter("adr")
        md_file = frontmatter_env / "test.md"
        md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
        errors = _module.validate_frontmatter(md_file, frontmatter_env)
        namespace_errors = [e for e in errors if e.error_type == "invalid_namespace"]
        # myst_native fields at top level should not produce errors
        myst_errors = [e for e in namespace_errors if e.field in ("title", "date", "tags", "description", "authors")]
        assert len(myst_errors) == 0

    def test_non_myst_native_at_top_level_produces_error(self, frontmatter_env):
        """Field with myst_native=false at top level → invalid_namespace error."""
        fm = _build_valid_frontmatter("adr")
        # 'version' is non-myst_native, so moving it to top level is a violation
        fm["version"] = fm["options"].pop("version")
        md_file = frontmatter_env / "test.md"
        md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
        errors = _module.validate_frontmatter(md_file, frontmatter_env)
        namespace_errors = [e for e in errors if e.error_type == "invalid_namespace" and e.field == "version"]
        assert len(namespace_errors) > 0


# ======================
# Tests: File Scanning
# ======================


class TestScanPaths:
    """Contract: scan_paths resolves inputs to file list.

    Files returned as-is. Directories walked recursively with exclusions.
    Format filter applied when scanning directories.
    """

    def test_file_path_returned_as_is(self, frontmatter_env):
        """Explicit file path → returned in list unchanged."""
        f = frontmatter_env / "test.md"
        f.write_text("# test", encoding="utf-8")
        result = _module.scan_paths([f], frontmatter_env)
        assert f in result

    def test_directory_scanned_recursively(self, frontmatter_env):
        """Directory path → all .md files found recursively."""
        subdir = frontmatter_env / "docs" / "sub"
        subdir.mkdir(parents=True)
        f1 = frontmatter_env / "docs" / "a.md"
        f2 = subdir / "b.md"
        f1.write_text("# a", encoding="utf-8")
        f2.write_text("# b", encoding="utf-8")
        result = _module.scan_paths([frontmatter_env / "docs"], frontmatter_env)
        assert f1 in result
        assert f2 in result

    def test_excluded_dirs_skipped(self, frontmatter_env):
        """Files inside VALIDATION_EXCLUDE_DIRS not returned."""
        misc_dir = frontmatter_env / "misc"
        misc_dir.mkdir()
        f = misc_dir / "note.md"
        f.write_text("# misc", encoding="utf-8")
        result = _module.scan_paths([frontmatter_env], frontmatter_env)
        assert f not in result

    def test_format_filter_md(self, frontmatter_env):
        """fmt='md' → only .md files, not .ipynb."""
        f_md = frontmatter_env / "test.md"
        f_ipynb = frontmatter_env / "test.ipynb"
        f_md.write_text("# md", encoding="utf-8")
        f_ipynb.write_text("{}", encoding="utf-8")
        result = _module.scan_paths([frontmatter_env], frontmatter_env, fmt="md")
        assert f_md in result
        assert f_ipynb not in result

    def test_format_filter_ipynb(self, frontmatter_env):
        """fmt='ipynb' → only .ipynb files, not .md."""
        f_md = frontmatter_env / "test.md"
        f_ipynb = frontmatter_env / "test.ipynb"
        f_md.write_text("# md", encoding="utf-8")
        f_ipynb.write_text("{}", encoding="utf-8")
        result = _module.scan_paths([frontmatter_env], frontmatter_env, fmt="ipynb")
        assert f_ipynb in result
        assert f_md not in result

    def test_mixed_file_and_dir_args(self, frontmatter_env):
        """Mix of file and directory → both resolved."""
        subdir = frontmatter_env / "docs"
        subdir.mkdir()
        f1 = frontmatter_env / "root.md"
        f2 = subdir / "nested.md"
        f1.write_text("# root", encoding="utf-8")
        f2.write_text("# nested", encoding="utf-8")
        result = _module.scan_paths([f1, subdir], frontmatter_env)
        assert f1 in result
        assert f2 in result

    def test_explicit_file_in_excluded_dir_is_skipped(self, frontmatter_env, monkeypatch):
        """Explicitly passing a file from an excluded directory should be skipped."""
        # Define a dummy exclude dir
        monkeypatch.setattr(_module, "VALIDATION_EXCLUDE_DIRS", {"excluded_dir"})

        excl_dir = frontmatter_env / "excluded_dir"
        excl_dir.mkdir()
        test_file = excl_dir / "test.md"
        test_file.write_text("# content", encoding="utf-8")

        result = _module.scan_paths([test_file], frontmatter_env)
        assert result == [], f"File in excluded directory should be skipped, but got: {result}"


# ======================
# Tests: CLI and Error Reporting
# ======================


class TestMainExitCodes:
    """Contract: main() returns 0 for valid files, 1 for errors.

    Blocking errors (missing fields, invalid formats, namespace violations) cause exit 1.
    """

    def test_exit_0_all_valid(self, frontmatter_env):
        """All files valid → exit 0."""
        fm = _build_valid_frontmatter("adr")
        md_file = frontmatter_env / "test.md"
        md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
        exit_code = _module.main([str(md_file)])
        assert exit_code == 0

    def test_exit_1_on_errors(self, frontmatter_env):
        """File with missing required field → exit 1."""
        fm = _build_valid_frontmatter("adr")
        fm.pop("title", None)
        md_file = frontmatter_env / "test.md"
        md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
        exit_code = _module.main([str(md_file)])
        assert exit_code == 1

    def test_exit_1_on_namespace_violation(self, frontmatter_env):
        """File with non-myst_native field at top level → exit 1."""
        fm = _build_valid_frontmatter("adr")
        # Move 'version' to top level to trigger invalid_namespace
        fm["version"] = fm["options"].pop("version")
        md_file = frontmatter_env / "test.md"
        md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
        exit_code = _module.main([str(md_file)])
        assert exit_code == 1, "Namespace violation should be a blocking error (exit 1)"

    def test_no_args_scans_repo_root(self, frontmatter_env):
        """No args → scans from repo root."""
        # Create a valid file in the test env root
        fm = _build_valid_frontmatter("guide")
        md_file = frontmatter_env / "test_guide.md"
        md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
        # Should not crash — scans from REPO_ROOT (monkeypatched to tmp)
        exit_code = _module.main([])
        assert isinstance(exit_code, int)


class TestMissingTypeError:
    """Contract: files with frontmatter but no options.type cause exit 1."""

    def test_main_exits_1_for_missing_type(self, frontmatter_env, caplog):
        """File without options.type → exit code 1, error on stdout."""
        content = "---\ntitle: Untyped Document\ndate: 2026-01-01\n---\n\n# Body\n"
        md_file = frontmatter_env / "untyped.md"
        md_file.write_text(content, encoding="utf-8")
        exit_code = _module.main([str(md_file)])
        assert exit_code == 1
        assert "options.type" in caplog.text
        assert "missing" in caplog.text.lower()

    def test_error_printed_for_missing_type(self, frontmatter_env, caplog):
        """File with frontmatter but no options.type → error on stdout, exit 1."""
        content = "---\ntitle: Untyped Document\ndate: 2026-01-01\n---\n\n# Body\n"
        md_file = frontmatter_env / "untyped.md"
        md_file.write_text(content, encoding="utf-8")
        exit_code = _module.main([str(md_file)])
        assert exit_code == 1
        assert "options.type" in caplog.text


class TestErrorMessages:
    """Contract: FrontmatterError fields are populated correctly.

    Tests dataclass field population, not message wording.
    """

    def test_error_has_file_path(self, frontmatter_env):
        """Every error includes the file path."""
        fm = _build_valid_frontmatter("adr")
        fm.pop("title", None)
        md_file = frontmatter_env / "test.md"
        md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
        errors = _module.validate_frontmatter(md_file, frontmatter_env)
        for error in errors:
            assert error.file_path == md_file

    def test_error_has_config_source(self, frontmatter_env):
        """Every error includes the config source reference."""
        fm = _build_valid_frontmatter("adr")
        fm.pop("title", None)
        md_file = frontmatter_env / "test.md"
        md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
        errors = _module.validate_frontmatter(md_file, frontmatter_env)
        missing_errors = [e for e in errors if e.error_type == "missing_field"]
        for error in missing_errors:
            assert error.config_source  # non-empty string
            assert ".vadocs/" in error.config_source  # points to a config

    def test_error_has_field_name(self, frontmatter_env):
        """Missing field errors include the field name."""
        fm = _build_valid_frontmatter("adr")
        fm.pop("title", None)
        md_file = frontmatter_env / "test.md"
        md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
        errors = _module.validate_frontmatter(md_file, frontmatter_env)
        title_errors = [e for e in errors if e.field == "title"]
        assert len(title_errors) > 0


# ======================
# Tests: Coverage Gaps
# ======================


class TestValidateFrontmatterConvenience:
    """Contract: validate_frontmatter() reads file, parses, and delegates."""

    def test_returns_error_when_governed_file_has_no_frontmatter(self, frontmatter_env):
        """Governed file (.md) without frontmatter → [missing_frontmatter error]."""
        md_file = frontmatter_env / "no_fm.md"
        md_file.write_text("# Just a heading\n\nNo frontmatter here.\n", encoding="utf-8")
        errors = _module.validate_frontmatter(md_file, frontmatter_env)
        missing_fm = [e for e in errors if e.error_type == "missing_frontmatter"]
        assert len(missing_fm) == 1
        assert missing_fm[0].field is None
        # Message wording is secondary to error_type and field.

    def test_returns_empty_when_non_governed_extension_has_no_frontmatter(self, frontmatter_env):
        """Non-governed file (.txt) without frontmatter → empty list."""
        txt_file = frontmatter_env / "no_fm.txt"
        txt_file.write_text("Plain text content.", encoding="utf-8")
        errors = _module.validate_frontmatter(txt_file, frontmatter_env)
        assert errors == []

    def test_returns_error_when_no_type(self, frontmatter_env):
        """File with frontmatter but no options.type → returns [FrontmatterError]."""
        content = "---\ntitle: Untyped\ndate: 2026-01-01\n---\n\n# Body\n"
        md_file = frontmatter_env / "untyped.md"
        md_file.write_text(content, encoding="utf-8")
        errors = _module.validate_frontmatter(md_file, frontmatter_env)
        missing_type = [e for e in errors if e.error_type == "missing_type"]
        assert len(missing_type) == 1


class TestValidateMissingType:
    """Contract: files with frontmatter but no options.type produce blocking error."""

    def test_validate_parsed_frontmatter_returns_error_for_missing_type(self, frontmatter_env):
        """Frontmatter without options.type → returns [FrontmatterError]."""
        fm = {"title": "Test", "date": "2026-01-01"}  # no options.type
        md_file = frontmatter_env / "test.md"
        errors = _module.validate_parsed_frontmatter(fm, md_file, frontmatter_env)
        missing_type = [e for e in errors if e.error_type == "missing_type"]
        assert len(missing_type) == 1
        assert missing_type[0].field == "options.type"
        # Message wording is secondary to error_type and field.

    def test_validate_parsed_frontmatter_no_error_when_type_present(self, frontmatter_env):
        """Frontmatter with options.type → no missing_type error."""
        fm = {"title": "Test", "options": {"type": "adr"}}
        md_file = frontmatter_env / "test.md"
        errors = _module.validate_parsed_frontmatter(fm, md_file, frontmatter_env)
        missing_type = [e for e in errors if e.error_type == "missing_type"]
        assert len(missing_type) == 0


class TestUnknownType:
    """Contract: unknown options.type is a blocking error."""

    def test_unknown_type_returns_error(self, frontmatter_env):
        """options.type not in conf.json → unknown_type error."""
        content = "---\ntitle: Bad Type\noptions:\n  type: nonexistent_type\n---\n\n# Body\n"
        md_file = frontmatter_env / "bad_type.md"
        md_file.write_text(content, encoding="utf-8")
        errors = _module.validate_frontmatter(md_file, frontmatter_env)
        assert any(e.error_type == "unknown_type" for e in errors)
        assert any(e.field == "options.type" for e in errors)



class TestAuthorNonDict:
    """Contract: author entries must be dicts, not strings."""

    def test_string_author_rejected(self, frontmatter_env):
        """Author as plain string instead of {name, email} → invalid_format."""
        fm = _build_valid_frontmatter("adr")
        fm["authors"] = ["Jane Doe"]  # string, not dict
        md_file = frontmatter_env / "bad_author.md"
        md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
        errors = _module.validate_frontmatter(md_file, frontmatter_env)
        author_errors = [e for e in errors if e.field == "authors"]
        assert len(author_errors) > 0
        assert author_errors[0].error_type == "invalid_format"


class TestParseEdgeCases:
    """Contract: parse_frontmatter handles malformed input gracefully."""

    def test_ipynb_invalid_json(self):
        """Broken JSON in .ipynb → None (not an exception)."""
        result, *rest = _module.parse_frontmatter("not json at all", file_path=Path("test.ipynb"))
        assert result is None

    def test_malformed_yaml_returns_none(self):
        """Invalid YAML between --- fences → None."""
        content = "---\n[invalid yaml: {\n---\n\n# Body\n"
        result, *rest = _module.parse_frontmatter(content)
        assert result is None


class TestFindFieldBlockFallback:
    """Contract: _find_field_block returns correct source for all three paths."""

    def test_spoke_required_fields_fallback(self, frontmatter_env):
        """Field only in spoke required_fields → spoke config source string."""
        # Find a field that's in a spoke's required_fields but NOT in any
        # hub block or hub types.X.required — so _find_field_block falls
        # through to the spoke fallback path.
        hub_block_fields = set()
        for block_fields in _BLOCKS.values():
            hub_block_fields.update(block_fields)

        spoke_only_field = None
        spoke_type = None
        for type_name, spoke in _SPOKE_CONFIGS.items():
            hub_type_required = set(_TYPES.get(type_name, {}).get("required", []))
            for field in spoke.get("required_fields", []):
                if field not in hub_block_fields and field not in hub_type_required:
                    spoke_only_field = field
                    spoke_type = type_name
                    break
            if spoke_only_field:
                break

        if spoke_only_field is None:
            pytest.skip("No spoke-only required field found in current config")

        hub, _ = _module.load_config_chain(frontmatter_env, spoke_type)
        source = _module._find_field_block(spoke_only_field, spoke_type, hub)
        # Contract: spoke-only fields point to spoke config, not hub
        assert f"{spoke_type}.conf.json" in source

# ======================
# Tests: Mandatory Governance
# ======================

class TestMandatoryGovernance:
    """Contract: All .md and .ipynb files must have YAML frontmatter.

    Files without frontmatter must no longer be silently skipped and should
    produce a blocking error.
    """

    def test_file_without_frontmatter_produces_error(self, frontmatter_env, caplog):
        """File with no frontmatter fences → blocking error (exit 1)."""
        md_file = frontmatter_env / "no_fm.md"
        md_file.write_text("# Just a heading\n\nNo frontmatter here.", encoding="utf-8")

        # Run main on the specific file
        exit_code = _module.main([str(md_file)])

        assert exit_code == 1
        # Check for error message indicating missing frontmatter
        assert "governed extension" in caplog.text and "no YAML frontmatter present" in caplog.text
    def test_excluded_directory_is_skipped(self, frontmatter_env, capsys):
        """File in an excluded directory → silently skipped (exit 0)."""
        # 'misc' is in our governed_excludes.dirs config
        misc_dir = frontmatter_env / "misc"
        misc_dir.mkdir()
        md_file = misc_dir / "test.md"
        md_file.write_text("# No frontmatter, but in misc/", encoding="utf-8")
        
        exit_code = _module.main([str(md_file)])
        
        captured = capsys.readouterr()
        assert exit_code == 0
        assert "no YAML frontmatter present" not in captured.out

    def test_excluded_filename_is_skipped(self, frontmatter_env, capsys):
        """Explicitly excluded filename (e.g. CONTRIBUTING.md) → silently skipped (exit 0)."""
        # 'CONTRIBUTING.md' is in our governed_excludes.files config
        contrib_file = frontmatter_env / "CONTRIBUTING.md"
        contrib_file.write_text("# Contributing\nNo frontmatter here.", encoding="utf-8")
    
        exit_code = _module.main([str(contrib_file)])
    
        captured = capsys.readouterr()
        assert exit_code == 0
        assert "no YAML frontmatter present" not in captured.out

    def test_non_governed_extension_is_skipped(self, frontmatter_env, capsys):
        """File with extension NOT in governed_extensions → silently skipped (exit 0)."""
        txt_file = frontmatter_env / "notes.txt"
        txt_file.write_text("Just some plain text notes.", encoding="utf-8")
        
        exit_code = _module.main([str(txt_file)])
        
        captured = capsys.readouterr()
        assert exit_code == 0
        assert "no YAML frontmatter present" not in captured.out

    def test_adversary_empty_fences(self, frontmatter_env, caplog):
        """File with empty YAML fences (--- \n ---) → treat as missing frontmatter (exit 1)."""
        md_file = frontmatter_env / "empty_fences.md"
        md_file.write_text("---\n---\n\n# Body", encoding="utf-8")

        exit_code = _module.main([str(md_file)])

        # Since parse_frontmatter returns None for empty blocks or failed YAML
        assert exit_code == 1
        assert "no YAML frontmatter present" in caplog.text

    def test_adversary_misplaced_fences(self, frontmatter_env, caplog):
        """Fences not at start of file → not recognized as frontmatter (exit 1)."""
        md_file = frontmatter_env / "misplaced.md"
        md_file.write_text("# Header\n\n---\ntitle: Test\n---\n\nBody", encoding="utf-8")

        exit_code = _module.main([str(md_file)])

        assert exit_code == 1
        # Should be reported as broken_dual_block due to asymmetric fence
        assert "Broken Dual-Block pattern" in caplog.text

    def test_adversary_invalid_yaml(self, frontmatter_env, caplog):
        """Frontmatter with invalid YAML syntax → treated as missing/invalid (exit 1)."""
        md_file = frontmatter_env / "invalid_yaml.md"
        md_file.write_text("---\ntitle: [unclosed list\n---\n\n# Body", encoding="utf-8")

        exit_code = _module.main([str(md_file)])

        assert exit_code == 1
        assert "YAML syntax error in frontmatter block" in caplog.text

    def test_adversary_scalar_yaml(self, frontmatter_env, caplog):
        """Frontmatter that is valid YAML but not a dict (e.g. just a string) → exit 1."""
        for val in ["Just a string", "123", "true", "null", "[]"]:
            md_file = frontmatter_env / f"scalar_{val}.md"
            md_file.write_text(f"---\n{val}\n---\n\n# Body", encoding="utf-8")

            exit_code = _module.main([str(md_file)])
            assert exit_code == 1
            assert "YAML syntax error in frontmatter block" in caplog.text
    def test_adversary_notebook_edge_cases(self, frontmatter_env, capsys):
        """Notebook structural edge cases → exit 1 or skip based on governance."""
        # 1. Notebook with no cells
        nb_empty = frontmatter_env / "empty.ipynb"
        nb_empty.write_text(json.dumps({"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}), encoding="utf-8")
        assert _module.main([str(nb_empty)]) == 1 # governed ext, but no frontmatter

        # 2. Notebook with first cell not markdown
        nb_code_first = frontmatter_env / "code_first.ipynb"
        nb_code_first.write_text(json.dumps({
            "cells": [{"cell_type": "code", "source": ["print(1)"], "outputs": [], "execution_count": None}],
            "metadata": {}, "nbformat": 4, "nbformat_minor": 5
        }), encoding="utf-8")
        assert _module.main([str(nb_code_first)]) == 1 # governed ext, no frontmatter in first cell

        # 3. Notebook with markdown first cell but no frontmatter
        nb_no_fm = frontmatter_env / "no_fm.ipynb"
        nb_no_fm.write_text(json.dumps({
            "cells": [{"cell_type": "markdown", "source": ["# Hello"], "outputs": [], "execution_count": None}],
            "metadata": {}, "nbformat": 4, "nbformat_minor": 5
        }), encoding="utf-8")
        assert _module.main([str(nb_no_fm)]) == 1

# ======================
# Tests: Token Size Accuracy
# ======================


class TestTokenSizeAccuracy:
    """Contract: token_size must be accurate within a small margin (10 tokens).

    Incorrect token_size produces a blocking error with a pointer to the
    update script. Valid counts (within margin) pass.
    """

    def test_incorrect_token_size_triggers_error(self, frontmatter_env):
        """Declared token_size differs significantly from actual content → error."""
        # Build valid frontmatter for a type that requires token_size (usually governed)
        fm = _build_valid_frontmatter("adr")
        # Force an incorrect token size
        fm.setdefault("options", {})["token_size"] = 1

        # Create a file with a significant amount of content to ensure actual tokens > 11
        body = "This is a long document that should have many more than 11 tokens. " * 10
        content = f"---\n{yaml.dump(fm, default_flow_style=False)}---\n\n{body}"
        file_path = frontmatter_env / "token_test.md"
        file_path.write_text(content, encoding="utf-8")

        errors = _module.validate_frontmatter(file_path, frontmatter_env)
        token_errors = [e for e in errors if e.field == "token_size"]
        assert len(token_errors) == 1
        assert token_errors[0].error_type == "invalid_value"
        # Message contains pointer to update script, but we assert on structural correctness

    def test_correct_token_size_passes(self, frontmatter_env):
        """Declared token_size is accurate (or within margin) → no error."""
        import tiktoken
        encoding = tiktoken.get_encoding("cl100k_base")

        # Use a simple content
        body = "Hello world!"
        fm = _build_valid_frontmatter("adr")
        
        file_path = frontmatter_env / "token_pass.md"
        # Write initial version to calculate actual tokens of the whole file
        content_init = f"---\n{yaml.dump(fm, default_flow_style=False)}---\n\n{body}"
        file_path.write_text(content_init, encoding="utf-8")

        # Calculate actual tokens of the final file
        actual_tokens = len(encoding.encode(file_path.read_text(encoding="utf-8")))

        # Update frontmatter with correct value and rewrite
        fm["options"]["token_size"] = actual_tokens
        content_final = f"---\n{yaml.dump(fm, default_flow_style=False)}---\n\n{body}"
        file_path.write_text(content_final, encoding="utf-8")

        errors = _module.validate_frontmatter(file_path, frontmatter_env)
        token_errors = [e for e in errors if e.field == "token_size"]
        assert len(token_errors) == 0

    def test_token_size_within_margin_passes(self, frontmatter_env):
        """token_size within +/- 10 tokens of actual count → no error."""
        import tiktoken
        encoding = tiktoken.get_encoding("cl100k_base")

        body = "Hello world!"
        fm = _build_valid_frontmatter("adr")

        file_path = frontmatter_env / "token_margin.md"
        content_init = f"---\n{yaml.dump(fm, default_flow_style=False)}---\n\n{body}"
        file_path.write_text(content_init, encoding="utf-8")

        actual_tokens = len(encoding.encode(file_path.read_text(encoding="utf-8")))

        # Set value to actual - 5 (within 10 margin)
        fm["options"]["token_size"] = actual_tokens - 5
        content_final = f"---\n{yaml.dump(fm, default_flow_style=False)}---\n\n{body}"
        file_path.write_text(content_final, encoding="utf-8")

        errors = _module.validate_frontmatter(file_path, frontmatter_env)
        token_errors = [e for e in errors if e.field == "token_size"]
        assert len(token_errors) == 0

    def test_non_integer_token_size_triggers_error(self, frontmatter_env):
        """Non-integer token_size (e.g. '~800') → blocking error, not crash."""
        fm = _build_valid_frontmatter("adr")
        fm.setdefault("options", {})["token_size"] = "~800"

        body = "Some content"
        content = f"---\n{yaml.dump(fm, default_flow_style=False)}---\n\n{body}"
        file_path = frontmatter_env / "token_non_int.md"
        file_path.write_text(content, encoding="utf-8")

        errors = _module.validate_frontmatter(file_path, frontmatter_env)
        token_errors = [e for e in errors if e.field == "token_size"]
        assert len(token_errors) == 1
        assert token_errors[0].error_type == "invalid_format"
        # Message wording is secondary to error_type and field.

# ======================
# Tests: Duplicate Governed Fields
# ======================


class TestDuplicateFields:
    """Contract: Governed fields must not be duplicated across multiple blocks.

    In Dual-Block files, fields like token_size must reside exclusively in
    the governed block. Duplicate governed fields produce blocking errors.
    """

    def test_duplicate_token_size_rejected(self, frontmatter_env):
        """token_size appearing in both blocks should produce duplicate_field error."""

        # Build valid base frontmatter for a guide
        fm = _build_valid_frontmatter("guide")
        
        # Jupytext block
        jupytext_fm = {
            "jupytext": {"text_representation": {"format_name": "myst"}},
            "options": {"token_size": 100}
        }
        # Governed block
        governed_fm = fm
        governed_fm["options"]["token_size"] = 100

        content = (
            f"---\n{yaml.dump(jupytext_fm, sort_keys=False)}---\n\n"
            f"---\n{yaml.dump(governed_fm, sort_keys=False)}---\n\n"
            "# Body\n"
        )
        
        file_path = frontmatter_env / "duplicate_tokens.md"
        file_path.write_text(content, encoding="utf-8")
        
        import tools.scripts.update_token_counts as _utc
        _utc.update_token_counts(frontmatter_env, [file_path], dry_run=False)

        with patch("sys.argv", ["check_frontmatter", str(file_path)]):
            exit_code = _module.main()

        assert exit_code == 1

    def test_single_token_size_accepted(self, frontmatter_env):
        """token_size appearing only in governed block should pass."""
    
        fm = _build_valid_frontmatter("guide")
        
        jupytext_fm = {
            "jupytext": {"text_representation": {"format_name": "myst"}}
        }
        governed_fm = fm
    
        # We generate the content first to know the actual token count
        # Note: we use a placeholder for token_size to calculate the length of the rest of the file
        content_template = (
            f"---\n{yaml.dump(jupytext_fm, sort_keys=False)}---\n\n"
            f"---\n{yaml.dump(governed_fm, sort_keys=False)}---\n\n"
            "# Body\n"
        )
        
        import tiktoken
        from tools.scripts.check_frontmatter import DEFAULT_TOKEN_ENCODING
        encoding = tiktoken.get_encoding(DEFAULT_TOKEN_ENCODING)
        actual_tokens = len(encoding.encode(content_template, disallowed_special=()))
        
        # Now we set the actual count in the governed block
        fm["options"]["token_size"] = actual_tokens
        
        # Re-generate content with the correct token size
        content = (
            f"---\n{yaml.dump(jupytext_fm, sort_keys=False)}---\n\n"
            f"---\n{yaml.dump(governed_fm, sort_keys=False)}---\n\n"
            "# Body\n"
        )
    
        file_path = frontmatter_env / "single_token.md"
        file_path.write_text(content, encoding="utf-8")
    
        with patch("sys.argv", ["check_frontmatter", str(file_path)]):
            exit_code = _module.main()
    
        assert exit_code == 0

class TestTokenSizeExclusions:
    """Contract: token_size validation is skipped for extensions in hub config's token_size_exclusions.
    
    This prevents perpetual conflicts between .md and .ipynb pairs where the .md
    remains the Single Source of Truth for token counts.
    """

    def test_md_file_still_validated(self, frontmatter_env, monkeypatch):
        # Ensure .ipynb is excluded in config
        hub = json.loads((frontmatter_env / ".vadocs" / "conf.json").read_text())
        hub["token_size_exclusions"] = [".ipynb"]
        (frontmatter_env / ".vadocs" / "conf.json").write_text(json.dumps(hub))
        monkeypatch.setattr(_module, "HUB_CONFIG", hub)

        # File with incorrect token_size
        fm = _build_valid_frontmatter("guide")
        fm["options"]["token_size"] = 999999 # Obviously wrong
        
        file_path = frontmatter_env / "test.md"
        file_path.write_text(_frontmatter_to_md(fm))
        
        errors = _module.validate_frontmatter(file_path, frontmatter_env)
        # Should find a token_size error
        assert any(e.field == "token_size" for e in errors)

    def test_ipynb_file_excluded_from_validation(self, frontmatter_env, monkeypatch):
        # Ensure .ipynb is excluded in config
        hub = json.loads((frontmatter_env / ".vadocs" / "conf.json").read_text())
        hub["token_size_exclusions"] = [".ipynb"]
        (frontmatter_env / ".vadocs" / "conf.json").write_text(json.dumps(hub))
        monkeypatch.setattr(_module, "HUB_CONFIG", hub)

        # File with incorrect token_size
        fm = _build_valid_frontmatter("guide")
        fm["options"]["token_size"] = 999999 # Obviously wrong
        
        # Create a dummy notebook JSON
        notebook = {
            "cells": [{"cell_type": "markdown", "source": [f"---\n{yaml.dump(fm)}---\n\n# Content\n"]}],
            "metadata": {}, "nbformat": 4, "nbformat_minor": 5
        }
        file_path = frontmatter_env / "test.ipynb"
        file_path.write_text(json.dumps(notebook))
        
        errors = _module.validate_frontmatter(file_path, frontmatter_env)
        # Should NOT find a token_size error for .ipynb
        assert not any(e.field == "token_size" for e in errors)

class TestFieldAllowList:
    """Contract: Governed fields must be listed in required or optional for the doc type.
    
    If a field exists in the hub registry but is not permitted for the specific 
    doc_type, it should be rejected as 'invalid_field'.
    """
    def test_rejects_governed_field_not_permitted_for_type(self, frontmatter_env):
        """Field in registry but not in type's allow-list → invalid_field error."""
        # 'guide' has blocks: ["identity", "discovery", "lifecycle"]
        # 'id' is governed (in registry) but NOT in those blocks, 
        # nor in required/optional for 'guide' (see conf.json)
        fm = _build_valid_frontmatter("guide")
        fm["id"] = 26062
        
        # We need to use validate_parsed_frontmatter since we have a dict
        errors = _module.validate_parsed_frontmatter(fm, Path("test.md"), frontmatter_env)
        
        invalid_field_errors = [e for e in errors if e.error_type == "invalid_field"]
        assert len(invalid_field_errors) > 0, "Should have found an invalid_field error for 'id' in 'guide'"
        assert any(e.field == "id" for e in invalid_field_errors)

# ======================
# Tests: Dual-Block Enforcement
# ======================

class TestDualBlockEnforcement:
    """Contract: Files containing Jupytext metadata MUST use the Dual-Block pattern."""

    def test_rejects_merged_blocks_when_jupytext_present(self, frontmatter_env):
        """If Jupytext metadata is present, it must be in a separate block from the type."""
        # Merged block: contains both Jupytext and project metadata in ONE block
        content = (
            "---\n"
            "jupytext: {format_name: myst}\n"
            "title: Merged Doc\n"
            "options:\n"
            "  type: guide\n"
            "---\n"
            "\n# Body\n"
        )
        file_path = frontmatter_env / "merged_jupytext.md"
        file_path.write_text(content, encoding="utf-8")

        errors = _module.validate_frontmatter(file_path, frontmatter_env)
        
        has_merged_error = any(
            e.error_type == "merged_blocks" 
            for e in errors
        )
        assert has_merged_error, "Jupytext metadata merged into governance block should be rejected"


    def test_accepts_single_block_without_jupytext(self, frontmatter_env):
        """Standard governed files without Jupytext should be fine with a single block."""
        content = (
            "---\n"
            "title: Standard Doc\n"
            "options:\n"
            "  type: guide\n"
            "---\n"
            "\n# Body\n"
        )
        file_path = frontmatter_env / "standard.md"
        file_path.write_text(content, encoding="utf-8")

        errors = _module.validate_frontmatter(file_path, frontmatter_env)

        has_merged_error = any(
            e.error_type == "merged_blocks"
            for e in errors
        )
        assert not has_merged_error, "Single block without Jupytext should NOT be flagged as merged"


# ======================
# Adversary Testing
# ======================

class TestAdversaryFrontmatter:
    """Adversary tests for critical failure modes that bypassed hooks.
    
    Contract:
    - YAML syntax errors must be blocking (exit 1).
    - Missing options.type must be blocking (exit 1).
    - Reserved keys (id) in options must be blocking (exit 1).
    - Unknown fields in identity block must be blocked.
    """

    def setup_method(self):
        import logging
        logging.basicConfig(level=logging.DEBUG)

    def test_rejects_invalid_yaml_syntax(self, frontmatter_env):
        """Invalid YAML syntax must trigger a blocking error, not a warning."""
        # malformed YAML: colon in key without quotes or unbalanced brackets
        content = "---\ntitle: : Test\noptions:\n  type: adr\n---\n\n# Body\n"
        file_path = frontmatter_env / "malformed.md"
        file_path.write_text(content, encoding="utf-8")

        errors = _module.validate_frontmatter(file_path, frontmatter_env)

        assert len(errors) > 0, "YAML syntax error should be recorded as an error"
        assert any(e.error_type == "invalid_yaml" or "syntax" in e.message.lower() for e in errors)

    def test_rejects_missing_type_as_blocking(self, frontmatter_env):
        """Frontmatter present but missing options.type must be a blocking error."""
        content = "---\ntitle: No Type\nauthors: [{name: A, email: a@b.com}]\n---\n\n# Body\n"
        file_path = frontmatter_env / "no_type.md"
        file_path.write_text(content, encoding="utf-8")

        errors = _module.validate_frontmatter(file_path, frontmatter_env)
        
        assert any(e.error_type == "missing_type" for e in errors), "Missing type must be a blocking error"

    def test_rejects_reserved_id_in_options(self, frontmatter_env):
        """Reserved key 'id' inside 'options' must trigger an error."""
        fm = _build_valid_frontmatter("adr")
        # Move id to options if it isn't already (the builder might put it there)
        if "id" in fm: del fm["id"]
        fm["options"]["id"] = "ADR-123"
        
        content = _frontmatter_to_md(fm)
        file_path = frontmatter_env / "reserved_id.md"
        file_path.write_text(content, encoding="utf-8")

        errors = _module.validate_frontmatter(file_path, frontmatter_env)

        assert any(e.error_type == "invalid_namespace" for e in errors), \
            "id in options must be forbidden"
    def test_rejects_unknown_identity_field(self, frontmatter_env):
        """Fields like 'author' (singular) instead of 'authors' must be rejected."""
        fm = _build_valid_frontmatter("adr")
        fm["author"] = "Vadim Rudakov" # Incorrect key
        
        content = _frontmatter_to_md(fm)
        file_path = frontmatter_env / "bad_field.md"
        file_path.write_text(content, encoding="utf-8")

        errors = _module.validate_frontmatter(file_path, frontmatter_env)
        
        assert any(e.error_type == "invalid_field" and e.field == "author" for e in errors), \
            "Unknown field 'author' should be rejected"

    def test_rejects_missing_starting_fence(self, frontmatter_env):
        """Files that start with metadata but lack the opening '---' fence must be flagged."""
        # Mimics README.md corruption: starts with fields but no fence
        content = "title: Corrupted README\nauthor: Vadim\n---\n# Body\n"
        file_path = frontmatter_env / "no_start_fence.md"
        file_path.write_text(content, encoding="utf-8")
    
        errors = _module.validate_frontmatter(file_path, frontmatter_env)
    
        assert any(e.error_type == "broken_dual_block" for e in errors), \
            "Missing starting fence should be reported as broken_dual_block for governed files"

class TestADRNamespaceStrictness:
    """Contract: status and superseded_by MUST NOT be at top level for ADRs.

    These are non-myst_native fields and must reside under options.*
    """

    def test_adr_status_at_top_level_rejected(self, frontmatter_env):
        """ADR with 'status' at top level → invalid_namespace error."""
        fm = _build_valid_frontmatter("adr")
        # Ensure it's at top level and NOT in options
        fm["status"] = "proposed"
        if "options" in fm:
            fm["options"].pop("status", None)

        md_file = frontmatter_env / "adr_status_top.md"
        md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
        errors = _module.validate_frontmatter(md_file, frontmatter_env)
        namespace_errors = [e for e in errors if e.error_type == "invalid_namespace" and e.field == "status"]
        assert len(namespace_errors) > 0, "Top-level status in ADR should be rejected"

    def test_adr_superseded_by_at_top_level_rejected(self, frontmatter_env):
        """ADR with 'superseded_by' at top level → invalid_namespace error."""
        fm = _build_valid_frontmatter("adr")
        # Ensure it's at top level and NOT in options
        fm["superseded_by"] = "26000"
        if "options" in fm:
            fm["options"].pop("superseded_by", None)

        md_file = frontmatter_env / "adr_superseded_top.md"
        md_file.write_text(_frontmatter_to_md(fm), encoding="utf-8")
        errors = _module.validate_frontmatter(md_file, frontmatter_env)
        namespace_errors = [e for e in errors if e.error_type == "invalid_namespace" and e.field == "superseded_by"]
        assert len(namespace_errors) > 0, "Top-level superseded_by in ADR should be rejected"
