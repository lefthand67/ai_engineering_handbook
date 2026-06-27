# Plan: Resolve Validation Deadlock & Implement Commit-Scoped Governance (FINALIZED)

**Date:** 2026-06-27
**Status:** Implemented
**Author:** Qwen Code

## 1. Context & Root Cause Analysis

### Current State
The project's governance hooks (`check-frontmatter` and `check-adr-index`) were configured with `pass_filenames: false`, forcing global scans of the entire repository on every commit.

### The "Validation Deadlock"
Strict new standards (ADR-26042) created a state where legacy debt in unstaged files blocked all commit attempts, even for unrelated compliant changes.

### Resolution Strategy
Transitioned from a **Global Quality Gate** to a **Commit-Scoped Filter**:
- **Staged Files**: Must be 100% compliant (Blocking $\rightarrow$ Exit 1).
- **Global Files**: Reported as warnings to maintain visibility of technical debt (Non-blocking $\rightarrow$ Exit 0).

---

## 2. Implementation Details

### Core Logic Changes
- **`tools/scripts/adr_utils.py`**: Added `is_blocking` field to `ValidationError` to distinguish the impact of a violation.
- **`tools/scripts/check_frontmatter.py`**: 
    - Updated `main()` to accept staged files via `sys.argv`.
    - Implemented dual-mode validation: errors in staged files or blueprint files are blocking; others are legacy warnings.
    - Fixed "Mermaid False Positive": prevented Mermaid diagram fences (`---`) from being detected as YAML blocks.
- **`tools/scripts/check_adr.py`**: 
    - Implemented dual-mode validation logic similar to `check_frontmatter`.
    - Added warnings for duplicate ADR numbers during index fixing.
- **`.pre-commit-config.yaml`**: 
    - Enabled `pass_filenames: true` for `check-frontmatter` and `check-adr-index`.
    - Removed obsolete `--check-staged` flags.

### Testing Overhaul (Adopting Testing Pyramid)
To eliminate brittleness, the testing strategy was shifted from "Set Menu" (Integration) to "A la Carte" (Unit) testing.

- **`tools/tests/test_check_adr.py`**: Completely rewritten. Removed brittle CLI integration tests in favor of focused unit tests for core logic (`TestIndexSyncEdgeCases`, `TestIndexRegeneration`, etc.), increasing coverage to 91%.
- **`tools/tests/test_check_frontmatter.py`**: 
    - Added `TestDualModeValidation` to verify blocking vs warning behavior.
    - Added `TestMermaidFalsePositives` to verify Mermaid fence handling.
    - Updated token size tests to avoid brittle hardcoded values.
- **`tools/tests/test_check_broken_links.py`**: Updated to verify that links to ignored files (`.gitignore`) are correctly detected as broken.
- **`tools/tests/test_git.py`**: Added unit tests for `is_ignored` logic.
- **`tools/scripts/testing_standards.md`**: Formalized the distinction between **Logic (Unit)** and **Plumbing (Integration)** testing to prevent future brittleness.

---

## 3. Verification Results

- **Test Case 1: Staged File Violation**: Verified that violations in staged files return Exit 1 (BLOCKING).
- **Test Case 2: Legacy File Violation**: Verified that violations in non-staged files return Exit 0 (LEGACY warning).
- **Test Case 3: Blueprint Violation**: Verified that blueprint files ALWAYS block (Exit 1) regardless of staged status.
- **Test Case 4: Mermaid Fences**: Verified that Mermaid diagrams do not trigger "Too many YAML blocks" errors.
- **Test Case 5: Git Ignore**: Verified that targets ignored by git are reported as broken links.

---

## 4. Final Checklist
- [x] `.pre-commit-config.yaml` updated for both hooks?
- [x] `check_frontmatter.py` distinguishes blocking vs non-blocking?
- [x] `check_adr.py` distinguishes blocking vs non-blocking?
- [x] `testing_standards.md` updated to formalize unit vs integration testing?
- [x] All tests pass and coverage is high?
- [x] Legacy debt is still visible but non-blocking?
