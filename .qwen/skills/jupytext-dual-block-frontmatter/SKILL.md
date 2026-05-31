---
name: jupytext-dual-block-frontmatter
description: How to structure frontmatter in MyST Markdown files paired with Jupyter notebooks to prevent synchronization stripping.
source: auto-skill
extracted_at: '2026-05-30T12:20:46.677Z'
---

# Jupytext Dual-Block Frontmatter Pattern

When working with MyST Markdown files that are paired with Jupyter notebooks via Jupytext, a specific "Dual-Block" frontmatter pattern must be used to ensure that both Jupytext synchronization and project governance validation (ADR-26042) function correctly.

## The Problem
If Jupytext configuration and project metadata (title, authors, etc.) are merged into a single YAML block, the `jupytext-sync` process may strip the project metadata when updating the `.md` file from the `.ipynb` source. This leads to data loss and validation failures in `check_frontmatter.py`.

## The Solution: Dual-Block Pattern
Governed files must separate tool-specific metadata from project governance metadata using a double-separator.

### Structure
```yaml
---
# Block 1: Jupytext/Kernel Metadata
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.1
kernelspec:
  name: python3
  display_name: Python 3 (ipykernel)
  language: python
---

---
# Block 2: Project Identity, Discovery, and Lifecycle
title: "Document Title"
authors:
  - name: Vadim Rudakov
    email: rudakow.wadim@gmail.com
date: "2026-05-01"
description: "Elevator pitch"
tags: [tag1, tag2]
options:
  type: guide  # Mandatory: determines the validation spoke config
  birth: "2026-01-01"
  version: 1.0.0
---
```

## Key Requirements
1. **Separation**: Block 1 and Block 2 must be separated by `---` followed by another `---` on the next line.
2. **Ordering**: The Jupytext/Kernel block must come first.
3. **Completeness**: The second block must include the mandatory `options.type` field to satisfy the governance validator.

## Verification
- Run `uv run python -m tools.scripts.check_frontmatter <file>` to verify that the `options.type` is correctly detected.
- Run `uv run jupytext --sync` to ensure that the synchronization does not strip the governance block.

## Troubleshooting: Structural Failures
A common error is the "Broken Dual-Block," where the project metadata block starts without its own opening `---` fence (i.e., only one separator exists between Block 1 and Block 2).

### The Symptom: Misleading "Missing Field" Error
When the opening fence of the second block is missing, the validator's parser may skip the metadata block entirely. This results in a misleading `missing_type` or `missing required field` error, even if the field is physically present in the file.

### The Fix
Ensure there is a clear `--- \n ---` sequence separating the blocks. If you see a "missing field" error in a file that appears to have the field, check for this structural failure first.

### Validator Improvement (TDD)
If you find a new structural edge case causing misleading errors:
1. Create a minimal reproduction file.
2. Add a failing test case to `tools/tests/test_check_frontmatter.py`.
3. Update `parse_frontmatter` to detect the anomaly and report a specific structural error (e.g., `broken_dual_block`) rather than a content error.
