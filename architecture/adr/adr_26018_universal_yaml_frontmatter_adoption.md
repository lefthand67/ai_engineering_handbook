---
id: 26018
title: Universal YAML Frontmatter Adoption for Machine-Readable Documentation
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: YAML frontmatter is mandated as the universal machine-readable interface
  for all documentation artifacts, requiring owner, version, and last_modified fields
  on every file.
tags:
- governance
- documentation
- context_management
date: 2026-04-01
options:
  type: adr
  birth: 2026-02-01
  version: 1.0.1
  token_size: 1146
  status: superseded
  superseded_by: ADR-26023
---
# ADR-26018: Universal YAML Frontmatter Adoption for Machine-Readable Documentation

## Title

Universal YAML Frontmatter Adoption for Machine-Readable Documentation

## Date

2026-02-02

## Status

superseded

Superseded by: {term}`ADR-26023`

## Supersession Rationale

The field names mandated here (`owner`, `version`, `birth`, `last_modified`) do not match the MyST frontmatter API and are silently ignored by the renderer. {term}`ADR-26023` replaced them with MyST-native field names, preserving the machine-readability goal while ensuring fields are visible in the rendered static site.

## Context
Our repository contains heterogeneous documentation formats, including MyST Markdown handbooks (`.md`) and Jupytext-paired notebooks (`.ipynb`). Currently, metadata such as ownership, versioning, and status are often embedded as unstructured markdown text in the document body.

This creates significant technical debt:
1. **AI Parseability**: LLMs and AI agents (e.g., Aider, Gemini) lack a deterministic interface to query document state, forcing them to rely on expensive and error-prone prose parsing.
2. **Automation Barriers**: CLI tools cannot efficiently audit the documentation library (e.g., "Find all stale docs older than 6 months") without complex regex logic.
3. **Traceability Decay**: Without a machine-readable schema, maintaining link integrity and lifecycle status (as defined in ADR-26016) across the entire stack is manually intensive and unverifiable [ISO 29148: Verifiability].

## Decision
We will mandate the adoption of YAML frontmatter as the **Universal Interface** for all documentation artifacts (`.md`, `.ipynb` via Jupytext) in the repository.

1. **Mandatory Schema**: Every file must contain a YAML block with at least `owner`, `version`, and `last_modified` fields.
2. **Jupytext Integration**: For notebooks, the YAML metadata must reside in the paired MyST Markdown file to ensure it is easily diffable and searchable via standard CLI tools.
3. **AI Tooling Alignment**: This structured block serves as the primary context injection point for AI assistants, ensuring they understand the "Freshness" and "Authority" of the document before processing the content.
4. **Human-Machine Sync**: To ensure human readability in non-rendering environments (like CLI `cat`), a standardized "Reflection Block" will be injected into the body, automatically synced from the YAML source via pre-commit hooks.

## Consequences

### Positive
- **Deterministic Context**: AI tools gain 100% accuracy in identifying document metadata, reducing hallucination risk regarding document status.
- **Library Auditing**: Enables the use of `yq` and `frontmatter` parsers to generate automated indexes and freshness reports.
- **SVA Compliance**: Maintains a CLI-first, vendor-neutral approach to documentation state.
- **RAG**: The transition to a Universal YAML Frontmatter is a prerequisite for high-performance Retrieval-Augmented Generation (RAG) and vectorized storage. In a vectorized database, the decision to move metadata from prose to YAML directly impacts the **Signal-to-Noise Ratio (SNR)** during the embedding and retrieval process.

### Negative / Risks
- **Metadata Redundancy**: If not automated, humans must maintain two blocks. **Mitigation**: Implementation of a `pre-commit` hook to automate the projection of YAML into the body text.
- **Sync Overhead**: Jupytext files require strict synchronization to prevent metadata drift between the `.md` and `.ipynb` files. **Mitigation**: Automated `jupytext --sync` commands in the CI/CD pipeline.

## Alternatives
- **Manual Prose Headers**: Rejected. Not parseable by machines and prone to formatting drift.
- **Database-Stored Metadata**: Rejected. Violates the principle of Git as the Single Source of Truth and adds unnecessary architectural complexity.
- **MyST-Only Metadata**: Rejected. Standard MyST frontmatter is invisible to humans in many raw terminal/Git environments.

## References
- [ADR-26014: Semantic Notebook Pairing Strategy](/architecture/adr/adr_26014_semantic_notebook_pairing_strategy.md)
- [ADR-26016: Metadata-Driven Architectural Records Lifecycle](/architecture/adr/adr_26016_metadata_driven_architectural_records_life.md)
- [YAML Frontmatter for AI-Enabled Engineering](/ai_system_layers/5_context/yaml_frontmatter_for_ai_enabled_engineering.ipynb)
- ISO/IEC/IEEE 29148:2018 Standards for Software Requirements

## Participants
1. Vadim Rudakov
2. Gemini (Senior DevOps Systems Architect)
