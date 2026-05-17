---
title: "Architecture Decision Workflow"
authors:
  - name: Vadim Rudakov
    email: rudakow.wadim@gmail.com
date: "2026-05-03"
description: "Describes the full lifecycle of architectural decisions, from evidence gathering to ADR promotion and validation."
tags: [architecture, governance, workflow]
---
---
options:
  type: guide
  version: 1.1.0
  birth: '2026-03-02'
  token_size: 4575
---
This guide covers the full lifecycle of an architectural decision — from understanding what an ADR is, through evidence gathering and writing, to validation. It complements the [ADR template](/architecture/adr/adr_template.md) (structure and fields) and `adr.conf.json` (validation rules).

**Guiding principle:** Write for the reader 3 years from now who has no context about today's implementation.

## What is an ADR?

**ADR (Architecture Decision Record) is a text document capturing a key architectural decision made within a project.** An ADR describes:

- How and why the decision was made,
- Which alternatives were considered,
- And what consequences this choice entails for the project.

ADRs preserve the team's collective memory — the entire history of decisions remains in the repository, even when team members change. They enable fast onboarding through transparency of decisions, mitigate risks by resolving recurring questions once, and maintain architectural consistency as the project evolves.

Each ADR is a separate file dedicated to one significant architectural topic (e.g., choice of database, integration pattern, framework).

## Creating an ADR

All ADRs live in `architecture/adr/` as a flat directory — files are never moved to an archive folder ({term}`ADR-26016`).

To create a new ADR:

