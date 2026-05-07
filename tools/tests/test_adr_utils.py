import pytest
from pathlib import Path
from tools.scripts import adr_utils

def test_extract_body_status():
    content = "## Status\n\naccepted"
    assert adr_utils.extract_body_status(content) == "accepted"
    
    content = "## Status\n\nPROPOSED"
    assert adr_utils.extract_body_status(content) == "proposed"
    
    content = "## Some other section\n\naccepted"
    assert adr_utils.extract_body_status(content) is None

def test_extract_status_from_frontmatter(tmp_path, monkeypatch):
    # Mock check_frontmatter.parse_frontmatter
    def mock_parse(content):
        if "---" in content:
            return {"status": "accepted"}
        return None
    monkeypatch.setattr("tools.scripts.check_frontmatter.parse_frontmatter", mock_parse)
    
    content = "---\nstatus: accepted\n---\n# ADR-1: Test"
    assert adr_utils.extract_status(content) == "accepted"

def test_extract_status_from_body(tmp_path, monkeypatch):
    # Mock check_frontmatter.parse_frontmatter to return None
    monkeypatch.setattr("tools.scripts.check_frontmatter.parse_frontmatter", lambda c: None)
    
    content = "# ADR-1: Test\n## Status\n\nproposed"
    assert adr_utils.extract_status(content) == "proposed"

def test_get_adr_files(tmp_path, monkeypatch):
    # Mock ADR_DIR and EXCLUDED_FILES
    monkeypatch.setattr(adr_utils, "ADR_DIR", tmp_path)
    monkeypatch.setattr(adr_utils, "EXCLUDED_FILES", {"adr_template.md"})
    
    # Create test ADR files
    adr1 = tmp_path / "adr_00001.md"
    adr1.write_text("# ADR-1: First ADR\n## Status\n\nproposed", encoding="utf-8")
    
    adr2 = tmp_path / "adr_00002.md"
    adr2.write_text("# ADR-2: Second ADR\n## Status\n\naccepted", encoding="utf-8")
    
    template = tmp_path / "adr_template.md"
    template.write_text("# ADR-0: Template\n## Status\n\nproposed", encoding="utf-8")
    
    # Mock check_frontmatter.parse_frontmatter
    monkeypatch.setattr("tools.scripts.check_frontmatter.parse_frontmatter", lambda c: {"title": "Test"})

    files = adr_utils.get_adr_files()
    
    assert len(files) == 2
    assert files[0].number == 1
    assert files[0].title == "First ADR"
    assert files[1].number == 2
    assert files[1].title == "Second ADR"

def test_parse_index(tmp_path, monkeypatch):
    # Mock INDEX_PATH
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

def test_get_staged_adr_files(tmp_path, monkeypatch):
    # 1. Set up a fake repo structure in tmp_path
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

    # 2. Mock git commands
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

    # 3. Mock ADR_DIR and ROOT to use tmp_path
    monkeypatch.setattr(adr_utils, "ADR_DIR", adr_dir)
    monkeypatch.setattr(adr_utils, "ROOT", tmp_path)

    # Mock check_frontmatter.parse_frontmatter to avoid complex setup
    monkeypatch.setattr("tools.scripts.check_frontmatter.parse_frontmatter", lambda c: {"title": "Test"})

    files = adr_utils.get_staged_adr_files()

    assert len(files) == 2
    assert isinstance(files[0], adr_utils.AdrFile)
    assert files[0].number == 1
    assert files[1].number == 2
