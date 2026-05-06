
---
title: Formalization of the Mandatory Script Suite Workflow
date: 2026-01-31
tags:
- governance
- development
options:
  token_size: 1151
  id: 26011
  status: superseded
  superseded_by: ADR-26045
  type: adr
  version: 1.0.0
  birth: '2026-01-31'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Mandating a synchronized 1:1:1 ratio for Scripts, Tests, and Documentation..
---
# ADR-26011: Formalization of the Mandatory Script Suite Workflow

## Title

Mandating a synchronized 1:1:1 ratio for Scripts, Tests, and Documentation.

## Status

Superseded by {term}`ADR-26045`

## Supersession Rationale

The documentation requirement (third leg of the triad) is replaced by contract docstrings governed ecosystem-wide by {term}`ADR-26045`. Evidence in [A-26014](/architecture/evidence/analyses/A-26014_script_suite_doc_redundancy.md) showed that per-script instruction docs drifted silently during config migrations, duplicated content already in docstrings and tests, and created co-staging friction. The script + test pairing remains enforced as an operational convention.

## Date

2026-01-26

## Context

As the repository grows, documentation drift and untested utility scripts create significant maintenance debt. Developers often follow outdated instructions or encounter broken scripts that lack corresponding test cases.

Current architectural decisions established Python as the standard for hooks {term}`ADR-26001` and `pre-commit` as the orchestration framework {term}`ADR-26002`. We now require a formal mechanism to ensure that no script is introduced or modified without its accompanying verification and instructional artifacts.

Here we are decoupling the **Script Suite Concept**—the mandatory 1:1:1 ratio of Code:Test:Doc—from the Tiered Commit Validation logic {term}`ADR-26003`. This ADR focuses exclusively on the structural integrity of the `tools/` directory and the automation required to enforce it.

The challenge identified is **Knowledge Fragmentation**. When a script is updated but its test or documentation is not, the repository's "Smallest Viable Architecture" (SVA) degrades into technical debt. By formalizing the "Suite" as a single atomic unit, we move from passive documentation to **Active Specification Enforcement**.

## Decision

We will enforce the **Script Suite** as a mandatory unit of development. A "Suite" is defined by the existence of three interconnected files following a strict naming convention:

1. **The Script:** Located in `tools/scripts/<name>.py`.
2. **The Test:** Located in `tools/tests/test_<name>.py`.
3. **The Documentation:** Located in `tools/docs/scripts_instructions/<name>_py_script.md` and its `.ipynb` pair.

**Enforcement Mechanisms:**

* **Local Enforcement:** A custom [Python script](/tools/scripts/check_script_suite.py) will run via `pre-commit`. It will fail the commit if a script is staged without its corresponding test and documentation, or if a script is modified without the documentation also being staged.
* **CI/CD Enforcement:** The same validation will run as a "Hard Gate" in the GitHub Actions `quality.yml` workflow to ensure remote state integrity.

## Consequences

### Positive

* **Zero-Drift Documentation:** Documentation is kept synchronized with code changes through mandatory co-staging.
* **Reliability:** Every utility script in the repository is guaranteed to have an associated test suite.
* **Reduced Cognitive Load:** Engineers can rely on the fact that documentation exists and is accurate for every tool in `tools/scripts/`.

### Negative

* **Development Friction:** Small, one-off utility scripts now require the overhead of a test and a doc file. **Mitigation:** The naming convention allows for the exclusion of clearly marked "experimental" or "temp" directories if necessary.
* **Latency:** The `pre-commit` hook adds a check for file existence/staging status. **Mitigation:** Python execution logic will be kept lean to stay within the 100-200ms window established in {term}`ADR-26001`.
* **"Documentation Quality Decay."** While the system enforces the *existence* of a documentation file, it cannot easily enforce its *meaningfulness*. You may end up with "empty" documentation files just to satisfy the hook. * **Mitigation:** Incorporate a minimum word count or a template-matching check (e.g., must contain `# Purpose` and `# Usage` headers) within [check_script_suite.py](/tools/scripts/check_script_suite.py).

## Alternatives

* **Manual PR Checklists:** Rejected as they are prone to human error and do not provide immediate feedback during the commit cycle.
* **Docstring-only Documentation:** Rejected because complex scripts require the rich formatting and interactive capabilities provided by MyST/Jupyter documentation.

## References

* {term}`ADR-26001`: Use of Python and OOP for Git Hook Scripts
* {term}`ADR-26002`: Adoption of the Pre-commit Framework
* [tools/docs/scripts_instructions/README.ipynb](/tools/docs/scripts_instructions/README.ipynb): Section on "Script and its Suite"

## Participants

1. Vadim Rudakov
2. Gemini (Senior DevOps Systems Architect)
