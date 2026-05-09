
---
title: Script Suite Documentation Redundancy — Triad to Dyad Evolution
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Analysis of the ADR-26011 script+test+doc triad. Per-script instruction
  docs are now redundant with contract docstrings and test suites. Recommends relaxing
  the triad to a dyad (script+test) and letting existing docs age out.
tags:
- governance
- documentation
date: 2026-03-23
options:
  type: analysis
  birth: 2026-03-23
  version: 1.0.0
  token_size: 1265
  id: A-26014
  status: active
  produces: []
---
# A-26014: Script Suite Documentation Redundancy — Triad to Dyad Evolution

+++

## Problem Statement

+++

ADR-26011 mandates a three-part convention for every script: the script itself,
a test suite, and an instruction document in `tools/docs/scripts_instructions/`.
The `check_script_suite.py` pre-commit hook enforces this triad — failing the
commit if any leg is missing when the others are modified.

Since ADR-26011 was written, two developments have changed the documentation
landscape:

1. **Contract docstrings became mandatory.** Every module must open with a
   docstring covering scope, public interface, design decisions, and
   dependencies (CLAUDE.md convention). This is exactly what the instruction
   docs were created to provide.

2. **Test suites document contracts by example.** With the TDD standard and
   test quality guidelines (semantic assertions, config-driven parametrization),
   tests serve as living documentation that stays in sync by construction.

The instruction docs now duplicate information that already lives in two other
places — and unlike docstrings and tests, docs are not verified by CI to be
correct.

+++

## Key Insights

+++

### Maintenance Cost Is Non-Trivial

During the YAML→JSON config migration (step 7 of the governance plan), every
script change required a corresponding doc update. The evidence script doc
referenced `evidence.config.yaml` and `architecture.config.yaml` — both
deleted files. These stale references would have passed CI silently (docs are
not validated for semantic correctness).

The current inventory:
- 15+ instruction docs in `tools/docs/scripts_instructions/`
- Each Jupytext-paired (.md + .ipynb), doubling the file count to 30+
- Each change to a script triggers `check_script_suite`, requiring the doc
  to be staged even if no doc content changed

### Three Documentation Layers Now Exist

| Layer | Location | Verified by CI | Stays in sync |
|---|---|---|---|
| Contract docstring | In the script file | Import-time (syntax) | Yes — lives with the code |
| Test suite | `tools/tests/test_*.py` | pytest | Yes — fails if contract breaks |
| Instruction doc | `tools/docs/scripts_instructions/` | `check_script_suite` (existence only) | No — content can drift |

The instruction doc is the only layer where content correctness is not enforced.
`check_script_suite` verifies the file exists and is staged — not that it
accurately describes the script.

### Package Extraction Makes Docs Obsolete

When vadocs is extracted as a standalone package (Phase 1.3 of the roadmap),
standard Python documentation tools (sphinx, mkdocs) auto-generate API
documentation from docstrings. Per-script instruction docs:

- Are not a standard Python packaging artifact
- Won't be included in the package distribution
- Would need manual migration to a different format

Investing in strong docstrings now produces documentation that travels with
the code through extraction.

### The Triad Served Its Original Purpose

ADR-26011 was written when scripts were atomic with no shared modules, minimal
docstrings, and no test quality standards. The instruction docs filled a real
gap — they were the only place explaining how a script worked. That gap no
longer exists.

+++

## Approach Evaluation

+++

### Option A: Relax Triad to Dyad (Recommended)

Supersede ADR-26011 with a new ADR requiring only script + test. Update
`check_script_suite.py` to drop the doc requirement. Existing docs remain
but are not maintained — they age out naturally.

**Pros:**
- Removes maintenance burden immediately
- No destructive action (docs stay for reference)
- Aligns with Python packaging conventions

**Cons:**
- Engineers lose a dedicated "how to use" guide per script
- Existing docs gradually become stale

**Mitigation:** The README in `tools/docs/scripts_instructions/` can link to
the package-level guide when vadocs is extracted.

### Option B: Keep Triad, Automate Doc Generation

Generate instruction docs from docstrings + test metadata. Keep
`check_script_suite` enforcing the triad but auto-produce the doc content.

**Pros:**
- Docs stay in sync automatically
- Preserves the learning resource

**Cons:**
- Significant implementation effort for a transitional artifact
- Auto-generated docs are typically less useful than hand-written ones
- Still produces files that won't survive package extraction

### Option C: Status Quo

Keep the triad as-is, accept the maintenance cost.

**Pros:**
- No changes needed
- Instruction docs remain available for onboarding

**Cons:**
- Every script change requires a doc update
- Docs drift from reality between updates
- Growing friction as the codebase matures toward package extraction

+++

## References

+++

- ADR-26011: Formalization of Mandatory Script Suite
- CLAUDE.md: Contract docstring convention, TDD approach, test quality standards
- `tools/scripts/check_script_suite.py`: Triad enforcement hook
- `misc/plan/techdebt.md` TD-004: Script suite triad doc requirement is redundant
