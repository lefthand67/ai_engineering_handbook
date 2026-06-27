---
id: 26024
title: Structured Commit Bodies for Automated CHANGELOG Generation
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Structured Commit Bodies for Automated CHANGELOG Generation.
tags:
- workflow
- ci
- documentation
- git
date: 2026-02-18
options:
  type: adr
  birth: '2026-02-18'
  version: 1.0.0
  token_size: 4053
  status: accepted
  superseded_by: null
---
# ADR-26024: Structured Commit Bodies for Automated CHANGELOG Generation

## Title

Structured Commit Bodies for Automated CHANGELOG Generation

## Date

2026-02-10

## Status

Accepted

## Context

The CHANGELOG has historically been manually curated, with RELEASE_NOTES.md composed by an LLM from a diff file. This approach has three problems:

1. **Manual curation doesn't scale.** As the ecosystem grows to multiple spoke repositories ({term}`ADR-26020`), maintaining changelogs manually across all repos becomes unsustainable.
2. **LLM-based generation is non-deterministic.** The existing workflow introduces "hallucination" risks in technical documentation — the same diff can produce different RELEASE_NOTES on different runs, with no audit trail from commit to changelog entry.
3. **Commit bodies are inconsistent.** Some contain prose, some are empty, none follow a structured format. This prevents any automated extraction tool — LLM or otherwise — from reliably producing hierarchical changelogs.

The existing [Production Git Workflow Standards](/tools/docs/git/01_production_git_workflow_standards.ipynb) define a Three-Tier Naming Structure. Tier 2 (Conventional Commits subject prefix) already provides type classification (`feat:`, `fix:`, `docs:`). Extending this with structured body bullets enables fully automated, deterministic CHANGELOG generation — the CHANGELOG transitions from a narrative/descriptive artifact to a computational/traceable artifact.

### The Problem Statement

Generate hierarchical changelogs (section → topic → sub-items) automatically from git commit history, across all repos in the ecosystem, without an LLM. The existing CHANGELOG format is richer than what any standard tool produces:

```
release 2.4.0
* ADR Validation Toolchain:                              ← topic (from commit subject)
    - check_adr_index.py renamed to check_adr.py...     ← sub-item (from commit body)
    - Term reference validation added...                 ← sub-item
* Architecture Decisions (ADRs) added:                   ← another topic
    - ADR-26016: Metadata-Driven...                      ← sub-item
```

## Decision

### 1. Mandate structured bullet bodies in all commits

Every commit on trunk must contain at least one changelog bullet in the body:

```
<type>[(<scope>)]: <subject line>

- <Verb>: <file-path> — <what_and_why>
```

The `<what_and_why>` portion explains what changed in the file and why — this is a changelog, so each bullet should capture both the substance and the motivation. Verb prefixes: `Created`, `Updated`, `Deleted`, `Renamed`, `Fixed`, `Moved`, `Added`, `Removed`, `Refactored`, `Configured`. No line length limit — one bullet = one line. Git trailers and `ArchTag:` lines are excluded from changelog parsing.

**Target Rules** — `<file-path>` is a path relative to the repo root:

1. **Single file**: `tools/scripts/check_adr.py`
2. **Glob or Jupytext pair**: `tools/docs/website/01_github_pages_deployment.(md|ipynb)`
3. **Multiple related files** (same verb, same reason): `adr_26001.md`, `adr_26002.md` — or use a glob `architecture/adr/adr_260{01,02}.md`
4. **Rename/move**: `old_name.py` → `new_name.py`
5. **Every change lives in a file** — always use the nearest file path. Dependencies → `pyproject.toml`, CI variables → `deploy.yml`, config keys → `myst.yml`. No conceptual or abstract targets allowed.

### 2. Enforce via pre-commit hook and CI

`validate_commit_msg.py` runs as a `commit-msg` stage hook locally and in CI, validating both the Conventional Commits subject format and the presence of body bullets. This implements the "Ingredients-First" pattern: input data is validated continuously so the generator never encounters malformed commits at release time.

### 3. Build a custom Python changelog generator

