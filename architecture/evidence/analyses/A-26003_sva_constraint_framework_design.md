
---
title: SVA Constraint Framework Design
date: 2026-03-02
tags:
- architecture
- governance
options:
  token_size: 2902
  id: A-26003
  status: active
  sources: []
  produces:
  - ADR-26037
  type: analysis
  version: 1.0.0
  birth: '2026-03-02'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Smallest Viable Architecture (SVA) is the governing design principle
  across 14+ ADRs, three consultant prompts, and the requirements engineering glossary.
---
# A-26003: SVA Constraint Framework Design

## Problem Statement

Smallest Viable Architecture (SVA) is the governing design principle across 14+ ADRs, three consultant prompts, and the requirements engineering glossary. Yet it has never been formally defined in its own ADR. The result: three consultant prompts define SVA constraints with **incompatible numbering**, ADRs reference constraint IDs that don't match any consultant, and there is no litmus test to validate SVA compliance consistently.

### Current State: Three Incompatible Constraint Sets

| Constraint concept | Local AI (C1-C4) | DevOps (C1-C4) | Hybrid (C1-C5) |
|---|---|---|---|
| Non-CLI/non-GitOps workflow | C1 | C1 | C2 |
| Not runnable locally | C2 | C2 | — |
| Vendor lock-in | — | — | C1 |
| Unversionable artifacts | C3 | C3 | C3 |
| Unjustified orchestration | C4 | C4 | C4 |
| Scalability limits | — | — | C5 |

### Inconsistency Evidence in ADRs

- **ADR-26024**: References "C1 violation" (manual CLI step) and "C4 violation" (persistent state-tracking layer) — uses local/devops numbering
- **ADR-26025**: References "C3" (git-tracked knowledge) — consistent across all variants
- **ADR-26026**: References "SVA principle C2 (separation of concerns)" — matches **no** consultant definition; this is an invented constraint
- **ADR-26005**: Rejects custom agent framework for "violating SVA by adding unjustified orchestration layers" — C4 in all variants, but no explicit C-number cited

### The Missing Constraint

The changelog self-filtering plan (`misc/plan/implemented/plan_20260228_changelog_self_filtering_warning.md`) exposed a critical gap. The original plan proposed extending `validate_commit_msg.py` with 4 functions, 1 dataclass, and 13 tests to show changelog filtering warnings at commit time. This plan satisfied all existing C1-C4 constraints:

- C1 (CLI/GitOps): Pass — runs in pre-commit hook
- C2 (local/vendor): Pass — pure Python, no external dependencies
- C3 (versionable): Pass — all artifacts in Git
- C4 (orchestration): Pass — no new orchestration layer

Yet it was **correctly rejected during implementation** because `generate_changelog.py --verbose` already provided the exact functionality. The plan would have duplicated filtering logic across two scripts. No existing constraint captured this violation.

## Approach Evaluation

### Design Methodology

Rather than reshuffling existing constraints, we derive the canonical set from established engineering principles:

1. **GitOps** — declarative, version-controlled, automated infrastructure
2. **Twelve-Factor App** — methodology for building SaaS (Heroku, 2011)
3. **UNIX Philosophy** — do one thing well, compose via standard interfaces (McIlroy, 1978)
4. **YAGNI / XP** — You Ain't Gonna Need It (Beck, 1999)
5. **SRE Principles** — operational simplicity, capacity planning (Google, 2016)
6. **ISO 29148** — requirements engineering (verifiability, traceability)
7. **DRY** — Don't Repeat Yourself (Hunt & Thomas, 1999)
8. **IEEE 1016** — software design descriptions (replaceability)

### Canonical C1-C6 Framework

#### C1: Automation-First Operation

- **Definition:** Every workflow step must be executable non-interactively via CLI or API, enabling CI/CD integration without manual gates.
- **Litmus test:** Can a CI runner execute this without human interaction? If a step requires a GUI, manual approval click, or interactive terminal input, it violates C1.
- **Sources:** GitOps (declarative automation), Twelve-Factor App (Factor V: Build/Release/Run), ISO 29148 (verifiable requirements — non-automated steps are non-verifiable at scale).

