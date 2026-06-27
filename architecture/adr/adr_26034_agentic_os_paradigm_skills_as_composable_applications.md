---
id: 26034
title: 'Agentic OS Paradigm: Skills as Composable Applications'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: 2026-02-25.
tags:
- context_management
date: 2026-02-25
options:
  type: adr
  birth: '2026-02-25'
  version: 1.0.0
  token_size: 1390
  status: rejected
  superseded_by: null
---
# ADR-26034: Agentic OS Paradigm: Skills as Composable Applications

## Date
2026-02-25

## Status
rejected

## Rejection Rationale

The "Agentic OS" framing — treating the agent as a full operating system with processors, OS layers, and applications — led to top-down architectural design (VFS, VRL, Document Type Registry) that was growing in complexity without a working runtime to validate it. A comprehensive landscape analysis ([A-26009](/architecture/evidence/analyses/A-26009_compass_realistic_state_of_agentic_ai_2026.md)) revealed that production agent success correlates with context engineering simplicity, not architectural sophistication.

{term}`ADR-26038` replaces the grand OS framing with **context engineering as the core design principle**: single-agent with skill dispatch, three-tier memory, and context budget as a first-class constraint. The valid concepts from this ADR survive:

- **Skills as composable units** — formalized in {term}`ADR-26038` as progressive disclosure units with SKILL.md format, fully specified in [ADR-26044](/architecture/adr/adr_26044_skills_as_progressive_disclosure_units.md)
- **Three-tier architecture (LLM / Agent / Skills)** — reframed as three-tier memory (working / episodic / semantic) in {term}`ADR-26038`
- **Procedural vs declarative knowledge split** — preserved in {term}`ADR-26032` as an orthogonal concern
- **SKILL.md + tools/ + tests/ folder structure** — validated by cross-vendor convergence (Anthropic, OpenAI) documented in [A-26009](/architecture/evidence/analyses/A-26009_compass_realistic_state_of_agentic_ai_2026.md)

The OS metaphor remains useful for communication but is no longer the architectural driver.

## Context
In the search for a viable, composable, and production-level architecture for a spoke repo "Mentor Generator," we must recognize that the paradigm has shifted from **monolithic prompting** to a **layered ["Agentic OS"](https://www.youtube.com/watch?v=CEvIs9y1uog) strategy**.

A production-grade agent is not just an LLM with a long system message; it is a system of **portable, versioned, and executable expertise**. 

Adopt the 3 Tier Architecture: LLM, Agent, Skills.

### 1. The 3-Tier Architecture of Expertise

Instead of a single JSON blob, we now treat the agent's brain as a stack of three distinct, decoupled layers. This separation prevents the "role confusion" and "state drift" identified in mentor generator experiments (see mentor_generator/docs/architecture/ docs).

* **Skills (The "How"):** Procedural, versioned knowledge. These are the "apps" of the Agentic OS. By moving these to a code-accessible `skills/` directory, we ensure they are **executable** and **testable** independently of the agent's specific subject matter.
* **Projects/Context (The "What"):** Grounding data. This includes the knowledge base, docs, databases, etc. This is the RAG - the **state** that the OS manages, kept distinct from the logic to avoid cognitive overload.
* **Orchestration (The "Universal Interface"):** The "Code is the universal interface" principle - the agent interacts with its environment—and its own memory—through typed, versioned tool calls (MCP, filesystem scripts, etc.) rather than loose narrative instructions.

### 2. From Instructions to Constraints

Our core insight from the mentor generator experiments is that **predictability comes from constraints, not instructions**.

* **The Template as Jail:** In "Mentor Generator," we moved from telling the LLM to "be a good teacher" to forcing it to fill a strictly validated 30-line YAML template. The template acts as the hardware spec of the Agentic OS.

### 3. Portability via "Code as Interface"

The goal of making expertise "portable" means a Skill created in this repository should be executable by any agentic system (Claude Code, a local Ollama instance, or a production RAG pipeline) because it adheres to a standard folder structure:

* `SKILL.md`: The procedural logic.
* `tools/`: The executable scripts (Python/Bash).
* `tests/`: Golden-file fixtures that verify the skill's logic with zero API calls.

## Decision
Adopt the **Agentic OS Paradigm** for agents built by the our organization:
1. **The Processor:** The LLM (Reasoning or Agentic class).
2. **The OS:** The Agent Runtime (file system, Python interpreter, MCP).
3. **The Skills:** Atomic folders containing `SKILL.md` and `/scripts`.

## Consequences

### Positive
- **Transferability:** Skills can be maintained and distributed via `uv` packages across the org.

## Alternatives
- **Instruction-Only Agents (The Status Quo):** Relying on massive system prompts to explain domain logic. **Rejection Reason:** Non-deterministic. As logic becomes complex (e.g., tax law), prompts fail where code succeeds. Leads to "Cognitive Overload" noted in mentor generator's post-mortem analyses.
- **Tool-Calling Without Procedural Code:** Using only external APIs (MCP) for all logic. **Rejection Reason:** Requires an active server for every small task. Local scripts in a "Skill" folder are more resilient and faster for deterministic data transformation.

## References
- Mentor Generator: Problem Catalog v0.41.0 - docs/architecture/research/v0.41.0/problem_catalog_v0.41.md
- [Don't Build Agents, Build Skills Instead – Barry Zhang & Mahesh Murag, Anthropic](https://www.youtube.com/watch?v=CEvIs9y1uog) - Video

## Participants
1. Vadim Rudakov
2. Gemini (Principal Systems Architect)