`generate_changelog.py` extracts structured bullets from `git log --first-parent` and produces hierarchical CHANGELOG output (section → topic → sub-items). It runs once at release time on a frozen release branch.

### 4. Adopt Rich-Body Squash as the merge strategy

1 PR = 1 Commit = 1 Logical Change. The repository enforces Squash-and-Merge. The Git host populates the squash commit message from the PR description, which contains the structured body bullets. This moves the system from *Micro-Atomic History* (line-level changes) to *Macro-Atomic History* (intent-level changes), reducing history noise by 70-90% while preserving 100% of the semantic metadata needed for changelogs.

### Architectural Pillars

#### Pillar 1: `git bisect` is formally deprioritized

In ML-heavy systems, regressions are more frequently caused by data/config drift or high-level logic errors, not single-line syntax bugs. Unit/eval tests catch logic bugs faster than history-walking. Maintaining perfect stacked-diff history for `bisect` represents "Process Debt" that violates SVA (Smallest Viable Architecture) principles — especially without specialized wrappers like Graphite or Sapling.

**Consequence:** We do not need atomic commit history within feature branches. The topic branch is a transient development workspace. Only the squashed commit on trunk matters.

#### Pillar 2: Release-Time Batch Generation ("Ingredients-First")

Running changelog extraction on every commit adds unnecessary latency to the local dev cycle. Generating the changelog only when the release branch is frozen ensures the artifact reflects the final, immutable state of the release candidate. A single generation event is easier to audit.

However, batch generation at release time *requires* that input data (commit bodies) was validated continuously — otherwise the generator will fail when needed most.

**Consequence:** Two decoupled concerns: (a) `validate_commit_msg.py` runs as a hard gate at every commit, ensuring "ingredients" are parseable; (b) `generate_changelog.py` runs once at release time, "cooking" the CHANGELOG from validated ingredients.

#### Pillar 3: Git log as single source of truth

No stateful changelog buffer file (`UNRELEASED.md` or `debian/changelog`). The Git log itself is the single source of truth.

**Consequence:** No "double-entry bookkeeping" risk, no merge conflicts on a buffer file, no manual CLI step.

#### Pillar 4: LLM-based generation is superseded

The previous approach used LLMs to compose RELEASE_NOTES.md from a diff file. This introduces non-determinism and "hallucination" risks in technical documentation. With structured commit bodies, a deterministic regex parser produces identical output every time — traceability from commit to changelog entry is 1:1.

## Consequences

### Positive

- **Deterministic CHANGELOG**: Same git history always produces same changelog — 1:1 traceability from commit to entry.
- **Ecosystem-portable**: As a spoke package ({term}`ADR-26020`), any repo can install the generator via `uv add`.
- **Zero manual curation**: CHANGELOG maintenance cost drops to zero after the initial convention adoption.
- **Supersedes LLM generation**: Eliminates non-determinism and hallucination risks in technical documentation.

### Negative

- **Adoption friction**: Contributors must learn the `- Verb: file-path — what_and_why` body convention.
- **Maintenance burden**: We own the parser (~200 lines) and validator. But scope is small and follows the established script suite pattern ({term}`ADR-26011`).
- **Bespoke convention**: The body format is an ecosystem-specific extension of Conventional Commits, not an industry standard. The parser is portable to any project adopting the same format, but the format itself is bespoke.
- **History rewrite risk**: If the parsing rules change, generating a changelog for older commits may produce different output.

## Alternatives

### Evaluation Criteria

| # | Criterion | Weight | Why it matters |
|---|-----------|--------|----------------|
| 1 | **Output fidelity** | High | Must produce hierarchical CHANGELOG with sub-items, not flat lists |
| 2 | **Python-native** | High | Ecosystem uses Python + uv exclusively ({term}`ADR-26001`, {term}`ADR-26003` rejected Node.js) |
| 3 | **Ecosystem portability** | High | Must work across all ecosystem repos, installable as a package |
| 4 | **Convention compliance** | Medium | How far from Conventional Commits spec? |
| 5 | **Maintenance burden** | Medium | Who maintains the tooling? |
| 6 | **Extensibility** | Medium | Can it adapt as needs evolve? |
| 7 | **Adoption friction** | Low-Med | How hard for contributors to learn? |

