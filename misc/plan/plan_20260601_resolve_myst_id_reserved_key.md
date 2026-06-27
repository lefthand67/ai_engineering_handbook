# Plan: Harden Frontmatter Validation and Resolve MyST Reserved Keys

## Context
A discrepancy was found between `mystmd` constraints and internal governance: `mystmd` forbids the `id` field inside the `options` block, but `tools/scripts/check_frontmatter.py` did not.

Furthermore, a "huge investigation" revealed that corrupted files (YAML syntax errors, missing types) bypassed pre-commit hooks. The root cause is that `check_frontmatter.py` silently suppresses `yaml.YAMLError` as a warning if at least one other block in the file is valid. Additionally, the `ai_agents/research/` directory was missing from governance exclusions, leading to noise in validation reports.

A critical contradiction was also identified: `README.md` is explicitly excluded from governance but contains corrupted frontmatter, which is an unacceptable state.

## Goal
Eliminate silent validation bypasses and align governance with tool-chain constraints by:
1. **Hardening the Parser:** Transforming silent `YAMLError` warnings into blocking errors.
2. **Enforcing Reserved Keys:** Forbidding `id` (and other reserved keys) within the `options` block.
3. **Correcting Exclusions:** Ensuring `ai_agents/research/` and other external repos are properly ignored via centralized logic.
4. **Resolving README Paradox:** Either including `README.md` in validation or removing its frontmatter.
5. **Systemic Remediation:** Identifying and fixing all corrupted frontmatter across the repository.

## Implementation Steps

### Phase 1: Validator Hardening (TDD)
1. **Add Adversary Tests:** Create test cases in `tools/tests/test_check_frontmatter.py` for:
    - Files with invalid YAML syntax (must trigger blocking error). ✅
    - Files with missing `options.type` (must trigger blocking error). ✅
    - Frontmatter with `id` inside `options` block (must trigger `invalid_namespace` or new `reserved_key_in_options` error). ✅
2. **Fix Silent Failures:** Modify `parse_frontmatter()` and `validate_frontmatter()` in `tools/scripts/check_frontmatter.py` to treat `yaml.YAMLError` as a blocking anomaly instead of a warning. ✅
3. **Implement Reserved Key Check:** Update `_check_options_namespace` or add a dedicated check to specifically forbid `id` within the `options` block. (In Progress)
4. **Verify Fix:** Run the test suite to ensure all adversary cases are now blocked. ✅

### Phase 2: Governance & Exclusion Fixes
1. **Unify Exclusion Logic:** Update `check_frontmatter.py` to respect `VALIDATION_EXCLUDE_DIRS` from `paths.py` in addition to `conf.json` excludes. This ensures `ai_agents/research/` and other external repos are automatically ignored. ✅
2. **Resolve README Corruption:** 
    - Decide if `README.md` should be governed.
    - If yes: remove from `governance_excludes.files` in `.vadocs/conf.json`.
    - If no: strip the corrupted frontmatter from `README.md`.
3. **Audit External Registry:** Verify `.vadocs/inventory/manage_external_repos.json` contains all active research directories to ensure `VALIDATION_EXCLUDE_DIRS` is accurate.

### Phase 3: Comprehensive Repository Audit
1. **Full Scan:** Run the hardened validator: `uv run python -m tools.scripts.check_frontmatter .`
2. **Categorize Failures:** Extract a list of files needing:
    - `id` move (from `options` to top-level).
    - YAML syntax correction.
    - `options.type` definition.

### Phase 4: Bulk Remediation
1. **Apply Fixes:** Systematically correct the identified files.
2. **Sync Pairs:** Ensure every fixed `.md` file has its paired `.ipynb` staged/synced via Jupytext.
3. **Final Verification:**
    - Run `uv run python -m tools.scripts.check_frontmatter .` (Expect 0 errors).
    - Run `uv run myst start` (Expect 0 reserved key errors).

## Rationale
Silent failures in pre-commit hooks are unacceptable as they provide a false sense of security and allow broken artifacts into production. By moving these checks into the governance script, we transform tool-specific failures into clear, actionable instructions for developers.

## Expected Output
- `check_frontmatter.py` returns exit code 1 for any YAML syntax error or reserved key violation.
- All governed files in `architecture/` and `ai_agents/` have valid, MyST-compliant frontmatter.
- `ai_agents/research/` is correctly excluded from validation.
- `README.md` is either validated and corrected or cleaned of metadata.
- `myst build` completes without frontmatter-related errors.
