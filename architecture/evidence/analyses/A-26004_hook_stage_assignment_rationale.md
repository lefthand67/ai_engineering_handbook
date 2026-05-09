
---
title: Hook Stage Assignment Rationale
date: 2026-03-07
tags:
- git
- governance
options:
  token_size: 926
  id: A-26004
  status: active
  sources:
  - S-26003
  produces: []
  type: analysis
  version: 1.0.0
  birth: '2026-03-07'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: The project uses three Git hook stages (`pre-commit`, `commit-msg`, `post-commit`)
  with different hooks assigned to each.
---
# A-26004: Hook Stage Assignment Rationale

## Problem Statement

The project uses three Git hook stages (`pre-commit`, `commit-msg`, `post-commit`) with different hooks assigned to each. The rationale for **why** each hook runs at its particular stage has never been explicitly documented. Source S-26003 (a Gemini 3 Flash dialogue) raises the question: is `post-commit` ever appropriate for validation, or should all validation move to blocking stages?

This analysis codifies the stage assignment rationale and validates that the current hook architecture is sound.

## Key Insights

### The Three-Stage Model

Git hooks form a pipeline with fundamentally different failure semantics:

| Stage | Timing | On failure | Appropriate for |
|-------|--------|------------|-----------------|
| `pre-commit` | Before commit message editor opens | Aborts — no commit created | Content validation (links, sync, secrets) |
| `commit-msg` | After message written, before commit finalized | Aborts — no commit created | Message format validation |
| `post-commit` | After commit hash exists in history | Cannot abort — commit already exists | Notifications, previews, informational output |

The critical distinction: `pre-commit` and `commit-msg` are **blocking** (exit non-zero = commit aborted), while `post-commit` is **non-blocking** (exit non-zero = warning only, commit persists).

### Current Hook Assignments

| Hook ID | Stage | Blocking? | Rationale |
|---------|-------|-----------|-----------|
| `check-broken-links` | `pre-commit` | Yes | Content must be valid before message is written |
| `check-link-format` | `pre-commit` | Yes | Link syntax is a content concern |
| `jupytext-sync` | `pre-commit` | Yes | Notebook pairs must be synchronized before commit |
| `jupytext-verify` | `pre-commit` | Yes | Verifies sync succeeded |
| `detect-api-keys` | `pre-commit` | Yes | Security gate — must block before secrets enter history |
| `validate-json` | `pre-commit` | Yes | Structural validity of data files |
| `test-scripts` | `pre-commit` | Yes | Scripts must pass their tests |
| `validate-commit-msg` | `commit-msg` | Yes | Message format is a message-stage concern |
| `changelog-preview` | `post-commit` | No | Informational — shows what CHANGELOG entry the commit will produce |

### Validation of Current Architecture

S-26003 warns against using `post-commit` for **validation** because:
1. Failed validation cannot undo the commit
2. Attempted fixes (e.g., `--amend`) create new hashes and potential loops
3. The developer sees errors after the damage is done

The current architecture correctly follows this principle:
- All **validation** hooks (`check-broken-links`, `validate-commit-msg`, etc.) run at blocking stages (`pre-commit` or `commit-msg`)
- The only `post-commit` hook (`changelog-preview`) is **purely informational** — it shows a preview but never fails or attempts corrections

**Conclusion:** No architecture change is needed. The stage assignments are sound.

## References

- `S-26003: Gemini 3 Flash — Post-Commit Hook Stage Advice` — source dialogue on hook stage risks
- [Pre-Commit Hooks and Staging: Instruction for Developers](/tools/docs/git/02_pre_commit_hooks_and_staging_instruction_for_devel.ipynb) — authoritative hook documentation
- [ADR-26024: Structured Commit Bodies for Automated CHANGELOG Generation](/architecture/adr/adr_26024_structured_commit_bodies_for_automated_changelog.md) — commit convention that `validate-commit-msg` enforces
