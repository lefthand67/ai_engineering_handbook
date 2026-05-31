---
name: cli-logging-migration
description: Approach for transitioning CLI tools from print-based diagnostics to the logging module while preserving UX and updating tests.
source: auto-skill
extracted_at: '2025-01-24T12:00:00Z'
---

# CLI Logging Migration

When upgrading a CLI tool from using `print` for all output to the `logging` module, follow this pattern to maintain a professional user experience and robust test suite.

## 1. Strategic Output Separation

Do not replace all `print` statements with `logging`. Distinguish between **User Interface (UI) Output** and **Diagnostic Output**.

- **UI Output (Keep as `print`)**: 
  - Final results (e.g., "✅ All links are valid!").
  - Errors that are critical to the user's immediate action.
  - Summary tables or lists.
  - *Rationale*: `logging` often includes timestamps, levels, and logger names which clutter the primary UX of a CLI tool.
- **Diagnostic Output (Move to `logging`)**:
  - "Checking file X..."
  - "Skipping directory Y because of rule Z."
  - Internal state transitions.
  - *Rationale*: These are useful for debugging but should be hidden by default.

## 2. Implementation Pattern

### Logger Configuration
Initialize a module-level logger and configure it in the main entry point.

```python
import logging
logger = logging.getLogger(__name__)

class ToolCLI:
    def run(self, argv=None):
        args = self.parser.parse_args(argv)
        
        # Basic config: only show messages, no timestamps/levels for CLI feel
        logging.basicConfig(level=logging.INFO, format="%(message)s")
        
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        # ...
```

### Mapping Verbosity
- **`logger.info()`**: General progress (e.g., "Scanning directory...").
- **`logger.debug()`**: Detailed diagnostics (e.g., "File X matches pattern Y, including in scan").
- **`logger.warning()`**: Non-fatal anomalies.
- **`logger.error()`**: Internal failures.

## 3. Testing Logging with Pytest

When you move output from `print` to `logging`, tests using `capsys` will fail because logs do not necessarily go to stdout.

### Replace `capsys` with `caplog`
Use the `caplog` fixture to capture and verify log messages.

```python
def test_verbose_output(tmp_path, caplog):
    # CRITICAL: Set the level in the test, otherwise DEBUG logs are ignored
    caplog.set_level(logging.DEBUG)
    
    # ... run the tool with --verbose ...
    
    # Assert on substrings to avoid brittle tests
    assert "Checking file" in caplog.text
    assert "SKIP Excluded Link" in caplog.text
```

### Non-Brittle Assertions
Avoid asserting on the exact string of a log message. Log formats change frequently. Use `in` to check for key identifiers or keywords.
- **Bad**: `assert caplog.text == "DEBUG:root:Checking file: /path/to/file\n"`
- **Good**: `assert "Checking file" in caplog.text`
