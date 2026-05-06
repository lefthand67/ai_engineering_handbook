import subprocess
import sys
import runpy
from pathlib import Path
from unittest.mock import ANY, MagicMock, patch

import pytest

from tools.scripts.check_link_format import (
    FileFinder,
    LinkExtractor,
    LinkFormatCLI,
    LinkFormatValidator,
    Reporter,
)
from tools.scripts.paths import (
    VALIDATION_EXCLUDE_DIRS,
    BROKEN_LINKS_EXCLUDE_FILES,
    BROKEN_LINKS_EXCLUDE_LINK_STRINGS,
)


@pytest.fixture(autouse=True)
def mock_paths_module():
    """Patch the import of paths module exclusions."""
    with patch.dict(
        sys.modules,
        {
            "tools.scripts.paths": MagicMock(
                VALIDATION_EXCLUDE_DIRS=VALIDATION_EXCLUDE_DIRS,
                BROKEN_LINKS_EXCLUDE_FILES=BROKEN_LINKS_EXCLUDE_FILES,
                BROKEN_LINKS_EXCLUDE_LINK_STRINGS=BROKEN_LINKS_EXCLUDE_LINK_STRINGS,
            )
        },
    ):
        yield


# ======================
# Unit Tests
# ======================


class TestLinkExtractor:
    @pytest.mark.parametrize(
        "content,expected_links",
        [
            ("[text](link.md)", [("link.md", 1)]),
            ("[a](x.md) and [b](y.ipynb)", [("x.md", 1), ("y.ipynb", 1)]),
            ("no links here", []),
            ("![image](img.png)", [("img.png", 1)]),
            # MyST include directives
            (
                "```{include} /architecture/adr_index.md\n:class: dropdown\n```",
                [("/architecture/adr_index.md", 1)],
            ),
            ("```{include} ../adr_index.md\n```", [("../adr_index.md", 1)]),
        ],
    )
    def test_extract_links(self, tmp_path, content, expected_links):
        file = tmp_path / "test.md"
        file.write_text(content, encoding="utf-8")
        extractor = LinkExtractor(verbose=False)
        links = extractor.extract(file)
        assert links == expected_links

    def test_extract_handles_decode_error(self, capsys):
        extractor = LinkExtractor(verbose=False)
        binary_file = Path(__file__).parent / "binary_file.bin"
        binary_file.write_bytes(b"\xff\xfe")
        try:
            links = extractor.extract(binary_file)
            assert links == []
            captured = capsys.readouterr()
            assert "Cannot decode file" in captured.err
        finally:
            binary_file.unlink(missing_ok=True)


