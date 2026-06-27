---
id: 26037
title: Smallest Viable Architecture (SVA) Constraint Framework
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: 2026-03-02.
tags:
- architecture
- governance
date: 2026-03-02
options:
  type: adr
  birth: '2026-03-02'
  version: 1.0.0
  token_size: 2388
  status: accepted
  superseded_by: null
---
# ADR-26037: Smallest Viable Architecture (SVA) Constraint Framework

## Date
2026-03-02

## Status

accepted

## Context

Smallest Viable Architecture (SVA) is the governing design principle across 14+ ADRs, three consultant prompts, and the requirements engineering glossary. Despite this, SVA has never been formally defined in its own ADR. Three consultant prompts define SVA constraints with **incompatible numbering**:

| Constraint concept | Local AI (C1-C4) | DevOps (C1-C4) | Hybrid (C1-C5) |
|---|---|---|---|
| Non-CLI/non-GitOps workflow | C1 | C1 | C2 |
| Not runnable locally | C2 | C2 | — |
| Vendor lock-in | — | — | C1 |
| Unversionable artifacts | C3 | C3 | C3 |
| Unjustified orchestration | C4 | C4 | C4 |
| Scalability limits | — | — | C5 |

### Inconsistency Evidence

- {term}`ADR-26024`: References "C1 violation" and "C4 violation" — uses local/devops numbering
- {term}`ADR-26025`: References "C3" (git-tracked knowledge) — consistent across all variants
- {term}`ADR-26026`: References "SVA principle C2 (separation of concerns)" — matches **no** consultant definition; this is an invented constraint ID
- {term}`ADR-26005`: Rejects custom agent framework for "violating SVA by adding unjustified orchestration layers" — C4 in all variants, but no explicit C-number cited

### The Missing Constraint

The changelog self-filtering warning plan exposed a critical gap. The original plan proposed extending `validate_commit_msg.py` with 4 functions, 1 dataclass, and 13 tests. This plan satisfied all existing C1-C4 constraints, yet was correctly rejected during implementation because `generate_changelog.py --verbose` already provided the exact functionality. The plan would have duplicated filtering logic across two scripts. No existing constraint captured this violation.

## Decision

Adopt a canonical C1-C6 SVA constraint framework, redesigned from first principles. Each constraint carries a -0.10 penalty on the P-score in the WRC (Weighted Response Confidence) calculation.

### C1: Automation-First Operation

- **Definition:** Every workflow step must be executable non-interactively via CLI or API, enabling CI/CD integration without manual gates.
- **Litmus test:** Can a CI runner execute this without human interaction? If a step requires a GUI, manual approval click, or interactive terminal input, it violates C1.
- **Sources:** GitOps (declarative automation), Twelve-Factor App (Factor V: Build/Release/Run), ISO 29148 (verifiable requirements — non-automated steps are non-verifiable at scale).

### C2: Vendor Portability

- **Definition:** No component may create single-vendor dependency that prevents migration to an equivalent alternative within a bounded, documented timeframe.
- **Litmus test:** If the vendor disappears tomorrow, can you replace the component with a functionally equivalent alternative without redesigning the system? If not, it violates C2.
- **Sources:** Twelve-Factor App (Factor IV: Backing services as attached resources), IEEE 1016 (design for replaceability), UNIX Philosophy (loose coupling).

### C3: Git-Native Traceability

- **Definition:** All artifacts that influence system behavior (code, configuration, prompts, documentation) must be stored in version-controlled, text-diffable formats within the repository.
- **Litmus test:** Can `git diff` show a meaningful, human-reviewable change for any modification? If an artifact is binary, stored externally, or invisible to `git log`, it violates C3.
- **Sources:** GitOps (Git as single source of truth), ISO 29148 (traceability), SRE — Site Reliability Engineering (postmortem culture — you cannot trace what you cannot version).

### C4: Proportional Complexity

- **Definition:** Every architectural component must justify its existence by the problem it solves; the cost of adding/maintaining it must not exceed the cost of the problem it addresses.
- **Litmus test:** Remove the component from the design. Does the system still meet its requirements, perhaps through an existing capability? If yes, the component violates C4.
- **Sources:** YAGNI — You Ain't Gonna Need It (Extreme Programming), UNIX Philosophy ("do one thing well"), KISS — Keep It Simple, Stupid, SRE — Site Reliability Engineering (operational simplicity reduces Mean Time To Recovery).

### C5: Reuse Before Invention

- **Definition:** New code, scripts, or abstractions must not duplicate logic already present in an existing, tested component within the system boundary.
- **Litmus test:** Does a tool or function already exist in the codebase that provides the required capability (perhaps with a flag or minor extension)? If yes, creating a parallel implementation violates C5.
- **Sources:** DRY — Don't Repeat Yourself, UNIX Philosophy ("expect the output of every program to become the input to another"), Single Source of Truth, XP — Extreme Programming (Simple Design).

