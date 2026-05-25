# Implementation Plan: Config-Driven Ignore Architecture
**Date:** 2026-04-27
**Slug:** config_driven_ignore_architecture
**Reference Analysis:** [A-26024](/architecture/evidence/analyses/A-26024_config_driven_ignore_architecture.md)

## 1. Full Context

### Directory Tree
```text
/home/commi/Yandex.Disk/it_working/projects/soviar-systems/ai_engineering_book/
├── .vadocs/
│   ├── conf.json
│   └── (new) ignores.json
│   └── (new) ignores.schema.json
└── tools/
    └── scripts/
        └── paths.py  <-- Target for refactoring
```

### File Breakdown: `tools/scripts/paths.py`
- **Lines 1-30**: Module docstring and imports.
- **Lines 32-45**: Configuration keys (`_TOOL_SECTION`, `_CONFIG_DIR_KEY`).
- **Lines 47-53**: Internal directory conventions.
- **Lines 56-80**: `get_config_path()` implementation.
- **Lines 83-91**: `SUBTYPE_PARENT_MAP` constants.
- **Lines 94-115**: `get_external_repo_paths()` implementation.
- **Lines 118-137**: `_STATIC_EXCLUDE_DIRS` (Hardcoded set - TARGET FOR REMOVAL).
- **Lines 140-143**: `_VALIDATION_EXCLUDE_DIRS` merge logic (TARGET FOR REFACTOR).
- **Lines 146-156**: `VALIDATION_EXCLUDE_DIRS` public alias.
- **Lines 159-170**: `BROKEN_LINKS_EXCLUDE_LINK_STRINGS` constants.
- **Lines 172-173**: `BROKEN_LINKS_EXCLUDE_FILES` constants.
- **Lines 176-188**: API Key scan configs.
- **Lines 191-194**: `is_excluded()` function (TARGET FOR REFACTOR).

## 2. Cross-Reference Map

| Source File | Line(s) | Target File/Pattern | Change Type | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| `paths.py` | 127-137 | `.vadocs/ignores.json` | Data Migration | Move hardcoded strings to manifest. |
| `paths.py` | 141-143 | `_load_ignore_manifest()` | Logic Shift | Replace static set with dynamic loader. |
| `paths.py` | 192-194 | `is_excluded()` | Signature Change | Add `tool_name` and `bypass_global` params. |

## 3. Rationale for Tasks

1. **Create `.vadocs/ignores.json`**: Establish the SSoT for exclusions. Moving data out of code enables org-agnostic configuration without requiring Python commits.
2. **Create `.vadocs/ignores.schema.json`**: Prevent "junk drawer" syndrome. Ensures the `global`/`tools` split is maintained and validated by pre-commit.
3. **Refactor `paths.py` Loading Logic**: Shift from static import-time sets to a dynamic loader that resolves paths relative to the repo root.
4. **Enhance `is_excluded()`**: Implement the "Layered Filter Pattern". Adding `bypass_global` prevents the "Global Blindspot" where tools needing `.git` access are blocked.
5. **TDD Verification**: Ensure no regressions in path discovery.

## 4. Complete File Content

### `.vadocs/ignores.json`
```json
{
  "$schema": "./ignores.schema.json",
  "$comment": "Unified Ignore Manifest — SSoT for path and string exclusions across the toolkit.",
  "global": [
    ".git",
    ".ipynb_checkpoints",
    ".pytest_cache",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "build",
    "_build",
    "misc"
  ],
  "tools": {}
}
```

### `.vadocs/ignores.schema.json`
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Vadocs Ignore Manifest Schema",
  "description": "Schema for the unified ignore manifest used by the vadocs toolkit.",
  "type": "object",
  "properties": {
    "global": {
      "type": "array",
      "description": "Paths that are environmental noise and should be ignored by all tools.",
      "items": {
        "type": "string"
      }
    },
    "tools": {
      "type": "object",
      "description": "Tool-specific exclusion rules.",
      "additionalProperties": {
        "type": "object",
        "properties": {
          "files": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "Specific files to exclude for this tool."
          },
          "strings": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "Specific strings to exclude (e.g. for link validation)."
          }
        },
        "required": ["files"]
      }
    }
  },
  "required": ["global", "tools"]
}
```

## 5. Exact Edit Operations

### `tools/scripts/paths.py`

**Operation 1: Add Loader Logic**
Insert after `_VALIDATION_DIR = "validation"` (Line 53):
```python
_IGNORES_MANIFEST = "ignores.json"

