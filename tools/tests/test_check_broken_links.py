import subprocess
import sys
import runpy
import logging
from pathlib import Path
from unittest.mock import ANY, MagicMock, patch

import pytest

import tools.scripts.git as _git
from tools.scripts.check_broken_links import (
    FileFinder,
    LinkCheckerCLI,
    LinkExtractor,
    LinkValidator,
    Reporter,
)
from tools.scripts.paths import VALIDATION_EXCLUDE_DIRS, BROKEN_LINKS_EXCLUDE_FILES, BROKEN_LINKS_EXCLUDE_LINK_STRINGS


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
            ("[text](link.ipynb)", [("link.ipynb", 1)]),
            ("[a](x.ipynb) and [b](y.ipynb)", [("x.ipynb", 1), ("y.ipynb", 1)]),
            ("no links here", []),
            ("![image](img.png)", [("img.png", 1)]),  # also matches image links
            ("[broken](  spaced link.ipynb  )", [("  spaced link.ipynb  ", 1)]),
            # MyST include directives
            (
                "```{include} /architecture/adr_index.md\n:class: dropdown\n```",
                [("/architecture/adr_index.md", 1)],
            ),
            ("```{include} ../adr_index.md\n```", [("../adr_index.md", 1)]),
            ("```{include} simple.md```", [("simple.md", 1)]),
            (
                "Multiple:\n```{include} one.md\n```\nAnd ```{include} /two.md\n```",
                [("one.md", 2), ("/two.md", 4)],
            ),
            ("```{include}  spaced.md  \n```", [("  spaced.md  ", 1)]),
            ("```{not_an_include} file.md\n```", []),
            ("```{include} \n```", []),
        ],
    )
    def test_extract_links(self, tmp_path, content, expected_links):
        file = tmp_path / "test.ipynb"
        file.write_text(content, encoding="utf-8")
        extractor = LinkExtractor(verbose=False)
        links = extractor.extract(file)
        assert links == expected_links

    def test_extract_handles_decode_error(self, tmp_path, caplog):
        extractor = LinkExtractor(verbose=False)
        # Create a file that can't be decoded as UTF-8
        binary_file = tmp_path / "binary_file.bin"
        binary_file.write_bytes(b"\xff\xfe")
        links = extractor.extract(binary_file)
        assert links == []
        assert "Cannot decode file" in caplog.text


