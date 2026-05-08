import pytest
from pathlib import Path
from tools.scripts import adr_utils

class TestStatusExtraction:
    """Tests for ADR status extraction logic.

    Contract:
    - extract_body_status: Extracts status from ## Status section.
    - extract_status: Prefers YAML frontmatter, falls back to ## Status section.
    - Both should normalize result to lowercase.
    """

    def test_extract_body_status(self):
        """Should extract status from ## Status section."""
        content = "## Status\n\naccepted"
        assert adr_utils.extract_body_status(content) == "accepted"

        content = "## Status\n\nPROPOSED"
        assert adr_utils.extract_body_status(content) == "proposed"

        content = "## Some other section\n\naccepted"
        assert adr_utils.extract_body_status(content) is None

    def test_extract_status_from_frontmatter(self, tmp_path, monkeypatch):
        """Should prefer YAML frontmatter for status extraction."""
        def mock_parse(content):
            if "---" in content:
                return {"status": "accepted"}
            return None
        monkeypatch.setattr("tools.scripts.check_frontmatter.parse_frontmatter", mock_parse)

        content = "---\nstatus: accepted\n---\n# ADR-1: Test"
        assert adr_utils.extract_status(content) == "accepted"

    def test_extract_status_from_body(self, tmp_path, monkeypatch):
        """Should fall back to body status if frontmatter is absent."""
        monkeypatch.setattr("tools.scripts.check_frontmatter.parse_frontmatter", lambda c: None)

        content = "# ADR-1: Test\n## Status\n\nproposed"
        assert adr_utils.extract_status(content) == "proposed"


class TestAdrFileDiscovery:
    """Tests for ADR file discovery and parsing.

    Contract:
    - get_adr_files: Finds all adr_*.md files, excludes templates, and returns sorted AdrFile objects.
    - parse_adr_file: Validates ADR header (# ADR-N: Title) and returns a populated AdrFile object.
    """

    def test_get_adr_files(self, tmp_path, monkeypatch):
        """Should discover all valid ADR files and exclude templates."""
        monkeypatch.setattr(adr_utils, "ADR_DIR", tmp_path)
        monkeypatch.setattr(adr_utils, "EXCLUDED_FILES", {"adr_template.md"})

        # Create test ADR files
        adr1 = tmp_path / "adr_00001.md"
        adr1.write_text("# ADR-1: First ADR\n## Status\n\nproposed", encoding="utf-8")

        adr2 = tmp_path / "adr_00002.md"
        adr2.write_text("# ADR-2: Second ADR\n## Status\n\naccepted", encoding="utf-8")

        template = tmp_path / "adr_template.md"
        template.write_text("# ADR-0: Template\n## Status\n\nproposed", encoding="utf-8")

        monkeypatch.setattr("tools.scripts.check_frontmatter.parse_frontmatter", lambda c: {"title": "Test"})

        files = adr_utils.get_adr_files()

        assert len(files) == 2
        assert files[0].number == 1
        assert files[0].title == "First ADR"
        assert files[1].number == 2
        assert files[1].title == "Second ADR"


class TestIndexParsing:
    """Tests for the ADR index parser.

    Contract:
    - parse_index: Extracts ADR numbers, titles, and links from the glossary block.
    - Correctly assigns the current active section (Proposed, Accepted, etc.) to each entry.
    """

    def test_parse_index(self, tmp_path, monkeypatch):
        """Should parse a complete ADR index with multiple sections."""
        index_file = tmp_path / "adr_index.md"
        index_file.write_text(
            "# ADR Index\n\n## **Proposed**\n\n:::{glossary}\n"
            "ADR-1\n: [First ADR](/architecture/adr/adr_00001.md)\n\n"
            "ADR-2\n: [Second ADR](/architecture/adr/adr_00002.md)\n"
            ":::\n\n## **Accepted**\n\n:::{glossary}\n"
            "ADR-3\n: [Third ADR](/architecture/adr/adr_00003.md)\n"
            ":::",
            encoding="utf-8"
        )
        monkeypatch.setattr(adr_utils, "INDEX_PATH", index_file)
        monkeypatch.setattr(adr_utils, "SECTION_HEADER_PATTERN", adr_utils.SECTION_HEADER_PATTERN)

        entries = adr_utils.parse_index()

        assert len(entries) == 3
        assert entries[0].number == 1
        assert entries[0].title == "First ADR"
        assert entries[0].section == "Proposed"

        assert entries[2].number == 3
        assert entries[2].title == "Third ADR"
        assert entries[2].section == "Accepted"


class TestStagedAdrDiscovery:
    """Tests for git-staged ADR discovery.

    Contract:
    - get_staged_adr_files: Detects staged ADR files via git, resolve absolute paths, and parses them.
    - Only returns valid AdrFile objects.
    """

    def test_get_staged_adr_files(self, tmp_path, monkeypatch):
        """Should detect and parse staged ADR files correctly."""
        vadocs_dir = tmp_path / ".vadocs"
        vadocs_dir.mkdir()
        (vadocs_dir / "conf.json").write_text('{"field_registry": {}}', encoding="utf-8")

        (tmp_path / "pyproject.toml").write_text(
            '[tool.vadocs]\nconfig_dir = ".vadocs"',
            encoding="utf-8"
        )

        adr_dir = tmp_path / "architecture" / "adr"
        adr_dir.mkdir(parents=True)

        adr1_path = adr_dir / "adr_00001.md"
        adr1_path.write_text("# ADR-1: Staged 1\n## Status\n\nproposed", encoding="utf-8")

        adr2_path = adr_dir / "adr_00002.md"
        adr2_path.write_text("# ADR-2: Staged 2\n## Status\n\naccepted", encoding="utf-8")

        def mock_run(args, **kwargs):
            import subprocess
            cmd = " ".join(args) if isinstance(args, list) else str(args)

            if "git diff --cached --name-only" in cmd:
                class MockResult:
                    def __init__(self, stdout):
                        self.stdout = stdout
                return MockResult("architecture/adr/adr_00001.md\narchitecture/adr/adr_00002.md\nother/file.txt")

            if "git rev-parse --show-toplevel" in cmd:
                class MockRootResult:
                    def __init__(self, stdout):
                        self.stdout = stdout.strip()
                return MockRootResult(str(tmp_path))

            return subprocess.run(args, **kwargs)

        monkeypatch.setattr("subprocess.run", mock_run)
        monkeypatch.setattr(adr_utils, "ADR_DIR", adr_dir)
        monkeypatch.setattr(adr_utils, "ROOT", tmp_path)
        monkeypatch.setattr("tools.scripts.check_frontmatter.parse_frontmatter", lambda c: {"title": "Test"})

        files = adr_utils.get_staged_adr_files()

        assert len(files) == 2
        assert isinstance(files[0], adr_utils.AdrFile)
        assert files[0].number == 1
        assert files[1].number == 2