#### C2: Vendor Portability

- **Definition:** No component may create single-vendor dependency that prevents migration to an equivalent alternative within one sprint.
- **Litmus test:** If the vendor disappears tomorrow, can you replace the component with a functionally equivalent alternative within two weeks? If not, it violates C2.
- **Sources:** Twelve-Factor App (Factor IV: Backing services as attached resources), IEEE 1016 (design for replaceability), UNIX Philosophy (loose coupling).

#### C3: Git-Native Traceability

- **Definition:** All artifacts that influence system behavior (code, configuration, prompts, documentation) must be stored in version-controlled, text-diffable formats within the repository.
- **Litmus test:** Can `git diff` show a meaningful, human-reviewable change for any modification? If an artifact is binary, stored externally, or invisible to `git log`, it violates C3.
- **Sources:** GitOps (Git as single source of truth), ISO 29148 (traceability), SRE (postmortem culture — you cannot trace what you cannot version).

#### C4: Proportional Complexity

- **Definition:** Every architectural component must justify its existence by the problem it solves; the cost of adding/maintaining it must not exceed the cost of the problem it addresses.
- **Litmus test:** Remove the component from the design. Does the system still meet its requirements, perhaps through an existing capability? If yes, the component violates C4.
- **Sources:** YAGNI (Extreme Programming), UNIX Philosophy ("do one thing well"), KISS, SRE (operational simplicity reduces MTTR).

#### C5: Reuse Before Invention

