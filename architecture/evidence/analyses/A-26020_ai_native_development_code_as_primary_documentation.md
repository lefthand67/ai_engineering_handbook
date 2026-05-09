
---
title: AI-Native Development — Code as Primary Documentation
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Code structure is the documentation layer in AI-native ecosystems. Contract
  docstrings, structured tests, and machine-readable metadata replace prose documentation
  for both human and agent consumers. Language-agnostic, ecosystem-wide.
tags:
- governance
- documentation
date: 2026-04-01
options:
  type: analysis
  birth: 2026-04-01
  version: 1.0.0
  token_size: 2826
  id: A-26020
  status: active
  sources: []
  produces: []
---
# A-26020: AI-Native Development — Code as Primary Documentation

+++

## Problem Statement

+++

The ecosystem uses AI agents (Claude Code, Qwen Code, aider) as primary
development tools. These agents read code, tests, and configuration files to
understand what they can safely modify. The question is: **what documentation
strategy maximizes agent safety and productivity across all languages and
project types?**

Traditional software documentation assumes a human reader with persistent
memory who navigates docs separately from code. AI agents operate differently:

1. **Agents are stateless.** Each session starts fresh — the agent reads the
   current file state, not a knowledge base built over months of onboarding
   ({term}`ADR-26030`).
2. **Agents have a finite context window.** Every token of documentation
   competes with code tokens for attention budget. NVIDIA RULER shows effective
   context is only 50-65% of advertised window size ({term}`ADR-26038`).
3. **Agents read code natively.** An LLM parses Python, JavaScript, YAML, or
   Bash as fluently as prose — often more reliably, because code has
   deterministic structure while prose is ambiguous.
4. **Agents cannot verify prose accuracy.** A docstring that contradicts the
   code is caught at import time. A separate doc file that contradicts the
   code passes all CI checks silently (A-26014, Table 1).

These properties invert the traditional documentation hierarchy: **code
structure is the primary documentation layer, and prose documentation is
supplementary context for cases where code alone is insufficient.**

+++

## Key Insights

+++

### 1. The Three-Layer Documentation Model

Evidence from A-26014 (script suite doc redundancy) established that three
documentation layers now exist in the ecosystem:

| Layer | Location | Verified by CI | Survives refactoring |
|---|---|---|---|
| Contract docstring | In the source file | Import/compile time | Yes — moves with the code |
| Test suite | Adjacent test file | Test runner | Yes — fails if contract breaks |
| Prose documentation | Separate file | Existence check only | No — drifts silently |

The contract docstring is the most agent-friendly layer because it is:
- **Co-located**: the agent reads the file and immediately has the contract
- **Verified**: syntax errors in docstrings break at import/compile time
- **Minimal**: scope + interface + boundaries + design decisions in 5-10 lines

The test suite is the second layer — it documents contracts by example with
parametrized inputs that pytest infrastructure renders as diagnostics.

Prose documentation is the weakest layer for agents. A-26014 found that 15+
instruction docs in `tools/docs/scripts_instructions/` contained stale
references to deleted config files (`evidence.config.yaml`,
`architecture.config.yaml`) that would have passed CI silently.

### 2. The Contract Docstring Pattern Is Language-Agnostic

The contract docstring structure answers one question: **"What does a future
agent need to read first to work safely in this file?"**
[A-26014: Script Suite Documentation Redundancy](/architecture/evidence/analyses/A-26014_script_suite_doc_redundancy.md)
established that contract docstrings are one of three documentation layers,
and the only one that is both CI-verified and co-located with the code it
describes.

The answer is the same regardless of language:

- **Scope / responsibility**: one sentence on what this file does and does NOT do
- **Public interface**: what callers/importers may use; internals marked private
- **Key design decisions**: the *why* behind non-obvious choices
- **Dependencies**: what the file relies on (imports, env vars, services)

This maps directly to language-specific constructs:

| Language | Docstring mechanism | Test mechanism |
|---|---|---|
| Python | Module/class/function docstrings | pytest |
| JavaScript/TypeScript | JSDoc / `/** */` blocks | Jest, Vitest |
| Bash | Header comment block (`# ---`) | bats, shunit2 |
| YAML/JSON configs | Description fields in schema | JSON Schema validation |
| SQL | `COMMENT ON` statements | pgTAP |

The pattern is: **structured metadata at the top of every unit of code, in
the language's native documentation format.** This is not a Python convention —
it is a development methodology.

### 3. Why "Any Code, Any Language" — The Agent Context Budget Argument

{term}`ADR-26038` establishes context engineering as the core design principle.
The MIT/Kellogg finding (cited in ADR-26038) shows that 80% of production agent
work is data engineering, governance, and workflow integration — not AI. This
means agents spend most of their context budget reading infrastructure code
(CI configs, deployment scripts, validation hooks) not just application code.

If only Python files have contract docstrings while Bash scripts, YAML configs,
and SQL migrations lack them, the agent must:
1. Read the entire file to understand scope (expensive)
2. Guess at boundaries and design decisions (error-prone)
3. Risk undoing intentional choices it cannot identify (dangerous)

The v0.30-v0.41 Mentor Generator postmortems (documented in
[A-26002](/architecture/evidence/analyses/A-26002_agentic_os_skills_tiered_memory_package_infra.md))
demonstrated this concretely: "Instructions don't scale. Each additional
instruction increases the probability of failure somewhere else." When agents
must infer intent from unstructured code, they compensate by asking more
questions or making conservative (often wrong) assumptions.

### 4. Test Diagnostics as Agent-Readable Documentation

Ecosystem practice has converged on test patterns that optimize for agent
consumers: testing contracts rather than implementation, using semantic
assertions, parametrizing inputs. This analysis formalizes these patterns
as three principles for agent-native TDD:

