import pytest
from pathlib import Path
from unittest.mock import patch
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

    def test_validate_sync_empty(self):
        """Contract: validate_sync should handle empty inputs without error."""
        errors = check_adr_index.validate_sync([], [])
        assert errors == []

    def test_validate_sync_duplicate_numbers(self, tmp_path, monkeypatch):
        """Contract: Multiple ADR files with the same number must trigger a 'duplicate_number' error."""
        adr1 = tmp_path / "adr_00001_a.md"
        adr1.write_text("# ADR-1: Test A\n## Status\n\nproposed", encoding="utf-8")
        adr2 = tmp_path / "adr_00001_b.md"
        adr2.write_text("# ADR-1: Test B\n## Status\n\nproposed", encoding="utf-8")

        monkeypatch.setattr(check_adr_index, "ADR_DIR", tmp_path)

        adr_files = [
            adr_utils.AdrFile(path=adr1, number=1, title="Test A"),
            adr_utils.AdrFile(path=adr2, number=1, title="Test B"),
        ]
        index_entries = [adr_utils.IndexEntry(number=1, title="Test A", link="...", section=None)]

        errors = check_adr_index.validate_sync(adr_files, index_entries)
        assert any(e.error_type == "duplicate_number" for e in errors)

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

    def test_validate_sync_title_mismatch_no_fm(self, tmp_path, monkeypatch):
        """Contract: ADR with no frontmatter should not trigger a title mismatch error."""
        adr_file = tmp_path / "adr_00001.md"
        adr_file.write_text("# ADR-1: Test\n## Status\n\nproposed", encoding="utf-8")

        monkeypatch.setattr(check_adr_index, "ADR_DIR", tmp_path)

        adr_files = [adr_utils.AdrFile(path=adr_file, number=1, title="Test", frontmatter=None)]
        index_entries = [adr_utils.IndexEntry(number=1, title="Test", link="/architecture/adr/adr_00001.md", section=None)]

        errors = check_adr_index.validate_sync(adr_files, index_entries)
        assert not any(e.error_type == "title_mismatch" for e in errors)

    def test_validate_sync_wrong_order(self, tmp_path, monkeypatch):
        """Contract: Index entries in a section must be in numerical order."""
        monkeypatch.setattr(check_adr_index, "PRIMARY_TAG_SECTIONING", False)

        adr1 = adr_utils.AdrFile(path=Path("adr_1.md"), number=1, title="T1")
        adr2 = adr_utils.AdrFile(path=Path("adr_2.md"), number=2, title="T2")
        adr_files = [adr1, adr2]

        # Out of order entries in the same section
        index_entries = [
            adr_utils.IndexEntry(number=2, title="T2", link="...", section="Proposed"),
            adr_utils.IndexEntry(number=1, title="T1", link="...", section="Proposed"),
        ]

        errors = check_adr_index.validate_sync(adr_files, index_entries)
        assert any(e.error_type == "wrong_order" for e in errors)

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

    def test_fix_index_advanced(self, tmp_path, monkeypatch):
        """Contract: fix_index must handle tag sectioning, orphans, and metadata annotations."""
        adr_dir = tmp_path / "adr"
        adr_dir.mkdir()
        index_file = tmp_path / "adr_index.md"

        # ADR 1: Basic
        adr1 = adr_dir / "adr_00001.md"
        adr1.write_text("# ADR-1: Basic\n## Status\n\nproposed", encoding="utf-8")
        # ADR 2: With tags, superseded, and description
        adr2 = adr_dir / "adr_00002.md"
        adr2.write_text("# ADR-2: Advanced\n## Status\n\nproposed", encoding="utf-8")

        monkeypatch.setattr(check_adr_index, "ADR_DIR", adr_dir)
        monkeypatch.setattr(check_adr_index, "INDEX_PATH", index_file)
        monkeypatch.setattr(check_adr_index, "SECTION_ORDER", ["Proposed", "Accepted"])
        monkeypatch.setattr(check_adr_index, "STATUS_SECTIONS", {"proposed": "Proposed", "accepted": "Accepted"})
        monkeypatch.setattr(check_adr_index, "DEFAULT_STATUS", "proposed")
        monkeypatch.setattr(check_adr_index, "PRIMARY_TAG_SECTIONING", True)

        def mock_get_files():
            return [
                adr_utils.AdrFile(path=adr1, number=1, title="Basic", status="proposed", frontmatter=None),
                adr_utils.AdrFile(
                    path=adr2,
                    number=2,
                    title="Advanced",
                    status="proposed",
                    frontmatter={"tags": ["core"], "superseded_by": "ADR-3", "description": "Advanced desc"}
                ),
            ]

        monkeypatch.setattr(adr_utils, "get_adr_files", mock_get_files)
        # Mock existing index with an orphan (ADR 99)
        monkeypatch.setattr(adr_utils, "parse_index", lambda: [
            adr_utils.IndexEntry(number=99, title="Orphan", link="...", section="Proposed")
        ])

        changes = check_adr_index.fix_index()

        content = index_file.read_text()
        # Verify tag sectioning
        assert "### core" in content
        # Verify metadata
        assert "superseded by {term}`ADR-3`" in content
        assert "Advanced desc" in content
        # Verify orphan removal in changes
        assert any("Removed orphan entry ADR 99" in c for c in changes)
        # Verify new additions in changes
        assert any("Added ADR 1" in c for c in changes)
        assert any("Added ADR 2" in c for c in changes)

    def test_fix_index_duplicate_locations(self, tmp_path, monkeypatch):
        """Verify that fix_index warns when an ADR appears in multiple locations."""
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

        def mock_get_files():
            # Return two different AdrFile objects with the same number to trigger the warning
            return [
                adr_utils.AdrFile(path=adr1, number=1, title="First", status="proposed"),
                adr_utils.AdrFile(path=adr1, number=1, title="First", status="accepted"),
            ]

        monkeypatch.setattr(adr_utils, "get_adr_files", mock_get_files)
        monkeypatch.setattr(adr_utils, "parse_index", lambda: [])

        # We just check it doesn't crash; the warning goes to logger
        check_adr_index.fix_index()

    def test_get_all_md_files(self, tmp_path, monkeypatch):
        """Verify that markdown files are discovered and excluded directories are ignored."""
        # Create a structure:
        # root/doc1.md
        # root/excluded_dir/doc2.md
        # root/other_dir/doc3.md
        doc1 = tmp_path / "doc1.md"
        doc1.write_text("content", encoding="utf-8")
        
        excl_dir = tmp_path / "excluded_dir"
        excl_dir.mkdir()
        doc2 = excl_dir / "doc2.md"
        doc2.write_text("content", encoding="utf-8")
        
        other_dir = tmp_path / "other_dir"
        other_dir.mkdir()
        doc3 = other_dir / "doc3.md"
        doc3.write_text("content", encoding="utf-8")

        # Mock VALIDATION_EXCLUDE_DIRS
        monkeypatch.setattr("tools.scripts.paths.VALIDATION_EXCLUDE_DIRS", ["excluded_dir"])

        files = check_adr_index.get_all_md_files(tmp_path)
        
        assert doc1 in files
        assert doc3 in files
        assert doc2 not in files
        assert len(files) == 2

    def test_main_cli(self, tmp_path, monkeypatch):
        """Verify all CLI paths and return codes."""
        adr_dir = tmp_path / "adr"
        adr_dir.mkdir()
        index_file = tmp_path / "adr_index.md"
        index_file.write_text("# ADR Index\n", encoding="utf-8")

        monkeypatch.setattr(check_adr_index, "ADR_DIR", adr_dir)
        monkeypatch.setattr(check_adr_index, "INDEX_PATH", index_file)

        # 1. Standard validation (Success)
        monkeypatch.setattr(adr_utils, "get_adr_files", lambda: [])
        monkeypatch.setattr(adr_utils, "parse_index", lambda: [])
        assert check_adr_index.main([]) == 0

        # 2. Standard validation (Failure - ADR missing in index)
        def mock_get_files_failure():
            return [adr_utils.AdrFile(path=adr_dir / "adr_1.md", number=1, title="T1")]
        monkeypatch.setattr(adr_utils, "get_adr_files", mock_get_files_failure)
        assert check_adr_index.main([]) == 1

        # 3. --fix mode
        monkeypatch.setattr(adr_utils, "parse_index", lambda: [])
        assert check_adr_index.main(["--fix"]) == 0

        # 4. --check-terms mode (Success)
        monkeypatch.setattr(check_adr_index, "get_all_md_files", lambda x: [])
        assert check_adr_index.main(["--check-terms"]) == 0

        # 5. --check-terms mode (Failure)
        def mock_get_md_files(_):
            f = tmp_path / "doc.md"
            f.write_text("See {term}`ADR 1`", encoding="utf-8")
            return [f]
        monkeypatch.setattr(check_adr_index, "get_all_md_files", mock_get_md_files)
        assert check_adr_index.main(["--check-terms"]) == 1

        # 6. --fix-terms mode
        assert check_adr_index.main(["--fix-terms"]) == 0

        # 7. --verbose mode (just check it doesn't crash)
        monkeypatch.setattr(adr_utils, "get_adr_files", lambda: [])
        monkeypatch.setattr(check_adr_index, "get_all_md_files", lambda x: [])
        assert check_adr_index.main(["--verbose"]) == 0

    def test_main_index_missing(self, tmp_path, monkeypatch):
        """Verify that main returns 1 when index file is missing and ADRs exist."""
        adr_dir = tmp_path / "adr"
        adr_dir.mkdir()
        
        # No index file created here
        
        monkeypatch.setattr(check_adr_index, "ADR_DIR", adr_dir)
        monkeypatch.setattr(check_adr_index, "INDEX_PATH", tmp_path / "missing_index.md")
        
        def mock_get_files():
            return [adr_utils.AdrFile(path=adr_dir / "adr_1.md", number=1, title="T1")]
        monkeypatch.setattr(adr_utils, "get_adr_files", mock_get_files)
        
        # Mock parse_index to raise FileNotFoundError
        def mock_parse_index():
            raise FileNotFoundError("Index not found")
        monkeypatch.setattr(adr_utils, "parse_index", mock_parse_index)
        
        assert check_adr_index.main([]) == 1

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

    def test_file_operation_errors(self, tmp_path, monkeypatch):
        """Verify that the script handles file read/write errors gracefully."""
        test_file = tmp_path / "error.md"
        test_file.write_text("content", encoding="utf-8")

        # Mock read_text to raise OSError
        with patch("pathlib.Path.read_text", side_effect=OSError("Permission denied")):
            # should skip the file and return empty results
            refs = check_adr_index.find_broken_term_references([test_file])
            assert refs == []

            errors = check_adr_index.validate_term_references([test_file])
            assert errors == []

            modified = check_adr_index.fix_term_references([test_file])
            assert modified == []

        # Mock read_text to raise UnicodeDecodeError
        with patch("pathlib.Path.read_text", side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")):
            refs = check_adr_index.find_broken_term_references([test_file])
            assert refs == []

    def test_get_primary_tag(self):
        """Verify primary tag extraction for various formats."""
        # Case 1: List of tags
        adr1 = adr_utils.AdrFile(path=Path("1.md"), number=1, title="T1", frontmatter={"tags": ["tag1", "tag2"]})
        assert check_adr_index._get_primary_tag(adr1) == "tag1"

        # Case 2: String tag
        adr2 = adr_utils.AdrFile(path=Path("2.md"), number=2, title="T2", frontmatter={"tags": "tag1"})
        assert check_adr_index._get_primary_tag(adr2) == "tag1"

        # Case 3: Empty tags list
        adr3 = adr_utils.AdrFile(path=Path("3.md"), number=3, title="T3", frontmatter={"tags": []})
        assert check_adr_index._get_primary_tag(adr3) == "untagged"

        # Case 4: No frontmatter
        adr4 = adr_utils.AdrFile(path=Path("4.md"), number=4, title="T4", frontmatter=None)
        assert check_adr_index._get_primary_tag(adr4) == "untagged"

    def test_format_entry(self):
        """Verify formatting of index entries with various frontmatter options."""
        # Case 1: Basic entry
        adr1 = adr_utils.AdrFile(path=Path("adr_1.md"), number=1, title="Title 1", frontmatter=None)
        lines = check_adr_index._format_entry(adr1)
        assert "ADR-1" in lines[0]
        assert "[Title 1](/architecture/adr/adr_1.md)" in lines[1]

        # Case 2: Entry with superseded_by
        adr2 = adr_utils.AdrFile(path=Path("adr_2.md"), number=2, title="Title 2", frontmatter={"superseded_by": "ADR-3"})
        lines = check_adr_index._format_entry(adr2)
        assert "superseded by {term}`ADR-3`" in lines[1]

        # Case 3: Entry with description
        adr3 = adr_utils.AdrFile(path=Path("adr_3.md"), number=3, title="Title 3", frontmatter={"description": "Some desc"})
        lines = check_adr_index._format_entry(adr3)
        assert "Some desc" in "".join(lines)

    def test_check_staged_blind_spot(self, tmp_path, monkeypatch):

        """Verify the blind spot is CLOSED: invalid ADRs in unstaged files are now detected."""
        # Create an ADR file that is missing from the index
        adr_dir = tmp_path / "adr"
        adr_dir.mkdir()
        adr_file = adr_dir / "adr_00001.md"
        adr_file.write_text("# ADR-1: Test\n## Status\n\nproposed", encoding="utf-8")

        index_file = tmp_path / "adr_index.md"
        index_file.write_text("# ADR Index\n", encoding="utf-8")

        monkeypatch.setattr(check_adr_index, "ADR_DIR", adr_dir)
        monkeypatch.setattr(check_adr_index, "INDEX_PATH", index_file)

        from tools.scripts.check_adr_index import main
        exit_code = main([])

        # SHOULD now return 1 because the broken ADR in the unstaged file is detected.
        assert exit_code == 1, "Blind spot still exists: script passed despite broken ADR in unstaged file"