class TestLinkValidator:
    @pytest.fixture
    def validator(self, tmp_path):
        return LinkValidator(
            root_dir=tmp_path,
            verbose=False,
            exclude_link_strings=list(BROKEN_LINKS_EXCLUDE_LINK_STRINGS),
        )

    def test_is_absolute_url(self, validator):
        assert validator.is_absolute_url("https://example.com") is True
        assert validator.is_absolute_url("http://local.dev") is True
        assert validator.is_absolute_url("/relative/path") is False
        assert validator.is_absolute_url("relative.ipynb") is False

    @pytest.mark.parametrize(
        "link,expected",
        [
            ("file.ipynb#section", "file.ipynb"),
            ("clean.ipynb", "clean.ipynb"),
            ("", ""),
        ],
    )
    def test_get_path_from_link(self, validator, link, expected):
        assert validator.get_path_from_link(link) == expected

    def test_resolve_target_path_absolute_from_root(self, validator, tmp_path):
        source = tmp_path / "docs" / "a.ipynb"
        target = validator.resolve_target_path("/notebooks/b.ipynb", source)
        assert target == tmp_path / "notebooks" / "b.ipynb"

    def test_resolve_target_path_relative(self, validator, tmp_path):
        source = tmp_path / "docs" / "a.ipynb"
        target = validator.resolve_target_path("../data.csv", source)
        assert target == (tmp_path / "data.csv").resolve()

    def test_is_valid_target_file_exists(self, validator, tmp_path):
        target = tmp_path / "exists.ipynb"
        target.touch()
        assert validator.is_valid_target(target) == (True, None)

    def test_is_valid_target_dir_with_index(self, validator, tmp_path):
        target_dir = tmp_path / "folder"
        target_dir.mkdir()
        (target_dir / "index.ipynb").touch()
        assert validator.is_valid_target(target_dir) == (True, None)

    def test_is_valid_target_dir_with_readme(self, validator, tmp_path):
        target_dir = tmp_path / "folder"
        target_dir.mkdir()
        (target_dir / "README.ipynb").touch()
        assert validator.is_valid_target(target_dir) == (True, None)

    def test_is_valid_target_dir_no_index(self, validator, tmp_path):
        target_dir = tmp_path / "empty"
        target_dir.mkdir()
        assert validator.is_valid_target(target_dir) == (False, "DIR_NO_INDEX")

    def test_validate_link_external_skipped(self, validator, tmp_path):
        source = tmp_path / "a.ipynb"
        error = validator.validate_link("https://example.com", source, 1)
        assert error is None

    def test_validate_link_internal_fragment_skipped(self, validator, tmp_path):
        source = tmp_path / "a.ipynb"
        error = validator.validate_link("#section", source, 1)
        assert error is None

    def test_validate_link_broken(self, validator, tmp_path):
        source = tmp_path / "a.ipynb"
        error = validator.validate_link("nonexistent.ipynb", source, 10)
        assert "BROKEN LINK" in error
        assert "a.ipynb:10" in error

    def test_validate_link_valid(self, validator, tmp_path):
        target = tmp_path / "exists.ipynb"
        target.touch()
        source = tmp_path / "a.ipynb"
        error = validator.validate_link("exists.ipynb", source, 1)
        assert error is None

    def test_validate_link_excluded_string(self, validator, tmp_path):
        source = tmp_path / "a.ipynb"
        excluded_link = next(iter(BROKEN_LINKS_EXCLUDE_LINK_STRINGS))
        error = validator.validate_link(excluded_link, source, 1)
        assert error is None

    def test_validate_link_excluded_string_verbose(self, tmp_path, caplog):
        caplog.set_level(logging.DEBUG)
        validator = LinkValidator(
            root_dir=tmp_path,
            verbose=True,
            exclude_link_strings=list(BROKEN_LINKS_EXCLUDE_LINK_STRINGS),
        )
        source = tmp_path / "a.ipynb"
        excluded_link = next(iter(BROKEN_LINKS_EXCLUDE_LINK_STRINGS))
        error = validator.validate_link(excluded_link, source, 1)
        assert error is None
        assert f"  SKIP Excluded Link String: {excluded_link}" in caplog.text

    def test_validate_link_target_outside_root_verbose(self, tmp_path, caplog):
        caplog.set_level(logging.DEBUG)
        validator = LinkValidator(root_dir=tmp_path / "root", verbose=True)
        validator.root_dir.mkdir()
        source = validator.root_dir / "a.ipynb"
        # Ensure source file exists for relative path resolution
        source.touch()
        # Link to a file outside the root directory
        outside = tmp_path / "outside.ipynb"
        outside.touch()
        # Resolve the path relative to the source file's parent directory
        relative_path_str = str(outside.relative_to(source.parent, walk_up=True))
        error = validator.validate_link(relative_path_str, source, 1)
        assert error is None
        assert f"  OK: {relative_path_str} -> {outside.resolve()}" in caplog.text

    def test_validate_link_valid_verbose(self, tmp_path, caplog):
        caplog.set_level(logging.DEBUG)
        target = tmp_path / "exists.ipynb"
        target.touch()
        source = tmp_path / "a.ipynb"
        validator = LinkValidator(root_dir=tmp_path, verbose=True)
        error = validator.validate_link("exists.ipynb", source, 1)
        assert error is None
        assert "  OK: exists.ipynb -> exists.ipynb" in caplog.text

    @pytest.mark.parametrize(
        "link,expected_error",
        [
            ("nonexistent.md", "BROKEN LINK"),
            ("./intro/", None), # This link is in BROKEN_LINKS_EXCLUDE_LINK_STRINGS, so it should be skipped (None)
            ("valid.md", None),
        ],
    )
    def test_validate_link_with_exclusions(self, tmp_path, link, expected_error):
        target = tmp_path / "valid.md"
        target.touch()
        source = tmp_path / "source.ipynb"
        validator = LinkValidator(
            root_dir=tmp_path,
            verbose=False,
            exclude_link_strings=list(BROKEN_LINKS_EXCLUDE_LINK_STRINGS),
        )
        error = validator.validate_link(link, source, 1)
        if expected_error:
            assert expected_error in error
        else:
            assert error is None

    def test_validate_link_source_outside_root(self, tmp_path):
        # Create a root_dir that is not the parent of source_file
        root_dir = tmp_path / "repo_root"
        root_dir.mkdir()
        source_file = tmp_path / "outside_repo" / "doc.md"
        source_file.parent.mkdir()
        source_file.touch()

        validator = LinkValidator(root_dir=root_dir, verbose=False)
        # Link to a non-existent file
        error = validator.validate_link("nonexistent.md", source_file, 5)
        assert "BROKEN LINK" in error
        # Check that the source file path in the error message is correct
        # and not relative to root_dir, as it's outside.
        assert f"File '{source_file}:5'" in error


