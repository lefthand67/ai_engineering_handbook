import pytest
import re
import sys
from pathlib import Path
from tools.scripts.update_token_counts import update_token_counts, main
from unittest.mock import patch

class TestUpdateTokenCounts:
    """
    Contract for update_token_counts:
    
    1. Discovery: Only files with a valid MyST-style frontmatter (delimited by '---') 
       are processed. Files without frontmatter are ignored.
    2. Calculation: Token count must be calculated based on the FULL file content, 
       including the frontmatter, to reflect actual context window cost.
    3. Structural Integrity:
       - The file body must remain unchanged.
       - The '---' delimiters must be preserved.
       - Existing frontmatter fields must be preserved.
    4. Type Safety & Recovery:
       - If 'options' is missing, it must be created as a dictionary.
       - If 'options' exists but is not a dictionary (e.g., a string or null), 
         it must be converted to a dictionary to allow token_size insertion.
       - If 'token_size' exists but is not an integer, it must be overwritten.
    5. Resilience: 
       - Malformed YAML within the frontmatter block must not cause the script 
         to crash; the file should be skipped gracefully.
       - Multiple '---' sequences in the body must not be mistaken for frontmatter.
    """

    def test_update_token_counts_basic(self, tmp_path):
        """Verify that a standard governed file has its token_size updated from 0 to actual."""
        file = tmp_path / "test.md"
        content = """---
title: Test
options:
  token_size: 0
---

Hello world!"""
        file.write_text(content)

        update_token_counts(root=tmp_path, paths=[file])

        updated_content = file.read_text()
        assert "token_size: " in updated_content
        assert "token_size: 0" not in updated_content

    def test_update_token_counts_missing_field(self, tmp_path):
        """Verify that the token_size field is created if it is missing from the options dict."""
        file = tmp_path / "test.md"
        content = """---
title: Test
options: {}
---

Hello world!"""
        file.write_text(content)

        update_token_counts(root=tmp_path, paths=[file])

        assert "token_size:" in file.read_text()

    def test_update_token_counts_preserves_content(self, tmp_path):
        """Verify that the body and frontmatter delimiters remain untouched."""
        file = tmp_path / "test.md"
        body = "This is the important body content that must not change."
        content = f"""---
title: Test
options:
  token_size: 0
---

{body}"""
        file.write_text(content)

        update_token_counts(root=tmp_path, paths=[file])

        updated = file.read_text()
        assert body in updated
        assert updated.count("---") == 2

    def test_update_token_counts_malformed_yaml(self, tmp_path):
        """
        Adversary: Verify that syntax errors in YAML do not raise exceptions.
        The contract specifies graceful skipping of malformed files.
        """
        file = tmp_path / "malformed.md"
        content = """---
title Test
options: [unclosed bracket
---

Body"""
        file.write_text(content)

        update_token_counts(root=tmp_path, paths=[file])
        assert file.exists()

    def test_update_token_counts_options_wrong_type(self, tmp_path):
        """
        Adversary: Verify recovery when 'options' is a scalar instead of a mapping.
        The contract requires conversion to a dict to ensure token_size can be stored.
        """
        file = tmp_path / "wrong_type.md"
        content = """---
title: Test
options: none
---

Body"""
        file.write_text(content)

        update_token_counts(root=tmp_path, paths=[file])
        
        updated = file.read_text()
        assert "options:" in updated
        assert "token_size:" in updated

    def test_update_token_counts_no_frontmatter(self, tmp_path):
        """Verify that files without frontmatter delimiters are ignored entirely."""
        file = tmp_path / "no_fm.md"
        content = "Just a plain text file with no frontmatter."
        file.write_text(content)

        update_token_counts(root=tmp_path, paths=[file])
        
        assert file.read_text() == content

    def test_update_token_counts_empty_frontmatter(self, tmp_path):
        """Verify that a minimal frontmatter block still results in a valid options.token_size."""
        file = tmp_path / "empty_fm.md"
        content = """---
---

Body"""
        file.write_text(content)

        update_token_counts(root=tmp_path, paths=[file])
        
        updated = file.read_text()
        assert "options:" in updated
        assert "token_size:" in updated

    def test_update_token_counts_multiple_delimiters(self, tmp_path):
        """Verify that horizontal rules (---) in the body are not treated as frontmatter boundaries."""
        file = tmp_path / "multi.md"
        content = """---
title: Test
options: {}
---

Body with --- horizontal rule"""
        file.write_text(content)

        update_token_counts(root=tmp_path, paths=[file])
        
        updated = file.read_text()
        assert "token_size:" in updated
        assert "--- horizontal rule" in updated
        assert updated.count("---") == 3

    def test_update_token_counts_dry_run(self, tmp_path):
        """Verify that dry_run=True does not modify the file."""
        file = tmp_path / "dry_run.md"
        content = """---
title: Dry Run
options:
  token_size: 0
---

Body"""
        file.write_text(content)

        # We need to modify the function signature in the implementation first, 
        # but for the test we assume the signature will be update_file_tokens(path, dry_run=False)
        from tools.scripts.update_token_counts import update_file_tokens
        update_file_tokens(file, dry_run=True)

        assert file.read_text() == content

    def test_update_token_counts_token_size_wrong_type(self, tmp_path):
        """
        Adversary: Verify that a non-integer token_size is overwritten.
        The contract mandates that the final value must be a numeric token count.
        """
        file = tmp_path / "ts_wrong_type.md"
        content = """---
title: Test
options:
  token_size: large
---

Body"""
        file.write_text(content)

        update_token_counts(root=tmp_path, paths=[file])
        
        updated = file.read_text()
        assert "token_size: large" not in updated
        assert re.search(r"token_size: \d+", updated)

    def test_update_token_counts_no_op(self, tmp_path):
        """Verify that the file is NOT modified if the token_size is already correct."""
        file = tmp_path / "no_op.md"
        # We create a file, run the script once to get the correct token size,
        # then run it again and verify the file doesn't change.
        content = """---
title: Test
options:
  token_size: 0
---

Hello world!"""
        file.write_text(content)

        # First pass: calculate and write the correct size
        update_token_counts(root=tmp_path, paths=[file])
        first_pass_content = file.read_text()

        # Get the modification time after first pass
        first_pass_mtime = file.stat().st_mtime

        # Second pass: should be a no-op
        import time
        time.sleep(0.1) # Ensure mtime would change if written
        update_token_counts(root=tmp_path, paths=[file])

        second_pass_content = file.read_text()
        second_pass_mtime = file.stat().st_mtime

        assert first_pass_content == second_pass_content
        assert first_pass_mtime == second_pass_mtime

    def test_removes_top_level_token_size(self, tmp_path):
        """
        Adversary: Verify that redundant top-level 'token_size' is removed.
        The fixer should migrate legacy top-level fields to 'options.token_size'.
        """
        file = tmp_path / "redundant.md"
        content = """---
title: Test
token_size: ~100
options:
  token_size: 50
---

Hello world!"""
        file.write_text(content)

        update_token_counts(root=tmp_path, paths=[file])

        updated = file.read_text()
        # Top level should be gone
        assert "token_size: ~100" not in updated
        # Root token_size should not be present in the root mapping
        # (roughly check that it doesn't appear before the first 'options:')
        parts = updated.split("options:")
        assert "token_size:" not in parts[0]
        # Governed field should still exist and be numeric
        assert "options:" in updated
        assert re.search(r"token_size: \d+", updated)
