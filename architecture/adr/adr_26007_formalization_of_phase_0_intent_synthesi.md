---
id: 26007
title: 'Formalization of Phase 0: Intent Synthesis (Requirements Engineering)'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Phase 0 Intent Synthesis is a mandatory human-lead + reasoning-model
  gateway before any aidx session, producing a Mission artifact that grounds all subsequent
  phases.
tags:
- workflow
- model
date: 2026-04-01
options:
  type: adr
  birth: 2026-01-24
  version: 1.0.1
  token_size: 873
  status: superseded
  superseded_by: ADR-26028
---
# ADR-26007: Formalization of Phase 0: Intent Synthesis (Requirements Engineering)

## Title

Standardizing a "Human-Lead + Reasoning LLM" Requirements Engineering phase (Phase 0) to eliminate architectural drift in the `aidx` pipeline.

## Status

Superseded

Superseded by: {term}`ADR-26028`

## Supersession Rationale

This ADR coupled the Intent Synthesis principle to the `aidx` pipeline's specific artifact format (`artifacts/MISSION_ID.md`), making the principle inaccessible to practitioners using other orchestration tools. {term}`ADR-26028` restates the principle in tool-agnostic terms applicable to any human-lead + reasoning-model discovery workflow.

## Date

2026-01-16

## Context

The current `aidx` industrial framework ({term}`ADR-26005`) initiates with **Phase 1: Research**. However, this assumes that the initial problem statement is sufficiently specified and free of business-logic ambiguities. In practice, starting the automated "Research-Apply" pipeline with an underspecified prompt leads to:

* **Token Waste**: Local 14B editors and cloud architects re-rolling logic due to unclear goals.
* **Cognitive Bottlenecks**: Local models failing to resolve multi-agent role definitions or complex business constraints.
* **Requirements Volatility**: Significant changes to `artifacts/plan.md` during implementation because the initial intent was not synthesized.

## Decision

We will implement a mandatory **Phase 0: Intent Synthesis** (Requirements Engineering) gateway before any `aidx` session.

1. **Lead-Driven Discovery**: A Human Lead utilizes a high-reasoning web-based model (e.g., Gemini Thinking/Pro) to stress-test the problem statement, clarify business goals, and define the high-level system architecture.
2. **Artifact Generation**: The output of Phase 0 must be a formal `artifacts/MISSION_ID.md` (or `artifacts/agents.md`) file.
3. **The Mission Contract**: This artifact serves as the "source of truth" for **Phase 2 (Architect)**, ensuring that technical planning is grounded in a verified business intent.
4. **Traceability**: All subsequent code changes must be traceable back to the specific goals defined in the Phase 0 Mission artifact.

## Consequences

### Positive

* **Zero-Drift Execution**: High-fidelity intent ensures the `aidx` pipeline operates on a "Contract of Intent".
* **Reduced Cognitive Load**: Offloads abstract ambiguity resolution to high-reasoning models before local hardware is engaged.
* **ISO 29148 Compliance**: Establishes a formal Requirements Elicitation process as per international standards.

### Negative

* **Increased Human Involvement**: Requires the Lead to participate in an initial discovery chat before automation starts.
* **Manual Handoff**: The Mission artifact must be manually or semi-automatically moved from the web chat environment to the local repository. **Mitigation**: Use standardized MyST-Markdown templates to ensure copy-paste compatibility.

## Alternatives

* **Automated Intent Prediction**: Rejected. Human-in-the-Loop is mandatory on the Requirements Engineering step.

## References

* {term}`ADR-26005`: Formalization of Aider as Primary Agentic Orchestrator
* ISO 29148: Requirements Engineering

## Participants

1. Vadim Rudakov
2. Senior AI Systems Architect