def _load_ignore_manifest(repo_root: Path) -> dict:
    """Load the unified ignore manifest from .vadocs/."""
    config_path = repo_root / ".vadocs" / _IGNORES_MANIFEST
    if not config_path.exists():
        return {"global": [], "tools": {}}
    with open(config_path) as f:
        return json.load(f)
```

**Operation 2: Remove Hardcoded Set and Update Merge Logic**
Replace lines 118-143:
```python
# Directories excluded from all validation scripts (links, jupytext, ADR, etc.)
# Static entries defined here — project infrastructure (.git, caches, build outputs).
#
# External cloned repo paths (e.g., research/ai_coding_agents, research/ai_infrastructure)
# are NOT added here — they are loaded from
# .vadocs/validation/external-repos.conf.json (ADR-26046) at import time.
# The registry is the SSoT for which external directories to exclude.
# When a directory is registered/unregistered via manage_external_repos.py,
# it automatically appears/disappears from this exclusion set.
#
# If you think you need to add a research/ path here, you're doing it wrong —
# use `manage_external_repos.py register` instead.
_STATIC_EXCLUDE_DIRS = {
    ".git",
    ".ipynb_checkpoints",
    ".pytest_cache",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "build",
    "_build",
    "misc",
}

# Runtime: merge of static excludes + registry entries (SSoT for external repos).
# All registered directories from external-repos.conf.json are excluded from
# git hooks, link checks, and jupytext processing.
_VALIDATION_EXCLUDE_DIRS = _STATIC_EXCLUDE_DIRS | get_external_repo_paths(Path(__file__).resolve().parents[2])
```
With:
```python
# Resolve the ignore manifest and external repo registry at import time.
# This ensures that VALIDATION_EXCLUDE_DIRS is available as a global constant for scripts.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_MANIFEST_DATA = _load_ignore_manifest(_REPO_ROOT)
_EXTERNAL_REPOS = get_external_repo_paths(_REPO_ROOT)

# SSoT for global exclusions: Manifest Global + External Registry.
_VALIDATION_EXCLUDE_DIRS = set(_MANIFEST_DATA.get("global", [])) | _EXTERNAL_REPOS
```

**Operation 3: Refactor `is_excluded()`**
Replace lines 191-194:
```python
def is_excluded(path: str) -> bool:
    """Check if path should be excluded from jupytext processing."""
    return any(excl in path for excl in VALIDATION_EXCLUDE_DIRS)
```
With:
```python
def is_excluded(path: str, tool_name: str | None = None, bypass_global: bool = False) -> bool:
    """Check if path should be excluded using the layered filter pattern.
    
    Args:
        path: The path to check.
        tool_name: Optional tool identifier to check tool-specific ignores.
        bypass_global: If True, skips the global noise filter.
    """
    normalized_path = Path(path).as_posix()
    
    # 1. Global Noise Filter
    if not bypass_global:
        if any(excl in normalized_path for excl in VALIDATION_EXCLUDE_DIRS):
            return True
            
    # 2. Tool-Specific Filter
    if tool_name:
        tool_cfg = _MANIFEST_DATA.get("tools", {}).get(tool_name, {})
        tool_files = tool_cfg.get("files", [])
        if any(excl in normalized_path for excl in tool_files):
            return True
            
    return False
```

## 6. Commands & Expected Output

| Command | Expected Output |
| :--- | :--- |
| `uv run pytest tools/tests/test_paths.py` | `passed` (After TDD implementation) |
| `cat .vadocs/ignores.json` | Valid JSON with `global` entries. |
| `uv run python -m tools.scripts.paths` | No `ImportError` or `FileNotFoundError`. |

## 7. Self-Review Checklist
- [ ] Absolute paths are NOT used in `ignores.json`.
- [ ] `_STATIC_EXCLUDE_DIRS` is completely removed.
- [ ] `is_excluded` handles `pathlib` normalization.
- [ ] `bypass_global` logic is implemented to avoid the Global Blindspot.
- [ ] JSON Schema is committed and covers the `tools` map.
- [ ] No breaking changes to existing scripts that call `is_excluded(path)` without arguments.
