---
name: propagate-utility-api-changes
description: Strategy for updating shared utility functions in a tool-heavy repository without introducing regressions.
source: auto-skill
extracted_at: '2026-05-31T10:00:00Z'
---

# Propagating API Changes in Shared Utilities

In repositories where multiple validation scripts and helper libraries share core utility functions (e.g., `parse_frontmatter` in `tools/scripts/check_frontmatter.py`), changing a function's return signature or required arguments can cause silent failures or runtime `TypeError`/`ValueError`s across the entire tool suite.

## The Risk: The Ripple Effect
A "local" fix in one script may break distant scripts that import the same utility. If these downstream scripts aren't exercised by the current test run, regressions may only be discovered in CI or production.

## The Propagation Protocol

### 1. Impact Analysis (Global Search)
Before committing a signature change, perform a global search for all occurrences of the function name to identify every caller.
```bash
grep -r "function_name" tools/scripts/
grep -r "function_name" tools/tests/
```

### 2. Systematic Update Order
Update callers in the following priority to ensure stability:
1. **The Utility Itself**: Implement the new signature and update its direct tests.
2. **Helper Libraries**: Update shared utility modules (e.g., `adr_utils.py`) that wrap the core function.
3. **Domain Scripts**: Update the main scripts (e.g., `check_adr.py`, `check_evidence.py`) that use the utility.
4. **Test Suites**: Update all tests that mock the function or call it directly.

### 3. Safe Unpacking Patterns
When changing a return value to a tuple (e.g., from `dict` to `(dict, int, list)`), use the "splat" operator in callers to maintain backward compatibility or easily migrate:
- **Old**: `result = func()`
- **New**: `result, *rest = func()` 
This allows the caller to access the primary result while ignoring new metadata without crashing on unpacking errors.

### 4. Verification Loop
Do not rely on the primary script's tests. Execute a broad verification:
1. **Targeted Tests**: Run tests for every modified file.
2. **Downstream Tests**: Run tests for all scripts identified in the global search.
3. **Coverage Check**: Run pytest with coverage on all affected scripts to ensure new logical branches (like anomaly detection) are actually exercised.
   ```bash
   uv run pytest tools/tests/test_A.py tools/tests/test_B.py --cov=tools.scripts.A --cov=tools.scripts.B --cov-report=term-missing
   ```

## Common Pitfalls
- **Mock Mismatch**: Forgetting to update `monkeypatch` or `unittest.mock` return values in tests, leading to `AttributeError` when the test expects a dict but receives a tuple.
- **Partial Migration**: Updating the script but not the helper library it uses, causing the script to fail during runtime.
- **Unpacking Errors**: Using `a, b = func()` when the function now returns three values, causing `ValueError: too many values to unpack`.
