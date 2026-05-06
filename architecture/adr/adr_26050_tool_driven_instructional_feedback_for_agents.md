---
title: Tool-Driven Instructional Feedback for Agents
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: 2026-05-04
description: Shift from static guidelines to just-in-time instructional feedback within
  validation scripts to guide agent behavior.
tags:
- architecture
- agents
- ci
options:
  type: adr
  id: 26050
  birth: 2026-05-04
  version: 1.0.0
  status: accepted
  superseded_by: null
  token_size: 732
---
## Context

Agents working in the repository are subject to strict, high-frequency structural constraints (e.g., commit message formats, frontmatter schemas, linked notebook pairs). While these rules are documented in `QWEN.md` and `AGENTS.md`, agents often suffer from "context drift" or ignore these guidelines during the implementation phase, leading to repetitive commit failures and iterative trial-and-error.

Post-mortem analysis (e.g., `post-mortem_slm_non-determinism_in_commit_generation.md`) confirms that LLMs, especially smaller models, struggle to maintain multiple simultaneous constraints (imperative mood, character limits, and conditional ArchTags) when those constraints are provided as distant prose.

## Decision

We will implement a "Tool-Driven Instructional Feedback" pattern. Validation scripts (hooks) will no longer function merely as boolean gates (Pass/Fail) but as **Just-In-Time (JIT) Instructors**.

### Core Principles

1. **Detection $\rightarrow$ Instruction:** Every validation error must be accompanied by a clear, actionable instruction on *how* to fix the violation.
2. **Positional Awareness:** Errors must identify the exact location of the failure (e.g., "Line 1 of body") and provide the expected corrected state.
3. **Governed Vocabulary:** Validation scripts will reference machine-readable registries (e.g., in `pyproject.toml`) to provide agents with a list of valid options rather than expecting them to guess or hallucinate tags.
4. **Rationale Integration:** Error messages should briefly explain *why* the rule exists (e.g., "Linking to an ADR prevents regression") to encourage agent alignment with architectural intent.

### Implementation Standard

All validation scripts must follow the reporting contract:
`file_path:field — <Instructional Message> [config_source]`

Example:
Instead of: `Missing ArchTag`
Use: `COMMIT_MSG:body — ArchTag required for 'refactor' type. Add 'ArchTag:TAG-NAME' as the first line of the body to link this change to its architectural justification. Suggestions: REFACTOR-MIGRATION, TECHDEBT-PAYMENT.`

## Consequences

### Pros
- **Reduced Iteration Cycles:** Agents can fix errors in a single step rather than guessing through multiple commit attempts.
- **Self-Documenting Constraints:** The scripts become the living documentation of the project's standards.
- **Increased Fidelity:** By providing the exact expected format in the error message, we bypass the "instruction fidelity" limitations of smaller models.

### Cons
- **Increased Script Complexity:** Validation logic must now handle instructional string generation and vocabulary lookups.
- **Maintenance Overhead:** Changes to conventions must be updated in both the logic and the instructional strings.

### Risks
- **Message Bloat:** Overly verbose error messages could clutter the CLI. We will mitigate this by keeping instructions concise and focused on the immediate fix.