### C6: Bounded Scalability

- **Definition:** The solution must degrade gracefully (not catastrophically) as input size grows by 10x, and must document known scaling boundaries.
- **Litmus test:** What happens when the input corpus (tokens, files, records) grows 10x? If the system fails silently, exhausts resources without warning, or requires a full rewrite, it violates C6. Documented scaling limits with mitigation paths do NOT violate C6.
- **Sources:** SRE — Site Reliability Engineering (capacity planning), Twelve-Factor App (Factor VIII: Concurrency), ISO 29148 (scalability as a non-functional requirement).

### Design Note: "Runnable Locally" (old local C2)

Intentionally dropped as a universal constraint. "Runs on CPU or consumer VRAM" is a deployment context specific to the local AI consultant's scope, not a universal architectural principle. The hybrid consultant correctly omitted it. For the local AI consultant, this remains part of the P_raw scoring (local stack suitability assessment), not a penalty deduction.

## Consequences

### Positive
- Single canonical constraint vocabulary: any document referencing SVA uses the same C1-C6 IDs with unambiguous meaning
- C5 closes the duplicate-logic gap — proposals that pass C1-C4 but duplicate existing functionality are now formally caught
- Litmus tests make SVA compliance falsifiable — a constraint either passes its litmus test or it doesn't
- Framework is derived from established engineering principles (not ad hoc), making it defensible and extensible

### Negative / Risks
- Existing ADRs reference old constraint numbering (C1-C4). **Mitigation:** Phased rollout — update each ADR when it is next modified, not retroactively in bulk.
- C5 (Reuse Before Invention) requires knowledge of the existing codebase, which may exceed context window limits or be impractical to research exhaustively at development time. **Mitigation:** C5 is a best-effort constraint during development — apply it when the duplication is known or discoverable. When duplication is found during production use, simplify by consolidating to the existing component. C5 does not require proving the absence of duplication; it prohibits creating known duplication.
- Six constraints increase the maximum penalty to -0.60, which could push more proposals below the P_min threshold. **Mitigation:** This is intentional — proposals with 6 violations should not be production-ready.

## Alternatives

- **Option A: Incremental extension (add C5 only to existing C1-C4).** Keep the current numbering and add "Reuse Before Invention" as C5. **Rejection Reason:** Does not address vendor portability (which was implicit, not formalized), does not add bounded scalability, and preserves the "runnable locally" constraint that is a deployment context, not a universal principle. Patching rather than redesigning perpetuates the inconsistencies.

- **Option B: Descriptive names without C-numbers.** Reference constraints by name (e.g., "SVA: Automation-First") without numbered identifiers. **Rejection Reason:** C-numbers are shorter for inline references in ADRs, enable concise penalty audit tables in WRC calculations, and are already in widespread use. The canonical framework uses both — names for clarity, numbers for brevity.

- **Option C: No universal framework — domain-specific constraint sets.** Each domain (local AI, DevOps, cloud) defines its own constraint set suited to its scope. **Rejection Reason:** ADRs reference SVA constraints without specifying a domain. This ambiguity already produced the invented "C2 (separation of concerns)" in {term}`ADR-26026`, which matched no defined constraint. Without a shared vocabulary, constraint references become meaningless.

## References

- [A-26003: SVA Constraint Framework Design](/architecture/evidence/analyses/A-26003_sva_constraint_framework_design.md) — full derivation analysis
- {term}`ADR-26005` — Rejected: Formalization of Aider as Primary Agentic Orchestrator (C2, C4 violations)
- {term}`ADR-26013` — Just-in-Time Prompt Transformation (C3, C4, C5 validation in alternatives)
- {term}`ADR-26024` — Structured Commit Bodies (references C1, C4)
- {term}`ADR-26025` — RFC-ADR Workflow Formalization (references C3)
- {term}`ADR-26026` — Dedicated Research Monorepo (invented ad hoc "C2")
- [Changelog Self-Filtering Warning Plan](/misc/plan/implemented/plan_20260228_changelog_self_filtering_warning.md) — case study: SVA pivot that validated C5
- 'The Pragmatic Programmer' [Hunt & Thomas], 1999 — DRY principle
- 'Extreme Programming Explained' [Beck], 1999 — YAGNI, Simple Design
- 'The Twelve-Factor App' [Wiggins], 2011
- 'Site Reliability Engineering' [Beyer, Jones, Petoff, Murphy], 2016
- 'The Art of UNIX Programming' [Raymond], 2003
- ISO/IEC/IEEE 29148:2018 — Requirements engineering
- IEEE 1016-2009 — Software design descriptions

## Participants

1. Vadim Rudakov
2. Claude Opus 4.6 (AI Systems Architect)
