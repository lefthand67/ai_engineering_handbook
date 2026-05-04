# Instructional Validation Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transition validation scripts from boolean "Pass/Fail" detectors to "Just-In-Time Instructors" that provide actionable fix guidance to agents.

**Architecture:**
We will centralize the ArchTag vocabulary in `pyproject.toml` to eliminate guessing. `validate_commit_msg.py` will be refactored to enforce strict positioning (Line 1 of body) and value validation against the registry, replacing generic errors with instructional messages that explain the "Why", "How", and "Suggestions".

**Tech Stack:** Python, Pytest, TOML (`pyproject.toml`).

---

### Task 1: Establish Governed Vocabulary

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add `archtag-valid-values` to `[tool.commit-convention]`**

```toml
# In pyproject.toml under [tool.commit-convention]
archtag-valid-values = [
    "TECHDEBT-PAYMENT", 
    "PERF-OPTIMIZATION", 
    "REFACTOR-MIGRATION", 
    "DEPRECATION-PLANNED", 
    "BREAKING-CHANGE",
    "ADR-.*"
]
```

- [ ] **Step 2: Commit**

```bash
git add pyproject.toml
git commit -m "chore: establish governed vocabulary for ArchTags"
```

### Task 2: Refactor `validate_commit_msg.py` for Instructional Feedback

**Files:**
- Modify: `tools/scripts/validate_commit_msg.py`
- Test: `tools/tests/test_validate_commit_msg.py`

- [ ] **Step 1: Update config loading to include `archtag-valid-values`**

Modify the config extraction to load `ARCHTAG_VALID_VALUES` from `_CONFIG`.

- [ ] **Step 2: Refactor `validate_archtag` for strict position**

Change the logic from `any(...)` to specifically check `body_lines[0]`. If the tag is found later, generate a "Position Error".

```python
# Expected logic:
if not body_lines:
    return [f"ArchTag required for {reason} — body is empty"]
if not _ARCHTAG_RE.match(body_lines[0]):
    # Check if it exists elsewhere to provide a "Move it" hint
    if any(_ARCHTAG_RE.match(line) for line in body_lines[1:]):
        return [f"ArchTag Position: ArchTag found in body, but it MUST be the first line. Move it to the top."]
    return [f"ArchTag required for {reason} — add 'ArchTag:TAG-NAME' as the first line of the body."]
```

- [ ] **Step 3: Implement Vocabulary Validation**

Extract the tag value from the first line and validate it against `ARCHTAG_VALID_VALUES` (supporting regex for `ADR-.*`).

```python
# Expected logic:
tag_value = body_lines[0].split(":", 1)[1].strip()
if not any(re.match(pattern, tag_value) for pattern in ARCHTAG_VALID_VALUES):
    return [f"Invalid ArchTag: '{tag_value}' is not recognized. Valid options: {', '.join(ARCHTAG_VALID_VALUES)}. If this is a new decision, create an ADR first."]
```

- [ ] **Step 4: Integrate Rationale into Error Messages**

Ensure error messages follow the contract: `file_path:field — <Instructional Message> [config_source]`.

- [ ] **Step 5: Run tests to verify failures**

Run: `uv run pytest tools/tests/test_validate_commit_msg.py`
Expected: FAIL (since existing tests expect old error formats).

- [ ] **Step 6: Commit**

```bash
git add tools/scripts/validate_commit_msg.py
git commit -m "refactor: transform ArchTag validation into instructional feedback"
```

### Task 3: Update Test Suite for Instructional Contracts

**Files:**
- Modify: `tools/tests/test_validate_commit_msg.py`

- [ ] **Step 1: Update `test_refactor_without_archtag_fails`**

Update assertions to check for the "Rationale" and "Suggestions" in the error message.

- [ ] **Step 2: Add `test_archtag_wrong_position_fails`**

Test a commit where the ArchTag is on line 2 and verify the "Move it to the top" instruction.

- [ ] **Step 3: Add `test_archtag_invalid_value_fails`**

Test an invented tag (e.g., `ArchTag:MAGIC-FIX`) and verify the valid options list is returned.

- [ ] **Step 4: Run tests to verify PASS**

Run: `uv run pytest tools/tests/test_validate_commit_msg.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tools/tests/test_validate_commit_msg.py
git commit -m "test: update commit validation tests to verify instructional feedback"
```

### Task 4: Synchronize Human Documentation with SSoT

**Files:**
- Modify: `tools/docs/git/01_production_git_workflow_standards.md`
- Modify: `misc/plan/techdebt.md`

- [ ] **Step 1: Update ArchTag table in Workflow Standards**

Ensure the list of tags in `01_production_git_workflow_standards.md` exactly matches the `archtag-valid-values` in `pyproject.toml`. Add the "Authoritative Source" note:
*"The authoritative list of allowed ArchTags is governed by `pyproject.toml [tool.commit-convention].archtag-valid-values`. This table provides the definitions and usage guidelines for those tags."*

- [ ] **Step 2: Clean up fragmented references in `techdebt.md`**

Remove manual lists of "example tags" from TD-008 and replace them with a reference to the `pyproject.toml` SSoT.

- [ ] **Step 3: Commit**

```bash
git add tools/docs/git/01_production_git_workflow_standards.md misc/plan/techdebt.md
git commit -m "docs: synchronize ArchTag documentation with pyproject.toml SSoT"
```

---

## Self-Review Checklist
- [ ] **Spec coverage:** Does it handle missing tags, wrong position, and invalid values? ✅
- [ ] **Documentation Sync:** Does it align human docs with the machine-readable SSoT? ✅
- [ ] **Placeholder scan:** Are all code snippets complete? ✅
- [ ] **Type consistency:** Does `ARCHTAG_VALID_VALUES` match `pyproject.toml` key? ✅
