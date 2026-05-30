
title: AI Engineering Handbook
author: rudakow.wadim@gmail.com
date: 2026-04-13
options:
  version: "3.0.0"
  birth: 2025-10-19
  token_size: 3371
---
# AI Engineering Handbook


This repository is a **Documentation-as-Code hub** for building production-grade AI systems. In the era of AI-backed development, AI systems — RAG pipelines, coding agents, AI assistants — consume documentation as their primary input. Poor documentation produces poor AI outputs. This repository treats documentation with the same rigor as production source code: versioned, tested, lifecycle-managed, and machine-readable.

Content is **generated through a hybrid LLM methodology**, **cross-validated by multiple models**, and **reviewed by a human** before promotion. Architectural decisions are governed by ADRs with machine-readable YAML frontmatter, enabling AI agents to filter and retrieve decisions by status, date, and scope.

> **Mission**: To build reliable, machine-readable documentation infrastructure that AI systems can trust as authoritative input — while enabling MLOps engineers and AI architects to construct audit-ready AI systems using a hybrid LLM+SLM methodology.


## What's new?

v3.0.0 — "The Agents Emerge"
* **Agent Research Program**: Systematic analysis of 7 open-source coding agents (Qwen Code, Claude Code, OpenCode, OpenClaude, Aider, KiloCode, Superpowers). [Context Management Overview](/ai_agents/architecture/context_management/context_management_in_ai_coding_agents.md) and [Comparison](/ai_agents/architecture/context_management/context_management_agent_comparison.md) cover how each agent handles conversation history, compaction, and state — with side-by-side tables and a decision guide. Architecture articles: [How Subagents Work](/ai_agents/architecture/orchestration/how_subagents_actually_work_myth_of_process_spawning.md), [Stability Against LLM Drift](/ai_agents/architecture/skills/stability_in_a_probabilistic_substrate_how_agents_fight_llm_drift.md), and [Skills Discovery](/ai_agents/architecture/skills/skill_discovery_across_ai_coding_platforms.md).
* **Repository Reorganization**: `ai_system/` → `ai_system_layers/` (clarifying that layers are engine components) and `ai_agents/` moves to the repo root (agents are the product, not another layer). `tools/docs/ai_agents/` → `ai_agents/guides/`. New `research/` directory for external product source code clones.
* **Code as Primary Documentation**: {term}`ADR-26045` (accepted) makes contract docstrings mandatory across the ecosystem, supersedes the triad convention ({term}`ADR-26011`). One new proposed ADR: {term}`ADR-26046` on external research directory governance.

v2.8.0 — "The Prompt Physics"
* **Prompt Engineering Research**: A three-article series with real measurements and reproducible code — [Format as Architecture](ai_system_layers/3_prompts/format_as_architecture_signal_noise_in_prompt_delivery.ipynb), [Token Economics of Prompt Delivery](ai_system_layers/3_prompts/token_economics_of_prompt_delivery.ipynb), and an [Appendix on YAML Serializer Variance](ai_system_layers/3_prompts/appendix_yaml_serializer_variance.ipynb). Central finding: token cost is `f(format, serializer, tokenizer)` — PyYAML vs. yq on the same JSON source can differ by 100+ tokens on a 150-line prompt and flip the YAML vs. JSON ranking. Backed by three analyses ([A-26016](architecture/evidence/analyses/A-26016_causal_masking_attention_mechanics_for_prompt_engineering.md), [A-26017](architecture/evidence/analyses/A-26017_yaml_serializer_variance_token_economics.md), [A-26018](architecture/evidence/analyses/A-26018_xml_tags_scope_isolation_prompt_architecture.md)).
* **Two-Stage Consultant Workflow**: [ai_brainstorming_colleague.json](ai_system_layers/3_prompts/consultants/ai_brainstorming_colleague.json) (v0.2.0) handles exploration; it hands off explicitly to the strict reviewers ([ai_systems_consultant.json](ai_system_layers/3_prompts/consultants/ai_systems_consultant.json), [devops_consultant.json](ai_system_layers/3_prompts/consultants/devops_consultant.json)) when formal validation is needed. The handoff is enforced by the prompt itself.
* **Governance Enforcement**: All governance configs migrated from YAML to JSON (`.vadocs/`). [check_frontmatter.py](tools/scripts/check_frontmatter.py) (work in progress) enforces {term}`ADR-26042` at commit time. Two new proposed ADRs: {term}`ADR-26044` and {term}`ADR-26054`.

