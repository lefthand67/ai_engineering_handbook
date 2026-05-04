# Tooling Scripts

This directory contains the internal utilities, validation scripts, and quality gates used to maintain the integrity of the AI Engineering Book.

## 🛠️ Toolkit Overview

The scripts in this directory are designed to automate the enforcement of repository standards. They are integrated into the development workflow via pre-commit hooks and CI/CD pipelines.

### Core Standards
To ensure consistency, all tools in this directory must adhere to the following standards:
- [Validation Standards](./validation_standards.md) — Rules for config-driven logic and agent-actionable reporting.
- [Testing Standards](./testing_standards.md) — Rules for TDD, Adversary testing, and the Script-Test Dyad.

## 🚀 Usage

Most scripts can be run via `uv run`:

```bash
# Example: Validate all ADRs
uv run tools/scripts/check_adr.py --fix

# Example: Check for broken links
uv run tools/scripts/check_broken_links.py --pattern "*.md"
```

## 📝 Development Guidelines

When adding a new script or modifying an existing one:
1. **Read the Standards:** Review `validation_standards.md` and `testing_standards.md`.
2. **TDD First:** Create a corresponding test in `tools/tests/test_<script_name>.py` before writing implementation code.
3. **Config-First:** Define your validation rules in `.vadocs/` before implementing the logic in Python.
4. **Verify:** Run the test suite to ensure no regressions:
   ```bash
   uv run pytest tools/tests/test_<script_name>.py
   ```
