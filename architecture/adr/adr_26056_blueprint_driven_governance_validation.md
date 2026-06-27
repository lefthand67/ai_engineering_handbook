---
id: 26056
title: Blueprint-Driven Governance Validation
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Ensuring templates and gold-standard files remain consistent with the
  .vadocs SSoT by enforcing a mandatory validation cycle.
tags:
- governance
- documentation
date: 2026-02-07
options:
  status: proposed
  superseded_by: null
  type: adr
  version: 1.0.0
  birth: '2026-02-07'
  token_size: 788
---
# ADR-26056: Blueprint-Driven Governance Validation

## Title

Blueprint-Driven Governance Validation

## Status

Proposed

## Date
2026-02-07

## Context

The repository uses a hub-and-spoke configuration system (`.vadocs/`) to enforce frontmatter standards (ADR-26042). Validation is primarily triggered by pre-commit hooks, which operate on a "changed-files-only" basis to maintain performance.

This creates a critical vulnerability for **templates** (e.g., `adr_template.md`). Because templates are modified infrequently, they may drift from the current SSoT rules defined in `.vadocs/conf.json` if the rules change but the template is not updated. This results in "drift propagation": every new artifact created from a broken template is born non-compliant, creating a large volume of technical debt.

## Decision

We will implement a "Blueprint" mechanism to ensure that gold-standard files are always validated against the current SSoT, regardless of whether they were modified in the current commit.

1. **Blueprint Registry**: The `.vadocs/conf.json` hub configuration will include a `blueprints` list containing relative paths to files that serve as templates or authoritative examples.
2. **Mandatory Validation**: Validation scripts (e.g., `check_frontmatter.py`) must be updated to:
   - Read the `blueprints` list from the hub config.
   - Append these files to the active validation set for every execution.
   - Treat any violation found in a blueprint file as a blocking error (exit code 1), preventing the commit.
3. **Zero-Drift Invariant**: The blueprint validation ensures that the transition from "Config Change" $\rightarrow$ "Template Update" $\rightarrow$ "New File Creation" is atomic and verified.

## Consequences

### Positive

* **Guaranteed Template Integrity**: Blueprints are forced to evolve in lock-step with the governance rules.
* **Prevention of Error Propagation**: Eliminates the scenario where agents or humans create dozens of non-compliant files because they relied on a stale template.
* **Centralized Definition**: Adding a new template to the governance loop only requires adding a string to a JSON list.

### Negative

* **Increased Validation Latency**: A few additional files are read and parsed per commit. Given the small number of blueprints, this impact is negligible (milliseconds).
* **Stricter Commits**: A commit that only changes a config file may now fail if it makes existing blueprints non-compliant, forcing the author to fix the templates immediately.

## Alternatives

* **Manual Template Audits**: Rejected as it relies on human memory and is prone to failure.
* **Separate Template-Only Hook**: Rejected as it duplicates logic and configuration; it is cleaner to integrate the blueprint list into the existing validation script's logic.

## References

* {term}`ADR-26036`: Config File Location and Naming Conventions
* {term}`ADR-26042`: Common Frontmatter Standard
* {term}`ADR-26054`: JSON as Governance Config Format

## Participants

1. Vadim Rudakov
2. Senior AI Architect (Consultant)
