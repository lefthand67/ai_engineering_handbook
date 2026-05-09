
---
title: ADR Index Restructuring — Two-Level Sectioning and Tag Vocabulary Audit
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: 'Analysis of ADR index navigation problems and tag vocabulary effectiveness.
  Proposes two-level index (status × primary tag), identifies `architecture` tag as
  tautological on ADRs, and establishes first-tag-is-primary convention. Data-driven:
  quantitative tag distribution across 44 ADRs.'
tags:
- governance
- documentation
date: 2026-03-23
options:
  type: analysis
  birth: 2026-03-23
  version: 1.0.0
  token_size: 1461
  id: A-26012
  status: active
  produces: []
---
# A-26012: ADR Index Restructuring — Two-Level Sectioning and Tag Vocabulary Audit

+++

## Problem Statement

+++

The ADR index (`architecture/adr_index.md`) uses three status-based sections: Active
Architecture, Evolutionary Proposals, Historical Context. As the ADR count grows (44 at
time of writing), the Active Architecture section becomes a flat list of 22 entries —
difficult to scan and navigate.

Additionally, the `architecture` tag appears on 33 of 44 ADRs, making it effectively
meaningless as a discriminator. Every ADR is an architectural decision by definition,
so tagging it `architecture` is tautological.

This analysis evaluates index restructuring options and audits the tag vocabulary to
support meaningful sectioning.

+++

## Key Insights

+++

### Tag distribution data (2026-03-23, 44 ADRs)

Individual tag frequency:

| Tag | Count | % of ADRs |
|-----|-------|-----------|
| architecture | 33 | 75% |
| governance | 16 | 36% |
| workflow | 13 | 30% |
| context_management | 13 | 30% |
| documentation | 13 | 30% |
| git | 5 | 11% |
| model | 5 | 11% |
| devops | 4 | 9% |
| ci | 2 | 5% |

- 36/44 ADRs have multiple tags; 8 have a single tag
- 7 ADRs have `[architecture]` as their only tag — they need re-tagging

### The `architecture` tag problem

The tag vocabulary in `.vadocs/conf.yaml` defines `architecture` as *"Technical design
decisions — system structure, component boundaries, patterns."* This is a valid narrow
definition, but it was applied broadly as a default tag. On ADRs specifically, the tag
is tautological — the document type itself implies architectural scope.

**Removing `architecture` from the first-tag position** produces meaningful section
distribution:

| Primary tag | Active | Proposed | Rejected | Superseded |
|-------------|--------|----------|----------|------------|
| governance | 7 | 4 | 1 | 2 |
| context_management | 1 | 4 | 1 | — |
| model | 2 | — | — | 3 |
| workflow | 2 | 1 | 2 | — |
| documentation | 2 | — | — | — |
| devops | 2 | — | — | — |
| git | 2 | — | 1 | — |
| ci | — | — | — | — |

7 ADRs that had only `[architecture]` need re-tagging:

| ADR | Title | Proposed primary tag |
|-----|-------|---------------------|
| 26009 | Ansible for Config Management | devops |
| 26010 | Molecule for Ansible Validation | testing |
| 26011 | Mandatory Script Suite Workflow | governance |
| 26012 | Extraction of Documentation Validation Engine | governance |
| 26013 | Just-in-Time Prompt Transformation | workflow |
| 26014 | Semantic Notebook Pairing Strategy | documentation |
| 26015 | Mandatory Sync-Guard & Diff Suppression | ci |

### Index restructuring approaches evaluated

**Approach A: Single mandatory `category` field**
- New frontmatter field for index grouping, tags remain multi-valued for search.
- Rejected: adds a field that semantically overlaps with tags. Extra maintenance
  burden without proportional benefit.

**Approach B: Ordered tags — first tag is primary** (selected)
- First tag in the list determines the index sub-section. No schema change.
- Convention must be documented in `adr_index.md` and enforced by `check_adr.py`.
- Trade-off: fragile if tags are reordered carelessly — mitigated by validation
  script warning when primary tag changes.

**Approach C: Tag-based sub-grouping within status sections**
- Subsumes B: uses first-tag convention within the existing status-based structure.
- Selected as the implementation: **two-level index** (status → tag sub-sections).

### Two-level index structure (status × primary tag)

```
## Active Architecture
### governance (N)
ADR-NNNNN: Title
...

### model (N)
...

## Evolutionary Proposals
### governance (N)
...

## Rejected
### workflow (N)
...

## Superseded
### model (N)
...
```

- Top-level: status sections (Active, Proposals, Rejected, Superseded, Deprecated).
  Historical Context split into Rejected and Superseded — different navigational
  intent (why rejected vs. what replaced it).
- Sub-level: primary tag groups within each status section.
- Empty sections/sub-sections are omitted from generated output.
- Each sub-section is a MyST `{glossary}` block (preserving `{term}` cross-references).

### `architecture` tag disposition

**Decision: keep in vocabulary, remove as default, re-tag ADRs.**

The tag retains its narrow definition (*system structure, component boundaries, patterns*)
but should only appear on ADRs that are genuinely about structural design — e.g.,
ADR-26020 (hub-and-spoke), ADR-26043 (package boundary). Most ADRs will drop it or
move it to a secondary position.

The tag remains valid for non-ADR artifacts (analyses, retrospectives) where the
document type doesn't imply architectural scope.

+++

## References

+++

- `.vadocs/conf.yaml` — tag vocabulary with descriptions
- `.vadocs/types/adr.conf.yaml` — ADR sections/status configuration (target path)
- `tools/scripts/check_adr.py` — index generation logic
- `architecture/adr_index.md` — current index structure
- [A-26010: Config File Distribution Patterns](/architecture/evidence/analyses/A-26010_config_file_distribution_patterns.md) — `.vadocs/` directory structure decision
