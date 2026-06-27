---
id: 26028
title: 'Tool-Agnostic Phase 0: Intent Synthesis'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Formalizing a Tool-Agnostic "Human-Lead + Reasoning-Class Model" Requirements
  Engineering Phase (Phase 0) Before Automated Execution..
tags:
- workflow
- model
date: 2026-02-15
options:
  type: adr
  birth: '2026-02-15'
  version: 1.0.0
  token_size: 1182
  status: accepted
  superseded_by: null
---
# ADR-26028: Tool-Agnostic Phase 0: Intent Synthesis

## Title

Formalizing a Tool-Agnostic "Human-Lead + Reasoning-Class Model" Requirements Engineering Phase (Phase 0) Before Automated Execution.

## Status

Accepted

Supersedes: {term}`ADR-26007`

## Date

2026-02-15

## Context

{term}`ADR-26007` established the principle of **Phase 0: Intent Synthesis** — a mandatory human-led discovery step using a reasoning-class model before any automated execution begins. This principle is sound and prevents architectural drift caused by underspecified prompts entering automated pipelines.

However, ADR-26007 couples the concept to the `aidx` pipeline and its specific artifact format (`artifacts/MISSION_ID.md`), making the principle inaccessible to practitioners using other tools.

The core insight is tool-agnostic:

* **Starting automated execution with an underspecified prompt wastes tokens and produces drift.** This is true regardless of whether the execution tool is `aider`, Claude Code, Cursor, or a custom agent.
* **Human-led discovery with a reasoning-class model resolves ambiguity before automation begins.** The model's role is to stress-test the problem statement, surface hidden constraints, and produce a clear intent specification.

## Decision

We formalize **Phase 0: Intent Synthesis** as a tool-agnostic requirements engineering gateway.

1. **Principle**: Before any automated code generation session, the Human Lead conducts a discovery conversation with a **reasoning-class model** (see {term}`ADR-26027`) to clarify business goals, identify constraints, and define the scope of work.

2. **Primary implementation — Consultant Prompts**: This repository provides structured JSON prompts (e.g., [`ai_systems_consultant.json`](/ai_system_layers/3_prompts/consultants/ai_systems_consultant.json), [`handbook_consultant.json`](/ai_system_layers/3_prompts/consultants/handbook_consultant.json)) that encode the project's methodology (WRC scoring, Simplest Viable Architecture, peer review protocols). These prompts are the recommended Phase 0 interface and can be loaded into any capable reasoning-class model via a web chat interface or API.

3. **Artifact output**: The Phase 0 conversation must produce a written specification (format is flexible — plan file, ADR draft, issue description, or structured prompt) that serves as the "contract of intent" for subsequent automated execution.

4. **Model selection**: Phase 0 prioritizes the **reasoning axis** from {term}`ADR-26027` — the model must excel at abstract synthesis, assumption-challenging, and architectural reasoning. Instruction adherence is secondary at this stage.

5. **No tool mandate**: Phase 0 can be conducted in any environment — a web chat interface, a CLI tool's planning mode, or a notebook. The principle is the human-led discovery step, not the tool used to perform it.

## Consequences

### Positive

* **Tool portability**: The Phase 0 principle works with any AI tool or interface.
* **Reduced waste**: Clarifying intent before automation prevents token waste from re-rolling underspecified tasks.
* **Methodology encoding**: The consultant prompts in `ai_system/3_prompts/consultants/` embed domain knowledge (ADR conventions, commit standards, testing policies) directly into the Phase 0 conversation, ensuring automated execution starts from a methodology-aligned specification.

### Negative

* **Increased human involvement**: Phase 0 requires the Lead to invest time in discovery before automation starts. **Mitigation**: This upfront cost is offset by reduced iteration and drift downstream.
* **Prompt maintenance**: Consultant prompts must be kept in sync with evolving project conventions. **Mitigation**: Prompts reference ADRs and conventions by structure, not by hardcoded values, and are versioned alongside the codebase.

## Alternatives

* **Skip Phase 0 and rely on automated planning**: Rejected. Without human-led intent synthesis, automated agents optimize for the literal prompt, not the actual goal, leading to architectural drift.
* **Retain ADR-26007**: Rejected. Its coupling to `aidx` artifacts limits applicability.

## References

* {term}`ADR-26007`: Formalization of Phase 0: Intent Synthesis (superseded)
* {term}`ADR-26027`: Model Taxonomy: Reasoning-Class vs Agentic-Class Selection Heuristic
* [`ai_systems_consultant.json`](/ai_system_layers/3_prompts/consultants/ai_systems_consultant.json) — primary Phase 0 consultant prompt
* [`handbook_consultant.json`](/ai_system_layers/3_prompts/consultants/handbook_consultant.json) — methodology-aware handbook consultant
* ISO 29148: Systems and Software Engineering — Requirements Engineering

## Participants

1. Vadim Rudakov
2. Claude Opus 4.6
