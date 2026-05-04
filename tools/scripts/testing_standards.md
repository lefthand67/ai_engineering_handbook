---
title: Testing Standards for Tooling
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: '2026-05-04'
description: Testing requirements for the repo's internal quality gates and scripts.
tags:
- testing
- documentation
options:
  type: guide
  birth: '2026-05-04'
  version: 1.0.0
  token_size: 725
---
# Testing Standards for Tooling

Validation scripts are the "gatekeepers" of the repository. A bug in a quality gate can block the entire development pipeline or allow corrupt data into production. Therefore, tooling tests must be more rigorous than standard feature tests.

## 1. The Script-Test Dyad

Every validation script must have a corresponding test file.
- **Script:** `tools/scripts/<name>.py`
- **Test:** `tools/tests/test_<name>.py`

A script without a test is considered incomplete and will be rejected during code review. Pre-commit hooks enforce this dyad: modifying a script requires staging the corresponding test.

## 2. TDD Workflow (Red $\rightarrow$ Green $\rightarrow$ Refactor)

Implementation must follow a strict Test-Driven Development cycle:
1. **Red:** Write a failing test that captures a specific validation requirement (e.g., "missing status field should cause exit 1").
2. **Green:** Implement the minimum amount of code to make that test pass.
3. **Refactor:** Clean up the implementation while ensuring the test remains green.

## 3. Non-Brittle Assertions

Avoid testing specific wording or formatting of error messages, as these change frequently. Instead, test the **contract**.

| Bad (Brittle) | Good (Contract-Based) |
| :--- | :--- |
| `assert "Field 'status' is missing" in output` | `assert exit_code == 1` |
| `assert len(output.split('\\n')) == 5` | `assert len(errors) > 0` |
| `assert "Error: /path/to/file.md" in output` | `assert any(err.file_path == expected_path for err in errors)` |

**Rule:** Verify the side effect (exit code) and the semantic result (which file failed), not the literal string.

## 4. Adversary Testing

To ensure robustness, scripts must be subjected to "adversary" test cases. Do not only test "happy paths" or "expected failures."

Test the following boundary conditions:
- **Malformed Input:** Files with invalid YAML, truncated JSON, or mixed encoding.
- **Empty States:** Completely empty files, files with only whitespace, or empty frontmatter blocks.
- **Edge Cases:** Files with names that look like config files but aren't, or files with extreme paths (long names, special characters).
- **Config Failures:** Missing hub/spoke config files or configs with invalid schemas.

## 5. Test Implementation Details

- **Parametrization:** Use `pytest.mark.parametrize` to test a wide variety of inputs through a single test logic.
- **Dynamic Data:** Generate valid frontmatter and filenames dynamically using the same config objects the script uses. Avoid hardcoding "valid" examples in tests.
- **Single Module Import:** Import the script module once at the top (e.g., `import tools.scripts.check_evidence as _module`) and access functions via `_module.func()`. This simplifies updates if the package is renamed.