1. **Names over messages.** Test method names are the primary diagnostic
   channel. `test_rejects_negative_timeout` tells the agent the contract;
   a custom assertion message repeats what the test name already says.
   Agents parse method names programmatically — assertion strings require
   natural language understanding.

2. **Parametrize over multiply-assert.** `@pytest.mark.parametrize` with
   varied inputs lets test infrastructure show which specific input failed.
   Custom assertion messages are the documentation-in-implementation
   anti-pattern — they couple to intent that the test name should convey.

3. **Contracts over pipelines.** Test docstrings describe what survives
   refactoring (exit codes, return types, side effects), not what breaks on
   refactoring (internal call sequences, mock counts). An agent reading
   `assert exit_code == 1` understands the contract; an agent reading
   `assert mock.call_count == 3` understands an implementation detail that
   will change on the next refactor.

These three principles produce a diagnostics hierarchy for agents
encountering a test failure: test name → test framework introspection →
contract docstring. Custom messages only where the failure mode is
genuinely ambiguous.

### 5. Relationship to Existing Governance

This methodology connects to multiple existing architectural decisions:

- **{term}`ADR-26038` (Context Engineering)**: If code structure is
  documentation, context budget is spent on code, not redundant prose.
  Every prose doc that paraphrases code is a context window tax.

- **{term}`ADR-26037` C3 (Git-Native Traceability)**: Structured commit
  bodies (`- Verb: file-path — what and why`) make commit history itself
  a machine-readable documentation layer.

- **{term}`ADR-26030` (Stateless JIT Context)**: Agents assemble context
  from current file state, not cached knowledge. Documentation must be
  co-located with the code it describes.

- **{term}`ADR-26042` (Common Frontmatter Standard)**: Machine-readable
  metadata (title, type, tags, description) enables agents to discover and
  filter documents without parsing prose — the documentation equivalent of
  contract docstrings.

- **[A-26011](/architecture/evidence/analyses/A-26011_vadocs_as_structural_type_checker_lean_analogy.md)
  (vadocs as Type Checker)**: Deterministic structural validation provides
  infinite signal-to-noise ratio. Contract docstrings + test suites are the
  code equivalent — deterministic documentation that cannot drift from
  reality.

### 6. What Prose Documentation Remains Necessary

Code-as-documentation does **not** eliminate all prose. The following require
human-authored narrative:

- **ADRs**: Architectural decisions record the *why* behind system-level
  choices that span multiple files. No single file's docstring captures this.
- **Onboarding guides**: High-level orientation for new contributors who
  need to understand the ecosystem before reading individual files.
- **API documentation**: Auto-generated from docstrings (sphinx, typedoc),
  not hand-maintained.
- **Workflow guides**: Multi-step procedures that cross system boundaries
  (CI/CD pipelines, release processes).

The distinction: prose documents explain **cross-cutting concerns** that no
single file owns. Per-file documentation belongs in the file.

+++

## Approach Evaluation

+++

### Option A: Formalize as Ecosystem-Wide Convention via ADR (Recommended)

Write an ADR mandating contract docstrings for all code in all languages
across the ecosystem. Enforcement via pre-commit hooks (language-specific
linters checking for module-level documentation). Existing code migrates
incrementally — new files must comply, existing files comply when modified.

**Pros:**
- Governed decision with traceability
- Language-agnostic principle with language-specific enforcement
- Enables downstream decisions (A-26014 dyad, vadocs package extraction)
- Incremental migration avoids big-bang risk

**Cons:**
- Enforcement complexity varies by language (Python: easy; Bash: harder)
- Risk of cargo-cult docstrings (existence without quality)

**Mitigation:** Enforcement checks structure (docstring exists, contains
required sections), not semantic quality. Quality comes from code review
and agent feedback loops.

### Option B: Keep as CLAUDE.md Convention Only

Leave the contract docstring requirement in CLAUDE.md without an ADR.

**Pros:**
- No governance overhead
- Already working in practice for Python

**Cons:**
- Not an architectural decision — CLAUDE.md is an agent instruction file,
  not a binding ecosystem standard
- Cannot be referenced by other ADRs as justification (the chain breaks)
- Does not extend to non-Python code or non-Claude-Code agents
- No enforcement mechanism beyond agent compliance

### Option C: Per-Language ADRs

Write separate ADRs for Python, Bash, YAML, SQL docstring conventions.

**Pros:**
- Language-specific enforcement details in each ADR

**Cons:**
- Violates one-decision-per-ADR only if the *principle* is the same
- The principle IS the same: contract docstrings for agent safety
- Multiple ADRs create cross-reference overhead

**Rejected:** The decision is language-agnostic. Language-specific enforcement
details belong in the ADR's Consequences section, not separate ADRs.

+++

## References

+++

- {term}`ADR-26038`: Context engineering as core design principle
- {term}`ADR-26037`: SVA constraint framework (C3: git-native traceability, C5: no duplicate logic)
- {term}`ADR-26030`: Stateless JIT context injection
- {term}`ADR-26042`: Common frontmatter standard (machine-readable metadata)
- {term}`ADR-26011`: Script suite triad convention (to be superseded)
- [A-26014: Script Suite Doc Redundancy](/architecture/evidence/analyses/A-26014_script_suite_doc_redundancy.md) — three-layer documentation model, maintenance cost evidence
- [A-26002: Agentic OS and Tiered Memory](/architecture/evidence/analyses/A-26002_agentic_os_skills_tiered_memory_package_infra.md) — v0.30-v0.41 postmortem evidence
- [A-26011: vadocs as Structural Type Checker](/architecture/evidence/analyses/A-26011_vadocs_as_structural_type_checker_lean_analogy.md) — deterministic validation model
