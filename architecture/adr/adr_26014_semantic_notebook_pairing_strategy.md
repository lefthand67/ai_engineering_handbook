
---
title: Semantic Notebook Pairing Strategy
date: 2026-01-31
tags:
- documentation
options:
  token_size: 787
  id: 26014
  status: accepted
  superseded_by: null
  type: adr
  version: 1.0.0
  birth: '2026-01-31'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Adoption of Jupytext Paired `.md`/`.ipynb` Artifacts for AI-Ready Version
  Control..
---
# ADR-26014: Semantic Notebook Pairing Strategy

## Title

Adoption of Jupytext Paired `.md`/`.ipynb` Artifacts for AI-Ready Version Control.

## Status

Accepted

## Date

2026-01-30

## Context

Standard `.ipynb` files are massive JSON objects containing metadata, execution counts, and binary-encoded images that make code reviews difficult. These files are "toxic" for Git diffs and consume excessive tokens when processed by Small Language Models (SLM) or LLM assistants like Aider. We require a methodology that satisfies industrial-grade MLOps criteria while operating under the constraints of CPU/RAM-limited local stacks. The goal is to adhere to the Simplest Viable Architecture (SVA) by providing high-fidelity Markdown inputs for AI assistants while preserving the execution state in notebooks.

## Decision

We will implement semantic notebook versioning by pairing every `.ipynb` file with a **MyST Markdown** (`.md`) equivalent using **Jupytext**.

* **Source of Truth**: The `.md` file is the primary source for logic, code reviews, and LLM ingestion.
* **Execution Artifact**: The `.ipynb` file is retained solely as an execution/output artifact.
* **Automation**: Configuration must be defined in the root `pyproject.toml` to automate pairing defaulting.
* **Environment**: Jupytext MUST be installed in the central JupyterLab environment to ensure server-side discoverability.

## Consequences

### Positive

* **Clean Diffs**: Provides a line-by-line, human-readable text diff in Git.
* **AI Efficiency**: Reduces token waste by allowing LLMs to read pure Markdown/Python logic instead of 5,000+ lines of JSON metadata.
* **No Vendor Lock-in**: Uses open formats (MyST Markdown and standard Jupyter).
* **Traceability**: Aligns with ISO 29148 requirements for unambiguous and verifiable specification artifacts.

### Negative

* **State Redundancy**: Storing two files for one notebook. **Mitigation**: Use `.gitattributes` to suppress `.ipynb` files in diffs and PR UIs.
* **Synchronization Overhead**: Requires a "Sync Guard" via pre-commit hooks to prevent file desynchronization. **Mitigation**: Automated `jupytext --sync` commands in development and CI pipelines.

## Alternatives

### Standard `.ipynb` Versioning

* **Reason for Rejection**: Large JSON diffs make peer review impossible and exhaust local SLM context windows.

### Plain Python (`.py`) Percent Format

* **Reason for Rejection**: While clean, it lacks the rich MyST Markdown support required for high-fidelity documentation and industrial specification standards.

## References

* [Semantic Notebook Versioning: AI-Ready Jupyter Docs Workflow](/tools/docs/jupyter_and_markdown/semantic_notebook_versioning_ai_ready_jupyter_docs.ipynb)
* ISO/IEC/IEEE 29148 Traceability Standards.
* Jupytext Documentation: Paired Notebooks.

## Participants

1. Vadim Rudakov
2. Senior AI Systems Architect (Gemini)
