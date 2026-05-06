
---
title: JSON as Governance Config Format
date: 2026-03-23
tags:
- governance
- architecture
options:
  token_size: 1441
  id: 26054
  status: proposed
  superseded_by: null
  type: adr
  version: 1.0.0
  birth: '2026-03-23'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: '<!-- Quality guidelines: /architecture/architecture_decision_workflow_guide.md
  -->.'
---
<!-- Quality guidelines: /architecture/architecture_decision_workflow_guide.md -->

# ADR-26054: JSON as Governance Config Format

## Date
2026-03-23

## Status
proposed

## Context

Governance configs in `.vadocs/` define validation rules, field registries, and tag vocabularies consumed by validation scripts. These configs are machine-consumed artifacts — read by scripts and agents, edited by humans only when governance rules change.

The initial implementation used YAML (`conf.yaml`, spoke configs). As configs grew beyond simple key-value pairs toward structured validation rules (field formats, block composition, type registries), three friction points emerged:

1. **No native schema language.** Adding format constraints for complex fields (e.g., `authors` as a list of `{name, email}` objects per the MyST spec) required inventing custom `value_format` structures — effectively building a bespoke schema language inside YAML. Each new constrained field would repeat this invention.

2. **Parsing ambiguities.** YAML's implicit typing (`NO` → `false`), colon-space sensitivity, and multiple syntax forms for the same data create failure modes that don't exist in stricter formats. The pre-commit config's `: ` gotcha was already documented in CLAUDE.md as a recurring pitfall.

3. **External dependency.** PyYAML is required for YAML parsing. The vadocs package ({term}`ADR-26043`) would carry this dependency solely for config parsing, while `json` is Python stdlib. Document frontmatter parsing still requires PyYAML, but config parsing does not need to.

See [A-26013: JSON as Governance Config Format](/architecture/evidence/analyses/A-26013_json_as_governance_config_format.md) for the full format comparison and rejected ideas.

## Decision

Adopt **JSON with JSON Schema** as the serialization format for all governance configs in `.vadocs/`.

1. **Config files use JSON.** Hub config (`conf.json`) and doc-type spoke configs (`types/<doc_type>.conf.json`) are JSON. Naming convention: `<name>.conf.json`.

2. **JSON Schema validates config structure.** Each config file may reference a companion `.schema.json` file via the `$schema` key. Schema definitions use the JSON Schema standard — no custom schema invention required. Field format constraints (type, required properties, allowed values) are expressed as standard JSON Schema, not bespoke validation structures.

3. **Document frontmatter remains YAML.** Frontmatter is embedded in markdown and parsed by MyST. Only `.vadocs/` config files migrate to JSON. Validation scripts continue to parse YAML frontmatter from documents.

4. **Convention-based discovery.** Scripts discover configs via `pyproject.toml [tool.vadocs].config_dir` → directory → `conf.json` (hub) or `types/<doc_type>.conf.json` (spoke). The `paths.get_config_path()` utility encodes this convention.

## Consequences

### Positive

- **Schema validation without invention**: field format constraints use JSON Schema — an industry standard with mature tooling (`jsonschema` library) — eliminating custom validation code for each new field type.
- **Unambiguous parsing**: JSON has a single, strict grammar. No implicit typing, no indentation sensitivity, no `: ` gotchas.
- **Zero config-parsing dependency**: `json` is Python stdlib. The vadocs package's config layer needs no external dependency.
- **Machine-readable documentation**: JSON Schema `description` fields document every config property structurally — agents can reason about config semantics programmatically.

### Negative / Risks

- **No inline comments in JSON.** Governance configs change rarely (set-once governance decisions), and JSON Schema descriptions serve as structured documentation. **Mitigation:** Use `$comment` keys for any necessary inline notes. JSON5 or JSONC remain available as future options if comment needs grow.
- **Migration cost for existing configs.** YAML-to-JSON conversion is mechanical but touches multiple files and scripts. **Mitigation:** One-time cost, completed as part of step 7 of the config architecture plan.
- **Two YAML parsers remain.** Document frontmatter stays YAML, so PyYAML remains a project dependency regardless. **Mitigation:** The benefit is decoupling *config* parsing from PyYAML, enabling a clean config layer in the vadocs package. Frontmatter YAML parsing is a separate concern.

## Alternatives

- **Stay YAML, add custom format keys.** Add `value_format` structures to express field constraints inside YAML config. **Rejected:** This is schema language invention. Each constrained field requires custom design and custom validation code. JSON Schema solves this problem as a standard. See A-26013 "Rejected Ideas" section.

- **YAML source with companion JSON Schema.** Keep YAML as the human-editable format, generate or maintain JSON Schema alongside. **Rejected:** Requires synchronizing two representations of the same config — one YAML file and one JSON Schema file. If JSON Schema is the validation target, the source should also be JSON (one format, one source of truth).

- **TOML for configs.** Already used in the ecosystem (`pyproject.toml`). **Rejected:** Governance configs have deeply nested structures (type registry → blocks → fields → properties). TOML's flat section headers (`[types.adr.blocks.identity]`) become verbose for this nesting depth. No native schema language exists for TOML either. See A-26013 format comparison table.

## References

- [A-26013: JSON as Governance Config Format](/architecture/evidence/analyses/A-26013_json_as_governance_config_format.md) — format comparison analysis and rejected ideas
- {term}`ADR-26036` — Config File Location and Naming Conventions (directory structure)
- {term}`ADR-26029` — pyproject.toml as Tool Configuration Hub (discovery entry point)
- {term}`ADR-26043` — vadocs Package Boundary (governance package identity)
- {term}`ADR-26042` — Common Frontmatter Standard (primary consumer of hub config)
- [JSON Schema specification](https://json-schema.org/) — industry standard for JSON validation

## Participants
1. Vadim Rudakov
2. Claude Opus 4.6 (AI Engineering Advisor)
