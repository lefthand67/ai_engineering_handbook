
---
title: 'Model Taxonomy: Reasoning-Class vs Agentic-Class Selection Heuristic'
date: 2026-02-15
tags:
- model
- workflow
options:
  token_size: 1007
  id: 26027
  status: accepted
  superseded_by: null
  type: adr
  version: 1.0.0
  birth: '2026-02-15'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Tool-Agnostic Model Selection Heuristic Based on the Reasoning-Class
  vs Agentic-Class Taxonomy..
---
# ADR-26027: Model Taxonomy: Reasoning-Class vs Agentic-Class Selection Heuristic

## Title

Tool-Agnostic Model Selection Heuristic Based on the Reasoning-Class vs Agentic-Class Taxonomy.

## Status

Accepted

Supersedes: {term}`ADR-26006`, {term}`ADR-26008`

## Date

2026-02-15

## Context

{term}`ADR-26006` and {term}`ADR-26008` introduced a valuable model taxonomy — distinguishing **Reasoning-Class** models (optimized for abstract synthesis and deep logic) from **Agentic-Class** models (optimized for instruction adherence and tool-use precision). However, both ADRs bind this taxonomy to a specific toolchain (`aidx`/`aider` phases), creating an unnecessary coupling between a general selection principle and a particular orchestration tool.

The AI engineering landscape has evolved:

* **Convergent model capabilities**: Modern frontier models increasingly combine strong reasoning with high instruction adherence, blurring the rigid two-class separation.
* **Tool-agnostic methodology**: This repository teaches principles that apply regardless of whether the practitioner uses `aider`, Claude Code, Cursor, or a custom agentic system.
* **Selection heuristic, not phase mandate**: The taxonomy is most useful as a *heuristic for choosing the right model for a given cognitive task*, not as a rigid mapping of model classes to pipeline phases.

## Decision

We adopt the Reasoning-Class vs Agentic-Class taxonomy as a **tool-agnostic selection heuristic** for AI engineering workflows.

1. **Two cognitive axes** (not rigid classes):
   * **Reasoning axis**: Abstract synthesis capacity, GPQA/AIME ceiling, ability to challenge assumptions and surface hidden architectural contradictions.
   * **Agentic axis**: Instruction adherence, tool-use precision, deterministic output structure, ability to follow templates without drift.

2. **Selection by task, not by pipeline phase**: Choose models based on the cognitive demands of the task at hand:
   * **Discovery and requirements engineering** → prioritize the reasoning axis.
   * **Structured plan generation and code execution** → prioritize the agentic axis.
   * **Verification and audit** → prioritize both axes (System 2 reasoning with structured output).

3. **No tool coupling**: This heuristic applies equally to web chat interfaces, CLI agents, IDE copilots, and custom orchestration systems. No specific tool is mandated.

4. **Hybrid models acknowledged**: Modern models may score high on both axes. The taxonomy remains useful as a *lens for evaluating fitness*, not as a binary classifier.

## Consequences

### Positive

* **Portable knowledge**: Practitioners can apply this selection heuristic regardless of their toolchain.
* **Future-proof**: As models evolve, the two-axis framework accommodates hybrid capabilities without requiring a new ADR.
* **Preserved value**: The core insight from ADR-26006 and ADR-26008 — that different cognitive tasks demand different model strengths — is retained and generalized.

### Negative

* **Less prescriptive**: Practitioners must evaluate models against both axes rather than following a simple "use model X for phase Y" rule. **Mitigation**: The [Model Classification notebook](/ai_system_layers/2_model/selection/general_purpose_vs_agentic_models.ipynb) provides concrete examples and a decision matrix.

## Alternatives

* **Retain ADR-26006 and ADR-26008**: Rejected. Their coupling to `aidx` phases contradicts the repository's tool-agnostic goals.
* **Abandon the taxonomy entirely**: Rejected. The reasoning/agentic distinction remains a valuable selection heuristic even as models converge.

## References

* {term}`ADR-26006`: Requirement for Agentic-Class Models for the Architect Phase (superseded)
* {term}`ADR-26008`: Selection of Reasoning-Class Models for Abstract Synthesis (superseded)
* [General Purpose vs Agentic Models](/ai_system_layers/2_model/selection/general_purpose_vs_agentic_models.ipynb) — detailed classification and decision matrix

## Participants

1. Vadim Rudakov
2. Claude Opus 4.6
