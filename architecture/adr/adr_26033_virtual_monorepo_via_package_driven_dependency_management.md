---
id: 26033
title: Virtual Monorepo via Package-Driven Dependency Management
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: 2026-02-25.
tags:
- governance
date: 2026-02-25
options:
  type: adr
  birth: '2026-02-25'
  version: 1.0.0
  token_size: 390
  status: proposed
  superseded_by: null
---
# ADR-26033: Virtual Monorepo via Package-Driven Dependency Management

## Date
2026-02-25

## Status
proposed

## Context
Managing spoke projects {term}`ADR-26020` as separate repos creates friction for developers who need to "dogfood" changes across the stack.

## Decision
Standardize on **`uv` Workspace-linked Packages** to create a "Virtual Monorepo" during development. Use internal PyPI/Git-based installs for production.

## Consequences

Need to be finished.

## Alternatives
- **Git Submodules:** Linking repos via `.gitmodules`. **Rejection Reason:** High "Maintenance Tax." Submodules are notoriously difficult to keep in sync and often lead to "Detached HEAD" states for developers.
- **Traditional Monorepo:** Merging all code into one giant repository. **Rejection Reason:** Violates the Hub-and-Spoke model. Prevents independent versioning of the `vadocs` engine and the `skills` library, which have different release cycles.

## References
- {term}`ADR-26020`: Hub-and-Spoke Ecosystem
- vadocs ADR-26001: Dogfooding for Self-Documentation

## Participants
1. Vadim Rudakov
2. Gemini (Principal Systems Architect)