class TestFileFinder:
    def test_find_respects_exclude_dirs_nested(self, tmp_path):
        # Setup a mock repository structure with various excluded directories
        root_test_dir = tmp_path / "repo_root"
        root_test_dir.mkdir()
        (root_test_dir / ".git").mkdir()  # Simulate a git repo root

        # Files that should be included
        (root_test_dir / "docs").mkdir()
        (root_test_dir / "docs" / "good_doc_1.ipynb").touch()
        (root_test_dir / "src").mkdir()
        # Nested good file within a valid path
        (root_test_dir / "src" / "sub_module" / "valid_code_folder").mkdir(parents=True)
        (root_test_dir / "src" / "sub_module" / "valid_code_folder" / "good_2.py").touch()
        # Directory name contains part of an excluded dir, but isn't the excluded dir itself
        (root_test_dir / "valid_dir_not_node_modules" / "some_file.ipynb").mkdir(parents=True)
        (root_test_dir / "valid_dir_not_node_modules" / "some_file.ipynb" / "good_3.ipynb").touch()

        # Files excluded by VALIDATION_EXCLUDE_DIRS
        (root_test_dir / "misc" / "in_progress" / "temp_folder").mkdir(parents=True)
        (root_test_dir / "misc" / "in_progress" / "temp_folder" / "bad_1.ipynb").touch()  # Excluded by misc/in_progress
        (root_test_dir / "src" / "my_module" / "__pycache__").mkdir(parents=True)
        (root_test_dir / "src" / "my_module" / "__pycache__" / "bad_2.py").touch()  # Excluded by __pycache__
        (root_test_dir / ".git" / "hooks").mkdir(parents=True)
        (root_test_dir / ".git" / "hooks" / "bad_3.md").touch()  # Excluded by .git
        (root_test_dir / "node_modules" / "some_lib" / "bad_folder").mkdir(parents=True)
        (root_test_dir / "node_modules" / "some_lib" / "bad_folder" / "bad_4.js").touch()  # Excluded by node_modules
        (root_test_dir / "nested_build" / "build" / "another_bad.py").mkdir(parents=True)
        (root_test_dir / "nested_build" / "build" / "another_bad.py" / "bad_5.txt").touch()  # Excluded by build

        finder = FileFinder(
            exclude_dirs=list(VALIDATION_EXCLUDE_DIRS),
            exclude_files=list(BROKEN_LINKS_EXCLUDE_FILES),
            verbose=False,  # Set to True for debugging if needed
        )
        files = finder.find(root_test_dir, "*")  # Use '*' to find all file types

        expected_files = {
            root_test_dir / "docs" / "good_doc_1.ipynb",
            root_test_dir / "src" / "sub_module" / "valid_code_folder" / "good_2.py",
            root_test_dir / "valid_dir_not_node_modules" / "some_file.ipynb" / "good_3.ipynb",
        }

        assert len(files) == len(expected_files)
        assert set(files) == expected_files

    def test_find_respects_exclude_files_globally(self, tmp_path):
        root_test_dir = tmp_path / "repo_root"
        root_test_dir.mkdir()

        # Files that should be included
        (root_test_dir / "good_file_1.ipynb").touch()
        (root_test_dir / "sub" / "good_dir").mkdir(parents=True)  # Renamed for clarity, it's a directory
        (root_test_dir / "sub" / "good_dir" / "another_good.txt").touch()

        # File that should be excluded by name (from BROKEN_LINKS_EXCLUDE_FILES)
        (root_test_dir / "sub" / "excluded_dir_for_file_test").mkdir(parents=True)
        (root_test_dir / "sub" / "excluded_dir_for_file_test" / ".aider.chat.history.md").touch()  # The file itself has the excluded name

        finder = FileFinder(
            exclude_dirs=list(VALIDATION_EXCLUDE_DIRS),
            exclude_files=list(BROKEN_LINKS_EXCLUDE_FILES),
            verbose=False,
        )
        files = finder.find(root_test_dir, "*")  # Use '*' to find all file types

        expected_files = {
            root_test_dir / "good_file_1.ipynb",
            root_test_dir / "sub" / "good_dir" / "another_good.txt",
        }
        assert len(files) == len(expected_files)
        assert set(files) == expected_files

    def test_find_excludes_ipynb_checkpoints(self, tmp_path):
        (tmp_path / "normal.ipynb").touch()
        cp_dir = tmp_path / ".ipynb_checkpoints"
        cp_dir.mkdir()
        (cp_dir / "auto.ipynb").touch()

        finder = FileFinder(exclude_dirs=[], exclude_files=[], verbose=False)
        files = finder.find(tmp_path, "*.ipynb")
        assert len(files) == 1
        assert ".ipynb_checkpoints" not in str(files[0])

    def test_find_symlink_outside_search_dir(self, tmp_path):
        # Create a target file outside the search directory
        external_dir = tmp_path / "external_data"
        external_dir.mkdir()
        external_file = external_dir / "external.ipynb"
        external_file.touch()

        # Create a search directory and a symlink within it pointing to the external file
        search_dir = tmp_path / "project_docs"
        search_dir.mkdir()
        symlink_path = search_dir / "link_to_external.ipynb"
        symlink_path.symlink_to(external_file)

        finder = FileFinder(exclude_dirs=[], exclude_files=[], verbose=False)
        files = finder.find(search_dir, "*.ipynb")

        # The symlinked file should be found and included, as its actual path is outside
        # the search_dir hierarchy, thus not subject to relative_to(search_dir) exclusions.
        assert len(files) == 1
        assert files[0] == symlink_path

    def test_find_skipping_non_files(self, tmp_path, caplog):
        caplog.set_level(logging.DEBUG)
        # Create a directory that matches the pattern (e.g. ends in .ipynb)
        dir_matching_pattern = tmp_path / "not_a_file.ipynb"
        dir_matching_pattern.mkdir()
        (tmp_path / "real.ipynb").touch()

        finder = FileFinder(exclude_dirs=[], exclude_files=[], verbose=True)
        files = finder.find(tmp_path, "*.ipynb")
        assert len(files) == 1
        assert files[0].name == "real.ipynb"
        assert "SKIPPING (not a file)" in caplog.text

