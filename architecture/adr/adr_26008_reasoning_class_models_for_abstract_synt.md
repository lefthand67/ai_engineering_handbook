---
id: 26008
title: Selection of Reasoning-Class Models for Abstract Synthesis (Phase 0)
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Reasoning-Class models (high abstract synthesis) are required for Phase
  0 to resolve requirements ambiguity before the aidx pipeline engages local hardware.
tags:
- model
- workflow
date: 2026-04-01
options:
  type: adr
  birth: 2026-01-24
  version: 1.0.1
  token_size: 1021
  status: superseded
  superseded_by: ADR-26027
---
# ADR-26008: Selection of Reasoning-Class Models for Abstract Synthesis (Phase 0)

## Title

Mandating the use of General-Purpose "Reasoning-Class" LLMs for Phase 0 to ensure maximum logic depth and abstract synthesis.

## Status

Superseded

Superseded by: {term}`ADR-26027`

## Supersession Rationale

This ADR bound the Reasoning-Class model requirement to Phase 0 of the `aidx` framework, coupling a general selection heuristic to a specific toolchain. Together with {term}`ADR-26006`, it was superseded by {term}`ADR-26027`, which defines the Reasoning-Class vs. Agentic-Class taxonomy as a tool-agnostic selection principle.

## Date

2026-01-16

## Context

As established in {term}`ADR-26006`, the **Phase 2 (Architect)** role requires **Agentic-Class** models optimized for "Workflow Adherence" and rigid instruction following. However, **Phase 0 (Intent Synthesis)** {term}`ADR-26007` represents a different cognitive requirement:

* **Abstract Synthesis**: The model must synthesize vague human ideas into a cohesive, structured architectural plan.
* **Reasoning Ceiling**: High-level logic (e.g., GPQA Diamond benchmarks) is required to identify hidden technical debt or architectural contradictions before they reach the local editor.
* **Conversational Nuance**: Unlike the "Rigid Architect," the Phase 0 model must be a "Thinking Partner" capable of multi-modal analysis and deep-dive logic.

## Decision

We mandate the use of **Reasoning-Class (Abstract Synthesis)** models for the Phase 0 gateway.

1. **Primary Criteria**: Models must be selected based on their **Reasoning Ceiling** (GPQA/AIME scores) rather than instruction adherence alone.

2. **Permitted Models**: Only SOTA reasoning models are approved for this phase. The actual list of models is available in ["General Purpose (Abstract Synthesis) vs Agentic (Instruction Adherence) Models"](/ai_system_layers/2_model/selection/general_purpose_vs_agentic_models.ipynb) and should be considered the Single Source of Truth when choosing the model.

3. **Role Separation**: These models are strictly forbidden for the **Phase 2 (Architect)** role (unless configured in a high-adherence sub-mode) to prevent "Instruction Drift".

## Consequences

### Positive

* **High-Fidelity Planning**: Leveraging the logic ceiling of the world's most capable models ensures a robust foundation for the local stack.
* **Ambiguity Resolution**: These models excel at identifying what the Human Lead *didn't* say, preventing downstream hallucinations.

### Negative

* **High Latency/Cost**: Reasoning-class models are significantly slower and more expensive than the Agentic-class models (like Gemini 3 Flash) used in Phase 2. **Mitigation**: Since this is a one-time "Phase 0" gateway, the cost is offset by the reduction in token waste during Phase 2 and 3.
* **Reduced Instruction Adherence**: These models may attempt to "over-engineer" the plan. **Mitigation**: The Human Lead must strictly enforce the use of the `aidx` templates during the final mission synthesis.

## Alternatives

* **Using Agentic Models (Phase 2 Models) for Phase 0**: Rejected. Models like Gemini 3 Flash (non-thinking mode) are optimized for speed and adherence but often lack the "Deep Thinking" necessary for complex problem elaboration.

## References

* {term}`ADR-26005`: Formalization of Aider as Primary Agentic Orchestrator
* {term}`ADR-26006`: Requirement for Agentic-Class Models for the Architect Phase
* {term}`ADR-26007`: Formalization of Phase 0: Intent Synthesis (Requirements Engineering)
* ["General Purpose (Abstract Synthesis) vs Agentic (Instruction Adherence) Models"](/ai_system_layers/2_model/selection/general_purpose_vs_agentic_models.ipynb)

## Participants

1. Vadim Rudakov
2. Senior AI Systems Architect
