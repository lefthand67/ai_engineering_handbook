
---
title: Stateless JIT Context Injection for Agentic Git Workflows
date: 2026-02-24
tags:
- context_management
- git
- workflow
options:
  token_size: 1070
  id: 26030
  status: proposed
  superseded_by: null
  type: adr
  version: 1.0.0
  birth: '2026-02-24'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: 2026-02-24.
---
# ADR-26030: Stateless JIT Context Injection for Agentic Git Workflows

## Date
2026-02-24

## Status
proposed

## Context
Standard agentic workflows rely on stateful "sessions" where chat history is preserved across turns. In the context of local SLM deployment (1B–14B parameters) on Fedora/Debian systems, this "Recursive Context Accumulation" creates two critical failures:
1. **Computational Debt**: Accumulating history consumes VRAM and CPU cycles linearly per turn, leading to performance degradation and context window saturation for models like `qwen2.5-coder` or `ministral`.
2. **State Drift**: LLMs often "hallucinate" based on code discussed in previous turns that may have since been reverted or modified in the actual filesystem.

Furthermore, commercial API usage incurs a "Context Tax"—paying repeatedly for the same history tokens. To satisfy the requirements of **ADR-26024** for a "computational/traceable artifact" (the CHANGELOG), the agent must have a perfectly accurate, high-fidelity view of the current staging area without the noise of conversational history.

## Decision
We will implement the **Stateless JIT (Just-In-Time) Injection** pattern for all Git-interfacing agents. The agent shall be treated as a "Stateless Observer"—a pure function that maps current system state to a structured command.

### 1. Zero-Context Execution
- The agent session (memory buffer) is purged before every invocation. 
- No `user`/`assistant` chat history is carried over between discrete Git operations.

### 2. Just-In-Time (JIT) State Assembly
The prompt payload is constructed at the moment of execution from the **Single Source of Truth (SSoT)**:
- **Scope**: `git status --short` provides the high-level modified file list.
- **Substance**: `git diff --cached` provides the hunk-level changes to be summarized.
- **Configuration**: Domain constants (valid types, section mappings) are pulled from `pyproject.toml [tool.commit-convention]` per turn to ensure compliance with **ADR-26029**.

### 3. Format Enforcement
- The agent is prompted to output only a valid Git command or a JSON object containing the commit body.
- The output MUST follow the structured format: `- Verb: file-path — what_and_why`.

## Consequences

### Positive
- **Token Economy**: Reduces token consumption by ~70–90% in multi-commit workflows by eliminating history redundancy.
- **Model Reliability**: Small LMs (1B–14B) exhibit higher adherence to structure when the context window is focused solely on the current diff.
- **Traceability**: Each commit message is guaranteed to be derived from the actual `git diff` present at the time of generation, eliminating "narrative hallucinations".
- **Portability**: Configuration is tied to the repository's `pyproject.toml`, supporting the hub-and-spoke model.

### Negative / Risks
- **Loss of Implicit Intent**: The agent does not "remember" the user's verbal reasoning from five minutes ago. **Mitigation**: The wrapper script shall support an optional `--intent` or `-m` hint to pass high-level motivation into the JIT payload.
- **Diff Bloat**: Large refactors may exceed the context window. **Mitigation**: Wrapper script must detect token count and truncate/summarize the diff via `git diff --stat` if it exceeds model limits (e.g., 4k tokens).

## Alternatives
- **Option A: Stateful Sessions.** **Rejection Reason**: Inherently scales poorly on local hardware; introduces VRAM exhaustion and non-deterministic "drift" in long sessions.
- **Option B: Manual Release Note Synthesis.** **Rejection Reason**: Superseded by **ADR-26024**; manual curation is non-scalable and lacks deterministic traceability.
- **Option C: Vector Store (RAG) for History.** **Rejection Reason**: Excessive complexity for local CLI tools; introduces a persistent state-tracking layer that violates the simplicity principle.

## References
- {term}`ADR-26024`: Structured Commit Bodies for Automated CHANGELOG Generation
- {term}`ADR-26029`: pyproject.toml as Tool Configuration Hub
- {term}`ADR-26025`: RFC→ADR Workflow Formalization

## Participants
1. Vadim Rudakov
2. Gemini (Principal Systems Architect)
