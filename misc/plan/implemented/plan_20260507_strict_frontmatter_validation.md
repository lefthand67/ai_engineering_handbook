# Frontmatter Strict Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enforce strict frontmatter validation in `check_frontmatter.py` to ensure all required fields are present, unknown fields are forbidden, and IDs follow type-specific prefixing.

**Architecture:** 
- Extend `_validate_field_value` to include regex-based ID validation mapped to `doc_type`.
- Implement `_check_unknown_fields` to scan both top-level and `options` blocks against the `FIELD_REGISTRY` and a set of permitted infrastructure keys (`jupytext`, `kernelspec`).
- Elevate `invalid_namespace` from a warning to a blocking error.

**Tech Stack:** Python 3.13, `re`, `yaml`.
**Workflow:** Strict TDD (Red $\rightarrow$ Green $\rightarrow$ Refactor). All changes must be verified with coverage.

---

### Task 1: Update Error Taxonomy and Blocking Logic

**Files:**
- Modify: `tools/scripts/check_frontmatter.py`

- [ ] **Step 1: Add `invalid_field` to `FrontmatterError` docstring**
  Update the `error_type` taxonomy in the `FrontmatterError` class to include `"invalid_field" — field present but not defined in hub registry (blocking)`. Ensure the docstring clearly defines the contract for this error.

- [ ] **Step 2: Make `invalid_namespace` a blocking error**
  In `main()`, remove `"namespace_warning"` (or rename it to `invalid_namespace`) from the logic that treats it as stderr-only. Ensure all `FrontmatterError` types now cause `exit 1`.

- [ ] **Step 3: Verify the change**
  Run a test case that triggers a namespace warning and verify it now returns exit code 1.

### Task 2: Implement ID Prefix Validation (TDD)

**Files:**
- Modify: `tools/scripts/check_frontmatter.py`
- Test: `tools/tests/test_check_frontmatter.py`

- [ ] **Step 1: Write failing tests (RED)**
  Add test cases to `test_check_frontmatter.py` covering:
  - `guide` using `A-` prefix (should fail).
  - `evidence` (analysis) using `S-` prefix (should fail).
  - `evidence` (source) using `A-` prefix (should fail).
  - `adr` using `A-` prefix (should fail).
  - Valid IDs for each type (should pass).
  Ensure the test class has a docstring explaining the ID prefix contract.

- [ ] **Step 2: Run tests to verify failure**
  `uv run pytest tools/tests/test_check_frontmatter.py`
  Expected: FAIL.

- [ ] **Step 3: Implement ID validation in `_validate_field_value` (GREEN)**
  Add logic to `_validate_field_value` for `field == "id"`:
  - If `doc_type == "adr"`, expect `^ADR-\d+$` or `^\d+$`.
  - If `doc_type == "evidence"`, check the `artifact_type` (from spoke config):
    - `analysis` $\rightarrow$ `^A-\d+$`
    - `source` $\rightarrow$ `^S-\d+$`
  - For other types (e.g., `guide`), if an ID is present, ensure it doesn't use reserved prefixes (`A-`, `S-`, `ADR-`).

- [ ] **Step 4: Run tests to verify success**
  `uv run pytest tools/tests/test_check_frontmatter.py`
  Expected: PASS.

- [ ] **Step 5: Refactor and Document**
  Ensure the implementation is clean and contains docstrings explaining the regex choices.

### Task 3: Implement Unknown Field Detection (TDD)

**Files:**
- Modify: `tools/scripts/check_frontmatter.py`
- Test: `tools/tests/test_check_frontmatter.py`

- [ ] **Step 1: Write failing tests (RED)**
  Add test cases to `test_check_frontmatter.py` covering:
  - Top-level unknown field (should fail with `invalid_field`).
  - `options` block unknown field (should fail with `invalid_field`).
  - Permitted infra keys (`jupytext`, `kernelspec`) (should pass).
  - Valid `FIELD_REGISTRY` fields (should pass).

- [ ] **Step 2: Run tests to verify failure**
  `uv run pytest tools/tests/test_check_frontmatter.py`
  Expected: FAIL.

- [ ] **Step 3: Implement `_check_unknown_fields` (GREEN)**
  Create a function that:
  1.  Defines `ALLOWED_INFRA_KEYS = {"options", "jupytext", "kernelspec"}`.
  2.  Checks top-level keys: If a key is not in `ALLOWED_INFRA_KEYS` AND is not a MyST-native field in `FIELD_REGISTRY`, raise `invalid_field`.
  3.  Checks `options` keys: If a key is not in `FIELD_REGISTRY`, raise `invalid_field`.
  Integrate this into `validate_parsed_frontmatter`.

- [ ] **Step 4: Run tests to verify success**
  `uv run pytest tools/tests/test_check_frontmatter.py`
  Expected: PASS.

- [ ] **Step 5: Refactor and Document**
  Ensure the contract for "unknown fields" is documented in the script.

### Task 4: Final Verification and Coverage

**Files:**
- Test: `tools/tests/test_check_frontmatter.py`

- [ ] **Step 1: Run full tests with coverage**
  Run: `uv run pytest tools/tests/test_check_frontmatter.py --cov=tools.scripts.check_frontmatter`
  Expected: High coverage (ideally 100% for the modified functions).

- [ ] **Step 2: Verify against already committed ADRs**
  Run the script against the `architecture/adr/` directory to ensure the refined logic doesn't break existing, correctly formatted ADRs, and identifies any legacy issues that need fixing.
  Run: `uv run python -m tools.scripts.check_frontmatter architecture/adr/`

- [ ] **Step 3: Final Atomic Commit**
  Stage all changes (script and tests) and create one clean atomic commit.
  `git add tools/scripts/check_frontmatter.py tools/tests/test_check_frontmatter.py`
  `git commit -m "fix: implement strict frontmatter validation and ID prefixing"`
