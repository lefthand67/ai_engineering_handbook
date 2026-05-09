
---
title: Frontmatter Validator Architecture — Config-Code Divergence and Resolution
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: SVA-grounded analysis of three approaches to hub-level frontmatter validation.
  Identifies config-code divergence as root cause. Recommends config-driven module
  with CLI entry point (Approach C).
tags:
- governance
- architecture
date: 2026-03-25
options:
  type: analysis
  birth: 2026-03-25
  version: 1.0.0
  token_size: 2467
  id: A-26015
  status: active
  sources:
  - S-26014
  produces: []
---
# A-26015: Frontmatter Validator Architecture — Config-Code Divergence and Resolution

+++

## Problem Statement

+++

The hub config (`conf.json`) defines a complete type system: 10 document types,
block composition (identity, discovery, lifecycle), a field registry of 16 fields,
and a tag vocabulary. No script enforces this type system at the hub level.

Two domain scripts — `check_adr.py` and `check_evidence.py` — independently
implement partial frontmatter validation against their spoke configs. Six of
ten types (tutorial, guide, policy, package_spec, script_instruction, service)
have zero validation.

The gap between what the config *declares* and what the scripts *enforce* grows
with every type added to the registry. This is a **config-code divergence**
problem, not a code-sharing problem.

### Duplication inventory

Both domain scripts independently implement:

- Config loading with parent_config resolution
- YAML frontmatter parsing from markdown
- Date format validation (YYYY-MM-DD regex from hub)
- Tag validation against parent config vocabulary
- Required field presence checking

The duplication exists because validation logic was written *before* the hub
config existed. ADR-26042 and the JSON migration (ADR-26054) came later. The
scripts never refactored to derive from the hub type system.

+++

## Approach Evaluation

+++

### Assumptions under test

| Assumption | Status | Falsification evidence |
|---|---|---|
| A library module reduces duplication | Plausible | Duplication moves from copy-paste to import+configure — net code decreases, but each domain script still decides which hub rules to enforce |
| All 10 types need frontmatter validation now | Unsupported | Only ADR and evidence have governed files today; other types may not have frontmatter yet |
| Domain scripts will be refactored to delegate | Plausible | Both scripts are actively maintained, but refactoring carries regression risk |
| Type discovery from directory path is reliable | Verified | Evidence config maps `artifact_types.*.directory_name`; ADR files live in `architecture/adr/`; pattern holds for all current types |
| Pre-commit hook ordering is manageable | Verified | `.pre-commit-config.yaml` already orders 10+ hooks; one more is not a scaling problem |

### SVA constraint audit (ADR-26037)

| Constraint | A (Library) | B (Standalone) | C (Module + CLI) |
|---|---|---|---|
| **C1** Automation-First | Pass | Pass | Pass |
| **C2** Vendor Portability | Pass | Pass | Pass |
| **C3** Git-Native Traceability | Pass | Pass | Pass |
| **C4** Proportional Complexity | Warning — wrapping duplication adds indirection without eliminating two-script boundary | Pass | Pass |
| **C5** Reuse Before Invention | Violation — domain scripts independently interpret hub rules; hub type system is not the driver | Pass — config drives validation | Pass — config drives validation |
| **C6** Bounded Scalability | Violation — adding a type requires a new domain script, O(n) effort | Pass — O(1) via config entry | Pass — O(1) via config entry |

**Calibration note on A/C5:** Approach A does reuse hub config, but through
domain-script interpretation rather than direct hub-driven validation. The
violation is that the hub type system is not *authoritative* — each script
decides independently which rules to enforce. This is a weaker violation than
ignoring the hub entirely, but still means hub and scripts can diverge silently.

### WRC assessment (Claude Opus 4.6 analysis)

**Approach A — Library Module**

| Component | Score | Rationale |
|---|---|---|
| E (Empirical) | 0.85 | Shared Python modules are standard deduplication |
| A (Adoption) | 0.80 | Common in pre-commit ecosystems |
| P_raw | 0.75 | Works for 2 scripts, 6 types uncovered |
| SVA penalties | −0.20 | C5 (hub not authoritative), C6 (O(n) scaling) |
| P_final | 0.55 | |

**WRC = (0.85 × 0.35) + (0.80 × 0.25) + (0.55 × 0.40) = 0.72** — PoC-only.

**Approach B — Standalone Validator**

| Component | Score | Rationale |
|---|---|---|
| E (Empirical) | 0.90 | Config-driven validators (eslint, pylint) are industry standard |
| A (Adoption) | 0.85 | Pre-commit + JSON Schema widespread |
| P_raw | 0.88 | All 10 types covered, duplication eliminated, vadocs-ready |
| SVA penalties | 0.00 | No violations |
| P_final | 0.88 | |

