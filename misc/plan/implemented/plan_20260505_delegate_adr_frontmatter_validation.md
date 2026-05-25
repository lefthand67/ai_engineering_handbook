# Delegate ADR Frontmatter Validation & Refactor Structure

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove redundant frontmatter parsing from `check_adr.py` (delegating to `check_frontmatter.py`), split `check_adr.py` into a structural validator and an index synchronizer, and ensure the test suite is robust and non-brittle.

**Architecture:** 
1. **Shared Domain:** `tools/scripts/adr_utils.py` contains `AdrFile` and index parsing logic.
2. **Structural Validator:** `tools/scripts/check_adr.py` focuses exclusively on internal ADR consistency (body sections, status sync, promotion gates).
3. **Index Synchronizer:** `tools/scripts/check_adr_index.py` handles the relationship between the ADR folder and `adr_index.md` and project-wide term references.
4. **Delegation:** All YAML/frontmatter validation is handled by `tools/scripts/check_frontmatter.py`.

**Tech Stack:** Python 3.13, PyYAML, `uv`, `pytest`.

**Commit Strategy:** Frequent, small commits after each logical task is verified.

---

## File Mapping

- **Create:** `tools/scripts/adr_utils.py` (Shared models and discovery)
- **Create:** `tools/scripts/check_adr_index.py` (Index sync and term refs)
- **Create:** `tools/tests/test_adr_utils.py`
- **Create:** `tools/tests/test_check_adr_index.py`
- **Modify:** `tools/scripts/check_adr.py`
  - Remove `FRONTMATTER_PATTERN` and `parse_frontmatter()`.
  - Remove all Index synchronization and Term reference logic.
  - Delegate frontmatter validation to `check_frontmatter.py`.
- **Modify:** `tools/tests/test_check_adr.py`
  - Remove index-related tests.
  - Refactor brittle assertions (remove `captured.out` checks).
  - Implement dynamic `token_size` calculation in test helpers.
- **Delete:** `tools/docs/scripts_instructions/check_adr_py_script.md`
- **Delete:** `tools/docs/scripts_instructions/check_adr_py_script.ipynb`

---

## Implementation Tasks

### Task 1: Shared Domain Utilities (Extraction)

**Files:**
- Create: `tools/scripts/adr_utils.py`
- Create: `tools/tests/test_adr_utils.py`

- [ ] **Step 1: Implement `adr_utils.py`**
  Move `AdrFile`, `IndexEntry`, `ValidationError` dataclasses and `get_adr_files()`, `parse_index()` from `check_adr.py` to `adr_utils.py`.

- [ ] **Step 2: Verify with `test_adr_utils.py`**
  Write tests to ensure files are discovered correctly and the index is parsed accurately.

- [ ] **Step 3: Commit**
  `git commit -m "chore: extract ADR shared utilities to adr_utils.py"`

### Task 2: ADR Index Synchronizer (Extraction)

**Files:**
- Create: `tools/scripts/check_adr_index.py`
- Create: `tools/tests/test_check_adr_index.py`

- [ ] **Step 1: Implement `check_adr_index.py` core logic**
  Move `validate_sync`, `fix_index`, `validate_term_references`, and `fix_term_references` from `check_adr.py` to this new script. Use `adr_utils.py`.

- [ ] **Step 2: Implement CLI Interface**
  Create a `main()` function in `check_adr_index.py` supporting `--fix`, `--check-staged`, and `--verbose` flags to ensure it is usable as a standalone tool and pre-commit hook.

- [ ] **Step 3: Verify with `test_check_adr_index.py`**
  Write TDD tests for index mismatch detection, auto-fixing, and term reference validation.

- [ ] **Step 4: Commit**
  `git commit -m "feat: implement standalone ADR index synchronizer"`

### Task 3: ADR Structural Validator (Refactor)

**Files:**
- Modify: `tools/scripts/check_adr.py`

- [ ] **Step 1: Purge Index and Frontmatter Logic**
  Remove all code related to index sync, term refs, and local frontmatter parsing/regex.

- [ ] **Step 2: Implement Delegation to `check_frontmatter.py`**
  Use `check_frontmatter.parse_frontmatter` and `validate_parsed_frontmatter` to handle YAML validation. Map `FrontmatterError` to `ValidationError`.

- [ ] **Step 3: Verify Status Synchronization**
  Ensure the structural check comparing Frontmatter status $\leftrightarrow$ Body status remains intact.

- [ ] **Step 4: Decouple `--fix` logic from `main()`**
  Remove all calls to `fix_index()` and `fix_term_references()` from `check_adr.py`'s `main()` function.

- [ ] **Step 5: Commit**
  `git commit -m "refactor: focus check_adr.py on internal structural validation"`

### Task 4: Robust Test Suite (Refactor)

**Files:**
- Modify: `tools/tests/test_check_adr.py`

- [ ] **Step 1: Remove Brittle Assertions**
  Replace `captured.out` checks with semantic assertions (e.g., checking `ValidationError` types or exit codes).

- [ ] **Step 2: Fix `token_size` Hardcoding**
  Update `create_adr_file_*` helpers to dynamically calculate the actual token count using `check_frontmatter.calculate_tokens`.

- [ ] **Step 3: Update Imports**
  Update all imports to reference `adr_utils` for domain models and `check_adr_index` for any remaining synchronization tests.

- [ ] **Step 4: Verify and Commit**
  `uv run pytest tools/tests/test_check_adr.py`
  `git commit -m "test: make ADR tests robust and non-brittle"`

### Task 5: Cleanup and Integration

**Files:**
- Delete: `tools/docs/scripts_instructions/check_adr_py_script.*`
- Modify: `.pre-commit-config.yaml`

- [ ] **Step 1: Remove stale documentation**
- [ ] **Step 2: Add `check_adr_index.py` to pre-commit hooks**
  Ensure the hook configuration includes necessary arguments (e.g., `--check-staged`) to optimize performance.
- [ ] **Step 3: Final full suite run and commit**
  `git commit -m "chore: cleanup ADR docs and integrate new validators into pre-commit"`
