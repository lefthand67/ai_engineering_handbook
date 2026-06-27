---
id: 26002
title: Adoption of the Pre-commit Framework
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Using the `pre-commit` package to manage and orchestrate Git hook execution..
tags:
- git
date: 2026-01-31
options:
  token_size: 722
  type: adr
  version: 1.0.0
  birth: '2026-01-31'
  status: accepted
  superseded_by: null
---
# ADR-26002: Adoption of the Pre-commit Framework

## Title

Using the `pre-commit` package to manage and orchestrate Git hook execution.

## Status

Accepted

## Date

2026-01-09

## Context

While {term}`ADR-26001` established Python and OOP as the standard for writing hook logic to improve testability and maintainability, we require a standardized way to distribute and execute these hooks across the team.

Currently, a `configure_repo.sh` script exists to manually install the `pre-commit` package and set up the Git hooks. Without a formal framework:

* Managing the installation of hooks in the `.git/hooks` directory remains a manual or script-heavy process.
* Running hooks only on changed files (to ensure performance) requires custom boilerplate logic.
* Integrating third-party quality tools (like linters or formatters) alongside our custom scripts (e.g., `check_broken_links.py`, `jupytext_sync.py`) would lead to fragmented configuration.

## Decision

We will adopt the **`pre-commit` framework** as our primary hook manager.

1. **Configuration:** All hooks will be defined in a `.pre-commit-config.yaml` file at the root of the repository.
2. **Local Hooks:** Our existing Python scripts (e.g., `sync_and_verify.py`, `format_string.py`) will be integrated as `repo: local` hooks within the config.
3. **Installation:** The `configure_repo.sh` script will remain the entry point for developers, using `uv` to install the dependency and execute `pre-commit install`.

## Consequences

### Positive

* **Efficiency:** `pre-commit` only runs on staged files by default, mitigating the execution latency risks noted in {term}`ADR-26001`.
* **Consistency:** Every developer runs the exact same hook versions defined in the configuration file.
* **Simplified Onboarding:** The `configure_repo.sh` script automates the environment setup via `uv`.
* **Standardization:** Provides a unified way to combine custom OOP-based hooks with industry-standard tools.

### Negative

* **Framework Dependency:** Adds `pre-commit` as a required development dependency.
* **Configuration Overhead:** Requires maintaining the `.pre-commit-config.yaml` file in addition to the Python scripts themselves.

## Alternatives

* **Manual Bash Hooks:** Rejected in {term}`ADR-26001` due to lack of testing and maintenance debt.
* **Husky:** Rejected as it introduces a Node.js dependency into a Python-standardized environment.

## References

* {term}`ADR-26001`: Use of Python and OOP for Git Hook Scripts
* [configure_repo.py](/tools/scripts/configure_repo.py) (Current repository configuration script)
* [Pre-commit Framework Documentation](https://pre-commit.com/)

## Participants

1. Vadim Rudakov
2. Gemini (AI Thought Partner)