class TestLinkFormatValidator:
    @pytest.fixture
    def validator(self, tmp_path):
        return LinkFormatValidator(
            root_dir=tmp_path,
            verbose=False,
            exclude_link_strings=list(BROKEN_LINKS_EXCLUDE_LINK_STRINGS),
        )

    def test_is_absolute_url(self, validator):
        assert validator.is_absolute_url("https://example.com") is True
        assert validator.is_absolute_url("http://local.dev") is True
        assert validator.is_absolute_url("/relative/path") is False
        assert validator.is_absolute_url("relative.md") is False

    @pytest.mark.parametrize(
        "link,expected",
        [
            ("file.md#section", "file.md"),
            ("clean.md", "clean.md"),
            ("", ""),
        ],
    )
    def test_get_path_from_link(self, validator, link, expected):
        assert validator.get_path_from_link(link) == expected

    def test_validate_md_link_with_ipynb_pair_error(self, validator, tmp_path):
        """Link to .md when .ipynb pair exists should error."""
        # Create both .md and .ipynb files
        md_file = tmp_path / "guide.md"
        ipynb_file = tmp_path / "guide.ipynb"
        md_file.touch()
        ipynb_file.touch()

        source = tmp_path / "source.md"
        error = validator.validate_link_format("guide.md", source, 10)

        assert error is not None
        assert "LINK FORMAT ERROR" in error
        assert "guide.md" in error
        assert "guide.ipynb" in error

    def test_validate_md_link_without_ipynb_pair_ok(self, validator, tmp_path):
        """Link to .md without .ipynb pair should be OK."""
        md_file = tmp_path / "standalone.md"
        md_file.touch()
        # No .ipynb file created

        source = tmp_path / "source.md"
        error = validator.validate_link_format("standalone.md", source, 5)

        assert error is None

    def test_validate_ipynb_link_ok(self, validator, tmp_path):
        """Link to .ipynb should always be OK (correct format)."""
        ipynb_file = tmp_path / "guide.ipynb"
        ipynb_file.touch()

        source = tmp_path / "source.md"
        error = validator.validate_link_format("guide.ipynb", source, 5)

        assert error is None

    def test_validate_external_url_skipped(self, validator, tmp_path):
        source = tmp_path / "a.md"
        error = validator.validate_link_format("https://example.com", source, 1)
        assert error is None

    def test_validate_internal_fragment_skipped(self, validator, tmp_path):
        source = tmp_path / "a.md"
        error = validator.validate_link_format("#section", source, 1)
        assert error is None

    def test_validate_excluded_link_string(self, validator, tmp_path):
        source = tmp_path / "a.md"
        excluded_link = next(iter(BROKEN_LINKS_EXCLUDE_LINK_STRINGS))
        error = validator.validate_link_format(excluded_link, source, 1)
        assert error is None

    def test_validate_non_md_link_ok(self, validator, tmp_path):
        """Non-.md links should pass (not our concern)."""
        source = tmp_path / "source.md"
        error = validator.validate_link_format("image.png", source, 5)
        assert error is None

    def test_validate_md_link_with_fragment_and_ipynb_pair(self, validator, tmp_path):
        """Link to .md#section when .ipynb pair exists should error."""
        md_file = tmp_path / "guide.md"
        ipynb_file = tmp_path / "guide.ipynb"
        md_file.touch()
        ipynb_file.touch()

        source = tmp_path / "source.md"
        error = validator.validate_link_format("guide.md#section", source, 10)

        assert error is not None
        assert "LINK FORMAT ERROR" in error

    def test_validate_verbose_output(self, tmp_path, capsys):
        """Test verbose output for various link types."""
        validator = LinkFormatValidator(
            root_dir=tmp_path,
            verbose=True,
            exclude_link_strings=list(BROKEN_LINKS_EXCLUDE_LINK_STRINGS),
        )
        source = tmp_path / "source.md"

        # External URL
        validator.validate_link_format("https://example.com", source, 1)
        captured = capsys.readouterr()
        assert "SKIP External URL" in captured.out

        # Non-.md link
        validator.validate_link_format("image.png", source, 1)
        captured = capsys.readouterr()
        assert "OK (not .md)" in captured.out

        # .md link without pair
        (tmp_path / "standalone.md").touch()
        validator.validate_link_format("standalone.md", source, 1)
        captured = capsys.readouterr()
        assert "OK (no .ipynb pair)" in captured.out


class TestFileFinder:
    def test_find_respects_exclude_dirs(self, tmp_path):
        root = tmp_path / "repo"
        root.mkdir()
        (root / "docs").mkdir()
        (root / "docs" / "good.md").touch()
        (root / ".venv").mkdir()
        (root / ".venv" / "bad.md").touch()

        finder = FileFinder(
            exclude_dirs=list(VALIDATION_EXCLUDE_DIRS),
            exclude_files=list(BROKEN_LINKS_EXCLUDE_FILES),
            verbose=False,
        )
        files = finder.find(root, "*.md")

        assert len(files) == 1
        assert files[0].name == "good.md"

    def test_find_excludes_ipynb_checkpoints(self, tmp_path):
        (tmp_path / "normal.md").touch()
        cp_dir = tmp_path / ".ipynb_checkpoints"
        cp_dir.mkdir()
        (cp_dir / "auto.md").touch()

        finder = FileFinder(exclude_dirs=[], exclude_files=[], verbose=False)
        files = finder.find(tmp_path, "*.md")

        assert len(files) == 1
        assert ".ipynb_checkpoints" not in str(files[0])


class TestReporter:
    def test_report_errors_exits_1(self, tmp_path, capsys):
        report_file = tmp_path / "report.txt"
        report_file.write_text("LINK FORMAT ERROR: ...\n", encoding="utf-8")
        with pytest.raises(SystemExit) as exc_info:
            Reporter.report(report_file, errors_found=True)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "❌" in captured.out

    def test_report_no_errors_exits_0(self, tmp_path, capsys):
        report_file = tmp_path / "empty.txt"
        report_file.write_text("", encoding="utf-8")
        with pytest.raises(SystemExit) as exc_info:
            Reporter.report(report_file, errors_found=False)
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "✅" in captured.out


# ======================
# Integration Tests
# ======================