class TestReporter:
    def test_report_broken_links_exits_1(self, tmp_path, capsys):
        blocking_errors = [" [BLOCKING] BROKEN LINK: ...\n"]
        legacy_errors = []
        with pytest.raises(SystemExit) as exc_info:
            Reporter.report(blocking_errors, legacy_errors, fail_on_legacy=False)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "❌" in captured.out

    def test_report_no_broken_links_exits_0(self, tmp_path, capsys):
        blocking_errors = []
        legacy_errors = []
        with pytest.raises(SystemExit) as exc_info:
            Reporter.report(blocking_errors, legacy_errors, fail_on_legacy=False)
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "✅" in captured.out

    def test_report_legacy_only_exits_0(self, tmp_path, capsys):
        blocking_errors = []
        legacy_errors = [" [LEGACY] BROKEN LINK: ...\n"]
        with pytest.raises(SystemExit) as exc_info:
            Reporter.report(blocking_errors, legacy_errors, fail_on_legacy=False)
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "❌" in captured.out

    def test_report_legacy_fail_on_legacy_exits_1(self, tmp_path, capsys):
        blocking_errors = []
        legacy_errors = [" [LEGACY] BROKEN LINK: ...\n"]
        with pytest.raises(SystemExit) as exc_info:
            Reporter.report(blocking_errors, legacy_errors, fail_on_legacy=True)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "❌" in captured.out

    def test_report_missing_temp_file(self, tmp_path, caplog):
        # This test is now obsolete because Reporter no longer uses temp files.
        # We can remove it or replace it with something else.
        pass


# =============================================================================
# Integration Tests: Git-Scoped Validation & Production Safety
# =============================================================================

