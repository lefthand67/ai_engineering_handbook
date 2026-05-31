---
title: Cross-Agent Standardization via Symlinked Governance Files
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: 2026-05-31
description: Implementing a Single Source of Truth (SSoT) for agent instructions by
  symlinking agent-specific files (QWEN.md, CLAUDE.md) to a central AGENTS.md.
tags:
- governance
- agents
- architecture
options:
  id: 26051
  token_size: 1018
  type: adr
  status: accepted
  superseded_by: null
  birth: 2026-05-31
  version: 1.0.0
---
# ADR-26051: Cross-Agent Standardization via Symlinked Governance Files

## Date
2026-05-31

## Status

accepted

## Context
Modern software development increasingly involves a variety of AI agents (e.g., Qwen Code, Claude Code, Aider). Each of these agents typically looks for a specific "instruction file" in the repository root to understand project conventions and constraints (e.g., `QWEN.md`, `CLAUDE.md`, `.aider.conf.yml`).

Maintaining separate copies of these instruction files leads to several critical issues:
1.  **Instruction Drift**: Updates to project standards are applied inconsistently across files, leading to different agents following different versions of the rules.
2.  **Maintenance Overhead**: A single change in project governance requires editing multiple files, increasing the risk of human error and omission.
3.  **Fragmented Behavior**: The "developer experience" becomes agent-dependent, where one agent adheres to the architectural standards while another ignores them because its specific instruction file was not updated.

## Decision
We will implement a **Cross-Agent Standardization Layer** using the filesystem's symbolic link (symlink) capability.

### 1. The Single Source of Truth (SSoT)
The file `AGENTS.md` is designated as the authoritative source of all agent instructions, governance rules, and operational protocols for the repository.

### 2. Interface Mapping via Symlinks
For every AI agent utilized in the project, a symlink will be created from the agent's expected filename to the central `AGENTS.md` file.

**Mandatory Mapping:**
- `QWEN.md` $\rightarrow$ `AGENTS.md`
- `CLAUDE.md` $\rightarrow$ `AGENTS.md`
- `CONVENTIONS.md` $\rightarrow$ `AGENTS.md`
- (And any other agent-specific filenames identified during tool adoption).

### 3. Modification Protocol
All edits to agent instructions must be performed directly on `AGENTS.md`. Modifying the symlinks or attempting to replace them with independent files is strictly prohibited.

## Consequences

### Positive
- **Guaranteed Consistency**: Every agent, regardless of the platform, reads the exact same instructions at the exact same time.
- **Zero-Cost Propagation**: A single edit to `AGENTS.md` is instantaneously propagated to all agents.
- **Simplified Auditing**: Governance auditors only need to review one file to verify the current state of agent instructions.
- **Agent Agnosticism**: The project's governance is decoupled from the specific agent tool being used, allowing for seamless switching between different AI providers.

### Negative / Risks
- **Lack of Agent-Specific Tuning**: This approach prevents the use of agent-specific formatting or "hints" that might only work for one model. **Mitigation**: General patterns are used in `AGENTS.md`, and highly specific tool-based instructions are moved into Modular SOPs (Skills), which are invoked by the agent based on the tool they are currently using.
- **Symlink Breakage**: Accidental deletion or replacement of the symlink with a real file. **Mitigation**: Pre-commit hooks or CI checks can be implemented to verify that `QWEN.md` and `CLAUDE.md` remain valid symlinks to `AGENTS.md`.

## Alternatives
- **Manual Synchronization**: Using a script to copy content from a master file to agent-specific files. **Rejection Reason**: Introduces a "synchronization lag" and depends on the script running successfully; symlinks provide atomic, real-time synchronization.
- **Universal Configuration File**: Attempting to force all agents to read a single, non-standard filename. **Rejection Reason**: AI agents are hard-coded to look for specific filenames; we cannot change the agent's internal logic, so we must adapt the repository's structure to match the agent's interface.

## References
- [ADR-26055: Transition from Monolithic Instruction Push to Modular Knowledge Pull](/architecture/adr/adr_26055_modular_knowledge_pull_architecture.md)

## Participants
1. Vadim Rudakov
2. Qwen Code