class TestUpdateTokenCountsIntegration:
    """Verify discovery and orchestration across a directory tree."""

    def test_respects_external_repo_exclusions(self, tmp_path, monkeypatch):
        """
        Adversary: Verify that files within registered external repos are ignored.
        We mock VALIDATION_EXCLUDE_DIRS to simulate a registered external path.
        """
        # 1. Mock the exclusion list to include a specific relative path
        external_path = "ai_agents/research/ai_coding_agents"
        monkeypatch.setattr("tools.scripts.update_token_counts.VALIDATION_EXCLUDE_DIRS", {external_path})
        monkeypatch.setattr("tools.scripts.update_token_counts.is_excluded", lambda p: external_path in p)

        # 2. Setup: a file in the excluded path and a file in a normal path
        excluded_dir = tmp_path / external_path
        excluded_dir.mkdir(parents=True)
        excluded_file = excluded_dir / "external.md"
        excluded_file.write_text("---\ntitle: External\noptions:\n  token_size: 0\n---\n\nBody")

        normal_dir = tmp_path / "docs"
        normal_dir.mkdir()
        normal_file = normal_dir / "internal.md"
        normal_file.write_text("---\ntitle: Internal\noptions:\n  token_size: 0\n---\n\nBody")

        # 3. Execute
        update_token_counts(root=tmp_path, paths=[tmp_path])

        # 4. Verify
        assert "token_size: 0" in excluded_file.read_text(), "Excluded file should NOT have been updated"
        assert "token_size: 0" not in normal_file.read_text(), "Internal file SHOULD have been updated"

    def test_update_token_counts_integration(self, tmp_path):

        """Verify that discovery finds governed files and skips excluded ones."""
        # Setup:
        # 1. Valid file in root
        root_file = tmp_path / "root.md"
        root_file.write_text("---\\ntitle: Root\\noptions:\\n  token_size: 0\\n---\\n\\nBody")

        # 2. Valid file in subdir
        subdir = tmp_path / "docs"
        subdir.mkdir()
        sub_file = subdir / "sub.md"
        sub_file.write_text("---\\ntitle: Sub\\noptions:\\n  token_size: 0\\n---\\n\\nBody")

        # 3. Non-governed file (no frontmatter)
        plain_file = tmp_path / "plain.txt"
        plain_file.write_text("Plain text")

        update_token_counts(root=tmp_path, paths=[tmp_path])

        assert "token_size:" in root_file.read_text()
        assert "token_size:" in sub_file.read_text()
        assert plain_file.read_text() == "Plain text"

    def test_explicit_file_in_excluded_dir_is_skipped(self, tmp_path, monkeypatch):
        """Explicitly passing a file from an excluded directory should be skipped.
        
        This verifies that the 'leak' where files in external research repositories
        are processed when passed as explicit arguments is fixed.
        """
        # Mock exclusion to a generic path
        excl_dir_name = "excluded_dir"
        monkeypatch.setattr("tools.scripts.update_token_counts.VALIDATION_EXCLUDE_DIRS", {excl_dir_name})
        monkeypatch.setattr("tools.scripts.update_token_counts.is_excluded", lambda p: excl_dir_name in p)


        excl_dir = tmp_path / excl_dir_name
        excl_dir.mkdir()
        test_file = excl_dir / "external.md"
        test_file.write_text("---\\ntitle: External\\noptions:\\n  token_size: 0\\n---\\n\\nBody")

        # Execute
        update_token_counts(root=tmp_path, paths=[test_file])

        # Verify: File should NOT have been updated
        assert "token_size: 0" in test_file.read_text(), "Excluded file should NOT have been updated"


    def test_main_cli_execution(self, tmp_path, monkeypatch):
        """Verify the main CLI entry point works with arguments."""
        file = tmp_path / "cli_test.md"
        content = """---
title: CLI
options:
  token_size: 0
---

Body"""
        file.write_text(content)

        # Patch sys.argv to simulate CLI call: script.py /path/to/dir
        monkeypatch.setattr(sys, "argv", ["update_token_counts.py", str(tmp_path)])

        exit_code = main()

        assert exit_code == 0
        assert "token_size:" in file.read_text()
        assert "token_size: 0" not in file.read_text()

    def test_main_dry_run(self, tmp_path, monkeypatch):
        """Verify that the --dry-run flag prevents file modifications."""
        file = tmp_path / "dry_run_cli.md"
        content = """---
title: Dry Run CLI
options:
  token_size: 0
---

Body"""
        file.write_text(content)

        monkeypatch.setattr(sys, "argv", ["update_token_counts.py", "--dry-run", str(tmp_path)])

        exit_code = main()

        assert exit_code == 0
        assert file.read_text() == content

    def test_main_single_file_target(self, tmp_path, monkeypatch):
        """Verify that providing a specific file updates ONLY that file."""
        file1 = tmp_path / "update_me.md"
        content1 = """---
title: Update
options:
  token_size: 0
---

Body"""
        file1.write_text(content1)
        
        file2 = tmp_path / "ignore_me.md"
        content2 = """---
title: Ignore
options:
  token_size: 0
---

Body"""
        file2.write_text(content2)

        monkeypatch.setattr(sys, "argv", ["update_token_counts.py", str(file1)])

        exit_code = main()

        assert exit_code == 0
        assert "token_size: 0" not in file1.read_text()
        assert "token_size: 0" in file2.read_text()

    def test_main_default_root(self, tmp_path, monkeypatch):
        """Verify that main() defaults to repo root when no paths are provided."""
        # Setup: Mock repo root to be tmp_path
        monkeypatch.setattr("tools.scripts.update_token_counts.detect_repo_root", lambda: tmp_path)

        # Setup: Create minimal pyproject.toml to satisfy get_config_path
        (tmp_path / "pyproject.toml").write_text('[tool.vadocs]\nconfig_dir = ".vadocs"')

        # Setup: Create minimal governance config in tmp_path
        vadocs = tmp_path / ".vadocs"
        vadocs.mkdir()
        conf_file = vadocs / "conf.json"
        conf_file.write_text('{"governed_extensions": [".md"]}')

        # Setup: Create a file to update
        file = tmp_path / "root_default.md"
        content = """---
title: Default
options:
  token_size: 0
---

Body"""
        file.write_text(content)

        monkeypatch.setattr(sys, "argv", ["update_token_counts.py"])

        exit_code = main()

        assert exit_code == 0
        assert "token_size: 0" not in file.read_text()

    def test_main_config_failure(self, tmp_path, monkeypatch):
        """Verify that main() returns 1 if the governance config cannot be loaded."""
        # Setup: Mock repo root to be tmp_path (where no config exists)
        monkeypatch.setattr("tools.scripts.update_token_counts.detect_repo_root", lambda: tmp_path)

        # We don't create .vadocs/conf.json here, so it should fail
        monkeypatch.setattr(sys, "argv", ["update_token_counts.py"])

        exit_code = main()

        assert exit_code == 1

    def test_main_log_level(self, tmp_path, monkeypatch, caplog):
        """Verify that the --log-level flag is accepted and changes logging output."""
        file = tmp_path / "log_test.md"
        content = """---
title: Log Test
options:
  token_size: 0
---

Body"""
        file.write_text(content)

        # Setup: Mock repo root and config
        monkeypatch.setattr("tools.scripts.update_token_counts.detect_repo_root", lambda: tmp_path)
        (tmp_path / "pyproject.toml").write_text('[tool.vadocs]\nconfig_dir = ".vadocs"')
        vadocs = tmp_path / ".vadocs"
        vadocs.mkdir()
        (vadocs / "conf.json").write_text('{"governed_extensions": [".md"]}')

        # Test DEBUG level - should see DEBUG messages
        caplog.set_level("DEBUG")
        monkeypatch.setattr(sys, "argv", ["update_token_counts.py", "--log-level", "DEBUG", str(file)])
        main()
        assert any("Found frontmatter" in record.message for record in caplog.records)

        # Test ERROR level - should NOT see DEBUG messages
        caplog.clear()
        caplog.set_level("ERROR")
        monkeypatch.setattr(sys, "argv", ["update_token_counts.py", "--log-level", "ERROR", str(file)])
        main()
        assert not any("Found frontmatter" in record.message for record in caplog.records)