**WRC = (0.90 × 0.35) + (0.85 × 0.25) + (0.88 × 0.40) = 0.88** — Production-adaptable.
Held back by medium migration effort and unresolved type discovery.

**Approach C — Config-Driven Module with CLI Entry Point (generated)**

Combines B's config-driven architecture with incremental migration:

1. Importable module: `validate_frontmatter(path, repo_root) → list[Error]`
2. CLI entry point for pre-commit: `python -m tools.scripts.check_frontmatter`
3. Domain scripts import module, replacing frontmatter logic incrementally
4. CLI covers all types immediately, including 6 with no domain script

| Component | Score | Rationale |
|---|---|---|
| E (Empirical) | 0.90 | Same config-driven pattern as B |
| A (Adoption) | 0.85 | Same industry backing as B |
| P_raw | 0.92 | Incremental migration, full coverage, clean vadocs.core boundary |
| SVA penalties | 0.00 | No violations |
| P_final | 0.92 | |

**WRC = (0.90 × 0.35) + (0.85 × 0.25) + (0.92 × 0.40) = 0.90** — Production-ready.

### Methodology comparison

| Methodology | WRC | Pros | Cons | Best For |
|---|---|---|---|---|
| A: Library module | 0.72 | Low effort, minimal disruption | 6 types uncovered, C5/C6 violations | Quick dedup in small projects |
| B: Standalone validator | 0.88 | Full coverage, clean separation | Big-bang migration, type discovery upfront | Greenfield projects |
| **C: Module + CLI** ★ | **0.90** | **Incremental migration, full coverage, vadocs-ready** | **Slightly more API surface** | **Evolving projects with extraction roadmap** |

+++

## Key Insights

+++

### Root cause: config-code divergence

The duplication between domain scripts is a symptom. The root cause is that
validation logic predates the hub config. Approach A treats the symptom (shared
functions). Approach C treats the cause (hub config becomes authoritative).

### Type discovery via frontmatter

The validator parses frontmatter first (generic operation), reads `options.type`
from the result, then applies type-specific rules. No directory mapping needed —
files are self-describing. Missing or unrecognized `options.type` is itself a
validation error, not a discovery problem.

### Scope boundary: full frontmatter ownership (WRC 0.91)

A follow-up SVA analysis evaluated three scope options:

- **Hub-only** (WRC 0.67, PoC-only) — validate blocks and field registry only,
  spoke validation stays in domain scripts. C5/C6 violations: domain scripts
  still implement spoke frontmatter logic, new types need new scripts.
- **Presence yes, values no** (WRC 0.54, rejected) — check field existence from
  hub+spoke, but value validation (statuses, severity) stays in domain scripts.
  C4 violation: splits one concern across two scripts with non-obvious boundary.
- **Full frontmatter** (WRC 0.91, production-ready) — load spoke config via
  `options.type`, validate all frontmatter: presence, format, and allowed values.
  No SVA violations. Spoke configs already contain everything needed.

The scope boundary becomes:

| Concern | Owner |
|---|---|
| Frontmatter: field presence, format, allowed values | `check_frontmatter.py` |
| Structural: sections, section order, conditional sections | domain scripts |
| Naming: filename patterns, ID format | domain scripts |
| Index: generation, glossary, sectioning | `check_adr.py` |
| Auto-fix: `status_corrections` | `check_adr.py` (mutates file, not validation) |

### Incremental migration eliminates the B risk

Approach B's weakness is big-bang migration. Approach C derisks this: domain
scripts delegate to the shared module one at a time. At any point, both old
and new validation coexist. The CLI entry point provides immediate coverage
for uncovered types regardless of migration progress.

### vadocs extraction alignment

Approach C's module boundary (`validate_frontmatter()` + `resolve_type()` +
`load_config_chain()`) maps directly to `vadocs.core` in Phase 1.3. The CLI
entry point becomes `vadocs docs check-frontmatter`. Domain scripts become
thin wrappers calling `vadocs.docs.check_adr()`. The package boundary is
designed from day one.

### Pitfalls

1. **Type discovery ambiguity** — files outside recognized directories with no
   `type` field must have an explicit fallback (skip with warning, not silent).
2. **Block inheritance** — validator must enforce strict additive semantics:
   spokes can add fields to blocks, never remove.
3. **Pre-commit overlap during migration** — temporary double-validation between
   `check-frontmatter` and domain scripts must not produce conflicting errors.
4. **conf.json as policy file** — modifications to `types` or `required` change
   what passes validation; protect with review policy.

+++

## References

+++

- ADR-26036: Config File Location and Naming Conventions
- ADR-26037: SVA Constraint Framework
- ADR-26042: Common Frontmatter Standard
- ADR-26054: JSON as Governance Config Format
- TD-005: check_frontmatter.py needed for hub-level validation
- `devops_consultant.json` system prompt (Claude Opus 4.6 analysis)
