---
id: 26020
title: Hub-and-Spoke Ecosystem Documentation Architecture
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: 2026-02-04.
tags:
- architecture
- documentation
date: 2026-02-04
options:
  type: adr
  birth: '2026-02-04'
  version: 1.0.0
  token_size: 1144
  status: accepted
  superseded_by: null
---
# ADR-26020: Hub-and-Spoke Ecosystem Documentation Architecture

## Date

2026-02-04

## Status

Accepted

## Context

As a documentation ecosystem grows, reusable packages get extracted into standalone repositories. This creates architectural questions about where different types of decisions should live:

- **Ecosystem standards** (coding conventions, testing requirements, integration patterns) apply across all packages
- **Implementation decisions** (internal structure, algorithm choices) are specific to each package
- **Package specifications** (what a package should do) differ from implementations (how it does it)

Without clear separation, ecosystems suffer from:
- ADR sprawl in a single repo mixing ecosystem and implementation concerns
- Drift when packages duplicate standards locally
- Discovery problems when contributors can't find governing decisions

## Decision

We adopt a **hub-and-spoke documentation architecture** with two tiers of architectural decisions.

### Architecture Overview

```
hub-repo/                         ← Meta-documentation hub
├── architecture/
│   ├── adr/                      ← Ecosystem-wide ADRs
│   └── packages/                 ← Package specifications
│       └── <package>-spec.md     ← "What package X should do"
└── content/                      ← Knowledge base

github.com/<org>/<package>/       ← Implementation spoke
├── docs/adr/                     ← Implementation ADRs
├── src/<package>/
└── ARCHITECTURE.md               ← Links to hub ADRs
```

### Two-Tier ADR System

| Level | Lives In | Scope | Example |
|-------|----------|-------|---------|
| Ecosystem ADR | Hub | Cross-cutting decisions, interfaces, conventions | "All validation packages use Validator ABC" |
| Implementation ADR | Spoke | How a specific package implements the spec | "Use dataclasses not Pydantic for models" |

### Hub Contents

The hub repository contains:

1. **Ecosystem ADRs** - Standards that govern all packages:
   - Development conventions (language style, testing requirements)
   - Integration patterns (pre-commit hooks, CI/CD)
   - Interface contracts (ABCs, error formats)

2. **Package Specifications** - What each package should do:
   - Purpose and scope
   - Required capabilities
   - Version roadmap
   - Links to governing ADRs

### Spoke Contents

Each package repository contains:

1. **ARCHITECTURE.md** - Entry point linking to:
   - Governing ADRs in the hub
   - Implementation ADRs in this repo

2. **Implementation ADRs** - Package-specific decisions:
   - Internal module structure
   - Library/dependency choices
   - Performance trade-offs

### Linking Strategy

Spoke repositories reference hub ADRs by URL in ARCHITECTURE.md:

```markdown
# ARCHITECTURE.md

This package implements specifications from [hub-repo](link).

## Governing ADRs (in hub)
- [ADR-XXXXX: Package Purpose](link) - Why this package exists
- [ADR-YYYYY: Testing Standards](link) - Required test coverage

## Implementation ADRs (in this repo)
- ADR-001: Model layer design
- ADR-002: API versioning strategy
```

## Consequences

### Positive

- **Single Source of Truth:** Ecosystem standards live in one place; packages reference rather than duplicate.
- **Clear Separation:** "Why" (hub) vs "How" (spoke) prevents decision confusion.
- **Independence:** Packages evolve their implementation without modifying hub.
- **Discoverability:** Hub explains ecosystem architecture; spokes explain implementation details.
- **Scalability:** Pattern supports any number of extracted packages without cluttering the hub.

### Negative / Risks

- **Link Maintenance:** Hub URLs in spoke ARCHITECTURE.md may break on file renames. **Mitigation:** Use stable permalink format; maintain redirects for moved ADRs.
- **Two-Repo Mental Model:** Contributors must understand the tier system. **Mitigation:** Clear README in hub's packages/ directory explaining the pattern.
- **Founding Document Copies:** Initial ADRs may need copying to spokes for historical context. **Mitigation:** Mark hub copy as canonical with pointer to implementation.

## Alternatives

1. **Monorepo:** Keep all packages in one repository. Rejected: Different release cycles and ownership models favor separation.

2. **Federated Standards:** Each package maintains complete standards locally. Rejected: Leads to drift across ecosystem.

3. **No Formal Structure:** Ad-hoc references between repos. Rejected: Inconsistent patterns and poor discoverability.

## References

- {term}`ADR-26012`: Extraction of Documentation Validation Engine (first package extraction motivating this pattern)

## Participants

1. Vadim Rudakov
2. Claude (AI Engineering Advisor)