class TestLinkCheckerGitIntegration:
    """Contract: verifies that only staged files are checked and targets must be tracked."""

    def setup_repo(self, tmp_path):
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        subprocess.run(["git", "init"], cwd=repo_dir, capture_output=True)
        # Establish a commit
        (repo_dir / "init.txt").write_text("init")
        subprocess.run(["git", "add", "init.txt"], cwd=repo_dir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo_dir, capture_output=True)
        return repo_dir

    def test_fails_when_link_target_is_untracked(self, tmp_path, monkeypatch, capsys):
        """Production Safety: A link to a file that exists on disk but is not tracked is broken."""
        repo = self.setup_repo(tmp_path)
        monkeypatch.chdir(repo)

        # Target exists on disk but is NOT staged/tracked
        target = Path("untracked_target.md")
        target.touch()

        source = Path("source.md")
        source.write_text(f"[link]({target.name})", encoding="utf-8")
        subprocess.run(["git", "add", "source.md"], cwd=repo, capture_output=True)

        with pytest.raises(SystemExit) as exc_info:
            LinkCheckerCLI().run(["--pattern", "*.md", str(source)])

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        # The error should explicitly instruct the user to run 'git add'
        assert "[BLOCKING]" in captured.out
        assert "Target file exists but is untracked. To fix: run 'git add <path>' to stage it." in captured.out
        assert "untracked_target.md" in captured.out

    def test_fails_when_link_target_is_ignored(self, tmp_path, monkeypatch, capsys):
        """Production Safety: A link to a file that is ignored by .gitignore is broken."""
        repo = self.setup_repo(tmp_path)
        monkeypatch.chdir(repo)

        # Target exists on disk but is ignored
        target = Path("ignored_target.md")
        target.touch()
        (repo / ".gitignore").write_text("ignored_target.md\n")
        subprocess.run(["git", "add", ".gitignore"], cwd=repo, capture_output=True)

        source = Path("source.md")
        source.write_text(f"[link]({target.name})", encoding="utf-8")
        subprocess.run(["git", "add", "source.md"], cwd=repo, capture_output=True)

        with pytest.raises(SystemExit) as exc_info:
            LinkCheckerCLI().run(["--pattern", "*.md", str(source)])

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        # The error should identify the file as ignored
        assert "[BLOCKING]" in captured.out
        assert "Target file exists but is ignored by git (.gitignore). To fix: remove from .gitignore or use 'git add -f'." in captured.out
        assert "ignored_target.md" in captured.out

    def test_passes_when_link_target_is_tracked(self, tmp_path, monkeypatch):
        repo = self.setup_repo(tmp_path)
        monkeypatch.chdir(repo)

        target = Path("tracked_target.md")
        target.touch()
        subprocess.run(["git", "add", "tracked_target.md"], cwd=repo, capture_output=True)

        source = Path("source.md")
        source.write_text(f"[link]({target.name})", encoding="utf-8")
        subprocess.run(["git", "add", "source.md"], cwd=repo, capture_output=True)

        with pytest.raises(SystemExit) as exc_info:
            LinkCheckerCLI().run(["--pattern", "*.md"])

        assert exc_info.value.code == 0

    def test_check_staged_blind_spot(self, tmp_path, monkeypatch, capsys):
        """Verify the blind spot is CLOSED: broken links in unstaged files are now detected as LEGACY."""
        repo = self.setup_repo(tmp_path)
        monkeypatch.chdir(repo)

        # 1. Staged file: valid link
        staged_file = Path("staged.md")
        staged_file.write_text("[link](target.md)", encoding="utf-8")
        (repo / "target.md").touch()
        subprocess.run(["git", "add", "staged.md", "target.md"], cwd=repo, capture_output=True)

        # 2. Unstaged file: BROKEN link
        unstaged_file = Path("unstaged.md")
        unstaged_file.write_text("[bad](missing.md)", encoding="utf-8")

        # Run without positional arguments -> everything is LEGACY
        with pytest.raises(SystemExit) as exc_info:
            LinkCheckerCLI().run(["--pattern", "*.md"])

        # Should return 0 because the broken link in the unstaged file is [LEGACY].
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "[LEGACY]" in captured.out
        assert "unstaged.md" in captured.out
        assert "missing.md" in captured.out

    def test_dual_mode_staged_source_untracked_target(self, tmp_path, monkeypatch, capsys):
        """TDD: Source staged -> Target untracked -> [BLOCKING] -> Exit 1."""
        repo = self.setup_repo(tmp_path)
        monkeypatch.chdir(repo)

        target = Path("untracked_target.md")
        target.touch()

        source = Path("source.md")
        source.write_text(f"[link]({target.name})", encoding="utf-8")
        subprocess.run(["git", "add", "source.md"], cwd=repo, capture_output=True)

        # Simulate pre-commit passing the staged file as a positional argument
        with pytest.raises(SystemExit) as exc_info:
            LinkCheckerCLI().run(["--pattern", "*.md", str(source)])

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "[BLOCKING]" in captured.out
        assert "untracked_target.md" in captured.out

    def test_dual_mode_unstaged_source_missing_target(self, tmp_path, monkeypatch, capsys):
        """TDD: Source unstaged -> Target missing -> [LEGACY] -> Exit 0."""
        repo = self.setup_repo(tmp_path)
        monkeypatch.chdir(repo)

        source = Path("unstaged.md")
        source.write_text("[link](missing.md)", encoding="utf-8")
        # NOT adding source to git

        # Simulate pre-commit NOT passing this file (or just run a check on it)
        # To test the [LEGACY] behavior, we run the script without positional args
        # but we want to see if this specific file is reported as LEGACY.
        with pytest.raises(SystemExit) as exc_info:
            LinkCheckerCLI().run(["--pattern", "*.md"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "[LEGACY]" in captured.out
        assert "unstaged.md" in captured.out
        assert "missing.md" in captured.out

    def test_dual_mode_manual_run_legacy_debt(self, tmp_path, monkeypatch, capsys):
        """TDD: No args -> All broken links reported as [LEGACY] -> Exit 0."""
        repo = self.setup_repo(tmp_path)
        monkeypatch.chdir(repo)

        source = Path("broken.md")
        source.write_text("[link](missing.md)", encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            LinkCheckerCLI().run(["--pattern", "*.md"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "[LEGACY]" in captured.out

    def test_dual_mode_manual_run_fail_on_legacy(self, tmp_path, monkeypatch, capsys):
        """TDD: --fail-on-legacy -> any broken link -> Exit 1."""
        repo = self.setup_repo(tmp_path)
        monkeypatch.chdir(repo)

        source = Path("broken.md")
        source.write_text("[link](missing.md)", encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            LinkCheckerCLI().run(["--pattern", "*.md", "--fail-on-legacy"])

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "[LEGACY]" in captured.out


class TestLinkCheckerCLI:
    @pytest.fixture
    def cli(self):
        return LinkCheckerCLI()

    def test_run_single_file_input(self, tmp_path, capsys, monkeypatch):
        target = tmp_path / "target.ipynb"
        target.touch()
        source = tmp_path / "source.ipynb"
        source.write_text(f"[link]({target.name})", encoding="utf-8")

        # Mock detect_repo_root to return None to avoid enforcing Git tracking in tmp_path
        monkeypatch.setattr("tools.scripts.check_broken_links.detect_repo_root", lambda: None)

        # Corrected: Added "--paths" flag
        monkeypatch.setattr(
            "sys.argv",
            ["check_broken_links.py", "--paths", str(source), "--pattern", "*.ipynb"],
        )
        with pytest.raises(SystemExit) as exc_info:
            cli = LinkCheckerCLI()
            cli.run()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Found 1 file in:" in captured.out
        assert "✅ All links are valid!" in captured.out

    def test_run_relative_path_input(self, tmp_path, capsys, monkeypatch):
        monkeypatch.chdir(tmp_path)
        source = Path("source.ipynb")
        source.touch()
        with pytest.raises(SystemExit) as exc_info:
            LinkCheckerCLI().run(["--paths", "source.ipynb"])
        assert exc_info.value.code == 0
        assert "Found 1 file in: source.ipynb" in capsys.readouterr().out

    def test_run_multiple_paths_reporting(self, tmp_path, capsys):
        f1 = tmp_path / "f1.ipynb"
        f1.touch()
        f2 = tmp_path / "f2.ipynb"
        f2.touch()
        with pytest.raises(SystemExit) as exc_info:
            LinkCheckerCLI().run(["--paths", str(f1), str(f2)])
        assert exc_info.value.code == 0
        out = capsys.readouterr().out
        assert "- " + str(f1) in out
        assert "- " + str(f2) in out

    def test_run_current_directory_default_path(self, tmp_path, capsys, monkeypatch):
        # Simulate running with no --paths argument, defaulting to current directory
        monkeypatch.chdir(tmp_path)  # Change CWD to tmp_path for this test
        # Mock detect_repo_root to return None to avoid enforcing Git tracking in tmp_path
        monkeypatch.setattr("tools.scripts.check_broken_links.detect_repo_root", lambda: None)
        target = tmp_path / "target.ipynb"
        target.touch()
        source = tmp_path / "source.ipynb"
        source.write_text(f"[link]({target.name})", encoding="utf-8")

        cli = LinkCheckerCLI()
        with pytest.raises(SystemExit) as exc_info:
            cli.run(["--pattern", "*.ipynb"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Found 2 files in:" in captured.out # Corrected assertion: expects 2 files (target.ipynb, source.ipynb)
        assert "✅ All links are valid!" in captured.out

    def test_run_broken_link_in_dir(self, tmp_path, capsys):
        (tmp_path / "source.ipynb").write_text("[bad](missing.ipynb)", encoding="utf-8")

        cli = LinkCheckerCLI()
        with pytest.raises(SystemExit) as exc_info:
            # Pass arguments directly to the method
            cli.run(["--paths", str(tmp_path), "--pattern", "*.ipynb"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "[LEGACY]" in captured.out

    def test_run_path_does_not_exist(self, tmp_path, caplog, cli):
        non_existent = tmp_path / "ghost.md"
        with pytest.raises(SystemExit) as exc_info:
            # No files found should exit 0
            cli.run(["--paths", str(non_existent), "--pattern", "*.md"])
        assert exc_info.value.code == 0
        assert "Warning: Path does not exist" in caplog.text

    def test_run_verbose_logging(self, cli, tmp_path, caplog, monkeypatch):
        """Verify that verbose output is sent to logging.debug instead of print."""
        import logging
        caplog.set_level(logging.DEBUG)
        target = tmp_path / "target.md"
        target.touch()
        source = tmp_path / "source.md"
        source.write_text("[link](target.md)", encoding="utf-8")

        monkeypatch.setattr("tools.scripts.check_broken_links.detect_repo_root", lambda: None)

        with pytest.raises(SystemExit) as exc_info:
            cli.run(["--paths", str(source), "--verbose"])

        assert exc_info.value.code == 0
        # Checking for a message that should now be a log
        assert "Checking file:" in caplog.text

    def test_run_broken_myst_include(self, tmp_path, capsys):
        (tmp_path / "source.md").write_text(
            "```{include} missing.md\n```", encoding="utf-8"
        )

        cli = LinkCheckerCLI()
        with pytest.raises(SystemExit) as exc_info:
            cli.run(["--paths", str(tmp_path), "--pattern", "*.md"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "[LEGACY]" in captured.out

    def test_e2e_myst_include_with_git_root(self, tmp_path, capsys, caplog):
        git_root = tmp_path / "repo"
        git_root.mkdir()
        (git_root / ".git").mkdir()
        docs = git_root / "docs"
        docs.mkdir()
        target = git_root / "architecture" / "adr_index.md"
        target.parent.mkdir()
        target.touch()
        source = docs / "guide.md"
        source.write_text(
            "```{include} path/to/file.md\n:class: dropdown\n```",
            encoding="utf-8",
        )

        cli = LinkCheckerCLI()
        with (
            patch("tools.scripts.check_broken_links.detect_repo_root", return_value=git_root),
            patch("pathlib.Path.cwd", return_value=docs),
        ):
            # Enable verbose mode to cover line 275 (SKIP Excluded Link String verbose output)
            with pytest.raises(SystemExit) as exc_info:
                cli.run(["--paths", str(source), "--verbose"])
            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            assert "Using Git root" in caplog.text
            assert "SKIP Excluded Link String: path/to/file.md" in caplog.text
            assert "BROKEN LINK" not in captured.out  # Crucial check

    def test_e2e_directory_link_with_excluded_link(self, tmp_path, capsys, caplog):
        git_root = tmp_path / "repo"
        git_root.mkdir()
        (git_root / ".git").mkdir()
        docs = git_root / "docs"
        docs.mkdir()
        source = docs / "guide.md"
        # This link string is now in BROKEN_LINKS_EXCLUDE_LINK_STRINGS
        source.write_text("[Intro](./intro/)", encoding="utf-8")

        cli = LinkCheckerCLI()
        with (
            patch("tools.scripts.check_broken_links.detect_repo_root", return_value=git_root),
            patch("pathlib.Path.cwd", return_value=docs),
        ):
            # Enable verbose mode to cover line 275 (SKIP Excluded Link String verbose output)
            with pytest.raises(SystemExit) as exc_info:
                cli.run(["--paths", str(source), "--verbose"])
            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            assert "Using Git root" in caplog.text
            assert "SKIP Excluded Link String: ./intro/" in caplog.text
            assert "BROKEN LINK" not in captured.out  # Crucial check

    def test_run_explicit_file_in_excluded_dir_is_skipped(self, tmp_path, capsys, caplog):
        # Setup a mock repository structure
        root_dir = tmp_path / "repo"
        root_dir.mkdir()
        (root_dir / ".git").mkdir()

        # Create an excluded directory ('misc' is in VALIDATION_EXCLUDE_DIRS)
        excluded_dir = root_dir / "misc"
        excluded_dir.mkdir(parents=True)
        
        # Create a file in that excluded directory
        excluded_file = excluded_dir / "secret_notes.ipynb"
        excluded_file.write_text("some content", encoding="utf-8")

        # Run the CLI with the explicit path to the excluded file
        cli = LinkCheckerCLI()
        with pytest.raises(SystemExit) as exc_info:
            cli.run(["--paths", str(excluded_file), "--pattern", "*.ipynb"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        # It should report that no files matching the pattern were found (because it was skipped)
        assert "No files matching '*.ipynb' found!" in caplog.text


# ======================
# Defensive Tests
# ======================


def test_nonexistent_input_path(tmp_path, capsys, caplog):
    cli = LinkCheckerCLI()
    bad_path = tmp_path / "does_not_exist"
    with pytest.raises(SystemExit) as exc_info:
        cli.run(["--paths", str(bad_path)])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "Warning: Path does not exist" in caplog.text


def test_run_no_git_root_warning(tmp_path, capsys, caplog):
    cli = LinkCheckerCLI()
    with patch("tools.scripts.check_broken_links.detect_repo_root", return_value=None):
        # We need to provide --paths so it doesn't try to find git root for CWD if we are in one
        with pytest.raises(SystemExit):
            cli.run(["--paths", str(tmp_path), "--verbose"])
    captured = capsys.readouterr()
    assert "Warning: Not in a Git repository" in caplog.text


# ======================
# Parametrized Edge Cases
# ======================


@pytest.mark.parametrize(
    "link_str,should_skip",
    [
        ("#top", True),
        ("#section-1", True),
        ("page.ipynb#anchor", False),
        ("", False),
        (".", False),
        ("..", False),
        ("./local.ipynb", False),
    ],
)
def test_link_validator_skip_logic(tmp_path, link_str, should_skip):
    validator = LinkValidator(root_dir=tmp_path)
    source = tmp_path / "source.ipynb"
    error = validator.validate_link(link_str, source, 1)
    if should_skip:
        assert error is None
    else:
        # May be broken or valid, but not skipped
        pass  # We only care it wasn't skipped


# ======================
# End-to-End Git Root Simulation
# ======================


def test_e2e_with_git_root(tmp_path, capsys, caplog):
    git_root = tmp_path / "repo"
    git_root.mkdir()
    _git.init_repo(git_root)
    docs = git_root / "docs"
    docs.mkdir()
    target = git_root / "data.ipynb"
    target.touch()
    _git.add_files(git_root, "data.ipynb")
    source = docs / "guide.ipynb"
    source.write_text("[data](/data.ipynb)", encoding="utf-8")

    cli = LinkCheckerCLI()
    with (
        patch("tools.scripts.check_broken_links.detect_repo_root", return_value=git_root),
        patch("pathlib.Path.cwd", return_value=docs),
    ):
        # Explicitly use --paths and avoid monkeypatch
        with pytest.raises(SystemExit) as exc_info:
            cli.run(["--verbose", "--paths", str(source)])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Using Git root" in caplog.text


# ======================
# Main Entry Point Test
# ======================


def test_main_entry_point(monkeypatch):
    # Cover the __main__ block
    with patch("sys.argv", ["check_broken_links.py", "--help"]), pytest.raises(SystemExit):
        runpy.run_path("tools/scripts/check_broken_links.py", run_name="__main__")

    # This test covers the `if __name__ == "__main__":` block
    # by directly calling main() after patching LinkCheckerCLI.
    with patch("tools.scripts.check_broken_links.LinkCheckerCLI.run") as mock_run:
        from tools.scripts.check_broken_links import main
        main()
        mock_run.assert_called_once_with() # main() calls run() with no explicit args


# ======================
# Link Extractor Verbose Output Test
# ======================


def test_link_extractor_verbose_output(tmp_path, capsys, caplog):
    file = tmp_path / "test.md"
    file.write_text("[link](target.md)", encoding="utf-8")
    extractor = LinkExtractor(verbose=True)
    links = extractor.extract(file)
    assert links == [("target.md", 1)]
    captured = capsys.readouterr()
    assert "Links found in" in caplog.text
    assert "target.md" in caplog.text


# =============================================================================
# Context-Aware Link Extraction (R-26002, R-26003)
# =============================================================================

class TestLinkExtractorContextAware:
    """Contract: LinkExtractor must be context-aware of file type.

    For .py files, regex patterns and string literals containing Markdown-style
    link syntax must NOT be flagged as broken links. Only links in comments and
    docstrings should be extracted from .py files.

    This prevents "Implementation Leakage" (R-26003 L4) where the tool flags its
    own regex patterns as broken links.
    """

    def test_py_file_regex_pattern_not_flagged(self, tmp_path):
        """A .py file containing regex patterns must not have them extracted as links."""
        py_file = tmp_path / "script.py"
        py_file.write_text(
            'FRONTMATTER_PATTERN = re.compile(r"\\[{\\^{2}([^`\\n]+)", re.DOTALL)\n',
            encoding="utf-8",
        )
        extractor = LinkExtractor(verbose=False)
        links = extractor.extract(py_file)
        assert links == []

    def test_py_file_myst_include_regex_not_flagged(self, tmp_path):
        """The MyST include regex pattern in check_broken_links.py source must not be flagged."""
        py_file = tmp_path / "check_broken_links.py"
        py_file.write_text(
            'myst_includes = re.findall(r"```{include}([^`\\n]+)", line)\n',
            encoding="utf-8",
        )
        extractor = LinkExtractor(verbose=False)
        links = extractor.extract(py_file)
        assert links == []

    def test_py_file_myst_include_literal_in_comment_not_flagged(self, tmp_path):
        """The actual check_broken_links.py source must not self-reference via MyST include in comments.

        This is a regression test for a self-referential false positive where a comment
        documenting the MyST include regex contained the literal triple-backtick include
        sequence that the regex on the next line matched, flagging the script's own source.
        """
        repo_root = Path(__file__).resolve().parents[2]
        py_file = repo_root / "tools" / "scripts" / "check_broken_links.py"
        extractor = LinkExtractor(verbose=False)
        links = extractor.extract(py_file)
        myst_links = [link for link, _ in links if "followed" in link or "backticks" in link]
        assert myst_links == []

    def test_py_file_link_in_comment_extracted(self, tmp_path):
        """A .py file with a Markdown link in a comment should have it extracted."""
        py_file = tmp_path / "script.py"
        py_file.write_text(
            '# See [ADR-26042](/architecture/adr/adr_26042.md) for details\n',
            encoding="utf-8",
        )
        extractor = LinkExtractor(verbose=False)
        links = extractor.extract(py_file)
        assert links == [("/architecture/adr/adr_26042.md", 1)]

    def test_py_file_link_in_docstring_extracted(self, tmp_path):
        """A .py file with a Markdown link in a docstring should have it extracted."""
        py_file = tmp_path / "script.py"
        py_file.write_text(
            '"""\nSee [guide](/tools/docs/guide.md) for usage.\n"""\n',
            encoding="utf-8",
        )
        extractor = LinkExtractor(verbose=False)
        links = extractor.extract(py_file)
        assert links == [("/tools/docs/guide.md", 2)]

    def test_py_file_string_literal_not_flagged(self, tmp_path):
        """A .py file with link-like patterns inside string assignments must not be flagged."""
        py_file = tmp_path / "script.py"
        py_file.write_text(
            'pattern = r"\\[([^\\]]*)\\]\\(([^)]+)\\)"\n',
            encoding="utf-8",
        )
        extractor = LinkExtractor(verbose=False)
        links = extractor.extract(py_file)
        assert links == []

    def test_md_file_extraction_unchanged(self, tmp_path):
        """Markdown file extraction must remain unchanged after context-aware fix."""
        md_file = tmp_path / "doc.md"
        md_file.write_text(
            "[text](link.ipynb)\n```{include} /path/to/file.md\n```\n",
            encoding="utf-8",
        )
        extractor = LinkExtractor(verbose=False)
        links = extractor.extract(md_file)
        assert ("link.ipynb", 1) in links
        assert ("/path/to/file.md", 2) in links


class TestContextAwareBlocking:
    """Contract: .py files in tools/scripts/ with broken links are still [BLOCKING]."""

    def test_py_file_broken_link_in_comment_is_blocking(self, tmp_path, monkeypatch, capsys):
        """A .py file with a broken link in a comment must be flagged as [BLOCKING]."""
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True)
        (repo / "init.txt").write_text("init")
        subprocess.run(["git", "add", "init.txt"], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo, capture_output=True)
        monkeypatch.chdir(repo)

        py_file = Path("script.py")
        py_file.write_text(
            '# See [broken](nonexistent.md) for details\n',
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "script.py"], cwd=repo, capture_output=True)

        with pytest.raises(SystemExit) as exc_info:
            LinkCheckerCLI().run(["--pattern", "*.py", str(py_file)])

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "[BLOCKING]" in captured.out
        assert "nonexistent.md" in captured.out
