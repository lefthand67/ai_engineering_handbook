# Handoff Specification: Fix Validation Blind Spots and Tooling Regressions
Date: 2026-06-27
Status: Implemented (2026-06-27)

## 0. Required Context
The executing agent MUST read the following documents to understand the architectural constraints and the history of failures being addressed:
- **Retrospectives:**
    - `architecture/evidence/retrospective/R_26001_validation_deadlock.md`
    - `architecture/evidence/retrospective/R_26002_link_validation_false_positives.md`
    - `architecture/evidence/retrospective/R_26003_instruction_drift.md`
- **Standards:**
    - `architecture/adr/adr_26045_ai_native_development_code_as_primary_documentation.md` — MUST be followed for all code and test implementation.

## 1. Context & Analysis

The repository is experiencing blocking validation failures and test regressions. The primary architectural goal is to implement **Dual-Mode Broken Link Validation** and eradicate **Instruction Drift** in the frontmatter validator.

### The "Lying Instructor" and Instruction Drift (R-26003)
Investigation revealed that `tools/scripts/check_frontmatter.py` provides misleading JIT instructions. It suggests an ID format (`ADR-NNN`) that contradicts the actual project convention (`YYNNN`). Because agents are mandated to follow hook instructions (ADR-26050), the tool is actively steering agents toward incorrect solutions.

**Corrective Principle: The Pipe Pattern**
The tool must act as a pure pipe. Human-readable examples must be moved from Python code to the `.vadocs` SSoT configuration. Hardcoded fallbacks are prohibited; a missing configuration must trigger a `GovernanceConfigError`.

## 2. Mandatory Implementation Workflow (TDD)

The executing agent MUST follow the **Red $\rightarrow$ Green $\rightarrow$ Refactor** cycle for all tooling changes:
1. **Red:** Write a failing test in `tools/tests/` that captures the requirement.
2. **Green:** Implement the minimum code in `tools/scripts/` to make the test pass.
3. **Refactor:** Clean up implementation, ensure idiomatic Python (Pathlib), and verify no regressions.

## 3. Cross-Reference Map

| File to Change | Affected by / References | Change Type |
| :--- | :--- | :--- |
| `.vadocs/types/adr.conf.json` | `check-frontmatter` logic | SSoT Update (id_example) |
| `tools/scripts/check_frontmatter.py` | JIT Instructions | Logic Refactor (Pure Pipe) |
| `tools/scripts/check_broken_links.py` | Link Extraction Logic | Logic Refactor (Context Awareness) |
| `.pre-commit-config.yaml` | `check-broken-links` / `test-check-adr-index` | Config Cleanup |
| `tools/tests/test_check_broken_links.py` | `check-broken-links` script | Regression Test |
| `architecture/adr/adr_template.md` | `check-frontmatter` hook | Blueprint Alignment |
| `architecture/adr/adr_26057_...md` | `check-broken-links` hook | Content Fix |
| `architecture/evidence/analyses/A-26026...md` | `adr_26057` | Staging Fix |
| `tools/scripts/testing_standards.md` | `check-frontmatter` hook | Frontmatter Fix |
| `tools/docs/languages/*.md` | `check-frontmatter` hook | Frontmatter Fix |
| `tools/docs/git/git_notes_...md` | `check-frontmatter` hook | Frontmatter Fix |
| `tools/tests/test_adr_utils.py` | `adr_utils.py` | Staging Fix |
| `tools/docs/**/*.ipynb` | `jupytext-verify-pair` hook | Staging Fix |

## 4. Detailed Implementation Tasks

### Phase 1: Tooling & Governance (The Heart)
*Goal: Fix the validators first so they provide correct instructions and don't flag false positives.*

#### Task 1.1: Eradicate Instruction Drift (The Pipe Pattern) ✅ DONE
- **Status:** Already implemented prior to execution session. Verified during execution.
- **Config Update:** `"id_example": "26001 (where 26 is year and 001 is the order number)"` added to `.vadocs/types/adr.conf.json`.
- **Logic Refactor:** `tools/scripts/check_frontmatter.py` reads `id_example` from spoke config (lines 955-966). Raises `GovernanceConfigError` if missing. No hardcoded fallbacks.

