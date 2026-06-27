---
id: 26026
title: Dedicated Research Monorepo for Volatile Experimental Projects
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: 2026-02-15.
tags:
- governance
- workflow
date: 2026-02-15
options:
  type: adr
  birth: '2026-02-15'
  version: 1.0.0
  token_size: 1279
  status: accepted
  superseded_by: null
---
# ADR-26026: Dedicated Research Monorepo for Volatile Experimental Projects

## Date
2026-02-15

## Status
accepted

## Context

The repository contains volatile research subprojects under `misc/research/` (e.g., `ai_code_generation_engineer`, `slm_from_scratch`). These projects exhibit characteristics fundamentally incompatible with the stable architecture documentation system:

- **Dependency volatility**: Research projects require experimental libraries (e.g., bleeding-edge PyTorch variants, custom CUDA kernels) that conflict with the main repo's production-grade dependency constraints. While `uv` supports nested `.venv` directories, maintaining isolated environments within a single repo creates cognitive overhead and risks accidental dependency leakage during tooling operations.

- **Lifecycle mismatch**: The main repo follows SVA principles with stable, version-controlled architectural decisions. Research subprojects undergo rapid iteration cycles with frequent breaking changes, abandoned branches, and ephemeral experimental code—patterns that pollute the architectural knowledge base with transient artifacts.

- **Toolchain divergence**: Research projects often require specialized tooling (e.g., JupyterLab extensions, dataset versioning with DVC) irrelevant to architectural documentation workflows. Co-locating these toolchains forces all contributors to install research-specific dependencies even when working exclusively on architecture docs.

- **RAG pipeline contamination**: Local RAG systems indexing the entire repository ingest volatile research artifacts as "architectural knowledge," reducing signal-to-noise ratio when querying for production constraints. Per ADR-26025, RAG consumers must prioritize `status: accepted` ADRs as authoritative—research code has no such status semantics.

The current co-location pattern violates SVA principle C2 (separation of concerns between stable architecture and experimental work) and creates maintenance friction during routine operations like dependency updates or security scans.

## Decision
Move all volatile research subprojects to a dedicated `research` monorepo with the following characteristics:

1. **Single research repository**: All experimental projects reside under one repository (`github.com/main/research`) rather than fragmented per-project repos.

2. **Per-project dependency isolation**: Each research subproject maintains its own `pyproject.toml` and `.venv` directory. Projects are *not* declared as `uv` workspace members to prevent transitive dependency resolution—each project is treated as an independent environment:
   ```bash
    # Initialize isolated project
    cd research/slm-from-scratch
    uv init --name slm-from-scratch    # Creates pyproject.toml with project metadata

    # Add dependencies (uv auto-creates .venv if missing)
    uv add torch transformers datasets  # Installs into ./slm-from-scratch/.venv

    # Verify isolation
    uv pip list --env  # Shows only this project's deps in its local .venv
    ```

3. **Knowledge distillation pattern**: The main architecture repo retains *only* distilled insights in different sections of the documentation with cross-references to specific research projects. Raw experimental code never resides in the architecture repo.

4. **Migration protocol**: 
   - Research code moved via `git filter-repo` to preserve commit history
   - Original directories replaced with `MOVED_TO_RESEARCH.md` stubs containing repo URLs and key findings

## Consequences

### Positive

- **Clean architectural boundary**: Main repo remains focused on production-grade decisions with stable dependencies. Research volatility cannot compromise architectural integrity.

- **Discoverability preserved**: Unified research repo enables cross-project discovery (e.g., insights from `slm-from-scratch` informing `ai-code-generation-engineer`) without fragmenting knowledge across 10+ micro-repos.

- **RAG signal enhancement**: Architecture-focused RAG pipelines exclude volatile research artifacts by default, improving precision when querying for binding constraints.

- **Reduced maintenance overhead**: Single research repo simplifies backup procedures, access control management, and tooling standardization versus managing dozens of micro-repos for abandoned experiments.

### Negative / Risks

- **Migration effort**: Initial relocation requires ~4 hours of engineering time to preserve history and update cross-references. **Mitigation:** Schedule during low-activity period; use automated `git filter-repo` scripts to minimize manual intervention.

- **Over-isolation**: Critical research breakthroughs might not propagate to architecture decisions. **Mitigation:** Monthly review cycle where research repo maintainers present distilled findings to architecture working group.

## Alternatives

1. Keep research subprojects in main repository with nested `.venv` directories. **Rejection Reason:** Nested environments create false sense of isolation; tooling operations at repo root still traverse entire directory tree unless explicitly excluded, violating principle of least surprise.

2. Create separate repository per research project (e.g., `slm-from-scratch`, `ai-code-generation-engineer` as independent repos). **Rejection Reason:** This may create "zombie repo" maintenance burden. A unified research monorepo reduces governance surface area while still enabling per-project isolation through directory-level boundaries. Micro-repos also fragment discovery—researchers cannot easily browse related experiments across repositories without manual navigation.

3. Hybrid approach: Maintain research code in main repo but exclude from RAG indexing via `.ragignore`. **Rejection Reason:** While this solves RAG contamination, it fails to address dependency pollution and lifecycle mismatch. Tooling operations (e.g., `uv pip list --all`) still traverse research directories, and contributors remain exposed to volatile code during routine navigation. Exclusion mechanisms create hidden state that new contributors cannot discover without reading obscure configuration files, increasing onboarding friction.

## References

## Participants

1. Vadim Rudakov
2. Qwen3-Max

