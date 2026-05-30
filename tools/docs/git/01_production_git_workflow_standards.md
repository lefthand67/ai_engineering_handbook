---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.1
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
---

---
title: Production Git Workflow Standards
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: 2026-05-04
description: Mandatory professional-grade conventions for Git branching and committing
  in the AI Engineering Book repository.
tags:
- git
- workflow
- documentation
options:
  type: guide
  version: 1.0.1
  birth: 2025-11-29
  token_size: 6125
---
# Production Git Workflow Standards

+++

This handbook establishes mandatory, professional-grade conventions for Git branching and committing. Adherence to these standards is essential for achieving traceability, enabling automated MLOps gates, ensuring accurate changelogs, and streamlining architectural reviews.

The workflow is enforced through a Three-Tier Naming Structure, a strict Conventional Commits policy with structured body bullets, and a Squash-and-Merge strategy that produces one atomic commit per PR on trunk.

+++

## **Intro: Three-Tier Naming Structure**

+++

All changes must follow this strictly enforced hierarchy for complete lifecycle context.

| Tier                 | Component                                                | Purpose                                                                            | Requirement                                                                     |
|:-----------------|:-----------------|:-----------------|:-----------------|
| **1. SCOPE**         | Branch Prefix + Ticket ID<br>`fix/29-fix-broken-feature` | Defines the **scope** of work (e.g., `feature/`) and its associated **work item**. | **MANDATORY** for all branches.                                                 |
| **2. INTENT**        | Commit Title Prefix<br>`fix: Fix login in app`           | Defines **what changed** (Conventional Commits type, e.g., `feat:`, `fix:`).       | **MANDATORY** for all commits.                                                  |
| **3. JUSTIFICATION** | Architectural Tag (ArchTag)                              | Defines **why** a structural change was made. Placed in the commit body.           | **CONDITIONAL** (Mandatory for `refactor:`, `perf:`, `BREAKING CHANGE` Footer). |

+++

## **Tier 1: Branch Prefixing Policy - Scope & Traceability**

+++

Branch names **MUST** use the format:

`<prefix>/<TICKET-ID>-<short-kebab-description>`

*Names must be lowercase with hyphens. This format enables automatic linking to issues and Pull Requests. Not implemented yet.*

| Prefix | Work Scope | Example  |
|:-----------------------|:-----------------------|:-----------------------|
| `main/`| The main development branch (e.g., `main`, `master`, or `develop`) | N/A  |
| `feat/`| New features or significant enhancements/additions.| `feat/456-add-metrics-endpoint`  |
| `fix/` | Correcting a user-impacting defect/bug.| `bugfix/123-login-404-error` |
| `hotfix/`  | Urgent fixes applied directly to the production branch.| `hotfix/123-payment-gateway-bug` |
| `release/` | Preparation for a formal release (e.g., final testing, version bumps). | `release/v1.2.0-final-prep`  |
| `chore/`   | For non-code tasks like dependency, docs updates.  | `chore/TICKET-789-update-deps`   |