1. Copy the [ADR template](/architecture/adr/adr_template.md)
2. Follow the structure, required fields, valid statuses, and tags defined in `adr.conf.json` — this file is the Single Source of Truth for all ADR validation rules. **Tagging convention:** the first tag is the *primary tag* and determines which sub-section the ADR appears under in the index. Choose the most specific domain tag first (e.g., `[devops, architecture]` not `[architecture, devops]`). Valid tags are defined in `conf.json`
3. [check_adr.py](/tools/scripts/check_adr.py) validates ADRs against the config and auto-updates the [ADR index](/architecture/adr_index.md) — never edit the index manually. Run: `uv run tools/scripts/check_adr.py --fix` (see [script docs](/tools/docs/scripts_instructions/check_adr_py_script.ipynb))
4. Follow the [quality guidelines](#writing-the-adr--core-discipline) and review the [anti-patterns checklist](#anti-patterns-checklist) before requesting promotion

## The RFC→ADR Workflow

In this project, `proposed` ADRs serve as RFCs (Requests for Comments). There is no separate RFC document type — the ADR itself is the living design document that collects discourse before promotion. See {term}`ADR-26025` for the full specification.

**Key points:**

- **RFC = Proposed ADR.** Draft a new ADR with `status: proposed`. Iterate on `## Alternatives` and `## Context` as analysis progresses
- **Promotion gate** (proposed → accepted). [check_adr.py](/tools/scripts/check_adr.py) enforces criteria that must be met before an ADR can transition to `accepted` — see {term}`ADR-26025` for the full list
- **AI consultation records.** Raw Gemini/Claude transcripts are working files — not committed to the repo. Analytical value is absorbed into evidence artifacts or the ADR's `## Alternatives` section (Fat ADR pattern)
- **Stale proposals.** ADRs remaining `proposed` >90 days without updates trigger a CI warning

## Status Transitions: Rejection, Supersession, Deprecation

Not every ADR reaches `accepted`. The [ADR template](/architecture/adr/adr_template.md) and `adr.conf.json` define five statuses: `proposed`, `accepted`, `rejected`, `superseded`, and `deprecated`. The first two are covered above; this section covers the terminal statuses that remove an ADR from active architecture.

All terminal-status ADRs remain in `architecture/adr/` (flat directory, no archive — {term}`ADR-26016`) and appear under **Historical Context** in the [ADR index](/architecture/adr_index.md).

### Rejection

Reject an ADR when its approach is **fundamentally incompatible** with current methodology or principles — even if individual concepts within it remain valid.

**How to reject:**

1. Set `status: rejected` in frontmatter (keep `superseded_by: null`)
2. Add a `## Rejection Rationale` section (required by `adr.conf.json` for rejected ADRs)
3. In the rationale, explain *why* the approach is incompatible — reference the principle or methodology evolution that invalidates it
4. Acknowledge any valid concepts and state where they are documented without the problematic coupling

**Example:** {term}`ADR-26005` rejected tool-specific orchestration mandates, but acknowledged the valid Hybrid Bridge pattern and state isolation concepts for documentation elsewhere.

### Supersession

Supersede an ADR when its **core principle is still valid** but a newer ADR provides a better solution or generalization that obsoletes the original.

**How to supersede:**

1. In the **superseded ADR**: set `status: superseded` and `superseded_by: ADR-NNNNN` in frontmatter. Add `Superseded by: {term}`ADR-NNNNN`` to the Status section body
2. In the **superseding ADR**: set `status: accepted`. Add `Supersedes: {term}`ADR-NNNNN`` to the Status section body. Explain why the older ADR is superseded — what the newer approach improves
3. The superseding ADR must stand on its own — a reader should not need to read the superseded ADR to understand the decision

**Example:** {term}`ADR-26023` superseded {term}`ADR-26018` and {term}`ADR-26019` — the principle of machine-readable metadata remained valid, but MyST-native field names eliminated the need for custom fields and workaround scripts.

### Deprecation

Deprecate an ADR when the decision is **no longer relevant** — the problem it addressed no longer exists, or the domain has changed enough that the decision provides no guidance. Unlike supersession, no replacement ADR is created.

> **Not yet formalized.** The `deprecated` status is defined in `adr.conf.json` but has no template support (no conditional section like `Rejection Rationale`), no validation rules in [check_adr.py](/tools/scripts/check_adr.py), and no ADRs have used it yet. The steps below are provisional — they will be formalized when the first ADR needs deprecation.

**Provisional steps:**

1. Set `status: deprecated` in frontmatter
2. Add a brief explanation in the Status section: why the decision is no longer applicable

### Valid Status Transitions

Not all transitions are valid. The starting status constrains which terminal statuses are reachable. The valid transitions are defined in `adr.conf.json` `status_transitions` (SSoT) and enforced by [check_adr.py](/tools/scripts/check_adr.py).

**Key rule:** Only `accepted` ADRs can be superseded or deprecated. Proposed ADRs that don't survive review are rejected — even if valid concepts within them are absorbed into other ADRs.

### Choosing the Right Terminal Status

| Situation | Status | Superseding ADR? |
|---|---|---|
| Approach conflicts with current principles | `rejected` | No |
| Principle valid, better solution exists | `superseded` | Yes — required |
| Decision no longer relevant to the project | `deprecated` | No |

### Version Semantics

The `options.version` field follows semver and is tied to the ADR's status:

| Status | Version range | Rationale |
|---|---|---|
| `proposed` | `0.x.y` | The decision is not yet accepted — pre-1.0 signals instability |
| `accepted` | `≥ 1.0.0` | Acceptance is the stability guarantee — bump to 1.0.0 on promotion |
| `superseded` / `rejected` / `deprecated` | Frozen | Terminal statuses do not receive further edits |

**Bump rules within a status:**
- `proposed`: patch (`0.1.0` → `0.1.1`) for fixes, minor (`0.1.0` → `0.2.0`) for structural changes to the decision
- `accepted`: patch for typos/formatting, minor for Consequences updates or new evidence, major for scope changes (which likely warrant a new ADR instead)

## Evidence Gathering

Before writing an ADR, determine whether the decision needs upstream research. Trade studies, alternative comparisons, and dialogue extractions all belong in the evidence pipeline before they appear in an ADR.

### When to Gather Evidence

Gather evidence when:

- Multiple viable alternatives exist and require systematic comparison
- The decision involves trade-offs that benefit from structured analysis
- External research (AI consultations, literature review) informs the choice
- A failure or incident motivates the decision (retrospective)

Skip evidence when the decision is straightforward with clear alternatives and no upstream research is needed. Not every ADR requires an analysis artifact.

### Evidence Artifact Types

All evidence artifacts live in `architecture/evidence/` and are governed by `evidence.conf.json`. See {term}`ADR-26035` for the full specification.

**Sources (S-YYNNN)** — Ephemeral transcripts and raw inputs.
Sources follow a three-commit lifecycle: capture → extract → delete. The source file is removed after its value is extracted into an analysis; git history preserves the original. See [Sources README](/architecture/evidence/sources/README.ipynb) for the full workflow.

**Analyses (A-YYNNN)** — Extracted findings, trade studies, and comparisons.
Analyses are the durable evidence artifacts. Required sections include Problem Statement and References. Link to the producing ADR via the `produces:` frontmatter field.

**Retrospectives (R-YYNNN)** — Post-mortems and failure analyses.
Retrospectives document what went wrong and why. Include a severity level (`low`, `medium`, `high`, `critical`) in frontmatter.

## Writing the ADR — Core Discipline

Four rules apply to every section of an ADR:

### Rule 1: Decisions, Not Descriptions

An ADR records a choice and its rationale. It is not a specification, tutorial, or design document. If a section reads like documentation rather than a decision record, it belongs elsewhere.

### Rule 2: Every Assertion Must Be Falsifiable or Traceable

Vague claims weaken an ADR. Every statement of benefit, risk, or impact should be something a future reader can verify or trace to evidence.

| Weak (unfalsifiable) | Strong (falsifiable/traceable) |
|---|---|
| "Improves developer experience" | "Reduces CI runtime from 12 min to 4 min" |
| "More maintainable" | "Eliminates the 3-file synchronization requirement" |
| "Better performance" | "Benchmarks show 40% reduction in memory usage (see A-26003)" |

### Rule 3: No Undefined Vocabulary

Expand every abbreviation on first use. Do not use terminology that is not defined in this repository or in a referenced standard.

| Do | Don't |
|---|---|
| "YAGNI (You Ain't Gonna Need It) prohibits speculative features" | "This violates YAGNI" (without prior expansion) |
| "Migration requires updating all three configuration files" | "This can be completed within one sprint" (undefined duration) |
| "SVA (Smallest Viable Architecture) constrains scope" | "The SVA principle applies here" (undefined term) |

### Rule 4: Separate Concerns Between ADRs

Separation of concerns in ADRs mirrors separation of concerns in code. When two aspects of a decision have independent justifications and change at different rates, split them into separate ADRs and use cross-references. An ADR that embeds another ADR's concern becomes brittle — every change to the embedded concern forces an edit to the host ADR.

**Example:** {term}`ADR-26036` decides *where* configs live and *how they're named* (structure), while {term}`ADR-26054` decides *what format* they use (serialization). By using `<ext>` placeholders and delegating format to {term}`ADR-26054`, the structure ADR survives format changes without edits — the same principle as depending on an interface rather than an implementation.

**Test:** If changing one aspect of your decision (e.g., the file format) would require editing prose in another section (e.g., naming conventions), those aspects belong in separate ADRs.

## Section-by-Section Guidance

### Context

1. **Start with the problem, not the solution.** The first sentence should describe what is broken, missing, or inadequate — not what you plan to build
2. **Include evidence.** Reference tables, metrics, specific failures, or analysis artifacts. A Context section without evidence is an opinion
3. **Do not front-load the solution.** The reader should understand *why* a decision is needed before learning *what* was decided

### Decision

1. **Use affirmative, active language.** "Adopt X," "Require Z," "Standardize on Y" — not "X should be considered" or "It was decided that..."
2. **Make it falsifiable.** A future reader should be able to determine whether the decision was followed or violated
3. **Keep implementation details out.** Migration mappings, file-by-file change lists, and step-by-step procedures belong in evidence artifacts (A-YYNNN), not in the ADR body. The ADR states *what* and *why*; evidence records *how*
4. **Decide at the capability level, not the tool level.** State the requirement; the chosen tool is the current implementation of that requirement — a detail inside the Decision body, not the decision itself. A reader three years from now must be able to judge whether the principle still holds even if the tool changed. If the tool name is the first word of your Decision section, the abstraction is likely too low.
5. **Never invent identifiers.** Every constraint ID, principle number, or framework label referenced in the decision must be defined in an authoritative source. Invented identifiers create false traceability (see {term}`ADR-26026`)

### Consequences

**Positive consequences:**
- Focus on capabilities and principles enabled by the decision, not on current artifacts or tooling. Artifacts change; principles persist
- Frame positives as durable outcomes: "Enables single-source validation for all evidence types" rather than "The check_evidence.py script will validate files"

**Negative consequences and risks:**
- Provide honest mitigations that address the actual risk mechanism. "When the constraint proves too restrictive, revise via a superseding ADR" addresses the risk. "This is unlikely to happen" does not
- Format mitigations as actions: "When X occurs, do Y" — not "This is unlikely because Z"
- Best-effort or deferred mitigations must say so explicitly: "**Mitigation (deferred):** Will be addressed when usage patterns stabilize"

### Alternatives

1. **Same level of abstraction as the decision.** If the decision is an architectural pattern, alternatives should be architectural patterns — not specific tools or libraries. A tool-level alternative to a principle-level decision is a category error (see {term}`ADR-26005`)
2. **Minimum two alternatives.** The [check_adr.py](/tools/scripts/check_adr.py) promotion gate enforces this for `proposed → accepted` transitions
3. **Rejection reasons grounded in principles or evidence.** "Rejected because it introduces coupling between layers 2 and 4" is grounded. "Rejected because it's too complex" is a dismissal
4. **"Do nothing" only when viable.** Include a status-quo alternative only when maintaining the current state is a genuine option, not as a strawman

### References

1. **Internal links:** Use markdown links `[Title](/repo-root-relative/path)` — backtick paths bypass [check_broken_links.py](/tools/scripts/check_broken_links.py) validation
2. **ADR cross-references:** Use `{term}`ADR-NNNNN`` format with a hyphen between "ADR" and the number
3. **Verify filenames:** ADR filenames use truncated slugs. Always glob (`architecture/adr/adr_26NNN*.md`) to verify the exact filename before creating links
4. **Include evidence:** When an analysis artifact informed the decision, link to it in References
5. **External links:** Use stable URLs only. Conference talk URLs, blog posts behind paywalls, and URLs with session tokens are not stable

### Participants

1. List all contributors who materially influenced the decision — authorship, review, or domain expertise
2. AI participants include the model name (e.g., "Claude claude-opus-4, Gemini 2.5 Pro")

## Anti-Patterns Checklist

Review every ADR against these eleven anti-patterns before promotion:

1. **Undefined domain vocabulary** — Terms used without definition in this repository or in a referenced standard
2. **Unexpanded abbreviations** — Abbreviations used without expansion on first occurrence
3. **Ephemeral implementation details** — Migration steps, file lists, or tooling specifics embedded in the ADR body instead of evidence artifacts
4. **Artifact-tied consequences** — Consequences that reference current filenames or tools instead of durable principles
5. **Reassurance mitigations** — Mitigations that dismiss the risk ("unlikely to happen") instead of addressing the mechanism
6. **Wrong-abstraction alternatives** — Alternatives at a different level of abstraction than the decision (e.g., tool alternatives to a principle decision)
7. **Invented identifiers** — Constraint IDs, principle numbers, or labels not defined in an authoritative source
8. **Tool-as-architecture** — Elevating a tool choice to an architectural decision when the real decision is the capability or pattern
9. **Future promises as mitigations** — "We will address this later" without a concrete trigger, owner, or timeline
10. **Dismissive alternatives** — Alternatives rejected without trade-off analysis or evidence
11. **Embedded sibling concerns** — An ADR that hardcodes details owned by another ADR (e.g., file extensions, format specifics) instead of cross-referencing. Changes to the sibling ADR force edits here — a coupling smell

## Validation

Pre-commit hooks automatically run structural validation on commit — [check_adr.py](/tools/scripts/check_adr.py), [check_evidence.py](/tools/scripts/check_evidence.py), [check_broken_links.py](/tools/scripts/check_broken_links.py), and [check_link_format.py](/tools/scripts/check_link_format.py) all execute as part of the hook chain.

The one validation step that cannot be automated is the [anti-patterns checklist](#anti-patterns-checklist). Walk through it item by item before requesting promotion. Each anti-pattern found in a promoted ADR required a follow-up commit to fix — catching them before promotion is cheaper.

## Governing Decisions

The following ADRs constrain the architecture decision workflow itself:

| ADR | Title | Governs |
|---|---|---|
| {term}`ADR-26016` | Metadata-Driven Architectural Records Lifecycle | Flat directory, metadata-driven lifecycle, no archive folders |
| {term}`ADR-26023` | MyST-Aligned Frontmatter Standard | Required frontmatter fields: `title`, `author`, `date`, `options.version`, `options.birth` |
| {term}`ADR-26025` | RFC→ADR Workflow Formalization | Proposed-as-RFC, promotion gates, stale proposal warnings |
| {term}`ADR-26029` | pyproject.toml as Tool Configuration Hub | Config in `pyproject.toml [tool.X]`, domain configs via `parent_config` |
| {term}`ADR-26035` | Architecture Knowledge Base Taxonomy | Evidence pipeline: Sources, Analyses, Retrospectives |

Anti-pattern examples from rejected or revised ADRs: {term}`ADR-26005` (tool choice masquerading as architecture), {term}`ADR-26026` (invented identifiers without authoritative source).

## For Further Study

- **Book:** "Documenting Software Architectures: Views and Beyond" — Clements et al. Provides a systematic approach to architectural documentation and decision rationale
- **Documentation:** Michael Nygard's [adr.github.io](https://adr.github.io/). Describes the classic ADR format — recognized as an industry standard

Quality is not a final polish step — it is the discipline that makes architectural decisions useful beyond the week they were written.
