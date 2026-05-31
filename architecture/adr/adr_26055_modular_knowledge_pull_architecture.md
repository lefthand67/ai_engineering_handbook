---
title: Transition from Monolithic Instruction Push to Modular Knowledge Pull
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: 2026-05-31
description: Shift from exhaustive system prompts to a routing-based architecture
  using a minimalist Constitution (QWEN.md) and modular SOPs (Skills).
tags:
- governance
- agents
- context_management
- architecture
options:
  id: 26055
  token_size: 1200
  type: adr
  status: proposed
  superseded_by: null
  birth: 2026-05-31
  version: 0.1.0
---
# ADR-26055: Transition from Monolithic Instruction Push to Modular Knowledge Pull

## Date
2026-05-31

## Status

proposed

## Context
The project currently utilizes `QWEN.md` and `AGENTS.md` as the primary vehicles for transmitting rules, conventions, and workflows to AI agents. As the project grows, this "Push" model—where all instructions are loaded into the system prompt—has encountered several critical failure modes:

1.  **Instruction Drift**: Overlapping or conflicting rules emerge as new instructions are appended without a systematic audit of existing ones.
2.  **Context Window Exhaustion (Token Bombs)**: Large volumes of detailed workflows (e.g., release management) consume significant token space, increasing costs and causing the agent to "forget" primary invariants.
3.  **The "Needle in a Haystack" Problem**: High-priority rules (e.g., absolute path requirements) are diluted by low-priority procedural details, leading to intermittent adherence failures.
4.  **Discovery Latency**: Agents often attempt to "guess" the correct way to perform a complex task rather than searching for the existing documented SOP because the prompt does not explicitly route them to a discovery process.

## Decision
We will transition from a Monolithic Instruction Push to a **Modular Knowledge Pull Architecture**. This system splits knowledge into two distinct tiers:

### 1. Tier 1: The Constitution (`QWEN.md`)
`QWEN.md` will be stripped of all detailed procedural workflows and reduced to a minimalist "Routing Layer." Its primary functions are:
- **Global Invariants**: Define "Always" and "Never" rules that apply to 100% of agent turns (e.g., absolute paths, Podman over Docker).
- **Discovery Routing**: Instruct the agent on how to discover specialized knowledge using the Skills system and documentation frontmatter.
- **Constraint Enforcement**: Act as the final arbiter of project-wide constraints.

### 2. Tier 2: Modular Standard Operating Procedures (SOPs) (Skills & Frontmatter)
Complex, scenario-specific workflows will be moved into specialized Skills (located in `.qwen/skills/`) and project documentation.
- **Modularization**: Every complex process (e.g., "API Change Propagation") will have its own dedicated Standard Operating Procedure (SOP) file.
- **Pull-Based Activation**: The agent is required to "pull" the relevant SOP by invoking the corresponding skill tool only when the task matches the skill's purpose.
- **Frontmatter-Driven Discovery**: Both Skills and documentation will use a standardized YAML frontmatter (per ADR-26042) containing `tags`, `description`, and `type`, enabling the agent to programmatically search and select the correct SOP.

### 3. Operational Framework (`AGENTS.md`)
`AGENTS.md` will be restructured from a list of rules into an **Operational Manual**. It will define the "How" of agent behavior, specifically the mandatory loop:
`Task Analysis` $\rightarrow$ `Knowledge Discovery (Pull)` $\rightarrow$ `SOP Application` $\rightarrow$ `Verification`.

## Consequences

### Positive
- **Reduced Cognitive Load**: Agents operate with a lean system prompt, leading to higher adherence to primary invariants.
- **Elimination of Token Bombs**: Detailed workflows are loaded into context only when needed, preserving the window for actual task execution.
- **Higher Precision**: By following a specific SOP rather than a general set of rules, the agent's output becomes deterministic and consistent.
- **Easier Maintenance**: SOPs can be updated independently without risking regressions in the global system prompt.

### Negative / Risks
- **Increased Tool Dependency**: The agent must be proficient in using discovery tools (`grep`, `glob`, `read_file`) to find the right skill. **Mitigation**: The "Discovery Protocol" in the new `AGENTS.md` will explicitly mandate this behavior.
- **Frontmatter Fragility**: If a skill's frontmatter is poorly defined, the agent may fail to "pull" it. **Mitigation**: Implement validation scripts to ensure all skills have correct, searchable frontmatter.

## Alternatives
- **Expanding Context Windows**: Relying on larger LLM context windows to handle the bloat. **Rejection Reason**: While windows are larger, "lost-in-the-middle" phenomena and token costs make this an inefficient and unreliable long-term strategy.
- **Agent Personas**: Creating different system prompts for different roles (e.g., "Release Agent"). **Rejection Reason**: Increases operational complexity and prevents a single agent from handling multi-disciplinary tasks in one session.

## References
- [ADR-26042: Common Frontmatter Standard](/architecture/adr/adr_26042_common_frontmatter_standard.md)
- [ADR-26050: Tool-Driven Instructional Feedback for Agents](/architecture/adr/adr_26050_tool_driven_instructional_feedback_for_agents.md)
- SOPs in `.qwen/skills/`

## Participants
1. Vadim Rudakov
2. Qwen Code
