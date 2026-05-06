
---
title: Formalization of Aider as the Primary Agentic Orchestrator
date: 2026-01-24
tags:
- workflow
options:
  token_size: 1212
  id: 26005
  status: rejected
  superseded_by: null
  type: adr
  version: 1.0.0
  birth: '2026-01-24'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Standardizing AI-assisted development and automation using the `aider`
  orchestration framework in a Hybrid Architect-Editor configuration..
---
# ADR-26005: Formalization of Aider as the Primary Agentic Orchestrator

## Title

Standardizing AI-assisted development and automation using the `aider` orchestration framework in a Hybrid Architect-Editor configuration.

## Status

Rejected

## Rejection Rationale

This ADR formalizes `aider` as the primary agentic orchestrator via the Hybrid Bridge pattern. The repository's methodology has since evolved toward **tool-agnostic** AI engineering principles — mandating a specific CLI tool as the orchestration backbone contradicts this goal, and the author plans to build custom agentic systems.

The underlying concepts remain valid:

* **Hybrid Bridge pattern**: Decoupling cloud-based planning from local execution to manage VRAM constraints is a sound architectural pattern applicable to any tool pairing.
* **State isolation**: Launching the execution agent with a clean context (receiving only the plan artifact) prevents context overload regardless of the specific tool used.

These patterns are documented elsewhere in the repository without tool-specific coupling.

## Date

2026-01-14

## Context

Our environment requires high-integrity CI/CD and automation while operating on bare-metal systems with limited VRAM (Fedora/Debian stack). We face a critical "Switching Moment" bottleneck where local 14B models (e.g., `qwen2.5-coder`) suffer from context overload and GPU crashes when inheriting full conversational histories from high-reasoning cloud models. Furthermore, we must adhere to:

* {term}`ADR-26001`: Python/OOP standards for all automation logic.
* {term}`ADR-26002`: Orchestration via the `pre-commit` framework.
* {term}`ADR-26003`: Strict Tiered Workflow enforcement via `gitlint`.
* {term}`ADR-26004`: Integration with Agentic RAG for knowledge retrieval.

## Decision

We will adopt `aider` as our primary agentic tool, implemented through a **Two-Pass Hybrid Bridge** to maintain architectural integrity and resource efficiency.

1. **Hybrid Configuration**: We will utilize a Cloud Architect (e.g., Gemini 3 Flash) for high-reasoning planning and a Local Editor (e.g., Qwen2.5-Coder 14B) for code implementation.
2. **State Isolation (The Bridge Pattern)**: To prevent VRAM crashes, the Architect and Editor phases will be decoupled. The Architect will generate a standalone `artifacts/plan.md` file, and the Editor will be initialized with a clean context to apply only that plan.
3. **OOP Python Wrapper**: Following {term}`ADR-26001`, we will not use raw Shell scripts for complex aider workflows. Instead, we will use the `aider` Python API (`aider.coders`) to build testable, class-based orchestrators (e.g., an `aidx` utility).
4. **Workflow Enforcement**: Aider's execution will be gated by `pre-commit` hooks and `gitlint` to ensure all generated code and commits meet Tier 3 standards.

## Consequences

### Positive

* **VRAM Stability**: Decoupling the "Architect" reasoning from the "Editor" execution prevents the  context growth that crashes local 14B models.
* **Data Sovereignty**: Highly sensitive code-writing tasks remain local, while only abstract planning is sent to cloud APIs.
* **Architectural Traceability**: Formalizing plans in `artifacts/plan.md` provides an audit trail for AI decisions.
* **ADR Compliance**: Using the Python API ensures all AI orchestration logic is unit-testable via `pytest` per {term}`ADR-26001`.

### Negative

* **Manual Bridge Overhead**: The Two-Pass approach requires explicit hand-off between planning and execution phases. **Mitigation**: Automate this via the `HybridOrchestrator` Python class and `aidx` (see {term}`ADR-26004`) wrapper.
* **Context Truncation Risk**: The Editor may lack "conversational nuance" if the Architect's plan is underspecified. **Mitigation**: Use strict MyST/Markdown templates for the Architect's output to ensure all technical requirements are captured.

## Alternatives

* **Native `/architect` Mode**: Rejected due to persistent GPU OOM (Out of Memory) errors on 14B models when handling long session histories and files in context.
* **Custom Agent Framework (LangGraph/AutoGPT)**: Rejected as it violates SVA (Smallest Viable Architecture) by adding unjustified orchestration layers and vendor lock-in.

## References

* {term}`ADR-26001`: Use of Python and OOP for Git Hook Scripts
* {term}`ADR-26002`: Adoption of the Pre-commit Framework
* {term}`ADR-26003`: Adoption of gitlint for Tiered Workflow Enforcement
* {term}`ADR-26004`: Implementation of Agentic RAG for Autonomous Research
* [Aider Scripting Documentation](https://aider.chat/docs/scripting.html)

## Participants

1. Vadim Rudakov
2. Senior DevOps Systems Architect (Gemini 3 Flash)
