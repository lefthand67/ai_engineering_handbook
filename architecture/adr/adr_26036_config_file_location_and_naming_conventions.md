---
id: 26036
title: Config File Location and Naming Conventions
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: '<!-- Quality guidelines: /architecture/architecture_decision_workflow_guide.md
  -->.'
tags:
- governance
- architecture
date: 2026-03-23
options:
  type: adr
  birth: '2026-03-23'
  version: 1.0.0
  token_size: 1602
  status: proposed
  superseded_by: null
---
<!-- Quality guidelines: /architecture/architecture_decision_workflow_guide.md -->

# ADR-26036: Config File Location and Naming Conventions

## Date
2026-03-23

## Status
proposed

## Context

As the repository's tooling grows, validation scripts need configuration files. Without a
convention for where configs live and how they're named, engineers face three problems:

1. **Discoverability:** Where is the config for a given script? Which directory? What filename?
2. **Naming inconsistency:** No pattern exists to predict a config file's name from its script
   or validation scope.
3. **Duplication:** Shared fields (e.g., tags) get copied between configs because there's no
   inheritance mechanism.

{term}`ADR-26029` established `pyproject.toml` as the tool configuration hub for simple tool
settings. But governance validation configs — deeply nested structures, conditional rules,
correction mappings — need a dedicated location. {term}`ADR-26029` does not specify where those
files live, how to name them, or how scripts discover them.

## Decision

Adopt a **centralized config directory** at the project root with a hub-spoke structure of
scope-isolated files.

### 1. Config Directory

All governance configs live in a single directory at the project root. The directory name is
determined by the governance package (currently `.vadocs/` per {term}`ADR-26043`). Scripts
discover the directory via `pyproject.toml [tool.vadocs].config_dir`. Any engineer or agent
knows where to look without scanning the directory tree.

### 2. Hub-Spoke Structure

The directory uses a two-level layout:

- **Hub config** (`conf.<ext>`) — cross-cutting definitions used by all validation scripts:
  field registry, block composition, type registry, tag vocabulary, date format.
- **Doc type configs** (`types/<doc_type>.conf.<ext>`) — operational rules for one doc type:
  ADR section structure and status transitions, evidence artifact naming and lifecycle. Each
  doc type config declares a `parent_config` pointer to the hub config to inherit common
  vocabulary.
- **Operational rules** (`validation/`) — path excludes, patterns, and other rules that support
  validation scripts but are not doc-type-specific.

Doc type configs do not reference each other — only the hub config. This is the `sudoers.d`
pattern: each file governs a different scope, files are independently testable, the hub
config provides the common foundation.

### 3. Naming Convention

| Kind | Pattern | Example |
|------|---------|---------|
| Hub config | `conf.<ext>` | `conf.json` |
| Doc type spoke | `types/<doc_type>.conf.<ext>` | `types/adr.conf.json` |
| Schema (optional) | `<name>.schema.<ext>` | `conf.schema.json` |
| Operational rules | `validation/<concern>.<ext>` | `validation/excludes.conf.json` |

The `<doc_type>` matches the validation concern (e.g., `adr`, `evidence`). The file extension
is determined by the serialization format decision ({term}`ADR-26054`).

### 4. Strict Additive Inheritance

Spoke configs add or tighten rules — they never remove or override hub-defined fields. A
validator can always trust that hub vocabulary is available in every spoke context.

## Consequences

### Positive

- **Single discovery location**: all governance config in one directory — no scanning
  artifact directories to find scattered configs.
- **No duplication**: shared vocabulary defined once in the hub config, inherited by doc
  type configs via `parent_config`.
- **Scope isolation**: each doc type file is independently readable and testable. Adding a
  new governance concern means adding a file, not editing a growing monolith.
- **Cross-cutting concerns have a home**: frontmatter schema and lifecycle rules live in the
  hub config, not awkwardly co-located with one arbitrary artifact directory.
- **Predictable naming**: `types/<doc_type>.conf.<ext>` is discoverable across the ecosystem.
- **Convention-based discovery**: `pyproject.toml` → config directory → hub or spoke. One
  utility function (`paths.get_config_path()`) encodes the full resolution chain.

### Negative / Risks

- **Migration overhead**: existing configs must move to the new directory and adopt the naming
  convention. **Mitigation:** one-time cost; a shared config discovery utility absorbs the
  resolution logic.
- **Directory name is tool-coupled**: the directory name (e.g., `.vadocs/`) ties the config
  location to the current governance tool. **Mitigation:** per the manifesto's replacement
  test, the directory pattern is the standard; the name is an implementation detail that
  changes with the tool.

## Alternatives

- **Co-located configs**: Each config lives next to its governed artifacts. **Rejected:**
  creates maintenance overhead — configs scattered across the directory tree with no single
  place to see the governance state. Volatile under refactoring: renaming or restructuring
  artifact directories forces config moves. Fails entirely for cross-cutting concerns
  (frontmatter, ephemeral) that span multiple directories.

- **Single monolithic config file**: All concerns in one file. **Rejected:** ADR operational
  rules alone are 170 lines; a combined file exceeds 500 lines and becomes difficult to
  navigate. Scope isolation is lost — editing ephemeral rules risks merge conflicts with ADR
  rules. See
  [A-26010](/architecture/evidence/analyses/A-26010_config_file_distribution_patterns.md).

- **Everything in pyproject.toml**: Inline all config as TOML tables. **Rejected:**
  governance configs require deeply nested structures that TOML handles poorly. {term}`ADR-26029`
  is for simple tool settings, not validation rule sets.

- **No convention**: Let each script hardcode its own config location. **Rejected:** does not
  scale. Without a naming or location pattern, every new config becomes a discovery problem.

## References

- [A-26010: Config File Distribution Patterns](/architecture/evidence/analyses/A-26010_config_file_distribution_patterns.md) — monolithic vs directory analysis, sudoers.d scope-isolation pattern
- {term}`ADR-26029` — pyproject.toml as Tool Configuration Hub (discovery entry point)
- {term}`ADR-26043` — vadocs package boundary (governance tool that implements this convention)
- {term}`ADR-26042` — common frontmatter standard (hub config's primary consumer)
- {term}`ADR-26054` — JSON as Governance Config Format (serialization format decision)
- {term}`ADR-26035` — Architecture Knowledge Base Taxonomy

## Participants
1. Vadim Rudakov
2. Claude Opus 4.6 (AI Engineering Advisor)