- **Definition:** New code, scripts, or abstractions must not duplicate logic already present in an existing, tested component within the system boundary.
- **Litmus test:** Does a tool or function already exist in the codebase that provides the required capability (perhaps with a flag or minor extension)? If yes, creating a parallel implementation violates C5.
- **Sources:** DRY (Don't Repeat Yourself), UNIX Philosophy ("expect the output of every program to become the input to another"), Single Source of Truth, XP (Simple Design).

#### C6: Bounded Scalability

- **Definition:** The solution must degrade gracefully (not catastrophically) as input size grows by 10x, and must document known scaling boundaries.
- **Litmus test:** What happens when the input corpus (tokens, files, records) grows 10x? If the system fails silently, exhausts resources without warning, or requires a full rewrite, it violates C6. Documented scaling limits with mitigation paths do NOT violate C6.
- **Sources:** SRE (capacity planning), Twelve-Factor App (Factor VIII: Concurrency), ISO 29148 (scalability as a non-functional requirement).

### Design Note: "Runnable Locally" (old local C2)

Intentionally dropped as a universal constraint. "Runs on CPU or consumer VRAM" is a **deployment context** specific to the local AI consultant's scope, not a universal architectural principle. The hybrid consultant correctly omitted it. For the local AI consultant, this remains part of the P_raw scoring (local stack suitability assessment), not a penalty deduction. A cloud-first team should not be penalized for choosing cloud-native components.

## Taxonomy Design

| New Canonical | Local AI (old) | DevOps (old) | Hybrid (old) | Notes |
|---|---|---|---|---|
| **C1: Automation-First** | C1 | C1 | C2 | Numbering shifted in hybrid |
| **C2: Vendor Portability** | — (implicit in `production_focus`) | — (implicit) | C1 | Elevated from implicit to formal |
| **C3: Git-Native Traceability** | C3 | C3 | C3 | Consistent across all variants |
| **C4: Proportional Complexity** | C4 | C4 | C4 | Broadened from "orchestration layers" to all disproportionate complexity |
| **C5: Reuse Before Invention** | — | — | — | **New.** Closes the duplicate-logic gap |
| **C6: Bounded Scalability** | — | — | C5 | Carried from hybrid |
| ~~"Not runnable locally"~~ | C2 | C2 | — | **Dropped.** Deployment context, not universal principle |

## Key Insights

### The Changelog Self-Filtering Warning Pivot

**Original plan:** Extend `validate_commit_msg.py` with a `ChangelogWarning` dataclass, `_matches_exclude_pattern()`, `_find_matching_pattern()`, `check_changelog_exclusions()`, and `_print_changelog_warnings()` — plus 13 tests.

**Actual solution:** Single post-commit hook entry: `bash -c 'uv run --active tools/scripts/generate_changelog.py --verbose HEAD~1..HEAD'`

| Constraint | Original Plan | Post-commit Hook |
|---|---|---|
| C1: Automation-First | Pass | Pass |
| C2: Vendor Portability | Pass | Pass |
| C3: Git-Native Traceability | Pass | Pass |
| **C4: Proportional Complexity** | **FAIL** — 4 functions + 1 dataclass + 13 tests for an informational warning | Pass — zero new code |
| **C5: Reuse Before Invention** | **FAIL** — `_matches_exclude_pattern` duplicates `generate_changelog.py` filtering logic | Pass — reuses existing tool with `--verbose` flag |
| C6: Bounded Scalability | Pass | Pass |

**Result:** Old C1-C4 framework: 0 violations (would approve the wrong plan). New C1-C6 framework: 2 violations (correctly flags it). This validates C5 as the critical missing constraint.

### Additional ADR Validation

- **ADR-26005** (rejected: Aider as orchestrator): C2 violation (vendor lock-in on Aider) + C4 violation (unjustified orchestration) — correctly caught by new framework
- **ADR-26013** (accepted: JIT prompt transformation): Rejected alternative (persistent YAML) fails C3 (artifact drift) + C4 (sync scripts) + C5 (duplicate storage) — new framework provides richer rejection rationale

## References

- 'The Pragmatic Programmer' [Hunt & Thomas], 1999 — DRY principle
- 'Extreme Programming Explained' [Beck], 1999 — YAGNI, Simple Design
- 'The Twelve-Factor App' [Wiggins], 2011 — https://12factor.net
- 'Site Reliability Engineering' [Beyer, Jones, Petoff, Murphy], 2016 — SRE principles
- 'The Art of UNIX Programming' [Raymond], 2003 — UNIX Philosophy
- ISO/IEC/IEEE 29148:2018 — Requirements engineering
- IEEE 1016-2009 — Software design descriptions
- [ADR-26005: Formalization of Aider as Primary Agentic Orchestrator](/architecture/adr/adr_26005_formalization_of_aider_as_primary_agentic.md) — rejected (C2, C4 violations)
- [ADR-26013: Just-in-Time Prompt Transformation](/architecture/adr/adr_26013_just_in_time_prompt_transformation.md) — C3, C4, C5 validation
- [ADR-26024: Structured Commit Bodies](/architecture/adr/adr_26024_structured_commit_bodies_for_automated_changelog.md) — references C1, C4 violations
- [ADR-26025: RFC-ADR Workflow Formalization](/architecture/adr/adr_26025_rfc_adr_workflow_formalization.md) — references C3
- [ADR-26026: Dedicated Research Monorepo](/architecture/adr/adr_26026_dedicated_research_monorepo_for_volatile.md) — invented ad hoc "C2"
- [AI Systems Consultant](/ai_system_layers/3_prompts/consultants/ai_systems_consultant.json) — SVA constraints C1-C6 (canonical)
- [DevOps Consultant](/ai_system_layers/3_prompts/consultants/devops_consultant.json) — SVA constraints C1-C6 (canonical)
- [Requirements Engineering: Gated Velocity](/ai_system_layers/4_orchestration/workflows/requirements_engineering/requirements_engineering_in_the_ai_era_the_gated_velocity.ipynb) — SVA glossary definition
- [Changelog Self-Filtering Warning Plan](/misc/plan/implemented/plan_20260228_changelog_self_filtering_warning.md) — Case study: SVA pivot
