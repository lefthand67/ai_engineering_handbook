
---
title: Prefixed Namespace System for Architectural Records
date: 2026-02-25
tags:
- governance
- documentation
- workflow
options:
  token_size: 789
  id: 26031
  status: rejected
  superseded_by: null
  type: adr
  version: 1.0.0
  birth: '2026-02-25'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: 2026-02-25.
---
# ADR-26031: Prefixed Namespace System for Architectural Records

## Date
2026-02-25

## Status
rejected

## Rejection Rationale

The namespace collision problem is real — when agents consume documentation from multiple ecosystem repos, duplicate IDs (e.g., `ADR-26001` exists in both the hub and mentor_generator) create confusion without full paths. However, the proposed solution — flat string prefixes like `HUB-`, `MNT-` — is a weak approach that doesn't solve the deeper problem of cross-repo discoverability and index fragmentation (acknowledged in the proposal's own unresolved negative consequence).

[A-26005](/architecture/evidence/analyses/A-26005_doc_type_interfaces_unified_validation.md) documents a Postgres-like namespace model (schema-per-repo with cross-schema queries) that provides a structurally superior alternative: logical isolation with the ability to query across repos when needed. That approach should be formalized as a dedicated ADR.

## Context
As the ecosystem expands into a hub-and-spoke model {term}`ADR-26020`, maintaining a single global incrementing ID for ADRs (e.g., `ADR-26001`) has become impossible. Multiple repositories are generating overlapping IDs, leading to "documentation debt" where it is unclear which decision governs which repository.

## Decision
We adopt a **Prefixed Namespace System** for all architectural records to ensure unique identification across the ecosystem.

1. **Formatting:** IDs must follow the pattern `[PREFIX]-[YY][NNN]` (e.g., `HUB-26001`). 
2. **Namespace Registry** is defined in the pyproject.toml of the repo. 
2. **Canonical Source:** The Hub repository (`adr_index.md`) remains the registry for `HUB-` records, while spoke repositories maintain their own local indices using their respective prefixes.

**Example** 

Namespace Registry examples:
   - `HUB-`: Ecosystem/Hub standards (High-level architecture).
   - `MNT-`: Mentor Generator specific implementation.
   - `SKL-`: Skills Library definitions and schemas.
   - `VAD-`: vadocs validation rules and engine logic.

## Consequences

### Positive
- **Collision Avoidance:** Developers can number ADRs within their repo without checking other spoke repos.
- **Contextual Clarity:** The ID itself signals the scope of the decision.

### Negative / Risks
- **Index Fragmentation:** There is no solution yet, brainstorm needed. Spoke ADRs depend on the hub's ADRs. How to interconnect them considering the fact these are the different repos with their own documentation base?

## Alternatives
- **Keep Flat Naming**: Rejected because such a naming structure asks for the full document path to understand what the repo this ADR belongs to. Everything will be much complicated if we move to the ecosystem united website where such duplicate terms will lead to the inevitable collisions.

## References
- {term}`ADR-26020`: Hub-and-Spoke Ecosystem Documentation Architecture
- {term}`ADR-26025`: RFC→ADR Workflow Formalization

## Participants
1. Vadim Rudakov
2. Gemini (Principal Systems Architect)
