# Frontmatter Structural Validation Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix `check_frontmatter.py` to correctly identify "Broken Dual-Block" patterns (missing opening fence for metadata) and dynamically resolve the document type field using the hub configuration.

**Architecture:** 
1. **Dynamic Resolution:** Shift type lookup from hard-coded `"options.type"` to a dynamic lookup based on `HUB_CONFIG["blocks"]["identity"]`.
2. **Structural Awareness:** Enhance `parse_frontmatter` to capture "broken" metadata blocks (missing opening fence) and return them as structural anomalies.
3. **Reporting Pipeline:** Integrate these anomalies into the `FrontmatterError` pipeline in `main()` and `validate_frontmatter()`, ensuring structural errors are reported explicitly.

**Tech Stack:** Python 3.13, Pytest, PyYAML.

---

### Task 1: Dynamic Type Resolution Refactor

**Files:**
- Modify: `tools/scripts/check_frontmatter.py`
- Test: `tools/tests/test_check_frontmatter.py`

- [ ] **Step 1: Implement `_get_type_field_name` helper**
Add a helper function to resolve the type field name from the hub config.

```python
def _get_type_field_name() -> str:
    """Resolve the field name used for document type from the hub config.
    
    Defaults to 'type' if not explicitly defined in a dedicated config key.
    """
    # Currently, the 'identity' block contains the 'type' field.
    identity_fields = HUB_CONFIG.get("blocks", {}).get("identity", [])
    if "type" in identity_fields:
        return "type"
    return "type" # Fallback to maintain backward compatibility
```

- [ ] **Step 2: Refactor `resolve_type` to be dynamic**

```python
def resolve_type(frontmatter: dict) -> str | None:
    """Read the type field from parsed frontmatter dynamically."""
    logger.debug(f"Resolving type from frontmatter: {frontmatter}")
    type_field = _get_type_field_name()
    options = frontmatter.get("options")
    if not isinstance(options, dict):
        logger.debug("Field 'options' is missing or not a dictionary")
        return None
    doc_type = options.get(type_field)
    if doc_type is None:
        logger.debug(f"Field 'options.{type_field}' is missing")
    return doc_type
```

- [ ] **Step 3: Update `main()` error messages to use the dynamic field name**
Replace hard-coded `"options.type"` strings with `f"options.{_get_type_field_name()}"` in the `missing_type` error messages.

- [ ] **Step 4: Run existing tests to ensure no regressions**
Run: `uv run pytest tools/tests/test_check_frontmatter.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tools/scripts/check_frontmatter.py
git commit -m "refactor: resolve document type field dynamically from hub config"
```

---

### Task 2: Structural Anomaly Detection (Broken Dual-Block)

**Files:**
- Modify: `tools/scripts/check_frontmatter.py`
- Test: `tools/tests/test_check_frontmatter.py`

- [ ] **Step 1: Update `parse_frontmatter` return signature and logic**
Modify `parse_frontmatter` to return `(merged_dict, block_count, anomalies)`. Update the split logic to detect when `parts[2]` is not empty but `parts[1]` contains `jupytext`.

```python
def parse_frontmatter(content: str, file_path: Path | None = None) -> tuple[dict | None, int, list[str]]:
    # ... (ipynb handling) ...
    blocks = []
    anomalies = []
    # ...
    if content.strip().startswith("---"):
        parts = re.split(r"^\s*---\s*$", content, flags=re.MULTILINE)
        if not parts[0].strip():
            if len(parts) > 1:
                blocks.append(parts[1].strip("\n"))
                if len(parts) > 3 and not parts[2].strip():
                    blocks.append(parts[3].strip("\n"))
                elif len(parts) > 2 and parts[2].strip():
                    # BROKEN DUAL-BLOCK: Metadata exists but opening fence is missing
                    # We still capture it so that the validator can check fields,
                    # but we flag the structural error.
                    blocks.append(parts[2].strip("\n"))
                    anomalies.append("broken_dual_block")
            # ...
    # ... (merging logic) ...
    return (merged_data if has_valid_block else None), len(blocks), anomalies
```

- [ ] **Step 2: Update `main()` to report `broken_dual_block` errors**
In the `main()` loop, iterate over `anomalies` and append `FrontmatterError` with `error_type="broken_dual_block"`.

- [ ] **Step 3: Update `validate_frontmatter` convenience wrapper**
Update the wrapper to handle the 3-tuple return and integrate anomalies into the error list.

- [ ] **Step 4: Run the failing test created earlier**
Run: `uv run pytest tools/tests/test_check_frontmatter.py::TestBrokenDualBlock`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tools/scripts/check_frontmatter.py
git commit -m "fix: detect broken Dual-Block pattern with missing separator fence"
```

---

### Task 3: Final Verification and Cleanup

**Files:**
- Test: `tools/tests/test_check_frontmatter.py`

- [ ] **Step 1: Add a test case for "Merged Blocks" to ensure it still fails correctly**
Verify that `--- \n Jupytext + Metadata \n ---` still triggers `merged_blocks`.

- [ ] **Step 2: Run full test suite**
Run: `uv run pytest tools/tests/test_check_frontmatter.py`
Expected: PASS

- [ ] **Step 3: Verify on the actual broken file**
Run: `uv run python -m tools.scripts.check_frontmatter tools/docs/website/02_self_hosted_deployment.md`
Expected: Error report starting with `broken_dual_block` instead of `missing_type`.

- [ ] **Step 4: Final Commit**

```bash
git add tools/tests/test_check_frontmatter.py
git commit -m "test: expand frontmatter structural validation cases"
```