### 1. git-cliff (Rust binary) — REJECTED

[git-cliff](https://git-cliff.org/) is a Rust-based changelog generator with regex parsers and Tera templates. `split_commits: true` processes each body line as a separate entry. This would turn each bullet into its own changelog line. But it **cannot produce hierarchical output** (subject as parent, bullets as children) — all lines become flat, same-level entries. Additionally, while `pip install git-cliff` exists, it wraps a Rust binary, breaking the Python-only ecosystem constraint ({term}`ADR-26001`).

| Criterion | Score | Notes |
|-----------|-------|-------|
| Output fidelity | **Partial** | Flat output only. No parent-child hierarchy. Would need post-processing. |
| Python-native | **No** | Rust binary. `pip install git-cliff` wraps Rust. Breaks {term}`ADR-26001`. |
| Ecosystem portability | Good | Configurable in pyproject.toml, pip-installable |
| Convention compliance | High | Standard CC, no custom body format needed |
| Maintenance burden | Low | Community-maintained (10k+ GitHub stars) |
| Extensibility | Medium | Tera templates are powerful but limited to what git-cliff exposes |

### 2. git-changelog (Python + Jinja2) — REJECTED

[git-changelog](https://pypi.org/project/git-changelog/) is a Python changelog generator with Jinja2 templates and CC parsing. Body included as a block in the template context. No bullet extraction. Jinja2 templates can render the body as-is but **cannot decompose it into structured sub-items** without custom Python filters — body bullet extraction is not a first-class feature.

| Criterion | Score | Notes |
|-----------|-------|-------|
| Output fidelity | **Partial** | Body as a block. Jinja2 COULD split on `\n- ` but it's a hack. |
| Python-native | Yes | Pure Python |
| Ecosystem portability | Good | pip-installable, Jinja2 templates |
| Maintenance burden | Low | Community-maintained |
| Extensibility | Medium | Body decomposition requires custom Jinja2 filters |

### 3. Commitizen (Python framework) — REJECTED

[Commitizen](https://commitizen-tools.github.io/commitizen/) is a Python framework for guided commits, version bumping, and changelog generation. Has `changelog_message_builder_hook` that can generate multiple changelog entries from a single commit. However, [known issues](https://github.com/commitizen-tools/commitizen/issues/524) with multiline body handling in custom configs — each line may appear as a separate entry incorrectly.

Commitizen is an **opinionated framework** (guided commits, version bumping), not just a changelog parser. Adopting it means adopting its workflow model, which exceeds our need for a focused parsing tool.

| Criterion | Score | Notes |
|-----------|-------|-------|
| Output fidelity | **Possible** | With `changelog_message_builder_hook` and custom template, but fragile. |
| Python-native | Yes | Pure Python |
| Maintenance burden | Low-Med | Community-maintained but custom hooks are our code |
| Extensibility | High | Full Python plugin system, custom rules, templates |

### 4. Hybrid: git-changelog + custom Jinja2 filter — REJECTED

Use git-changelog as the parsing engine (handles git log, CC parsing, version grouping) but add a custom Jinja2 filter that decomposes body text into bullet sub-items. Less code to write than a full custom parser. But it **creates a dependency on git-changelog's internal data model** — if git-changelog changes how it exposes body text, the filter breaks.

| Criterion | Score | Notes |
|-----------|-------|-------|
| Output fidelity | Good | git-changelog handles structure, custom filter handles bullets |
| Python-native | Yes | Both are Python |
| Maintenance burden | Low-Med | Only the filter is our code |
| Extensibility | Medium | Limited by what git-changelog exposes to templates |

### 5. Debian `dch` (stateful metadata buffer) — REJECTED

The `dch` approach introduces the concept of a **Changelog Buffer**. Instead of the Git history being the sole source of truth, a structured file (e.g., `UNRELEASED.md`) acts as a staging area. While this provides higher editorial control, it introduces **"Double-Entry Bookkeeping"** — the delta between what was actually committed and what was recorded in the changelog buffer can drift.

Critical problems:
- **The "Amend" Problem:** `dch` doesn't know if you `git commit --amend`. A stateful buffer ends up with duplicate entries unless the hook is idempotent (checks for commit hash).
- **Merge Conflict Hell:** If two developers modify the same `CHANGELOG.md` via a `dch`-style tool, the conflict is harder to resolve than a simple Git rebase.
- **SVA Violations:** Requires a manual CLI step (C1 violation) and adds a persistent state-tracking layer (C4 violation).

**Mitigation adopted:** The "Unreleased Stanza" concept is preserved — `generate_changelog.py` can output commits since the last tag, providing the same "what's pending" visibility without a separate file.

### 6. Stacked Diffs — REJECTED

Maintain atomic commit history within feature branches for `git bisect` granularity. Each diff = separate PR, reviewed independently.

Critical problems:
- **Rebase toil:** Managing a stack of 10 atomic commits manually requires constant rebasing, increasing "Conflict Fatigue" risk in local development.
- **Tooling gap:** True stacked diffs require specialized CLI wrappers (Graphite, Sapling) to maintain integrity; standard Git makes this a high-toil manual process.
- **Bisect deprioritized:** The primary benefit of stacked diffs — preserving line-level bisect granularity — no longer justifies the overhead since `git bisect` is formally deprioritized (see Pillar 1).

### 7. LLM-Based Generation (previous approach) — SUPERSEDED

Uses LLMs to compose RELEASE_NOTES.md from a diff file. Zero effort for developers. But **non-deterministic**: same input can produce different output across runs. No audit trail from commit to changelog entry. Violates traceability requirements.

### 8. Custom Python Parser (spoke package) — SELECTED

A custom Python package published as a spoke package in the ecosystem. Understands the structured body convention natively. First-class bullet extraction. Knows that `- Verb: file-path — what_and_why` lines are changelog sub-items. Ignores prose lines. Excludes ArchTag and trailers.

**The only approach that can produce the exact hierarchical CHANGELOG format natively** — all others require hacks or post-processing. Fits the ecosystem model perfectly: a spoke package that any repo can install via `uv add`. Full control means it can evolve with the ecosystem.

| Criterion | Score | Notes |
|-----------|-------|-------|
| Output fidelity | **Full** | Designed for our exact CHANGELOG format. Hierarchical output is the primary feature. |
| Python-native | Yes | Pure Python, follows {term}`ADR-26001` |
| Ecosystem portability | **Excellent** | Spoke package, `uv add` in any repo. Follows {term}`ADR-26020` hub-spoke model. |
| Convention compliance | Medium | Extends CC with structured body. Non-standard but well-documented. |
| Maintenance burden | Medium | We own it. But scope is small (~200 lines parser + tests). |
| Extensibility | **High** | Full control. Can add SemVer detection, RELEASE_NOTES skeleton later. |

### Decision Matrix

| Criterion | git-cliff | git-changelog | commitizen | Custom parser | Hybrid | dch | Stacked | LLM |
|-----------|:---------:|:-------------:|:----------:|:-------------:|:------:|:---:|:-------:|:---:|
| Output fidelity | partial | partial | possible | **full** | good | good | N/A | partial |
| Python-native | **no** | yes | yes | yes | yes | yes | yes | yes |
| Ecosystem portability | good | good | good | **excellent** | good | poor | poor | medium |

## References

- [Production Git Workflow Standards](/tools/docs/git/01_production_git_workflow_standards.ipynb) — Structured Commit Body Format section
- [Pre-Commit Hooks and Staging Instruction](/tools/docs/git/02_pre_commit_hooks_and_staging_instruction_for_devel.ipynb) — Commit Message Validation section
- {term}`ADR-26001`: Use of Python and OOP for Git Hook Scripts
- {term}`ADR-26002`: Adoption of the Pre-commit Framework
- {term}`ADR-26003`: Adoption of gitlint for Tiered Workflow Enforcement
- {term}`ADR-26011`: Formalization of the Mandatory Script Suite Workflow
- {term}`ADR-26020`: Hub-and-Spoke Ecosystem Documentation Architecture
- [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)

## Participants

1. Vadim Rudakov
2. Senior DevOps Systems Architect (Gemini)
3. Claude Opus 4.6
