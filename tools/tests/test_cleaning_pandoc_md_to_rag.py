import pytest
from pathlib import Path
import tools.scripts.cleaning_pandoc_md_to_rag as _module

class TestCleaningPandocMarkdown:
    """
    Tests the cleaning contract for Pandoc Markdown files prepared for RAG.
    
    The contract ensures:
    1. Boilerplate headers are stripped, and content begins at the first meaningful top-level header.
    2. Pandoc-specific metadata (curly braces, inline formatting) is removed.
    3. HTML tags are converted to Markdown or stripped.
    4. Mid-sentence line breaks in standard paragraphs are re-stitched.
    5. Block-level structures (headers, code, lists, images) are preserved.
    """

    def _run_cleaner(self, tmp_path, content):
        input_file = tmp_path / "input.md"
        output_file = tmp_path / "output.md"
        input_file.write_text(content, encoding="utf-8")
        _module.clean_any_pandoc_markdown(str(input_file), str(output_file))
        return output_file.read_text(encoding="utf-8")

    def test_boilerplate_removal_boundary(self, tmp_path):
        """
        Verify behavior boundary: content must start at the first non-boilerplate header.
        """
        content = (
            "# Copyright\n(c) 2026\n\n"
            "# Contents\n- Intro\n\n"
            "# Introduction\nStart here.\n\n"
            "# Chapter 1\nMore content."
        )
        result = self._run_cleaner(tmp_path, content)
        
        assert result.startswith("# Introduction")
        assert "Copyright" not in result
        assert "Contents" not in result

    def test_no_meaningful_header(self, tmp_path):
        """
        Adversary test: file containing only boilerplate or no headers.
        Should return the original content if no meaningful header is found.
        """
        content = "# Copyright\n(c) 2026\n\nSome random text without headers."
        result = self._run_cleaner(tmp_path, content)
        
        # According to script logic, if no header is found, content_start_line remains 0.
        assert "Some random text" in result

    def test_empty_file(self, tmp_path):
        """
        Adversary test: empty input file.
        """
        result = self._run_cleaner(tmp_path, "")
        assert result == ""

    @pytest.mark.parametrize("input_snippet", [
        "This is [text]{.class}",
        "Some {metadata}",
        "Empty anchor []{#id}",
        "Div <div>content</div>",
        "Link [Text](#anchor)",
        "::: block\ncontent\n:::",
    ])
    def test_metadata_and_html_removal_invariants(self, tmp_path, input_snippet):
        """
        Semantic validation: ensure Pandoc markers and HTML are absent from the output.
        """
        content = f"# Content\n\n{input_snippet}"
        result = self._run_cleaner(tmp_path, content)
        
        assert "{" not in result
        assert "}" not in result
        assert "<div>" not in result
        assert "</div>" not in result
        assert "](#" not in result
        assert ":::" not in result

    def test_image_conversion_contract(self, tmp_path):
        """
        Verify HTML images are converted to Markdown image syntax.
        """
        content = "# Content\n\n<img src=\"path/to/img.png\" alt=\"test\">"
        result = self._run_cleaner(tmp_path, content)
        
        assert "![](" in result
        assert "path/to/img.png" in result
        assert "<img" not in result

    def test_paragraph_smoothing_contract(self, tmp_path):
        """
        Verify re-stitching of broken lines and flattening of quotes.
        """
        content = (
            "# Content\n\n"
            "This is a long\n"
            "line that should\n"
            "be one paragraph.\n\n"
            "> Quote line 1\n"
            "> Quote line 2"
        )
        result = self._run_cleaner(tmp_path, content)

        # Mid-sentence breaks should be replaced by space
        assert "This is a long line that should be one paragraph." in result
        # Quotes should be flattened into one line starting with >
        assert "> Quote line 1 Quote line 2" in result
        # There should be no internal quote line breaks
        assert "\n>" not in result[result.find(">"):]

    def test_structural_preservation(self, tmp_path):
        """
        Verify that headers, code blocks, and lists are NOT smoothed.
        """
        content = (
            "# Header\n\n"
            "```python\n"
            "def hello():\n"
            "    print('world')\n"
            "```\n\n"
            "- List item 1\n"
            "- List item 2"
        )
        result = self._run_cleaner(tmp_path, content)
        
        assert "# Header" in result
        assert "    print('world')" in result # Indentation preserved
        assert "- List item 1" in result
        assert "- List item 2" in result

    def test_integration_realistic_mix(self, tmp_path):
        """
        Complex case mixing multiple cleaning phases.
        """
        content = (
            "# Copyright\n\n"
            "# Introduction\n\n"
            "The [AI Book]{.title} is great.\n\n"
            "Check <img src=\"fig1.png\">\n\n"
            "A split\n"
            "paragraph.\n\n"
            "<div>Div content</div>\n\n"
            "```bash\nls\n```"
        )
        result = self._run_cleaner(tmp_path, content)
        
        # Invariants
        assert result.startswith("# Introduction")
        assert "{" not in result
        assert "}" not in result
        assert "<img" not in result
        assert "<div>" not in result
        assert "A split paragraph." in result
        assert "```bash\nls\n```" in result
