# Technical Debt Register

Traceable record of intentional shortcuts. Each entry has a date, location, and migration path.

## Open

### TD-002: Technical Debt Register has no formal governance (2026-02-27)

- **Location:** `misc/plan/techdebt.md` (this file)
- **Context:** This register was created ad-hoc to track intentional shortcuts. There is no ADR, config, or script governing its format, naming convention, ID scheme, or lifecycle (when entries move from Open to Resolved).
- **Current state:** Free-form markdown in `misc/plan/`. Not validated by CI, not referenced by any ADR.
- **Migration path:** Write an ADR formalizing the tech debt tracking convention (format, ownership, review cadence). Optionally add a validation script and pre-commit hook following the ADR-26011 script suite pattern.
- **Roadmap:** Phase 1.1, item 9 (Tech Debt Governance ADR)
- **Introduced by:** plan_20260227_architecture_knowledge_base_taxonomy_tooling.md (Batch 2)

### TD-003: ADR deprecation workflow not formalized (2026-03-02)

- **Location:** `.vadocs/types/adr.conf.json` (status `deprecated`), `architecture/adr/adr_template.md`, `tools/scripts/check_adr.py`
- **Context:** The `deprecated` status is defined in `adr.conf.json` and mapped to the "Historical Context" index section, but unlike `rejected` (which has a conditional `Rejection Rationale` section and template support), deprecation has no template guidance, no conditional section, and no validation rules in `check_adr.py`. No ADRs have used this status yet.
- **Current state:** Provisional guidance documented in [Architecture Decision Workflow](/architecture/architecture_decision_workflow_guide.md). The guide marks the deprecation section as "not yet formalized."
- **Migration path:** When the first ADR needs deprecation: (1) add a conditional `Deprecation Rationale` section to `adr_template.md`, (2) add validation rules to `adr.conf.json` and `check_adr.py`, (3) remove the "not yet formalized" caveat from the guide.
- **Roadmap:** Phase 1.2 (validation scripts — check_adr.py conditional validation)
- **Introduced by:** plan_20260302_adr_writing_guide.md

### TD-006: WRC scoring has no governing ADR (2026-03-29)

- **Location:** `ai_system/3_prompts/consultants/ai_systems_consultant_hybrid.json`, `ai_system/3_prompts/consultants/devops_consultant.json`
- **Context:** WRC (Weighted Response Confidence) is a scoring metric embedded directly in two consultant prompts. It is referenced in ADR-26037 (SVA framework) and in release notes, but there is no ADR defining its scope, formula rationale, component weights, or lifecycle. It is currently an undocumented architectural decision — the metric exists and is in use, but its authority comes from the prompt JSON, not from a governed decision record.
- **Current state:** Formula and component definitions live in the `system_context` block of `ai_systems_consultant_hybrid.json`. ADR-26037 references WRC as an implementation detail of SVA penalties but does not define it.
- **Migration path:** Write ADR defining WRC as an ecosystem evaluation standard: formula, component definitions (E/A/P), weight rationale, threshold semantics (≥0.89 = production-ready), and relationship to SVA constraints. Update prompt JSONs to reference the ADR rather than embed the authoritative definition.
- **Roadmap:** Phase 1.17, Heuer plan phase 4 (WS-3: WRC Formalization ADR)
- **Introduced by:** v2.8.0 release notes session (2026-03-29)

### TD-007: Format as model-specific semantic contract — open research question (2026-03-29)

- **Location:** ai_system/3_prompts/format_as_architecture_signal_noise_in_prompt_delivery.md, Section 4
- **Context:** If format response is learned from training corpus, the same format primes different cognitive modes in models trained on different corpora. Format becomes a hidden variable in cross-model instruction-following benchmarks.
- **Evidence needed:** Controlled experiment — same semantic content × multiple formats (JSON/YAML/Markdown) × multiple models (Claude, Qwen, GigaChat, Gemini) × behavioral outcome (instruction adherence rate, section survival, field preservation).
- **Future artifact:** S-YYNNN (collected evidence) → analysis → Section 4 update
- **Roadmap:** Phase 2.0 (Research: Frontier CLI Agents — cross-model format behavior)
- **Introduced by:** meetup talk brainstorming session (2026-03-29)

## Resolved

### TD-008: ArchTag has no governed vocabulary or resolution path (2026-04-11)

- **Location:** `pyproject.toml` (`archtag-required-types`), `tools/scripts/validate_commit_msg.py`
- **Context:** ArchTag is required for `refactor:` and `perf:` commits as the first body line (`ArchTag:TAG-NAME`). It links commits to architectural decisions, tech debt payments, or perf justifications.
- **Resolution:** Fixed by introducing `archtag-valid-values` in `pyproject.toml` as the SSoT and refactoring `validate_commit_msg.py` to provide just-in-time instructional feedback based on this governed vocabulary.
- **Resolved:** 2026-05-04

### TD-001: common_required_fields in evidence.config.yaml (2026-02-27)
- Resolved by ADR-26042 (Common Frontmatter Standard) — hub-and-spoke config replaces fragmented common_required_fields
- Resolved: 2026-03-11

### TD-005: check_frontmatter.py needed for hub-level validation (2026-03-23)
- Resolved by standing items cleanup: check_frontmatter.py created (70 tests, 97% coverage), sub-type spoke resolution implemented, pre-commit hooks added
- Resolved: 2026-04-02

### TD-004: Script suite triad doc requirement is redundant (2026-03-23)
- Resolved by ADR-26045 (AI-Native Development — Code as Primary Documentation) superseding ADR-26011. Doc requirement dropped from `check_script_suite.py` and pre-commit hook. Existing docs in `tools/docs/scripts_instructions/` left to age out.
- Resolved: 2026-04-01
