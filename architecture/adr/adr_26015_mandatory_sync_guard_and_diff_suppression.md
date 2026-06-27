---
id: 26015
title: Mandatory Sync-Guard & Diff Suppression
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Implementation of GitOps integrity via Pre-commit synchronization and
  Git attribute diff suppression..
tags:
- ci
date: 2026-02-01
options:
  type: adr
  birth: '2026-02-01'
  version: 1.0.0
  token_size: 821
  status: accepted
  superseded_by: null
---
# ADR-26015: Mandatory Sync-Guard & Diff Suppression

## Title

Implementation of GitOps integrity via Pre-commit synchronization and Git attribute diff suppression.

## Status

Accepted

## Date

2026-01-30

## Context

The adoption of paired `.md`/`.ipynb` artifacts introduces a redundancy risk where the two files may diverge if edited in isolation—specifically when using AI assistants like Aider on the Markdown source. Without a formalized enforcement mechanism, the "Single Source of Truth" (SSoT) is compromised, leading to merge conflicts and non-deterministic execution states. Additionally, standardizing on Markdown for code reviews requires the suppression of high-entropy `.ipynb` JSON noise in the version control history.

## Decision

We will enforce repository integrity through a three-tier synchronization and suppression strategy:

1. **Pre-commit Sync Guard** (ADR 26002):
* Integrate a mandatory `jupytext --sync` hook into the `.pre-commit-config.yaml`.
* This hook must execute `uv run jupytext --sync` on all staged `.md` and `.ipynb` files.
* The commit will be blocked if synchronization results in file modifications.


2. **Diff Suppression via `.gitattributes`**:
* Configure `*.ipynb -diff` and `*.ipynb linguist-generated=true` to de-emphasize the notebook JSON.
* Configure `*.md diff=markdown` to treat the Markdown pair as the primary human-readable source for reviews.


3. **Automated AI Linting**:
* Configure the AI assistant (Aider) via `.aider.conf.yml` to run `uv run jupytext --sync` as a `lint-cmd` after every edit.
* Disable Aider's `auto-commits` to ensure atomic staging of both paired files.



## Consequences

### Positive

* **Version Integrity**: Guarantees that the human-readable logic (`.md`) and execution state (`.ipynb`) are bit-identical at every commit.
* **Review Efficiency**: Reviewers focus solely on semantic changes in Markdown while `.ipynb` files are treated as binary artifacts.
* **AI Compatibility**: Ensures AI-generated edits to Markdown are propagated to the notebook without manual intervention.

### Negative

* **Commit Latency**: Adds a minor execution penalty during the `pre-commit` phase for synchronization.
* **Staging Complexity**: Requires users to stage both files in the pair or rely on the pre-commit hook to re-stage them.

## Alternatives

* **Manual Synchronization**: Rejected. High probability of human error leading to "Artifact Drift" and broken CI pipelines.
* **Ignore `.ipynb` in Git**: Rejected. Results in loss of execution outputs and rich rendering in Jupyter environments, violating the need for verifiable documentation.

## References

* [ADR 26002: Adoption of the Pre-commit Framework](/architecture/adr/adr_26002_adoption_of_pre_commit_framework.md)
* [Semantic Notebook Versioning: AI-Ready Jupyter Docs Workflow](/tools/docs/jupyter_and_markdown/semantic_notebook_versioning_ai_ready_jupyter_docs.ipynb)
* ISO 29148: Consistency and Verifiability

## Participants

1. Vadim Rudakov
2. Gemini (AI Thought Partner)
