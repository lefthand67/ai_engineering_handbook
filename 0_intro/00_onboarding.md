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
title: Onboarding
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: 2026-02-08
description: Onboarding guide for the AI Engineering Book repository, covering setup
  and key materials.
tags:
- documentation
- development
options:
  type: guide
  version: 0.4.1
  birth: 2026-01-03
  token_size: 904
---

+++

General fast way to understand the architecture and workflows is to follow this docs workflow:

```
ADR -> tools -> workflow directories
```

+++

## **Step 1. Setup Your Environment**

+++

Run this scripts in your GNU/Linux terminal:

```bash
bash ./tools/scripts/configure_repo.sh
```

(in development) Configure JupyterLab for working with the files in this repo.

+++

## **Step 2. Read Most Important Materials**

+++

### Arthicture

+++

1. ["A Multi-Layered AI System Architecture"](/0_intro/a_multi_layered_ai_system_architecture.ipynb) to understand the repo structure.
2. Series on how we work with Git in `/tools/docs/git/`.
3. ADRs in `/architecture/adr` to understand our choices and our stack.

+++

### Working with the Repository

+++

1. [Setup Jupytext and git hooks](/tools/docs/jupyter_and_markdown/semantic_notebook_versioning_ai_ready_jupyter_docs.ipynb)
1. ["Production Git Workflow Standards"](/tools/docs/git/01_production_git_workflow_standards.ipynb)

+++

### Document Metadata Conventions

+++

Every content article must include a **YAML frontmatter** block with MyST-native field names (`title`, `author`/`authors`, `date`) so that ownership and freshness are rendered directly on the static site. Custom fields (`version`, `birth`) go under `options.*` for RAG/tooling use.

1. ["YAML Frontmatter for AI-Enabled Engineering"](/ai_system_layers/5_context/yaml_frontmatter_for_ai_enabled_engineering.ipynb) — the frontmatter schema and why it matters for RAG
1. {term}`ADR-26023` — the MyST-aligned frontmatter standard

+++

### Your AI Tools

+++

1. ["Multi-Phase AI Pipeline"](/ai_system_layers/4_orchestration/workflows/multi_phase_ai_pipeline.ipynb) - the Research-Apply pipeline for AI-assisted engineering.
1. ["General Purpose (Abstract Synthesis) vs Agentic (Instruction Adherence) Models"](/ai_system_layers/2_model/selection/general_purpose_vs_agentic_models.ipynb) - what models to use for different types of tasks.
1. [Terminal AI Agents Workflow](/ai_agents/guides/terminal_ai_agents_workflow.ipynb) (to be created — hybrid strategy and Ollama setup)

+++

## **Keep Your Work Clean**

+++

This repository contains the very different types of files - docs, configs, code. Before commit and push to the repository all you have done must be tested and validated for not breaking what is already built, like cross-links, scripts for internal use, etc.

The most of validation is done for you by automatic checks (or will be done for you as soon as possible) via [pre-commit hooks](/tools/docs/git/02_pre_commit_hooks_and_staging_instruction_for_devel.ipynb) and GitHub actions. But some validation should be done by you manually - it concerns publishing new `.ipynb` docs in the first hand.

Before commiting, run the MyST server locally from your terminal 

```bash
uv run myst start
```

and:
- analyze the stdout messages for any errors,
- take a look at your new articles or modified files by opening `localhost:3000` in your web browser.

Fix what you can fix or ask for help from the peers before Pull Request.
