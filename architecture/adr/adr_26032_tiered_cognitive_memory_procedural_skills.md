---
id: 26032
title: 'Tiered Cognitive Memory: Procedural Skills vs. Declarative RAG'
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
  token_size: 446
  status: proposed
  superseded_by: null
---
# ADR-26032: Tiered Cognitive Memory: Procedural Skills vs. Declarative RAG

## Date
2026-02-25

## Status
proposed

## Context
To achieve "Predictability from constraints", we must solve the "Context Tax" problem where the agent is overloaded with reference data that obscures its core instructions. Additionally, this is the token usage problem {term}`ADR-26030` Stateless JIT Context Injection for Agentic Git Workflows.

## Decision
Implement a **Tiered Memory Architecture**:
- **Skills:** High-density procedural logic (Level 1/2 Disclosure).
- **RAG:** Low-density declarative knowledge (JIT Retrieval).

## Consequences

Need to be finished.

## Alternatives
- **Pure RAG for Everything:** Store logic/instructions in the vector store. **Rejection Reason:** Vector search is probabilistic and partial; the agent might retrieve the wrong "how-to" step, leading to catastrophic failure in structured tasks like YAML generation.
- **Pure Skills (No RAG):** Try to fit all domain knowledge into the context window. **Rejection Reason:** The context window constrains lead to the agent cognitive degradation and too high token usage lead to high computational/financial costs. Historical logs and large specs must remain external.

## References
- {term}`ADR-26030`: Stateless JIT Context Injection
- {term}`ADR-26013`: Just-in-Time Prompt Transformation

## Participants
1. Vadim Rudakov
2. Gemini (Principal Systems Architect)
