---
id: 26045
title: AI-Native Development — Code as Primary Documentation
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Contract docstrings are mandatory for all code in all languages across
  the ecosystem. Code structure is the primary documentation layer for both human
  and agent consumers.
tags:
- development
- governance
date: 2026-04-01
options:
  type: adr
  birth: 2026-04-01
  version: 1.0.0
  token_size: 1399
  status: accepted
  superseded_by: null
---
<!-- Quality guidelines: /architecture/architecture_decision_workflow_guide.md -->

# ADR-26045: AI-Native Development — Code as Primary Documentation

## Date

2026-04-01

## Status

Accepted

Supersedes {term}`ADR-26011`.

## Context

The ecosystem uses AI agents as primary development tools. These agents are
stateless ({term}`ADR-26030`), context-budget constrained ({term}`ADR-26038`),
and read code as fluently as prose. A comprehensive analysis
([A-26020: AI-Native Development — Code as Primary Documentation](/architecture/evidence/analyses/A-26020_ai_native_development_code_as_primary_documentation.md))
establishes that:

1. **Agents cannot verify prose accuracy.** A docstring that contradicts code
   is caught at import time. A separate doc file that contradicts code passes
   all CI checks silently.

2. **Every token of documentation competes with code for attention budget.**
   Effective context is only 50-65% of advertised window size (NVIDIA RULER,
   cited in {term}`ADR-26038`). Redundant prose that paraphrases code is a
   context window tax.

3. **Code structure is already the primary documentation layer.** Contract
   docstrings + test suites provide CI-verified, co-located, refactoring-safe
   documentation. Prose docs are the only layer that drifts silently
   ([A-26014: Script Suite Doc Redundancy](/architecture/evidence/analyses/A-26014_script_suite_doc_redundancy.md),
   Table 1).

Currently, the contract docstring convention exists only as an agent
instruction in `AGENTS.md` — not as a governed architectural decision. This
means it cannot be referenced by other ADRs, does not extend to non-Python
code, and has no enforcement mechanism beyond agent compliance.

## Decision

Every source file in the ecosystem — regardless of language — must open with
a **contract docstring** in that language's native documentation format.

The contract docstring answers: **"What does a future agent need to read first
to work safely in this file?"** It must contain:

- **Scope / responsibility**: what this file does and what it does NOT do
- **Public interface**: what callers/importers may use; internals marked private
- **Key design decisions**: the *why* behind non-obvious choices
- **Dependencies**: what the file relies on (imports, env vars, services)

For **test files**, additionally:

- **What belongs here** vs what does not
- **Naming convention** in use

The contract docstring format is language-native:

| Language | Mechanism |
|---|---|
| Python | Module/class/function docstrings |
| JavaScript/TypeScript | JSDoc / `/** */` blocks |
| Bash | Header comment block |
| YAML/JSON configs | Description fields in schema |
| SQL | `COMMENT ON` statements |

### Scope

This convention applies to all code written in the ecosystem. Migration is
incremental: new files must comply immediately, existing files comply when
next modified.

### What This ADR Does NOT Cover

- Prose documentation (ADRs, onboarding guides, workflow docs) — these
  document cross-cutting concerns that no single file owns
- Auto-generated API documentation (sphinx, typedoc) — derived from
  contract docstrings, not hand-maintained
- Test methodology details — A-26020 formalizes agent-native TDD principles
  separately

## Consequences

### Positive

- **Agent safety**: agents read the contract before modifying a file,
  reducing the risk of undoing intentional design decisions
- **Governed authority**: other ADRs can reference this decision (e.g.,
  relaxing {term}`ADR-26011`'s doc requirement)
- **Language-agnostic**: applies uniformly across the polyglot ecosystem
- **Zero context overhead**: co-located documentation adds no extra files
  to the context window

### Negative

- **Enforcement complexity**: linting for docstring presence varies by
  language. Python (`pydocstyle`, custom pre-commit) is mature; Bash and
  SQL enforcement requires custom tooling.
  **Mitigation**: Enforce structure (docstring exists, contains required
  sections), not semantic quality. Start with Python and Bash; extend
  incrementally.

- **Cargo-cult risk**: developers may write minimal docstrings that satisfy
  the check without providing useful context.
  **Mitigation**: Quality comes from code review and agent feedback loops,
  not from the linter. The linter prevents absence; review prevents vacuity.

## Alternatives

- **Keep as CLAUDE.md convention only.** Rejected: not an architectural
  decision, cannot be referenced by other ADRs, does not extend to
  non-Python code or non-Claude-Code agents.

- **Per-language ADRs.** Rejected: the principle is language-agnostic.
  Language-specific enforcement details belong in Consequences, not
  separate ADRs (one ADR = one decision).

## References

- [A-26020: AI-Native Development — Code as Primary Documentation](/architecture/evidence/analyses/A-26020_ai_native_development_code_as_primary_documentation.md) — full evidence synthesis
- [A-26014: Script Suite Doc Redundancy](/architecture/evidence/analyses/A-26014_script_suite_doc_redundancy.md) — three-layer documentation model, maintenance cost evidence
- {term}`ADR-26038`: Context engineering as core design principle
- {term}`ADR-26030`: Stateless JIT context injection
- {term}`ADR-26037`: SVA constraint framework (C3: git-native traceability)

## Participants

1. Vadim Rudakov
2. Claude Opus 4.6 (analysis synthesis, ADR drafting)
