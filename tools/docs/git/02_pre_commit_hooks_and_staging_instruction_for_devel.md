---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.1
---

---
title: "Pre-commit Hooks and Staging: Instruction for Developers"
authors:
  - name: Vadim Rudakov
    email: rudakow.wadim@gmail.com
date: "2026-05-03"
description: "Instructions for developers on how to correctly use pre-commit hooks and git staging to preserve user intent."
tags:
  - git
  - ci
  - development
  - workflow
options:
  type: guide
  version: "1.3.0"
  birth: "2026-01-04"
  token_size: 1515
---
# Pre-commit Hooks and Staging: Instruction for Developers

+++

## **1. Philosophy**

+++

**Never stage files in a `pre-commit` hook that the user didn’t already explicitly `git add`.**

Git’s staging area reflects the developer’s intentional choice about what belongs in the next commit. Your `pre-commit` hook must **respect that intent**—not override it.

+++

### ✅ What you *can* do

+++

(e.g., auto-formatting a file the user added.)
- Apply **safe, deterministic, non-semantic changes**: formatting, lint fixes, license headers.
- Use established tooling like [`pre-commit`](https://pre-commit.com/)—it handles partial staging correctly by stashing unstaged changes, running hooks, then restoring them.

+++

### ❌ What you *must not* do

+++

- **Stage new files** (e.g., build artifacts, config files, logs) that weren’t already in the index.
- Silently add files the user never touched or reviewed.
- Mix unstaged and staged changes by formatting a file only partially added (unless you handle it like `pre-commit` does).

+++

### ⚠️ Why it matters

+++

- Auto-staging unknown files risks **committing secrets, temp files, or unintended changes**.
- It breaks trust: developers expect `git commit` to include *only* what they staged.
- Debugging becomes harder when commits contain “mystery” changes.

+++

### 🔧 Better alternatives

+++

- If a file *must* be up to date (e.g., `package-lock.json`), **fail the commit** and ask the user to run a script or add it manually.
- Enforce correctness in **CI**, not by silently altering the commit contents.
- Use wrapper scripts (e.g., `./commit.sh`) for workflows that require pre-staging—keep automation **explicit**.

---

> **Golden Rule**:
> A `pre-commit` hook may *refine* what’s staged—but never *expand* it.
> Preserve user agency. Respect the index.

+++

## **2. Installation and Configuration**

+++

We use a Python package `pre-commit` for handling local hooks (see ["ADR 26002: Adoption of the Pre-commit Framework"](/architecture/adr/adr_26002_adoption_of_pre_commit_framework.md)).

The `.pre-commit-config.yaml` file is already configured in the repo, so the developer needs to install pre-commit and install the config to `.git/hooks` repo:

```bash
$ uv add pre-commit
$ uv run pre-commit install
$ uv run pre-commit install --hook-type commit-msg
$ uv run pre-commit install --hook-type post-commit
```

```{code-cell}
ls ../../../.git/hooks | grep -E '^(pre-commit|commit-msg|post-commit)$'
```

:::{warning} **Hook stages require separate installation**
`pre-commit install` only installs the default `pre-commit` stage hook. Each additional stage (`commit-msg`, `post-commit`, `pre-push`, `prepare-commit-msg`, etc.) requires its own `--hook-type` install call. If you add hooks at new stages in `.pre-commit-config.yaml`, the corresponding `--hook-type` install must happen in your setup — otherwise the hooks exist in config but never fire.
:::

Run the [repo configuration script](/tools/scripts/configure_repo.py), it will automatically handle all hook types.

+++

## **3. Testing**

+++

```bash
$ uv run pre-commit [<hook_id>] [--all-files]
```

+++

## **4. Commit Message Validation**

+++

Commit message validation runs at the **`commit-msg`** stage — not `pre-commit` (which fires before the message is written) and not `post-commit` (which cannot abort the commit). The `commit-msg` hook receives the draft message and can reject it with a non-zero exit code, aborting the commit before it enters history. This makes it the only stage where message structure can be enforced as a blocking gate. See [A-26004: Hook Stage Assignment Rationale](/architecture/evidence/analyses/A-26004_hook_stage_assignment_rationale.md) for the full stage analysis.

+++

The `validate_commit_msg.py` script runs as a `commit-msg` stage pre-commit hook, enforcing both the [Conventional Commits](https://www.conventionalcommits.org/) subject format (Tier 2) and the [Structured Commit Body](/tools/docs/git/01_production_git_workflow_standards.ipynb) convention.

**What it validates:**

| Check | Severity | Description |
|:------|:---------|:------------|
| Subject format | **Hard fail** | Must match `<type>[(<scope>)]: <description>` with a valid type prefix (`feat:`, `fix:`, `docs:`, etc.) |
| Body bullets | **Hard fail** | Body must contain at least one line starting with `- ` (a changelog bullet) |
| ArchTag presence | **Hard fail** | For `refactor:`, `perf:`, or `BREAKING CHANGE` commits, `ArchTag:TAG-NAME` must be present (Tier 3) |

**With Squash-and-Merge**, intermediate commit messages during development are less critical — the squash commit message (derived from the PR description) is the one that must pass validation. However, the hook runs on all local commits to build good habits and catch formatting issues early.

+++

## **5. Changelog Preview (Post-Commit)**

+++

After each commit, the `changelog-preview` hook runs `generate_changelog.py --verbose` on the just-created commit. This shows the developer:

- The CHANGELOG entry their commit will produce
- Any bullets or subjects that will be filtered by exclusion patterns (e.g., `CLAUDE.md`, `misc/`)

This is **informational only** — it never blocks the commit. If the output looks incorrect, use `git commit --amend` to fix the commit message.

:::{seealso}
> - {term}`ADR-26003`: Adoption of gitlint for Tiered Workflow Enforcement
> - {term}`ADR-26024`: Structured Commit Bodies for Automated CHANGELOG Generation
> - [Production Git Workflow Standards — Structured Commit Body Format](/tools/docs/git/01_production_git_workflow_standards.ipynb)
:::
