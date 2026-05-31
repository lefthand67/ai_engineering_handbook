import os
import re
import sys


def main():
    """
    Main function to clean Pandoc Markdown files.

    Usage:
        python clean_pandoc_markdown.py <input_file> <output_file>

    Example:
        python clean_pandoc_markdown.py input.md output.md

    This script will read the input file, remove any boilerplate front-matter,
    convert HTML image tags to Markdown, and strip Pandoc-specific metadata.
    The cleaned content will be saved to the specified output file.

    Note: Ensure that the input file is a valid Pandoc Markdown document.

    Example of the pandoc output command:
        pandoc ./book.epub -f epub -t markdown --extract-media=./book_assets -o book.md
    """
    # Example usage that can be tied to a shell script command
    if len(sys.argv) > 1:
        clean_any_pandoc_markdown(sys.argv[1], sys.argv[2])
    else:
        # Default fallback names if run directly without arguments
        print("Usage: python clean_pandoc_markdown.py <input_file> <output_file>")


def clean_any_pandoc_markdown(input_path, output_path):
    """
    Cleans any Pandoc Markdown file by removing boilerplate front-matter,
    converting HTML image tags to Markdown, and stripping Pandoc-specific metadata.

    Args:
        input_path (str): The path to the input Pandoc Markdown file.
        output_path (str): The path where the cleaned Markdown will be saved.
    """
    print(f"Processing: {input_path}")
    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # --- PHASE 1: DYNAMIC FRONT-MATTER REMOVAL ---
    # We loop through the file until we find the first meaningful top-level header (#)
    # that isn't a boilerplate page (copyright, praise, cover, table of contents).
    content_start_line = 0
    boilerplate_keywords = [
        "cover",
        "praise",
        "copyright",
        "revision history",
        "title page",
        "table of contents",
        "contents",
    ]

    for i, line in enumerate(lines):
        if line.strip().startswith("# "):
            header_text = line.replace("#", "").strip().lower()
            # If the header doesn't match any boilerplate keywords, this is our true start!
            if not any(kw in header_text for kw in boilerplate_keywords):
                content_start_line = i
                print(
                    f"--> Dynamically detected true content start at header: '{line.strip()}'"
                )
                break

    # Join the lines back together starting from our dynamic anchor point
    content = "".join(lines[content_start_line:])

    # --- PHASE 2: GENERIC REGEX CLEANING (No book-specific strings) ---

    # 1. Convert all HTML image tags to Markdown images generically
    content = re.sub(
        r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>', r"\n\n![](\1)\n\n", content
    )

    # 2. Flatten inline formatting enclosures like [Text Content]{.anything} -> Text Content
    content = re.sub(r"\[(.*?)\]\s*\{.*?\}", r"\1", content)

    # 3. Strip all Pandoc index annotations and metadata attributes completely
    # This targets anything like {data-type="..."} or {.class-name} or {=html}
    content = re.sub(r"\{[^\}]+\}", "", content)

    # 4. Clean up any empty anchor elements left behind by Pandoc (e.g., []{#anchor-id})
    content = re.sub(r"\[\]\{#[^\}]+\}", "", content)

    # 5. Erase standalone structural colon blocks cleanly (e.g., ::: legal, :::::::)
    content = re.sub(r"^\s*::+\s*[a-zA-Z-]*$", "", content, flags=re.MULTILINE)

    # 6. Safely eliminate all residual layout HTML wrappers (<div>, <figure>, etc.)
    content = re.sub(r"<[^>]+>", "", content)

    # 7. Dissolve internal cross-reference hyperlink brackets [Link Text](#internal-anchor) -> Link Text
    content = re.sub(r"\[(.*?)\]\((#[^\)]+)\)", r"\1", content)

    # --- PHASE 3: PARAGRAPH SMOOTHING & TOKENS OPTIMIZATION ---
    chunks = content.split("\n\n")
    optimized_paragraphs = []

    for chunk in chunks:
        stripped = chunk.strip()
        if not stripped:
            continue

        # Leave code blocks, headers, bullet lists, and markdown images untouched
        if (
            stripped.startswith("#")
            or stripped.startswith("```")
            or stripped.startswith("-")
            or stripped.startswith("*")
            or stripped.startswith("![")
        ):
            optimized_paragraphs.append(stripped)
        elif stripped.startswith(">"):
            # Flatten multi-line quotes into a single clean line break structure
            flattened_quote = re.sub(r"\s*\n\s*>\s*", " ", stripped)
            optimized_paragraphs.append(flattened_quote)
        else:
            # Re-stitch mid-sentence line breaks caused by book text column limits
            flattened_text = re.sub(r"\s+", " ", stripped)
            optimized_paragraphs.append(flattened_text)

    # Re-compile text with clean double carriage returns
    final_text = "\n\n".join(optimized_paragraphs)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_text)

    print(f"Success! Exported clean asset directly to: {output_path}\n")


if __name__ == "__main__":
    main()