> Branches are different from commits—they are temporary and mainly used until merged. Introducing too many types for branches would be unnecessary and would make them harder to manage and remember.
>
> -- [Conventional Branch docs](https://conventional-branch.github.io/)

:::{seealso}
> 1. [Conventional Branch](https://conventional-branch.github.io/) - external link
> 2. [ADR 26003: Adoption of `gitlint` for Tiered Workflow Enforcement](/architecture/adr/adr_26003_adoption_of_gitlint_for_tiered_workflow.md)
:::

+++

## **Tiers 2 & 3: Conventional Commit Policy - Intent & Justification**

+++

### Tier 2: Commit Title Prefix - **What** Changed

+++

The commit title **MUST** start with `<type>: <description>`. The description must be **50 characters maximum** and written in the **imperative mood**.

| Group  | Type| Intent | ArchTag Required? | SemVer Impact |
|:--------------|:--------------|:--------------|:--------------|:--------------|
| **Core**   | `feat:` | A new feature or enhancement.  | NO | **Minor** |
|| `fix:`  | A bug fix. | NO| **Patch** |
| **Breaking**   | *(any type)* + `BREAKING CHANGE` footer | Introduces an incompatible API/behavior change.| **YES**   | **Major** |
| **Architectural**  | `refactor:` | Code restructuring that neither fixes a bug nor adds a feature; can change public API. | **YES**   | Patch/Minor/Major |
|| `perf:` | Code change that measurably improves performance; can change public API.   | **YES**   | Patch/Minor/Major |
| **Routine**| `docs:` | Changes to documentation only. | NO| None  |
|| `test:` | Adding or correcting tests.| NO| None  |
|| `chore:`| Routine maintenance, dependency updates, minor clean-up.   | NO| None  |
|| `ci:`| Changes to CI/CD configuration and workflows.   | NO| None  |
|| `pr:`| Promotional or announcement posts (e.g., Telegram channel).   | NO| None  |

:::{important}
Commit types inform SemVer, but do not dictate it. Final SemVer must be validated against API/behavior contracts.

See: [SemVer: Artifact Versioning Policy (AVP)](/tools/docs/git/semver_artifact_versioning_policy_avp.ipynb)
:::

:::{tip} Machine-readable configuration
The valid types, ArchTag-required types, and CHANGELOG section mappings are configured in `pyproject.toml` under `[tool.commit-convention]`. Both `validate_commit_msg.py` and `generate_changelog.py` read from this single source of truth. 

**The authoritative list of allowed ArchTags is governed by `pyproject.toml [tool.commit-convention].archtag-valid-values`. This table provides the definitions and usage guidelines for those tags.** If a commit lacks a required tag or uses an invalid one, the validator provides just-in-time instructional feedback based on this configuration.
:::

+++

#### **BREAKING CHANGE** Footer

+++

The official way to signal changes that **break compatibility** is:

```
<type>(<optional scope>): <description>

BREAKING CHANGE: <description of breaking impact>
```

| Intent  | Correct Conventional Commit Form   |
|-----------------------------|-------------------------------------------|
| **Removing a feature** (user-facing)| `feat: remove legacy auth API`<br>`BREAKING CHANGE: The /v1/login endpoint is deleted. Use /v2/auth.`  |
| **Removing internal code** (no external impact) | `refactor: delete unused cache module`<br>*(No `BREAKING CHANGE` needed)*  |
| **Removing a config option or API** (breaking)  | `fix: drop support for deprecated TLS 1.0`<br>`BREAKING CHANGE: TLS 1.0 connections are now rejected.` |

:::{important} Key principle
A **breaking change** is defined by **observable behavior change for consumers** — not by the act of change itself.
:::

:::{seealso}
> [Conventional Commits – Breaking Changes: Commit Message with Description and Breaking Change Footer](https://www.conventionalcommits.org/en/v1.0.0/#commit-message-with-description-and-breaking-change-footer)
:::

+++

### Tier 3: Architectural Tagging - **Why** Changed

+++

For commits of type
- `refactor:`,
- `perf:`, or
- `BREAKING CHANGE` Footer,

the architectural intent **MUST** be provided as an ArchTag (Architectural Tag).

- **Format:** The tag **MUST** be the **first line** of the commit body: `ArchTag:TAG-NAME` (one tag only). Structured body bullets (see [Structured Commit Body Format](#structured-commit-body-format)) follow after the ArchTag line. Each bullet uses the format `- <Verb>: \`<file-path>\` — <what/why>`.
- **Syntax Rules:** The tag **MUST NOT** include the `#` symbol or any spaces.
- **Validation:** CI/CD automation tools will validate the tag's presence and correctness.

| Tag Name  | Intent   | Heuristic / Automation Gate |
|:-----------------------|:-----------------------|:-----------------------|
| `DEPRECATION-PLANNED` | Sunset code, APIs, or features scheduled for removal.| PR requires Architect Approval (Hard Gate). |
| `TECHDEBT-PAYMENT`| Reducing complexity, upgrading dependencies, or simplifying code.| Signals maintenance work.   |
| `REFACTOR-MIGRATION`  | Major architecture shift or pattern change (e.g., monolith to microservice). | PR requires Architect Approval (Hard Gate). |
| `PERF-OPTIMIZATION`   | Code change explicitly addressing a performance bottleneck.  | Benchmarks must be provided in the commit body. |

+++

:::{tip} Example of a full commit with `ArchTag` and structured body bullets
```
refactor: Simplify model loading logic

ArchTag:TECHDEBT-PAYMENT
- Refactored: `model_loader.py` — cyclomatic complexity was 15, causing test failures on edge cases; reduced to 8 by extracting format-specific loaders
- Deleted: `legacy_loader.py` — its ONNX path was the only unique logic; moved into the main loader to eliminate a 200-line file with no test coverage
```
:::

+++

``` mermaid
---
config:
  layout: dagre
  theme: redux
---
flowchart TB
    A["Commit w/ Tag"] --> B["ArchTag:"]
    B -- PERF-OPTIMIZATION --> C["Perf Tests"]
    B -- REFACTOR-MIGRATION --> D["Architect Review"]
    B -- DEPRECATION-PLANNED --> E["API Docs Update"]
    B -- TECHDEBT-PAYMENT --> F["Debt Score Δ"]
    C --> G["Changelog Section"]
    D --> G
    E --> G
    F --> G
```

+++

## **Structured Commit Body Format**

+++

Every commit on trunk (the squashed commit produced by Squash-and-Merge) **MUST** have a structured body with at least one changelog bullet. This extends Tier 2 (Intent) with detailed change manifests that enable automated CHANGELOG extraction.

+++

### Body Convention

+++

```
<type>[(<scope>)]: <subject line>

- <Verb>: <file-path> — <what_and_why>

Co-Authored-By: ...
```

The `<what_and_why>` portion explains what changed in the file and why — this is a changelog, so each bullet should capture both the substance and the motivation.

**Rules:**

1. Body **MUST** contain at least one line starting with `- ` (a changelog bullet).
2. Each bullet is a self-contained changelog entry. **No line length limit** — one bullet = one line, regardless of length. Commits are primarily read in Git host UIs which wrap automatically.
3. Verb prefix before `:` — `Created`, `Updated`, `Deleted`, `Renamed`, `Fixed`, `Moved`, `Added`, `Removed`, `Refactored`, `Configured`.
4. **`<file-path>` is a path relative to the repo root.** Single file: `check_adr.py`. Glob/pair: `01_guide.(md|ipynb)`. Rename: `old.py` → `new.py`. Every change lives in a file — always use the nearest file path, no abstract targets.
5. Git trailers (after blank line, `Key: Value` format) are excluded from parsing.
6. Non-bullet lines in the body (prose context) are ignored by the parser but allowed for human context.
7. `ArchTag:TAG-NAME` line (Tier 3) is preserved for justification validation but excluded from changelog output.
8. **Sub-bullets** provide detail under a file target: 4-space indent + em-dash + space + lowercase verb + description (`    — added feature X`). Sub-bullets MUST follow a main bullet — orphan sub-bullets are rejected. Sub-bullets are excluded from CHANGELOG output (only main bullets survive).

+++

### Sub-bullet Format

+++

Sub-bullets break down *what* changed within a single file target. They are validated by the pre-commit hook but do not appear in the generated CHANGELOG (only main bullets are extracted).

```
- <Verb>: <file-path> — <what_and_why>
    — <lowercase_verb> <specific_detail>
    — <lowercase_verb> <another_detail>
- <Verb>: <file-path> — <what_and_why>
```

Sub-bullet rules:
- Format: exactly 4 spaces + `— ` (em-dash + space) + lowercase verb + description
- MUST follow a main bullet — no orphan sub-bullets
- Multiple main bullets can each have their own sub-bullet group
- Sub-bullets are validated but **not** included in CHANGELOG output

+++

### Examples

+++

:::{dropdown} Complex commit (docs) — real commit `3e652bc`
```
docs: Restructure website deployment documentation

- Created: tools/docs/website/01_github_pages_deployment.(md|ipynb) — the GitHub Pages guide was invisible on the website because it lacked a Jupytext pair; new canonical guide consolidates scattered setup instructions
- Renamed: mystmd_website_deployment_instruction.(md|ipynb) → 02_self_hosted_deployment.(md|ipynb) — clear numbering signals the active guide (01) vs deprecated alternative (02)
- Refactored: 02_self_hosted_deployment.md — duplicated MyST init/config/testing sections diverged from the canonical guide; replaced with cross-references to eliminate drift
- Deleted: tools/docs/git/github_pages_setup.md — content fully absorbed into 01_github_pages_deployment; keeping both would cause conflicting instructions
- Updated: architecture/adr/adr_26022...md — self-hosted link pointed to a renamed file; split single reference into two entries (active + deprecated) for clarity
- Updated: architecture/packages/README.md — GitHub Pages setup link pointed to the deleted file
- Updated: architecture/packages/creating_spoke_packages.md — same dead link fix in Next Steps section
- Fixed: configs/mutli-site/ → configs/multi-site/ directory typo

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```
:::

:::{dropdown} Simple commit (fix)
```
fix: Correct broken MyST term reference in ADR-26019

- Fixed: `{term}`ADR 26001`` → `{term}`ADR-26001`` across 11 ADR files — missing hyphen caused unresolved glossary references, breaking cross-linking in the rendered site

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```
:::

:::{dropdown} Refactor with ArchTag (Tier 3 + structured body coexist)
```
refactor: Simplify model loading logic

ArchTag:TECHDEBT-PAYMENT
- Refactored: model_loader.py — cyclomatic complexity was 15, causing test failures on edge cases; reduced to 8 by extracting format-specific loaders
- Deleted: legacy_loader.py — its ONNX path was the only unique logic; moved into the main loader to eliminate a 200-line file with no test coverage

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```
:::

:::{dropdown} Multi-file change with sub-bullets (feat) — real commit `00362f0`
```
feat: support sub-bullet format in commit body validation

- Updated: tools/scripts/validate_commit_msg.py
    — added _SUB_BULLET_RE for 4-space indented em-dash lines
    — added validation that sub-bullets must follow a main bullet
    — updated validate_body docstring with format examples
- Updated: tools/tests/test_validate_commit_msg.py
    — added TestParseCommitMessage class (4 tests for message parsing)
    — added 7 sub-bullet validation tests (orphan, valid, multiple mains)
    — added CLI integration tests for sub-bullet format

Co-Authored-By: Qwen-Coder <qwen-coder@alibabacloud.com>
```
:::

:::{seealso}
> {term}`ADR-26024`: Structured Commit Bodies for Automated CHANGELOG Generation
:::

+++

## **Release-Time CHANGELOG Generation**

+++

The CHANGELOG is a **generated artifact**, not a manually curated document. It is produced at release time by `generate_changelog.py`, which extracts structured body bullets from git history.

**The "Ingredients-First" pattern:**

1. **At commit time**: `validate_commit_msg.py` (pre-commit hook, `commit-msg` stage) ensures every commit body contains parseable bullets — the "ingredients" are validated continuously.
2. **At release time**: `generate_changelog.py` runs once on the frozen release branch, extracting all structured bullets since the last tag — "cooking" the CHANGELOG from validated ingredients.

```bash
# Generate changelog between two refs
uv run tools/scripts/generate_changelog.py v2.4.0..HEAD --version 2.5.0
```

The generator uses `git log --first-parent` to scan only squashed trunk commits, ignoring noise from deleted feature branches. Legacy commits (pre-standard, no body bullets) are included with subject line only — graceful degradation, not failure.

The type → CHANGELOG section mapping (e.g., `feat:` → "New Features") and section ordering are configured in `pyproject.toml` under `[tool.commit-convention.changelog-sections]`.

:::{seealso}
> {term}`ADR-26024`: Structured Commit Bodies for Automated CHANGELOG Generation
>
> Sourcing:
> - [validate_commit_msg.py](/tools/scripts/validate_commit_msg.py) — commit-msg hook (ingredients validation)
> - [generate_changelog.py](/tools/scripts/generate_changelog.py) — release-time CHANGELOG generation
:::

+++

## **Local Checkpoint Commits: Handling Intermediate Work**

+++

`WIP:` is **not a valid commit type** — the validator rejects it. For local checkpoint saves (end of day, switching machines), use `--no-verify` to bypass the pre-commit hook:

```bash
git commit --no-verify -m "WIP: save work before switching context"
```

This is an explicit opt-out: the developer consciously bypasses validation, and CI will reject the commit if it reaches a PR without being squash-merged into a proper commit.

Since the repository enforces **Squash-and-Merge** (see [Merge Strategy](#merge-strategy-atomic-change-submission)), local checkpoint commits are automatically eliminated when the PR is merged — the Git host produces a single squashed commit on trunk.

**Optional local hygiene:** Developers *may* use `git rebase -i` to clean up their branch history before opening a PR. This improves PR reviewability but is not required — the squash at merge time handles consolidation.

+++

### PR System Guardrails (Hard Gates)

+++

- **Mandatory Merge Strategy:** The repository is configured to **enforce "Squash and Merge"** for all feature branches into mainline branches. The Git host must populate the squash commit message from the PR description, ensuring structured body bullets flow into the final commit. This guarantees that the final history is composed of single, clean, semantic commits.

The most effective enforcement mechanism is layered: automated hooks catch structural issues, reviewers assess semantic quality.

| Policy   | Implementation | Rationale  |
|:-----|:--------|:------|
| **Commit Message Validation** | `validate_commit_msg.py` runs as a `commit-msg` pre-commit hook locally. CI repeats the check on the PR's squash commit candidate. | **Hard gate.** Enforces Conventional Commits subject format and structured body bullets at both commit time and merge time. Rejects all non-conforming commits including `WIP:`, `Merge `, `fixup!`, `squash!`. The only bypass is `--no-verify`. See {term}`ADR-26024`. |
| **Reviewer Responsibility** | Peer reviewers assess the **semantic quality** of the PR description (which becomes the squash commit body): are the bullets accurate, complete, and meaningful? | Structural validation is automated. Humans focus on whether the message correctly reflects the change's intent — a judgment that cannot be automated. |
| **Enforce Squash-and-Merge** | Set the repository merge policy to "Squash and Merge" only. Configure the Git host to populate the squash commit message from the PR description template. | Each PR becomes exactly one commit on trunk. The squash commit body contains the structured changelog bullets. Reverts are atomic (one commit = one revert). |

+++

### Guidance: Checkpoint Saves vs. Standard Commit Types

+++

New engineers must understand the difference to avoid misusing checkpoint saves.

| Scenario  | Recommended Approach  | Rationale   |
|:-------|:-----|:--------|
| **Saving work** at the end of the day or switching machines. | `git commit --no-verify -m "WIP: current state"`  | Work is incomplete, not ready for review. `--no-verify` explicitly bypasses validation. Must be squash-merged later. |
| **Completing a logical unit** of work (e.g., finishing the utility function signature, adding a new test). | `test: add unit test for X service` or `refactor: extract Z function from module A` | The change is coherent, stable, and useful, even if the overall feature is unfinished. It improves branch history readability *before* the final squash. |
| **Fixing a minor bug** discovered while working on a feature. | `fix: prevent divide by zero in function Y` | This is a small, atomic fix that is technically correct and may be valuable on its own. It can be squashed later or kept as a separate atomic commit. |

:::{important} **Key Takeaway**
If the commit is stable, complete, and describes an atomic, logical change that could stand on its own in the history, use a standard type with a proper structured body. If the code is broken, half-finished, or purely a checkpoint, use `git commit --no-verify` — the validator does not make exceptions.
:::

+++

## **Atomic Commits: The Guiding Principle**

+++

The goal of every feature branch’s final history is **logical atomicity**. An **Atomic Commit** is a self-contained, complete, and logically isolated unit of work.

+++

### Rules of Atomicity

+++

- **Rule 1: One Goal Per Commit.** A commit must achieve one objective only (e.g., *refactor logic*, *add unit tests*, *fix a bug*).
- **Rule 2: The Squashed Commit Must Be Stable.** The final squashed commit on trunk **MUST** be buildable and pass all tests. Intermediate feature branch commits are transient development artifacts — they are eliminated by Squash-and-Merge and need not individually pass CI.
- **Rule 3: Cohesive Narrative.** The sequence of commits in a Pull Request (PR) should tell a clear story for reviewers. However, only the squashed commit matters for trunk history and changelog extraction — internal feature branch history is invisible after Squash-and-Merge.

+++

### The "Commit by Logic" Workflow

+++

Granular atomic commits on feature branches are **recommended for PR reviewability** but are not required. Only the squashed commit on trunk matters for history and changelog extraction — internal feature branch history is invisible after Squash-and-Merge.

To create clean commits on your feature branch, **DO NOT** use `git add .` indiscriminately.

| Step  | Action   | Tool | Goal|
|:-----------------|:-----------------|:-----------------|:-----------------|
| **Stage Selectively** | Use the patch utility to stage only changes relevant to a single logical task.  | `git add -p`  | **Group changes by function and purpose,** not by file or timing.|
| **Review and Commit** | Review the staged changes (`git diff --staged`). If they represent one complete, stable, logical step, commit them with a semantic type. | `git commit -m "feat: implement X interface"` | Ensure the commit is **atomic**. |

:::{seealso} Read more
> - ["Pro Git", Chapter 7: Git Tools - Rewriting History'](https://git-scm.com/book/en/v2/Git-Tools-Rewriting-History) by Scott Chacon and Ben Straub
:::

+++

### Merge Strategy: Atomic Change Submission

+++

All changes merged into mainline branches (`main`, `develop`, etc.) **MUST** be integrated as a **single, atomic, logical unit**. This is a **fundamental engineering discipline** used in scaled production environments (Google, Meta, Microsoft) to ensure **reviewability, revertability, and traceability**.

+++

#### One Change, One Commit: The BigTech Standard

+++

In professional code review systems:
* A Pull Request (PR) or Change List (CL) represents **one logical modification** to the system.
* Intermediate development steps (e.g., test scaffolding, incremental refactors) are **development artifacts**, not production history.
* Preserving them in `main` adds **noise without operational value** and **dilutes accountability**.

:::{important} **Key Principle**
*“If it can’t be reviewed, reverted, or reasoned about as a single unit, it’s not production-ready.”*
:::

+++

### Debugging Without "git bisect" Granularity

+++

`git bisect` is **formally deprioritized** as a debugging tool in this workflow. In ML-heavy systems, regressions are more frequently caused by data/config drift or high-level logic errors, not single-line syntax bugs. Unit tests and evaluation suites catch logic bugs faster than history-walking.

Maintaining perfect stacked-diff history for `bisect` represents "Process Debt" — especially without specialized wrappers like Graphite or Sapling.

**Primary debugging tools:**
- **Unit and evaluation tests** (catch regressions at the logic level),
- **Structured logging** (with trace IDs),
- **Metrics and alerting** (e.g., latency, error rates),
- **Atomic revert** (if a change breaks, revert the **entire squashed commit** — not part of it).

If a change is **too large to debug or revert safely**, it **violates atomicity** and should have been split into separate PRs **before submission**.

+++

### (Not Recommended) Stacked Diff Workflow

+++

:::{caution}
Stacked Diffs are **not recommended** for this ecosystem. They were evaluated (WRC 0.68) and rejected due to high rebase toil and tooling requirements (Graphite/Sapling). Since `git bisect` is formally deprioritized, the primary benefit of stacked diffs — preserving line-level bisect granularity — no longer justifies the overhead. See {term}`ADR-26024` for the full alternatives analysis.
:::

If a large feature needs decomposition, split it into **separate PRs** (each squash-merged independently) rather than stacking dependent diffs within a single branch.

+++

### Enforcement

+++

| Guardrail | Implementation |
|:-----------------------------------|:-----------------------------------|
| **Reviewer Gate**  | Reviewers **reject PRs** that are not logically atomic (e.g., mix refactor + feature) o... [truncated]