v2.7.0 — "The Context Engineering Pivot"
* **From Agentic OS to Context Engineering**: v2.6.0 explored an ambitious vision — agents as operating systems. That research produced valuable insights, but the key finding was simpler: what matters is not how many agents you have, but what each agent sees. {term}`ADR-26038` adopts context engineering as the core principle — one agent, skills loaded on demand, context window as the primary constraint. The multi-agent vs single-agent boundary will be analyzed more thoroughly in future releases.
* **Infrastructure Blueprint**: 7 new ADRs define the technical stack for the ecosystem's next phase — database, deployment, data access, metadata format, and governance packaging. The goal: everything needed to deploy a working application from a single `podman play kube` command plus an API key.
* **First Consolidation**: 4 ADRs promoted to accepted standards, 3 rejected with their insights absorbed. The ecosystem moves from pure exploration to selective commitment.


## Live Documentation Site

The rendered knowledge base is published on GitHub Pages ({term}`ADR-26022`). GitHub is the **source of truth**; the site is the **rendered view** for reading.


## Documentation as Source Code for AI

Traditional documentation is written for humans to read after the fact. In AI-backed development, documentation is the **primary input** that AI systems consume to produce outputs. This makes documentation quality a first-class engineering concern: stale docs produce hallucinations, unstructured metadata makes retrieval blind, missing lifecycle allows noise to accumulate.

This repository implements the Documentation-as-Code paradigm:

- **Docs = source code**: versioned, diffed, tested via Jupytext pairing ({term}`ADR-26014`)
- **Metadata = API contract**: MyST-native frontmatter makes every document machine-queryable ({term}`ADR-26023`, {term}`ADR-26016`)
- **Lifecycle = garbage collection**: superseded content is deleted to prevent RAG noise; ADRs are preserved as negative knowledge ({term}`ADR-26021`)
- **Structure = architecture**: repository layout is deliberate design, not accumulation; restructuring is governed by ADRs like refactoring is governed by tests ({term}`ADR-26020`, {term}`ADR-26026`)
- **ADRs = development backbone**: every major decision is an ADR; proposed ADRs serve as living RFCs ({term}`ADR-26025`)
- **CI/CD = deployment**: automated validation, sync-guard, broken-link checks ({term}`ADR-26015`)

This stands in direct opposition to pre-AI knowledge bases — collections of articles with no enforced structure, no traceability, and no automated verification.

See the full rationale in [architecture/manifesto.md](/architecture/manifesto.md).

> In this paradigm: prompts = source code, articles = build artifacts, reviews = QA gates.


## Architectural Governance

ADRs are the **main context for development** in this repository. Every structural, methodological, or tooling decision is recorded as an ADR before implementation.

- **36 active ADRs** govern the repo — see the full list in [architecture/adr_index.md](/architecture/adr_index.md)
- **RFC→ADR workflow**: proposed ADRs serve as living RFCs; accepted ADRs are authoritative ({term}`ADR-26025`)
- **Machine-readable metadata**: YAML frontmatter with status, date, tags enables AI filtering ({term}`ADR-26016`, {term}`ADR-26017`)
- **Automated validation**: `check_adr.py` enforces format, required sections, term references, and index partitioning ({term}`ADR-26017`)
- **Asymmetric lifecycle**: articles are deleted when superseded; ADRs are preserved as negative knowledge — decision history is never lost ({term}`ADR-26021`)


## Hub-and-Spoke Ecosystem

This repository is the **standards hub** — it holds conventions, specifications, and ecosystem ADRs ({term}`ADR-26020`). Implementation lives in independent spokes:

