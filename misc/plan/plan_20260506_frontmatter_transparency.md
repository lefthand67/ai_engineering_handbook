# Frontmatter Validator Transparency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert frontmatter validation from a "black box" to a "glass box" by removing silent skips in `check_adr.py` and adding detailed diagnostics/logging to `check_frontmatter.py`.

**Architecture:**
1. **Explicit Failure:** Remove the `if adr.frontmatter:` guard in `check_adr.py` so that all files are passed to the validator.
2. **Graceful None-Handling:** Update `check_frontmatter.py` to treat `None` as a valid input representing missing frontmatter, returning a formal `missing_frontmatter` error.
3. **Diagnostic Trace:** Add DEBUG logging for the YAML parsing process and structural warnings for non-standard patterns (e.g., empty blocks).
4. **Guided Correction:** Append "DIAGNOSTIC TIPS" to common validation errors to help agents resolve parser-related failures.

**Tech Stack:** Python, Pytest, PyYAML.

---

### Task 1: Handle Null Frontmatter in `check_frontmatter.py`

**Files:**
- Modify: `tools/scripts/check_frontmatter.py`
- Test: `tools/tests/test_check_frontmatter.py`

- [ ] **Step 1: Write failing test for `validate_parsed_frontmatter(None)`**

```python
def test_validate_parsed_frontmatter_handles_none(frontmatter_env):
    file_path = frontmatter_env / "missing.md"
    file_path.write_text("# No frontmatter here", encoding="utf-8")
    
    # Call with None to simulate parse_frontmatter failure
    errors = _module.validate_parsed_frontmatter(None, file_path, frontmatter_env)
    
    assert len(errors) == 1
    assert errors[0].error_type == "missing_frontmatter"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tools/tests/test_check_frontmatter.py`
Expected: FAIL (likely `AttributeError` in `resolve_type`)

- [ ] **Step 3: Implement `None` handling in `resolve_type` and `validate_parsed_frontmatter`**

In `resolve_type(frontmatter: dict | None)`:
```python
if frontmatter is None:
    return None
```

In `validate_parsed_frontmatter(frontmatter, ...)`:
```python
if frontmatter is None:
    return [
        FrontmatterError(
            file_path=file_path,
            error_type="missing_frontmatter",
            field=None,
            message="file has governed extension but no YAML frontmatter present...",
            config_source=f"{HUB_CONFIG_REL} → governed_extensions",
        )
    ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tools/tests/test_check_frontmatter.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tools/scripts/check_frontmatter.py tools/tests/test_check_frontmatter.py
git commit -m "fix: handle None frontmatter in validator to prevent silent skips"
```

### Task 2: Implement Parser Transparency (Logging & Warnings)

**Files:**
- Modify: `tools/scripts/check_frontmatter.py`
- Test: `tools/tests/test_check_frontmatter.py`

- [ ] **Step 1: Write test for empty YAML block warning**

```python
def test_parse_frontmatter_warns_on_empty_block(caplog):
    content = "---\n---\n\n# Body"
    with caplog.at_level("WARNING"):
        _module.parse_frontmatter(content, file_path=Path("empty.md"))
    assert "contains an empty YAML block" in caplog.text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tools/tests/test_check_frontmatter.py`
Expected: FAIL (no warning emitted)

- [ ] **Step 3: Implement DEBUG logging and structural warnings in `parse_frontmatter`**

Add logs:
- `logger.debug(f"Found {len(blocks)} YAML blocks in {file_path}")`
- Inside loop: `logger.debug(f"Block {i} parsed successfully as {data}")` or `logger.debug(f"Block {i} failed to parse: {e}")`
- At end: `logger.debug(f"Final resolved frontmatter: {merged_data}")`

Add warning:
```python
if not block_text.strip():
    logger.warning(f"{file_path} contains an empty YAML block at the top. This is non-standard.")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tools/tests/test_check_frontmatter.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tools/scripts/check_frontmatter.py tools/tests/test_check_frontmatter.py
git commit -m "perf: add parser transparency via debug logs and structural warnings"
```

### Task 3: Add Diagnostic Tips to Errors

**Files:**
- Modify: `tools/scripts/check_frontmatter.py`

- [ ] **Step 1: Implement diagnostic tips for `missing_type` and `missing_field`**

Modify `validate_parsed_frontmatter`:
For `missing_type` error:
`message = "frontmatter present but missing required 'options.type'... \nDIAGNOSTIC TIP: If the field is visibly present, check for double '---' delimiters or leading whitespace at the very top of the document."`

For `missing_field` error:
`message = f"missing required field '{field}' \nDIAGNOSTIC TIP: Check for YAML syntax errors (e.g. unquoted colons) in the block containing this field."`

- [ ] **Step 2: Commit**

```bash
git add tools/scripts/check_frontmatter.py
git commit -m "docs: add diagnostic tips to frontmatter validation errors"
```

### Task 4: Remove Guards in `check_adr.py`

**Files:**
- Modify: `tools/scripts/check_adr.py`

- [ ] **Step 1: Remove `if adr.frontmatter:` guard**

Find:
```python
        # Generic frontmatter delegation
        if adr.frontmatter:
            fm_errs = check_frontmatter.validate_parsed_frontmatter(...)
```

Replace with:
```python
        # Generic frontmatter delegation
        fm_errs = check_frontmatter.validate_parsed_frontmatter(
            adr.frontmatter, adr.path, detect_repo_root(), content=adr.content
        )
```

- [ ] **Step 2: Verify with an ADR missing frontmatter**

Create temp file `architecture/adr/adr_00000_test.md` with no frontmatter.
Run: `uv run tools/scripts/check_adr.py`
Expected: Error `ADR 0 [missing_frontmatter]: ...`

- [ ] **Step 3: Commit**

```bash
git add tools/scripts/check_adr.py
git commit -m "fix: remove silent skip of frontmatter validation in check_adr.py"
```

### Task 5: Final Verification & Coverage

**Files:**
- Test: `tools/tests/test_check_frontmatter.py`
- Test: `tools/tests/test_check_adr.py`

- [ ] **Step 1: Run full frontmatter test suite with coverage**

Run: `uv run pytest tools/tests/test_check_frontmatter.py --cov=tools.scripts.check_frontmatter --cov-report=term-missing`
Expected: All tests PASS, coverage for new logic (None handling, logging) is 100%.

- [ ] **Step 2: Run full ADR test suite with coverage**

Run: `uv run pytest tools/tests/test_check_adr.py --cov=tools.scripts.check_adr --cov-report=term-missing`
Expected: All tests PASS, coverage for the removal of the guard is verified.

- [ ] **Step 3: Final Commit**

```bash
git commit -m "test: verify frontmatter transparency with full coverage"
```
