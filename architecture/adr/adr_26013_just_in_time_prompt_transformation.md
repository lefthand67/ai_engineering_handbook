---
id: 26013
title: Just-in-Time Prompt Transformation
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Implementation of Just-in-Time (JIT) JSON-to-YAML conversion for LLM
  prompt loading..
tags:
- workflow
date: 2026-01-31
options:
  type: adr
  birth: '2026-01-31'
  version: 1.0.0
  token_size: 759
  status: accepted
  superseded_by: null
---
# ADR-26013: Just-in-Time Prompt Transformation

## Title

Implementation of Just-in-Time (JIT) JSON-to-YAML conversion for LLM prompt loading.

## Status

Accepted

## Date

2026-01-30

## Context

The current workflow utilizes JSON as the "Source of Truth" for prompt storage, but requires YAML for LLM inference (compatible with `ollama` and `qwen2.5-coder` / `ministral` stacks). The proposal to store these converted YAML files as ready-to-go artifacts in the Git repository introduces several risks:

1. **Single Source of Truth (SSoT) Violation:** Changes to JSON might not be reflected in YAML, leading to non-deterministic behavior [ISO 29148: Consistency].
2. **Git Noise:** Storing derivative artifacts doubles diff sizes and complicates peer reviews.
3. **Local Stack Constraints:** Maintaining redundant files increases disk overhead on restricted local systems.

## Decision

We will **not** store converted YAML prompts in the repository. Instead, the system will implement a JIT (Just-in-Time) transformation layer within the Python application logic.

* All prompts remain stored exclusively in JSON format.
* A `PromptManager` class will handle the conversion in-memory during the application's initialization or at runtime.
* The `.gitignore` will be updated to explicitly exclude any ephemeral `.yaml` prompt exports.

## Consequences

### Positive

* **Guaranteed Traceability:** A specific Git commit hash now maps to exactly one prompt state [SWEBOK: Quality-2.1].
* **Reduced Technical Debt:** Eliminates the need for "synchronization scripts" or manual conversion steps before commits.
* **Modular Design:** Separates the storage concern (JSON) from the presentation/inference concern (YAML).

### Negative

* **Runtime Overhead:** Adds a negligible computational cost (millisecond range) during the loading phase. **Mitigation**: Implement `functools.lru_cache` for frequently accessed prompts.
* **Initial Refactoring:** Requires a one-time update to the local Python stack to include a robust conversion utility. **Mitigation**: Use `pydantic` for schema validation during the JIT process.

## Alternatives

### Persistent Artifact Storage (Rejected)

Convert prompts to YAML for quick access when needed without conversion from JSON.

* **Reason:** High risk of "Artifact Drift" where the YAML used in production does not match the JSON in the repository. Violates SVA (Smallest Viable Architecture) principles by adding unnecessary orchestration layers. (WRC 0.47).

### YAML as Source of Truth (Rejected)

* **Reason:** JSON is more natively handled by the existing Python/SQL/Bash stack and provides stricter schema validation capabilities via standard libraries compared to YAML's more permissive syntax.

## References

* [ISO 29148: Traceability and Consistency]
* [SWEBOK: Software Configuration Management]

## Participants

1. Vadim Rudakov
2. Senior AI Systems Architect (Gemini)
