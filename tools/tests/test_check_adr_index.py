import pytest
from pathlib import Path
from tools.scripts import adr_utils
from tools.scripts import check_adr_index

class TestAdrIndexSynchronizer:
    """
    Verifies the contract for ADR Index Synchronization.
    
    Contracts:
    - ADR files and index entries must have a 1:1 mapping.
    - Index entries must use the canonical link format: /architecture/adr/<filename>.
    - Index entries must be ordered numerically within their status sections.
    - MyST term references must use the configured separator (hyphen by default).
    - The index can be automatically regenerated from the current set of ADR files.
    """

    def test_validate_sync_missing_in_index(self, tmp_path, monkeypatch):
        """Contract: An ADR file without a corresponding index entry must trigger a 'missing_in_index' error."""
        adr_file = tmp_path / "adr_00001.md"
        adr_file.write_text("# ADR-1: Test\n## Status\n\nproposed", encoding="utf-8")
        
        monkeypatch.setattr(check_adr_index, "ADR_DIR", tmp_path)
        
        adr_files = [adr_utils.AdrFile(path=adr_file, number=1, title="Test")]
        index_entries = []
        
        errors = check_adr_index.validate_sync(adr_files, index_entries)
        assert any(e.error_type == "missing_in_index" for e in errors)

    def test_validate_sync_orphan_in_index(self, tmp_path, monkeypatch):
        """Contract: An index entry without a corresponding ADR file must trigger an 'orphan_in_index' error."""
        monkeypatch.setattr(check_adr_index, "ADR_DIR", tmp_path)
        
        adr_files = []
        index_entries = [adr_utils.IndexEntry(number=1, title="Test", link="...", section=None)]
        
        errors = check_adr_index.validate_sync(adr_files, index_entries)
        assert any(e.error_type == "orphan_in_index" for e in errors)

    def test_validate_sync_wrong_link(self, tmp_path, monkeypatch):
        """Contract: An index entry with a link deviating from /architecture/adr/<filename> must trigger a 'wrong_link' error."""
        adr_file = tmp_path / "adr_00001.md"
        adr_file.write_text("# ADR-1: Test\n## Status\n\nproposed", encoding="utf-8")
        
        monkeypatch.setattr(check_adr_index, "ADR_DIR", tmp_path)
        
        adr_files = [adr_utils.AdrFile(path=adr_file, number=1, title="Test")]
        index_entries = [adr_utils.IndexEntry(number=1, title="Test", link="/wrong/path", section=None)]
        
        errors = check_adr_index.validate_sync(adr_files, index_entries)
        assert any(e.error_type == "wrong_link" for e in errors)

    def test_fix_index(self, tmp_path, monkeypatch):
        """Contract: fix_index must generate a valid index file based on discovered ADR files."""
        adr_dir = tmp_path / "adr"
        adr_dir.mkdir()
        index_file = tmp_path / "adr_index.md"
        
        adr1 = adr_dir / "adr_00001.md"
        adr1.write_text("# ADR-1: First\n## Status\n\nproposed", encoding="utf-8")
        
        monkeypatch.setattr(check_adr_index, "ADR_DIR", adr_dir)
        monkeypatch.setattr(check_adr_index, "INDEX_PATH", index_file)
        monkeypatch.setattr(check_adr_index, "SECTION_ORDER", ["Proposed", "Accepted"])
        monkeypatch.setattr(check_adr_index, "STATUS_SECTIONS", {"proposed": "Proposed", "accepted": "Accepted"})
        monkeypatch.setattr(check_adr_index, "DEFAULT_STATUS", "proposed")
        monkeypatch.setattr(check_adr_index, "PRIMARY_TAG_SECTIONING", False)
        
        def mock_get_files():
            return [adr_utils.AdrFile(path=adr1, number=1, title="First", status="proposed")]
        
        monkeypatch.setattr(adr_utils, "get_adr_files", mock_get_files)
        monkeypatch.setattr(adr_utils, "parse_index", lambda: [])

        changes = check_adr_index.fix_index()
        
        assert len(changes) > 0
        assert index_file.exists()
        assert "ADR-1" in index_file.read_text()

    def test_term_reference_validation(self, tmp_path):
        """Contract: references using the wrong separator (e.g. space instead of hyphen) must be detected as broken."""
        test_file = tmp_path / "doc.md"
        # Use a known broken pattern (space)
        test_file.write_text(f"See {{term}}`ADR 26001` for details.", encoding="utf-8")
        
        files = [test_file]
        errors = check_adr_index.validate_term_references(files)
        
        assert len(errors) == 1
        assert errors[0].error_type == "broken_term_reference"

    def test_term_reference_fixing(self, tmp_path):
        """Contract: fix_term_references must replace broken references with the canonical hyphenated format."""
        test_file = tmp_path / "doc.md"
        test_file.write_text(f"See {{term}}`ADR 26001` for details.", encoding="utf-8")
        
        files = [test_file]
        modified = check_adr_index.fix_term_references(files)
        
        assert len(modified) == 1
        # Verify the result matches the canonical format (ADR-XXXXX)
        assert f"{{term}}`ADR-{adr_utils.TERM_SEPARATOR}26001`" not in test_file.read_text() # Correct logic check
        # Simple check for the hyphen
        assert "{term}`ADR-26001`" in test_file.read_text()