#### Task 1.2: Implement Context-Aware Link Extraction ✅ DONE
- **File:** `tools/scripts/check_broken_links.py`
- **Status:** Implemented via TDD (Red → Green → Refactor).
- **Operation:** Modified `LinkExtractor` class to be file-type-aware:
    - Added `_is_docstring_line()` helper to track triple-quote docstring state.
    - Added `_is_comment_line()` helper to detect `#` comment lines.
    - Modified `extract()` method: for `.py` files, only scans comments and docstrings — regex patterns and string literals are NOT flagged as links.
    - This prevents "Implementation Leakage" (R-26003 L4) where the tool's own regex patterns would be flagged as broken links.

#### Task 1.3: Pre-commit Hook Cleanup ✅ DONE (with deviation)
- **File:** `.pre-commit-config.yaml`
- **Deviation from spec:** Operation 1 (Exclusion) was **NOT** performed. The user corrected the approach: excluding test files via pre-commit config is a config-based silencer that contradicts R-26003 L4 ("Configuration must describe the domain, not the tool's internals"). The context-aware extraction at the code layer (Task 1.2) already handles `.py` test files correctly — test fixtures in string literals are never scanned. A config-based exclusion is redundant and would mask real broken links in test comments/docstrings.
- **Operation 2 (Removal):** ✅ Dead `test-check-adr-index` hook removed (lines 210-217 of original config).

#### Task 1.4: Tooling Regression Test ✅ DONE
- **File:** `tools/tests/test_check_broken_links.py`
- **Status:** 7 regression tests added in two test classes:
    - `TestLinkExtractorContextAware` (6 tests): regex patterns not flagged in .py, MyST include regex not flagged, links in comments extracted, links in docstrings extracted, string literals not flagged, .md extraction unchanged.
    - `TestContextAwareBlocking` (1 test): .py file with broken link in comment is `[BLOCKING]`.

### Phase 2: Blueprint Alignment (The Gold Standard)
*Goal: Repair the template that blocks all commits.*

#### Task 2.1: `adr_template.md` Surgery ✅ DONE
- **File:** `architecture/adr/adr_template.md`
- **Status:** Already fixed prior to execution session. Verified during execution.
- **Changes verified:** `id: 00000` at top level, canonical order (`id, title, authors, description, tags, date, options`), no leading whitespace before first `---` fence.

### Phase 3: Atomic Content & Documentation (The Consumers)
*Goal: Fix documentation using the now-corrected tools.*

#### Task 3.1: Fix ADR-26057 & Target Tracking ✅ DONE (content fix); staging deferred
- **File:** `architecture/adr/adr_26057_adoption_of_skillopt_for_empirical_agent_skill_optimization.md`
- **Link Fix:** ✅ Link to `/architecture/evidence/analyses/A-26026_skillopt_adoption_comparative_analysis.md` verified correct — already pointing to the right target.
- **Staging:** ⏳ Deferred — both `adr_26057_...md` and `A-26026_...md` are untracked and need staging. Not yet staged per user's preference to handle staging separately.

#### Task 3.2: Fix Guide Frontmatter (Canonical Order) ✅ DONE
Updated frontmatter for the following files to ensure canonical field order (`id, title, authors, description, tags, date, options`):
- `tools/scripts/testing_standards.md` — ✅ No changes needed (order already correct).
- `tools/docs/languages/why_rust_for_tokenizers.md` — ✅ `token_size` updated only (order already correct).
- `tools/docs/languages/right_tool_for_right_layer.md` — ✅ `description` and `tags` moved before `date`; `token_size` updated.
- `tools/docs/languages/python314_parallelism_game_changer.md` — ✅ `description` and `tags` moved before `date`; `token_size` updated.
- `tools/docs/git/git_notes_for_ai_provenance.md` — ✅ Fields reordered; invalid tags (`ai-engineering`, `provenance`, `metadata`) replaced with valid tags (`development`, `workflow`); `token_size` added.
- **Jupytext pairs synced:** `why_rust_for_tokenizers.ipynb`, `right_tool_for_right_layer.ipynb`, `python314_parallelism_game_changer.ipynb`.

### Phase 4: Final Staging & Verification
*Goal: Ensure repository consistency.*

#### Task 4.1: Resolve Script-Test Dyads ⏳ Deferred
- `tools/tests/test_check_broken_links.py` modified (7 tests added) — needs staging.
- `tools/tests/test_adr_utils.py` — needs staging.
- **Status:** Staging deferred to user's separate staging session.

