
---
title: JSON as Governance Config Format — Migration from YAML
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: 'Analysis of config file format options for the vadocs governance engine.
  YAML identified as an inertia-driven default with growing friction: no native schema,
  parsing ambiguities, external dependency. JSON + JSON Schema selected as the target
  format for .vadocs/ configs.'
tags:
- governance
- architecture
date: 2026-03-23
options:
  type: analysis
  birth: 2026-03-23
  version: 1.0.0
  token_size: 1672
  id: A-26013
  status: active
  produces:
  - ADR-26054
---
# A-26013: JSON as Governance Config Format — Migration from YAML

+++

## Problem Statement

+++

The `.vadocs/` governance config (`conf.yaml`) was created as a YAML file by convention —
YAML is common in documentation tooling (MyST uses `myst.yml`). As the config grew from
a simple vocabulary registry toward a validation schema, YAML's limitations emerged:

1. **No native schema validation.** When the `authors` field needed format specification
   (list of `{name, email}` objects per MyST spec), we faced a choice: invent a custom
   `value_format` structure in YAML, or adopt a standard schema language. Custom invention
   means every new constraint type requires custom design and custom validation code.

2. **Parsing ambiguities.** YAML's implicit typing (Norway problem: `NO` → `false`),
   colon-space gotcha (already documented in CLAUDE.md as a project pitfall), and
   indentation sensitivity create failure modes that don't exist in stricter formats.

3. **External dependency.** Python's `yaml` module requires PyYAML. The vadocs package
   (Phase 1.3) would carry this dependency solely for config parsing, while `json` is
   stdlib and `tomllib` (for pyproject.toml) is also stdlib since 3.11.

4. **Format invention pressure.** The `date_format` regex at the bottom of `conf.yaml`
   was already a validation rule mixed into the vocabulary registry. Adding `authors`
   format would repeat the pattern. Each new complex field would require another custom
   structure — essentially building a bespoke schema language inside YAML.

The question: should governance configs remain YAML, move to JSON, or use another format?

+++

## Key Insights

+++

### Format comparison for machine-consumed governance configs

| Concern | YAML | JSON | TOML |
|---------|------|------|------|
| Schema validation | None native; requires custom invention | JSON Schema — industry standard, `jsonschema` library | None native |
| Parsing ambiguity | Implicit typing, `: ` gotcha, multiple syntax forms | Unambiguous grammar | Unambiguous, typed |
| Python stdlib parser | No (`PyYAML` required) | Yes (`json` module) | Yes (`tomllib`, 3.11+) |
| Nested structures | Good | Good | Weak (verbose `[section.sub.key]`) |
| Comments | Native | Not supported | Native |
| Human editing frequency | Governance configs change rarely | Rare edits are fine without comments | Rare edits are fine |
| Agent consumption | Parses structure, doesn't benefit from comments | Parses structure natively | Parses structure natively |

### Why not TOML?

TOML is already used in the ecosystem (`pyproject.toml`, ADR-26029). However, the
governance configs have deeply nested structures — type registry with blocks, required/
optional fields, field registry entries with multiple properties. TOML's flat section
headers (`[types.adr.blocks]`) become verbose for this depth. JSON handles arbitrary
nesting naturally.

### The comments question

YAML's only clear advantage over JSON is native comments. But for governance configs:

1. **Configs change rarely** — they're set-once governance decisions, not frequently-edited
   application configs. The lack of inline comments is acceptable for rare edits.

2. **JSON Schema replaces comments** — every field, property, and constraint in JSON Schema
   has a `description` key. Documentation lives *in the schema itself* and is machine-readable,
   not just human-readable. This is strictly better than freeform YAML comments for a
   validation engine.

3. **Agents don't benefit from comments** — they parse structure, not prose. Field
   descriptions in JSON Schema are structured data that agents can reason about
   programmatically.

### JSON Schema as the validation foundation

With JSON + JSON Schema, the `authors` format problem becomes standard:

```json
{
  "authors": {
    "type": "array",
    "items": {
      "type": "object",
      "required": ["name", "email"],
      "properties": {
        "name": { "type": "string", "description": "Full name" },
        "email": { "type": "string", "format": "email" }
      }
    }
  }
}
```

This eliminates custom format invention entirely. The same schema can validate:
- The `.vadocs/conf.json` structure itself (meta-validation)
- Document frontmatter against the field registry (runtime validation)

The `jsonschema` Python library provides validation with zero custom code for field
formats. vadocs validators would call `jsonschema.validate()` instead of implementing
custom checking logic for each field type.

### Scope boundary: config format vs frontmatter format

Document frontmatter remains YAML — it's embedded in markdown files and parsed by MyST.
Only `.vadocs/` governance config files migrate to JSON. The scripts continue to parse
YAML frontmatter from documents; they switch from YAML to JSON only for loading their
own config.

### Migration path

1. Convert `.vadocs/conf.yaml` → `.vadocs/conf.json` (mechanical translation)
2. Create `.vadocs/conf.schema.json` (new: defines hub config structure and field formats)
3. Convert spoke configs to JSON during directory restructuring
4. Update scripts: `yaml.safe_load(config_path)` → `json.load(config_path)`
5. Existing YAML config tests adapt to JSON fixtures

The migration is atomic — all configs switch in one commit as part of step 7.

+++

## Rejected Ideas

+++

### Stay YAML, add custom `value_format` keys

Attempted during brainstorming: added `value_format: {type: list, items: {required: [name, email]}}` to the `authors` field in `conf.yaml`. Immediately identified as schema language invention — if applied consistently to other fields (`tags`, `date`, `version`, `status`), it would become a bespoke schema format that requires custom validation code. JSON Schema already solves this.

### YAML with companion JSON Schema

Keep YAML as human-editable source, generate JSON Schema alongside. Rejected because it requires maintaining synchronization between two files (or building a generator). If JSON Schema is the validation target, the source should also be JSON — one format, one source of truth.

+++

## References

+++

- `.vadocs/conf.yaml` — current hub config (to be replaced by `conf.json`)
- [A-26010: Config File Distribution Patterns](/architecture/evidence/analyses/A-26010_config_file_distribution_patterns.md) — `.vadocs/` directory structure decision
- `misc/plan/plan_20260320_ecosystem_governance_model_config_architecture.md` — step 7 plan
- JSON Schema specification: https://json-schema.org/
- MyST frontmatter spec: https://mystmd.org/guide/frontmatter (authors format reference)
- Python `jsonschema` library: https://python-jsonschema.readthedocs.io/