class TestLinkFormatCLI:
    @pytest.fixture
    def cli(self):
        return LinkFormatCLI()

    @patch("tools.scripts.check_link_format.subprocess.run")
    def test_get_git_root_dir_success(self, mock_run, cli):
        mock_run.return_value = MagicMock(stdout="/fake/repo\n")
        root = cli.get_git_root_dir()
        assert root == Path("/fake/repo").resolve()

    @patch("tools.scripts.check_link_format.subprocess.run")
    def test_get_git_root_dir_failure(self, mock_run, cli):
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        root = cli.get_git_root_dir()
        assert root is None

    def test_run_detects_format_error(self, tmp_path, capsys):
        """CLI detects .md link that should be .ipynb."""
        # Create paired files
        (tmp_path / "target.md").touch()
        (tmp_path / "target.ipynb").touch()

        # Source file links to .md (wrong format)
        source = tmp_path / "source.md"
        source.write_text("[link](target.md)", encoding="utf-8")

        cli = LinkFormatCLI()
        with pytest.raises(SystemExit) as exc_info:
            cli.run(["--paths", str(tmp_path), "--pattern", "*.md"])

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "LINK FORMAT ERROR" in captured.out

    def test_run_passes_correct_format(self, tmp_path, capsys):
        """CLI passes when .md links to .ipynb correctly."""
        (tmp_path / "target.ipynb").touch()

        source = tmp_path / "source.md"
        source.write_text("[link](target.ipynb)", encoding="utf-8")

        cli = LinkFormatCLI()
        with pytest.raises(SystemExit) as exc_info:
            cli.run(["--paths", str(tmp_path), "--pattern", "*.md"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "✅" in captured.out

    def test_run_passes_md_without_pair(self, tmp_path, capsys):
        """CLI passes when .md link has no .ipynb pair."""
        (tmp_path / "standalone.md").touch()

        source = tmp_path / "source.md"
        source.write_text("[link](standalone.md)", encoding="utf-8")

        cli = LinkFormatCLI()
        with pytest.raises(SystemExit) as exc_info:
            cli.run(["--paths", str(tmp_path), "--pattern", "*.md"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "✅" in captured.out

    def test_run_no_files_found(self, tmp_path, capsys):
        cli = LinkFormatCLI()
        with pytest.raises(SystemExit) as exc_info:
            cli.run(["--paths", str(tmp_path), "--pattern", "*.xyz"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "No files matching '*.xyz' found!" in captured.out

    def test_explicit_file_in_excluded_dir_is_skipped(self, tmp_path, capsys, monkeypatch):
        """Explicitly passing a file from an excluded directory should be skipped.
        
        This verifies that the 'leak' where files in external research repositories
        are processed when passed as explicit arguments is fixed.
        """
        # Mock exclusion
        excl_dir_name = "excluded_dir"
        monkeypatch.setattr("tools.scripts.check_link_format.is_excluded", lambda p: excl_dir_name in str(p))


        excl_dir = tmp_path / excl_dir_name
        excl_dir.mkdir()
        
        # Create a file with a format error
        target = excl_dir / "target.md"
        target.touch()
        (excl_dir / "target.ipynb").touch()
        
        source = excl_dir / "source.md"
        source.write_text("[link](target.md)", encoding="utf-8")

        cli = LinkFormatCLI()
        # Run on the specific source file
        with pytest.raises(SystemExit) as exc_info:
            cli.run(["--paths", str(source)])

        # It should be skipped, thus no errors found
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "✅" in captured.out or "No files matching" in captured.out



    def test_run_with_verbose(self, tmp_path, capsys):
        (tmp_path / "target.ipynb").touch()
        source = tmp_path / "source.md"
        source.write_text("[link](target.ipynb)", encoding="utf-8")

        cli = LinkFormatCLI()
        with pytest.raises(SystemExit) as exc_info:
            cli.run(["--paths", str(tmp_path), "--verbose"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Checking file:" in captured.out


# ======================
# Defensive Tests
# ======================


def test_nonexistent_input_path(tmp_path, capsys):
    cli = LinkFormatCLI()
    bad_path = tmp_path / "does_not_exist"
    with pytest.raises(SystemExit) as exc_info:
        cli.run(["--paths", str(bad_path)])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "Warning: Path does not exist" in captured.err


def test_run_no_git_root_warning(tmp_path, capsys):
    cli = LinkFormatCLI()
    with patch.object(LinkFormatCLI, "get_git_root_dir", return_value=None):
        with pytest.raises(SystemExit):
            cli.run(["--paths", str(tmp_path), "--verbose"])
    captured = capsys.readouterr()
    assert "Warning: Not in a Git repository" in captured.out


# ======================
# Main Entry Point Test
# ======================


def test_main_entry_point():
    with patch("sys.argv", ["check_link_format.py", "--help"]), pytest.raises(
        SystemExit
    ):
        runpy.run_path("tools/scripts/check_link_format.py", run_name="__main__")

    with patch("tools.scripts.check_link_format.LinkFormatCLI.run") as mock_run:
        from tools.scripts.check_link_format import main

        main()
        mock_run.assert_called_once_with()


# ======================
# LinkFixer Tests
# ======================


class TestLinkFixer:
    def test_fix_links_in_file(self, tmp_path):
        """Test that LinkFixer correctly replaces links in a file."""
        from tools.scripts.check_link_format import LinkFixer

        # Create test file with wrong link format
        source = tmp_path / "source.md"
        source.write_text("[Guide](target.md)\n[Other](other.md)", encoding="utf-8")

        # Create paired .ipynb files
        (tmp_path / "target.ipynb").touch()
        (tmp_path / "other.ipynb").touch()

        issues = [
            {"link": "target.md", "suggested": "target.ipynb", "line": 1},
            {"link": "other.md", "suggested": "other.ipynb", "line": 2},
        ]

        fixer = LinkFixer(verbose=False)
        count = fixer.fix_links_in_file(source, issues)

        assert count == 2
        content = source.read_text()
        assert "target.ipynb" in content
        assert "other.ipynb" in content
        assert "target.md" not in content
        assert "other.md" not in content

    def test_fix_links_preserves_other_content(self, tmp_path):
        """Test that fixing links doesn't affect other content."""
        from tools.scripts.check_link_format import LinkFixer

        source = tmp_path / "source.md"
        original_content = "# Title\n\nSome text [Guide](target.md) more text.\n\n## Section"
        source.write_text(original_content, encoding="utf-8")
        (tmp_path / "target.ipynb").touch()

        issues = [{"link": "target.md", "suggested": "target.ipynb", "line": 3}]

        fixer = LinkFixer(verbose=False)
        fixer.fix_links_in_file(source, issues)

        content = source.read_text()
        assert "# Title" in content
        assert "Some text [Guide](target.ipynb) more text." in content
        assert "## Section" in content


class TestLinkFormatCLIFixModes:
    def test_fix_all_mode(self, tmp_path, capsys):
        """Test --fix-all mode fixes all errors without prompts."""
        # Create paired files
        (tmp_path / "target.md").touch()
        (tmp_path / "target.ipynb").touch()

        # Source file links to .md (wrong format)
        source = tmp_path / "source.md"
        source.write_text("[link](target.md)", encoding="utf-8")

        cli = LinkFormatCLI()
        with pytest.raises(SystemExit) as exc_info:
            cli.run(["--paths", str(tmp_path), "--pattern", "*.md", "--fix-all"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Fixed" in captured.out

        # Verify the file was actually fixed
        content = source.read_text()
        assert "target.ipynb" in content
        assert "target.md" not in content

    def test_fix_all_mode_multiple_files(self, tmp_path, capsys):
        """Test --fix-all mode fixes multiple files."""
        # Create paired files
        (tmp_path / "a.ipynb").touch()
        (tmp_path / "b.ipynb").touch()

        # Create source files with wrong links
        (tmp_path / "file1.md").write_text("[link](a.md)", encoding="utf-8")
        (tmp_path / "file2.md").write_text("[link](b.md)", encoding="utf-8")
        (tmp_path / "a.md").touch()
        (tmp_path / "b.md").touch()

        cli = LinkFormatCLI()
        with pytest.raises(SystemExit) as exc_info:
            cli.run(["--paths", str(tmp_path), "--fix-all"])

        assert exc_info.value.code == 0

        # Verify both files were fixed
        assert "a.ipynb" in (tmp_path / "file1.md").read_text()
        assert "b.ipynb" in (tmp_path / "file2.md").read_text()

    def test_fix_all_no_issues(self, tmp_path, capsys):
        """Test --fix-all mode with no issues to fix."""
        (tmp_path / "target.ipynb").touch()
        source = tmp_path / "source.md"
        source.write_text("[link](target.ipynb)", encoding="utf-8")

        cli = LinkFormatCLI()
        with pytest.raises(SystemExit) as exc_info:
            cli.run(["--paths", str(tmp_path), "--fix-all"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "All link formats are correct" in captured.out


class TestReporterFixes:
    def test_report_fixes_all_fixed(self, capsys):
        """Test report when all issues are fixed."""
        from tools.scripts.check_link_format import Reporter

        with pytest.raises(SystemExit) as exc_info:
            Reporter.report_fixes(5, 5)
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Fixed all 5" in captured.out

    def test_report_fixes_partial(self, capsys):
        """Test report when some issues are fixed."""
        from tools.scripts.check_link_format import Reporter

        with pytest.raises(SystemExit) as exc_info:
            Reporter.report_fixes(3, 5, 2)
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Fixed 3/5" in captured.out
        assert "Skipped: 2" in captured.out

    def test_report_fixes_none_fixed(self, capsys):
        """Test report when no issues are fixed."""
        from tools.scripts.check_link_format import Reporter

        with pytest.raises(SystemExit) as exc_info:
            Reporter.report_fixes(0, 5)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "No fixes applied" in captured.out
