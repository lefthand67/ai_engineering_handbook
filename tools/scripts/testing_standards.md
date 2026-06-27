---
title: Testing Standards for Tooling
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Testing requirements for the repo's internal quality gates and scripts.
tags:
- testing
- documentation
date: '2026-05-04'
options:
  type: guide
  birth: '2026-05-04'
  version: 1.0.0
  token_size: 1103
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

## 4. Logic vs. Plumbing (Unit vs. Integration)

A common failure mode in tooling tests is using "Set Menu" (Integration) tests to verify "A la Carte" (Unit) logic. Testing a logic branch via the CLI is brittle because it couples the core logic to the environment (filesystem, argument parsing, OS).

### The Distinction

| Approach | "A la Carte" (Unit Testing) | "Set Menu" (Integration Testing) |
| :--- | :--- | :--- |
| **Focus** | Core Logic / Brains | Plumbing / Hands |
| **Target** | Individual functions (isolated) | The CLI entry point (`main()`) |
| **Inputs** | In-memory objects, mocks | Real files, CLI flags |
| **Goal** | Exhaustive edge-case coverage | Smoke testing the "happy path" |
| **Speed** | Extremely Fast | Slow (Disk I/O) |

### The Strategy
To avoid brittleness, distribute your tests according to the Testing Pyramid:

1. **Use Unit Tests for the Heavy Lifting:** Verify all logical branches, regexes, and edge cases by calling functions directly. If you are testing "what happens if the ADR number is duplicate," do it in a unit test by passing a list of mock objects.
2. **Use Integration Tests for the Final Handshake:** Use CLI tests only to verify that the "plumbing" works—e.g., that flags are parsed correctly, files are found on disk, and the correct exit code is returned to the OS.

**Anti-Pattern:** Creating 20 different physical files on disk to test 20 different regex edge cases.
**Correct Pattern:** One unit test with `pytest.mark.parametrize` testing 20 strings in memory, and one integration test verifying the script runs on a sample file.

## 5. Adversary Testing

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
