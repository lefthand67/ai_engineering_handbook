---
title: Documentation as Source Code for AI
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: "2026-05-02"
description: Declaration of principles for treating documentation as production source code for AI consumption.
tags:
- architecture
- documentation
- development
- governance
---
---
options:
  type: guide
  version: "1.0.1"
  birth: "2026-02-16"
  token_size: 1123
---
# Documentation as Source Code for AI

## The Problem

In the era of AI-backed development, AI systems — RAG pipelines, coding agents, AI assistants — consume documentation as their primary input. They don't read your codebase first; they read your docs. Traditional documentation practices fail in this context:

- **Stale content → hallucinations**: outdated docs produce confidently wrong AI outputs.
- **Unstructured metadata → blind retrieval**: without machine-readable frontmatter, RAG pipelines can't filter by date, status, or scope.
- **No lifecycle → noise accumulation**: superseded articles left in place pollute retrieval results indefinitely.
- **Flat collections → untraceable references**: pre-AI knowledge bases are article dumps with no enforced structure, no dependency graph, and no automated verification.

Poor documentation is no longer just an inconvenience for humans. It is a **bug in the AI system**.

## The Principle

All content in this repository is treated as **production source code** — versioned, tested, lifecycle-managed, and machine-readable — because it is the primary input for AI systems.

This is not a metaphor. The same engineering rigor applied to production code — diffing, testing, code review, CI/CD, garbage collection of dead code — applies to every document, ADR, and notebook in this repository.

Sean Grove (OpenAI, "The New Code") articulates the underlying insight: "code is a lossy projection from the specification" — discarding specifications while keeping generated code is like shredding the source and version-controlling the binary. In an AI-consumed repository, documentation IS the source that AI systems compile into outputs.

## How This Repository Implements the Principle

Each aspect of the Documentation-as-Code paradigm is governed by a concrete ADR:

| Principle | What it means | Governing ADR |
|---|---|---|
| **Docs = source code** | Jupytext pairing makes docs diffable, mergeable, testable | ADR-26014 |
| **Metadata = API contract** | MyST-native frontmatter makes every document machine-queryable | ADR-26023, ADR-26016 |
| **Lifecycle = garbage collection** | Superseded articles are deleted to prevent RAG noise; ADRs are preserved as negative knowledge | ADR-26021 |
| **Structure = architecture** | Repository layout is deliberate design, not accumulation; restructuring = refactoring | ADR-26020, ADR-26026 |
| **ADRs = development backbone** | Every major decision is an ADR; proposed ADRs serve as living RFCs | ADR-26025 |
| **CI/CD = deployment** | Sync-guard validates documentation integrity before deployment | ADR-26015 |
| **Hub = authoritative specs** | Hub holds conventions and specifications; spokes hold implementation. The hub is the "POSIX standard" — it defines what conforming implementations must do. Implementations (vadocs, mentor_generator) are replaceable; standards outlive them. **The replacement test:** if the implementing tool were replaced, would this decision still apply? Yes → hub. No → implementation repo | ADR-26020 |

## The Structural Analogy

In source code, architecture determines where modules live, how they reference each other, and what contracts they expose. The same applies to documentation:

- **Placement is semantic**: a document's directory location defines its layer, scope, and discoverability — not a flat "articles" collection.
- **References are traceable**: ADR cross-references, frontmatter tags, and status fields create a dependency graph analogous to import statements.
- **Restructuring requires governance**: moving or splitting content is a refactoring operation that demands an ADR (e.g., ADR-26026 for research extraction, ADR-26020 for hub-spoke separation) — not a casual drag-and-drop.
- **Verification is automated**: broken-link checks, sync-guard, and metadata validation catch structural regressions the same way unit tests catch code regressions.

This stands in direct opposition to pre-AI knowledge bases — collections of articles with no enforced structure, no traceability between documents, and no automated verification. Those collections were adequate when only humans consumed them. They are inadequate when AI systems depend on them.

## Role of This Document

This manifesto is not an ADR. ADRs are decisions — reversible, with alternatives considered, subject to promotion gates. This document is a **declaration of principles** — the unchanging foundation that individual ADRs implement. It answers "why does this repository exist?" while ADRs answer "how do we build it?"

## References

- Sean Grove, "The New Code" (OpenAI) — https://www.youtube.com/watch?v=8rABwKRsec4
- [ADR Index](/architecture/adr_index.md) — the full set of architectural decisions implementing these principles