- **Extracted packages** (e.g., [vadocs](https://github.com/lefthand67/vadocs)) are independent spokes with their own implementation decisions
- **Research** is extracted to a dedicated monorepo ({term}`ADR-26026`) — only distilled insights are retained in the hub
- The hub holds the **"why"**; spokes hold the **"how"**


## Methodology

Content generation follows a tool-agnostic, cognitive-model approach:

- **Model taxonomy**: reasoning-class models (synthesis, requirements) vs. agentic-class models (execution, structure) — selected by capability, not by name ({term}`ADR-26027`)
- **Phase 0: Intent Synthesis**: human-led discovery with a reasoning-class model before any automated execution ({term}`ADR-26028`)
- **Consultant prompts** in `ai_system_layers/3_prompts/consultants/` encode methodology as JIT-transformable JSON ({term}`ADR-26013`)

```mermaid
graph LR
A[Phase 0: Intent synthesis] --> B[Draft generation]
B --> C[Cross-validation by multiple models]
C --> D[Human review]
D --> E[CI/CD gates]
E --> F[Promotion to published directories]

style A fill:#fff,stroke:#333,stroke-width:2px
style B fill:#fff,stroke:#333,stroke-width:2px
style C fill:#fff,stroke:#333,stroke-width:2px
style D fill:#fff,stroke:#333,stroke-width:2px
style E fill:#fff,stroke:#333,stroke-width:2px
style F fill:#fff,stroke:#333,stroke-width:2px
```


## Coverage

Content is organized around five layers of AI systems. Security is a **cross-cutting concern** woven into all layers, not a separate layer.

1. **Execution & Optimization**: CPU/GPU hybrid pipelines, VRAM/RAM management, NVIDIA tuning
2. **Model Development**: SLM selection, tokenization, embeddings
3. **Prompt Engineering**: Modular design, XML schemas, template lifecycle, consultant prompts
4. **Orchestration**: RAG, workflow chaining, agent specialization, structured output
5. **Context Management**: Vector stores, hybrid retrieval, indexing strategies

Read more in [A Multi-Layered AI System Architecture](/0_intro/a_multi_layered_ai_system_architecture.ipynb).


## Repository Structure

```text
.
├── 0_intro/                # Introductory material, high-level overviews
├── ai_agents/              # Real-world agent framework analysis (assembled product)
│   ├── context_management/ # Context window strategy analysis
│   ├── session_history_management/ # Session history analysis
│   ├── skills/             # Skill system analysis
│   └── tooling/            # Tool architecture analysis
├── research/               # External source code repos for comparative study
│   ├── ai_coding_agents/   # Nested git repos (external agent source code)
│   └── ai_infrastructure/  # Nested git repos (non-agent AI projects)
├── ai_system_layers/       # Core content organized by layer (engine parts catalog)
│   ├── 1_execution/        # CPU/GPU optimization, CUDA, VRAM management
│   ├── 2_model/            # Model selection, tokenization, embeddings
│   ├── 3_prompts/          # Prompt-as-Infrastructure: formatting, versioning, consultants
│   ├── 4_orchestration/    # Workflow, agent specialization, structured output
│   └── 5_context/          # RAG, knowledge bases, hybrid retrieval
├── architecture/           # Architectural governance
│   ├── adr/                # Formal ADR documents (YAML frontmatter, machine-readable)
│   ├── evidence/           # Architecture Knowledge Base (analyses, sources, retrospectives)
│   ├── packages/           # Spoke package documentation and PoCs
│   └── post-mortems/       # Retrospectives on failures and lessons learned
├── misc/                   # Non-core work
│   ├── in_progress/        # Drafts, experiments, work-in-progress
│   ├── plan/               # Implementation plans (saved between context switches)
│   └── pr/                 # Telegram channel posts, review checklists
├── mlops/                  # MLOps tooling and pipelines
│   ├── ci_cd/              # GitHub Actions, quality-gate scripts
│   └── security/           # Secret scanning, compliance checks
├── security/               # Centralized security policy hub (placeholder)
└── tools/                  # Supporting utilities
    ├── configs/            # Tool configuration files
    ├── docs/               # Documentation generation helpers, style guides
    ├── scripts/            # Automation: link checking, ADR validation, Jupytext sync
    └── tests/              # Test suites for scripts
```


## Toolchain & CI/CD

The repository uses automated validation to enforce documentation quality:

- **Pre-commit hooks** in OOP Python style ({term}`ADR-26001`) within the pre-commit framework ({term}`ADR-26002`)
- **Jupytext pairing** with sync-guard: `.ipynb` and `.md` files stay synchronized; CI blocks unsynced changes ({term}`ADR-26014`, {term}`ADR-26015`)
- **Tool configuration** centralized in `pyproject.toml [tool.X]` sections ({term}`ADR-26029`)
- **CI/CD pipelines**: `quality.yml` (broken links, jupytext sync, script tests) + `deploy.yml` (GitHub Pages deployment)
- **Validation scripts**: `check_adr.py`, `check_evidence.py`, `check_frontmatter.py`, `check_broken_links.py`, `validate_commit_msg.py`, `check_link_format.py`
- **External repo management**: `manage_external_repos.py` — clone, update, and list external research repositories in `research/`


## Authorship & Contact

My name is Vadim Rudakov, I am a **Systems Engineer and AI Methodology Architect** from Sverdlovsk oblast, Russia. This repository solves a specific problem: the fragility of AI prototypes and the risk of institutional "tribal knowledge."

- **The Architect**: I design the knowledge-generation systems, validation protocols, and the Documentation-as-Code methodology.
- **Cognitive Roles**: Reasoning-class models handle architecture and planning; agentic-class models handle execution and structure. The tools change — the cognitive model stays.
- **Institutional Resilience**: Systems are documented so thoroughly that they survive staff turnover. The methodology is encoded in the system itself.

The repository is licensed under **GPLv3** for its core assets and **CC-BY-SA 4.0** for the article content.


## Contact Information

Vadim Rudakov, rudakow.wadim@gmail.com
