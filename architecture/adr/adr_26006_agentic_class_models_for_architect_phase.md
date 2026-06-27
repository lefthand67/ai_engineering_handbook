---
id: 26006
title: Requirement for Agentic-Class Models for the Architect Phase
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Agentic-Class models (high instruction adherence) are required for the
  aidx Architect phase to prevent instruction drift in generated plans.
tags:
- model
- workflow
date: 2026-04-01
options:
  type: adr
  birth: 2026-01-24
  version: 1.0.1
  token_size: 1329
  status: superseded
  superseded_by: ADR-26027
---
# ADR-26006: Requirement for Agentic-Class Models for the Architect Phase

## Title

Standardizing the use of Agentic-Class LLMs for the `aidx` Architect Phase to Ensure Logic Rigidity and Execution Integrity.

## Status

Superseded

Superseded by: {term}`ADR-26027`

## Supersession Rationale

This ADR bound the model selection taxonomy (Agentic-Class vs. Reasoning-Class) to the `aidx` orchestration framework, creating unnecessary coupling between a general selection principle and a particular toolchain. {term}`ADR-26027` decouples the taxonomy into a tool-agnostic selection heuristic applicable to any agent orchestration approach.

## Date

2026-01-15

## Context

As defined in {term}`ADR-26005`, the `aidx` framework utilizes a **Two-Pass Hybrid Bridge** pattern to decouple architectural planning from code implementation. This pattern relies on a high-reasoning "Cloud Architect" to generate a standalone `artifacts/plan.md` file, which is subsequently applied by a "Local Editor".

The current implementation faces a critical quality bottleneck in the planning stage:

* **Instruction Drift**: General-purpose models (optimized for abstract synthesis) often treat system-level instructions as "suggestions," leading to "Pro Polish" debt—recommending patterns that are too complex for local 14B editors to implement.
* **Agentic Precision Requirement**: The Architect role is fundamentally an agentic task requiring strict adherence to templates and technical constraints to prevent the "Context Truncation Risk" during hand-off.
* **Logic Rigidity**: The Architect must act as a logic gate, verifying the findings of the **Agentic RAG Researcher** ({term}`ADR-26004`) and translating them into a verifiable plan.

General-purpose models prioritize creativity and conversational nuance, which introduces non-deterministic noise into the technical pipeline. Conversely, **Agentic-class models** (e.g., Gemini 3 Flash) are purpose-built for high instruction adherence and tool-use precision, making them the appropriate tool for this specific agentic purpose.

## Decision

We mandate the use of **Agentic-Class models** (prioritizing **Instruction Adherence** over Abstract Synthesis) for the Architect role within the `aidx` framework. See ["General Purpose (Abstract Synthesis) vs Agentic (Instruction Adherence) Models"](/ai_system_layers/2_model/selection/general_purpose_vs_agentic_models.ipynb)

1. **Model Classification**: Only models verified for "High Instruction Adherence" (e.g., Gemini 3 Flash, Claude 3.7/4.0 Sonnet) are permitted for the Architect role.
2. **Primary Choice**: **Gemini 3 Flash** (in **Thinking: High** mode) is established as the default Architect model due to its high "Intelligence Density" and 2026 benchmarks for agentic rigidity.
3. **Artifact Enforcement**: The Architect must strictly output the `artifacts/plan.md` using the templates defined in the `aidx` wrapper to ensure the local editor receives a high-integrity instruction set.
4. **Logic Interrogation**: The Architect must be prompted to perform an audit of its own plan, identifying potential implementation bottlenecks for the local 14B editor before finalization.

## Consequences

### Positive

* **Deterministic Hand-off**: Agentic models produce plans that strictly follow technical protocols, reducing the risk of malformed inputs for the local editor.
* **Improved Local Success Rate**: By leveraging models that understand execution-level constraints, we minimize the "Execution Gap" where local models attempt to implement overly-abstract cloud logic.
* **Architectural Traceability**: The rigid structure of agentic output provides a better audit trail for automated system verification.

### Negative

* **Reduced Abstract Breadth**: Agentic models may lack the "Blue-Sky" creativity of general-purpose models. **Mitigation**: Ensure the human-led discovery phase (pre-aidx, see further ADRs) handles abstract exploration.
* **Model Dependency**: Formalizes a dependency on specific "Agentic" tiers of cloud providers. **Mitigation**: Use a common interface (e.g., LiteLLM) to swap between Agentic models like Flash and Sonnet as needed.
* **Model Version Drift:** Ensure the `aidx` framework pins specific model versions (e.g., `gemini-3-flash-001`) to prevent your "Step 0" logic from breaking after a silent cloud update.

## Alternatives

* **General-Purpose Models (e.g., Gemini 3 Pro, GPT-5)**: Rejected for the Architect role. Their focus on abstract synthesis leads to instruction drift and overly-verbose plans that exceed the "Attention" window of local editors.
* **Local 14B Models (Native `/architect` mode)**: Rejected due to GPU OOM (Out of Memory) errors and the "Switching Moment" bottleneck where local models fail to maintain plan integrity over long session histories.

## References

* {term}`ADR-26004`: Implementation of Agentic RAG for Autonomous Research
* {term}`ADR-26005`: Formalization of Aider as Primary Agentic Orchestrator
* ["General Purpose (Abstract Synthesis) vs Agentic (Instruction Adherence) Models"](/ai_system_layers/2_model/selection/general_purpose_vs_agentic_models.ipynb)
* ISO 29148: Systems and Software Engineering — Requirements Engineering
* SWEBOK Guide V4.0 - Software Engineering Body of Knowledge

## Participants

1. Vadim Rudakov
2. Senior AI Architect (Gemini 3 Flash)