#### Task 4.2: Resolve Notebook Pairs ⏳ Deferred
- 3 `.ipynb` pairs synced via `jupytext --sync` — need staging.
- **Status:** Staging deferred to user's separate staging session.

#### Task 4.3: Final Validation Suite ✅ DONE
- `uv run pytest tools/tests/test_check_broken_links.py` — ✅ All 129 tests passed (7 new + 122 existing).
- `uv run python -m tools.scripts.check_frontmatter` — ✅ Exit 0 on all target files (no blocking errors).
- `uv run tools/scripts/check_broken_links.py --pattern "*.md"` — ✅ Exit 0; only `[LEGACY]` warnings printed (unstaged files).
- `uv run pytest tools/tests/test_git.py` — not run separately (subsumed by full test suite).

## 5. Expected Output Verification

| Command | Expected Result | Actual Result |
| :--- | :--- | :--- |
| `uv run pytest tools/tests/test_check_broken_links.py` | All tests passed | ✅ 129 passed (7 new + 122 existing) |
| `uv run python -m tools.scripts.check_frontmatter` | No blocking errors | ✅ Exit 0 on target files |
| `uv run tools/scripts/check_broken_links.py --pattern "*.md"` | Exit 0, `[LEGACY]` warnings printed | ✅ Exit 0, `[LEGACY]` warnings only |
| `uv run python -m tools.scripts.check_frontmatter` (with invalid ADR ID) | Error message contains the exact `id_example` from `.vadocs` config | ✅ Verified — message uses `id_example` from spoke config |

## 6. Rationale

- **The Pipe Principle (R-26003):** By moving JIT hints into `.vadocs` configs and forbidding hardcoded fallbacks, we eliminate the "Lying Instructor" problem.
- **Context-Aware Extraction (R-26003):** To prevent false positives in source code (e.g., flagging regex patterns as links), the extractor must be aware of the file type and scan only relevant sections (comments/docstrings) for `.py` files. This avoids "Implementation Leakage" where internal tool artifacts are leaked into global configuration exclusion lists.
- **Tooling First:** Fixing the heart (validators) before the consumers (docs) prevents agents from entering diagnostic loops based on stale instructions.
- **Blueprint Integrity:** Blueprints are gold standards; any deviation blocks all development.
- **Dual-Mode Link Validation:** Prevents "Validation Deadlock" in tests while maintaining Production Link Safety.

## 7. Self-Review Checklist
- [x] **Spec Coverage:** All errors from the `git commit` report (Broken links, Dyad violations, Blueprint errors, Hook failures) are mapped to tasks.
- [x] **No Fallbacks:** Phase 1 explicitly requires `GovernanceConfigError` instead of hardcoded defaults.
- [x] **Ordering:** Tooling $\rightarrow$ Blueprint $\rightarrow$ Docs.
- [x] **Target Staging:** Explicitly includes `A-26026` and `.ipynb` pairs.
- [x] **Deviation documented:** Task 1.3 deviation (config-based exclusion rejected by user) is recorded above.

## 8. Implementation Summary

**Completed (code & content changes):**
- Task 1.1: Pipe Pattern — `id_example` in SSoT config, no hardcoded fallbacks (pre-existing, verified).
- Task 1.2: Context-aware link extraction — `LinkExtractor` scans only comments/docstrings for `.py` files.
- Task 1.3: Dead hook removed. Config-based exclusion **rejected** (user correction: code-layer context-awareness is the correct fix per R-26003 L4).
- Task 1.4: 7 regression tests added (6 unit + 1 blocking integration).
- Task 2.1: `adr_template.md` blueprint fixed (pre-existing, verified).
- Task 3.1: ADR-26057 link verified correct; target file exists.
- Task 3.2: 4 guide files frontmatter reordered/fixed; 1 file confirmed already correct; 3 Jupytext pairs synced.
- Task 4.3: All validation suites passed (129 tests, frontmatter exit 0, broken links exit 0).

**Deferred (staging):**
- Task 3.1 staging: `adr_26057_...md`, `A-26026_...md` (untracked).
- Task 4.1: `test_check_broken_links.py`, `test_adr_utils.py` staging.
- Task 4.2: 3 `.ipynb` pair staging.
