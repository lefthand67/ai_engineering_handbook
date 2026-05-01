# Release Notes

## release v3.0.0 "The Agents Emerge"

### Summary of Changes

v2.8.0 established prompt format as empirical science and operationalized the governance infrastructure. v3.0.0 extends the research program to the tools that built it — **the AI coding agents themselves become the objects of study.**

This release delivers a systematic comparative analysis of 7 open-source agent codebases (Qwen Code, Claude Code, OpenCode, OpenClaude, Aider, KiloCode, Superpowers) — their context management strategies, skill discovery mechanisms, and stability against LLM drift. The central finding challenges the repository's own structure: agents are not another layer in the stack, they are the *product* that assembles all layers. This drove a reorganization — `ai_system/` becomes `ai_system_layers/` (clarifying that layers are components), and a new `ai_agents/` directory appears at the repo root as the consumer of all layers.

Four strategic themes define v3.0.0:

1. **Context Engineering Across 7 Agents** — The first cross-agent empirical guide: [ai_agents/context_management/](/ai_agents/architecture/context_management/context_management_in_ai_coding_agents.md) covers how every major open-source coding agent handles conversation history, compaction, and state management. The central insight: every agent uses a fundamentally different strategy — sliding windows, reactive compaction, async background summarization, multi-tier systems — and understanding these differences is essential for choosing the right tool. The comparison tables and decision guide help practitioners navigate this fragmented landscape without trial-and-error.

2. **Agent Architecture Demystified** — Three articles answer questions every practitioner has: How do subagents actually work? (Spoiler: not OS fork/exec — three real patterns: separate API calls, prompt role orchestration, HTTP process management.) What keeps agents stable when LLM outputs drift? (Hard guarantees like tool denial and circuit breakers, not soft techniques like tag conventions.) Why does Qwen Code use TypeScript, not Python? (Async I/O dominance and shell command architecture.) These are not opinions — they are extracted from source code evidence.

3. **Code as Primary Documentation** — The ecosystem adopts a principle that follows directly from context engineering: **every source file must open with a contract docstring** in its language's native format. When agents are your primary code consumers, every token of documentation competes with code for their attention budget. Code with outdated docstrings fails at import time. Prose docs that contradict code pass CI silently. The contract docstring — "what does a future agent need to read first to work safely in this file?" — is the only documentation layer that stays correct by construction.

4. **Skills Discovery and Prompt Brittleness** — Analysis of Superpowers v5.0.7's skill system across 5 agent platforms reveals three failure modes (context limits, instruction drift, hallucination/skipping) and empirically-derived countermeasures (HARD-GATE tags, rationalization tables, two-stage review). This is not theoretical — these are countermeasures that survived contact with real agent sessions.

### Architecture Decisions

*   **[ADR-26045: AI-Native Development — Code as Primary Documentation](architecture/adr/adr_26045_ai_native_development_code_as_primary_documentation.md) — Accepted**:
    Every source file in the ecosystem must open with a contract docstring answering: "What does a future agent need to read first to work safely in this file?" This is not a coding style preference — it is a consequence of context engineering. Agents are stateless, context-constrained, and read code as fluently as prose. Redundant documentation that paraphrases code is a context window tax. Code structure + contract docstrings + test suites provide CI-verified, co-located, refactoring-safe documentation.

*   **[ADR-26046: External Product Repos as Research Directories](architecture/adr/adr_26046_external_product_repos_as_research_directories.md) — Proposed**:
    Governs how external product source code is cloned and tracked for comparative research. Defines a centralized path registry with relocation safety — when a research directory moves, the registry and all consumer files update atomically. This prevents the silent breakage that occurs when external repos change paths.

### Accepted ADRs (Promoted in This Release)

| ADR | Title | Theme |
| :--- | :--- | :--- |
| [ADR-26045](architecture/adr/adr_26045_ai_native_development_code_as_primary_documentation.md) | AI-Native Development — Code as Primary Documentation | Development |

### Open RFCs (Proposed ADRs)

New proposed ADRs introduced in this release:

| ADR | Title | Theme |
| :--- | :--- | :--- |
| [ADR-26046](architecture/adr/adr_26046_external_product_repos_as_research_directories.md) | External Product Repos as Research Directories | Governance |

Carry-over proposed ADRs (open for review and comment):

| ADR | Title | Theme |
| :--- | :--- | :--- |
| [ADR-26042](architecture/adr/adr_26042_common_frontmatter_standard.md) | Common Frontmatter Standard | Governance |
| [ADR-26036](architecture/adr/adr_26036_config_file_location_and_naming_conventions.md) | Config File Location and Naming Conventions | Governance |
| [ADR-26043](architecture/adr/adr_26043_ecosystem_package_boundary.md) | Ecosystem Package Boundary | Governance |
| [ADR-26039](architecture/adr/adr_26039_pgvector_as_ecosystem_database_standard.md) | pgvector as Ecosystem Database Standard | Data Infrastructure |
| [ADR-26041](architecture/adr/adr_26041_client_side_logic_with_server_side_retrieval.md) | Client-Side Logic with Server-Side Retrieval | Data Infrastructure |
| [ADR-26032](architecture/adr/adr_26032_tiered_cognitive_memory_procedural_skills.md) | Tiered Cognitive Memory: Procedural Skills vs. Declarative RAG | Skills Architecture |
| [ADR-26033](architecture/adr/adr_26033_virtual_monorepo_via_package_driven_dependency_management.md) | Virtual Monorepo via Package-Driven Dependency Management | Governance |
| [ADR-26030](architecture/adr/adr_26030_stateless_jit_context_injection_for_agentic_git_workflow.md) | Stateless JIT Context Injection for Agentic Git Workflows | Context Management |

### New Features and Articles Added

*   **Agent Research Program** (7 codebases analyzed):

    The core deliverable — a systematic study of how open-source AI coding agents manage context, discover skills, and maintain stability:

    - [Context Management Overview](/ai_agents/architecture/context_management/context_management_in_ai_coding_agents.md) — pattern taxonomy: full history, sliding window, reactive compaction, async summarization, tiered systems
    - [Context Management Comparison](/ai_agents/architecture/context_management/context_management_agent_comparison.md) — side-by-side tables across 7 agents: trigger mechanisms, compaction strategies, state preservation, decision guide
    - [Individual agent deep dives](/ai_agents/architecture/context_management/context_management_in_ai_coding_agents.md): Qwen Code (autocompact buffer + /compress), Claude Code (5-tier system), OpenCode (reactive compaction), OpenClaude (5-tier system), Aider (async background summarization), KiloCode (OpenCode fork)
    - [How Subagents Work](/ai_agents/architecture/orchestration/how_subagents_actually_work_myth_of_process_spawning.md) — debunks OS fork/exec myth, documents three real patterns
    - [Stability Against LLM Drift](/ai_agents/architecture/skills/stability_in_a_probabilistic_substrate_how_agents_fight_llm_drift.md) — hard guarantees vs soft techniques
    - [Skill Discovery Across Platforms](/ai_agents/architecture/skills/skill_discovery_across_ai_coding_platforms.md) — Superpowers v5.0.7 analysis across 5 platforms
    - [Prompt Brittleness in Skills](/ai_agents/architecture/skills/prompt_brittleness_in_skill_based_orchestration.md) — three failure modes with empirically-derived countermeasures

*   **[manage_external_repos.py](/tools/scripts/manage_external_repos.py) — External Research Repo Management** (19 tests, 85% coverage):

    CLI tool for cloning, updating, and listing external research repositories. Supports `setup`, `update`, `list`, `register`, `unregister`, and `relocate` commands. The `relocate` command is the key safety feature: when a research directory moves, it updates the registry and consumer files atomically.

*   **Commit Message Format Enhancement**:

    Sub-bullet format now supported in commit body validation (`    — <lowercase_verb> <detail>`). Enables richer changelog entries while maintaining the structured format that `generate_changelog.py` parses.

*   **ADR Conditional Validation and Index Duplicate Detection**:

    ADR validator now enforces conditional sections: rejected ADRs must have Rejection Rationale, superseded ADRs must have Supersession Rationale, deprecated ADRs must have Deprecation Rationale (minimum 3 words — prevents empty/TBD sections). The index builder detects duplicate ADR entries and reports their location.

*   **Qwen JSON Export Converter** (41 tests, 93% coverage):

    Converts Qwen chat export JSON to evidence source artifacts with thread reconstruction and auto-ID from git history. Enables capturing research sessions directly from Qwen conversations — the JSONL session log format used by Qwen Code is a separate research track.

### Updates in Existing Files

*   **KV Cache Internals — Technical Accuracy Review**: The [what_kv_cache_actually_contains.ipynb](/ai_system_layers/1_execution/what_kv_cache_actually_contains.ipynb) document received a comprehensive technical accuracy pass: fixed GQA weight matrix dimensions, FLOP count consistency, FlashAttention complexity claims, SwiGLU FFN FLOP counts, autoregressive complexity notation, bandwidth ratios, and arXiv source citations.

*   **Consultant Prompt Consolidation**: Hybrid consultant prompts consolidated under canonical names. Unused variants deleted. [Consultants README](/ai_system_layers/3_prompts/consultants/README.md) added as usage guide and catalog.

### Repository Structure Changes

| Original Path | New Path |
| :--- | :--- |
| `ai_system/` | `ai_system_layers/` |
| `tools/docs/ai_agents/` | `ai_agents/guides/` |
| — | `ai_agents/` (new — root-level agent research hub) |
| — | `research/` (new — external product source code clones) |

## release v2.8.0 "The Prompt Physics"

### Summary of Changes

v2.7.0 settled the ecosystem's strategic direction: context engineering over multi-agent orchestration. v2.8.0 turns that principle into empirical engineering. The release delivers a three-article series on prompt format — with real measurements, plots, and reproducible code — backed by three new analyses grounding every claim in reviewed evidence. The central finding challenges a common assumption: token cost is not a property of the format alone. It is a function of format, serializer, and tokenizer together, and the relative ranking of YAML vs. JSON can flip depending on which Python library you use to generate the YAML.

Alongside the research, this release closes the governance infrastructure loop: all configs migrated to JSON, the frontmatter validator deployed and enforced at commit time. The two threads — empirical prompt research and governance automation — serve the same goal from the ecosystem roadmap: build the evidence base and the tooling foundation before writing the first production application.

Three strategic themes define v2.8.0:

1. **Prompt Format as Engineering Science** — The [Format as Architecture](/ai_system_layers/3_prompts/format_as_architecture_signal_noise_in_prompt_delivery.ipynb) series answers a question that most practitioners answer by intuition: which format should a system prompt use? The answer is not a preference — it has a mechanistic explanation rooted in BPE tokenizer architecture and transformer attention. JSON is optimal for development artifacts (validation, tooling). YAML is optimal for runtime instructions (low structural noise). XML provides scope isolation where injection resistance matters. The series includes token measurements across four formats on a production prompt, validated across three tokenizers (cl100k\_base, o200k\_base, Qwen-72B).

2. **Two-Stage Consultant Workflow** — The prompt engineering toolchain gains a structured two-phase workflow. [ai_brainstorming_colleague.json](/ai_system_layers/3_prompts/consultants/ai_brainstorming_colleague.json) (v0.2.0) is the first stage: unconstrained ideation, architectural discussion, "what-if" scenarios. When a direction needs formal validation, it hands off explicitly to [ai_systems_consultant.json](/ai_system_layers/3_prompts/consultants/ai_systems_consultant.json) or [devops_consultant.json](/ai_system_layers/3_prompts/consultants/devops_consultant.json) — the strict reviewers with WRC scoring and SVA compliance. The brainstorming colleague enforces this boundary itself: when it detects validation-intent keywords, it executes the handoff protocol rather than attempting a review it is not designed for. This prevents the common failure mode of asking an exploratory tool for production-grade architectural judgement.

3. **Governance Infrastructure Operational** — [ADR-26042: Common Frontmatter Standard](architecture/adr/adr_26042_common_frontmatter_standard.md) and [ADR-26036: Config File Location and Naming Conventions](architecture/adr/adr_26036_config_file_location_and_naming_conventions.md) / [ADR-26054: JSON as Governance Config Format](architecture/adr/adr_26054_json_as_governance_config_format.md) move from specified to enforced. [check_frontmatter.py](/tools/scripts/check_frontmatter.py) (work in progress) validates document frontmatter at commit time against the composable schema. All governance configs are migrated from YAML to JSON. The `.vadocs/` configuration system is complete: `conf.json` hub → `types/*.conf.json` spokes → `pyproject.toml` entry point for all tools.

### Architecture Decisions

*   **[ADR-26054: JSON as Governance Config Format](architecture/adr/adr_26054_json_as_governance_config_format.md) — Config Serialization**:
    Governance configs use JSON (not YAML, not TOML) because JSON Schema is the de-facto standard for machine-validated structured configuration with mature tooling in Python (`jsonschema` library) and across the broader ecosystem. YAML was rejected despite its readability advantage because schema tooling for YAML is fragmented and no dominant standard exists. TOML has no schema standard at all. Document frontmatter stays YAML (MyST-native, human-authored) — JSON governs only machine-read governance configs in `.vadocs/`. A JSON Schema companion [conf.schema.json](/.vadocs/conf.schema.json) validates the hub config structure.

*   **[ADR-26044: Skills as Progressive Disclosure Units](architecture/adr/adr_26044_skills_as_progressive_disclosure_units.md) — Skills Architecture**:
    ADR-26044 formally defines a skill as a self-contained instruction block injected into the agent's context on demand. Skills are not subagents — they carry no separate LLM calls, no state, no negotiation. They are loaded when needed (progressive disclosure) and expire when the conversation ends. This definition sharpens the boundary introduced in ADR-26038: managing what the agent sees (context budget) is the primary engineering constraint, and skills are the mechanism for doing so without spawning multiple agents. The `sv-` namespace in Claude Code demonstrates the pattern in practice: six consultant prompts loaded as skills via symlinks to their JSON sources in `ai_system/3_prompts/consultants/`. The two validation-focused skills (`sv-ai-systems-consultant-hybrid`, `sv-devops-consultant`) use WRC scoring — Weighted Response Confidence, a 0–1 metric composed of empirical benchmark evidence (35%), enterprise production adoption (25%), and predicted performance on the target stack (40%); currently defined inside the prompt, pending a governing ADR (tracked in `techdebt.md` TD-006) — and SVA compliance ([ADR-26037: Smallest Viable Architecture Constraint Framework](architecture/adr/adr_26037_smallest_viable_architecture_constraint_framework.md)) as their output standard — making formal architectural review available on demand without context pollution between exploration and validation phases.

*   **[ADR-26036: Config File Location and Naming Conventions](architecture/adr/adr_26036_config_file_location_and_naming_conventions.md) and [ADR-26042: Common Frontmatter Standard](architecture/adr/adr_26042_common_frontmatter_standard.md) — Now Operational**:
    Both ADRs were proposed in v2.7.0. This release marks their operational transition: `.vadocs/` contains all governance configs in JSON (ADR-26036), and `check_frontmatter.py` enforces the composable frontmatter schema (ADR-26042) at commit time. Promotion to accepted awaits ecosystem-wide validation in the next release cycle.

### Accepted ADRs (Promoted in This Release)

No ADRs were promoted in this release. v2.8.0 is a research and operationalization cycle: the prompt engineering series builds the empirical foundation; the governance tooling enforces v2.7.0 decisions. Promotion of [ADR-26042: Common Frontmatter Standard](architecture/adr/adr_26042_common_frontmatter_standard.md), [ADR-26036: Config File Location and Naming Conventions](architecture/adr/adr_26036_config_file_location_and_naming_conventions.md), and [ADR-26054: JSON as Governance Config Format](architecture/adr/adr_26054_json_as_governance_config_format.md) to accepted requires validation across the full ecosystem, which begins next cycle.

### Open RFCs (Proposed ADRs)

New proposed ADRs introduced in this release:

| ADR | Title | Theme |
| :--- | :--- | :--- |
| [ADR-26054](architecture/adr/adr_26054_json_as_governance_config_format.md) | JSON as Governance Config Format | Governance |
| [ADR-26044](architecture/adr/adr_26044_skills_as_progressive_disclosure_units.md) | Skills as Progressive Disclosure Units | Context Management |

Carry-over proposed ADRs (open for review and comment):

| ADR | Title | Theme |
| :--- | :--- | :--- |
| [ADR-26042](architecture/adr/adr_26042_common_frontmatter_standard.md) | Common Frontmatter Standard | Governance |
| [ADR-26036](architecture/adr/adr_26036_config_file_location_and_naming_conventions.md) | Config File Location and Naming Conventions | Governance |
| [ADR-26043](architecture/adr/adr_26043_ecosystem_package_boundary.md) | Ecosystem Package Boundary | Governance |
| [ADR-26039](architecture/adr/adr_26039_pgvector_as_ecosystem_database_standard.md) | pgvector as Ecosystem Database Standard | Data Infrastructure |
| [ADR-26041](architecture/adr/adr_26041_client_side_logic_with_server_side_retrieval.md) | Client-Side Logic with Server-Side Retrieval | Data Infrastructure |
| [ADR-26032](architecture/adr/adr_26032_tiered_cognitive_memory_procedural_skills.md) | Tiered Cognitive Memory: Procedural Skills vs. Declarative RAG | Skills Architecture |
| [ADR-26033](architecture/adr/adr_26033_virtual_monorepo_via_package_driven_dependency_management.md) | Virtual Monorepo via Package-Driven Dependency Management | Governance |
| [ADR-26030](architecture/adr/adr_26030_stateless_jit_context_injection_for_agentic_git_workflow.md) | Stateless JIT Context Injection for Agentic Git Workflows | Context Management |

### New Features and Articles Added

*   **Prompt Engineering Series** (3 articles + 3 analyses):

    The core deliverable of this release — an empirically grounded series on how prompt format affects LLM behavior:

    - [Format as Architecture: Signal-to-Noise in Prompt Delivery](/ai_system_layers/3_prompts/format_as_architecture_signal_noise_in_prompt_delivery.ipynb) — qualitative format comparison, training-distribution effects, the two-audience principle (compiler vs. runtime model), security analysis, and the decision framework. Central claim: structural tokens (brackets, quotes, commas) are not ignored — the model processes each one to determine it is irrelevant, incurring compute cost and receiving a lower but non-zero attention weight. Their presence dilutes the share of attention available to instructional content. The more structural noise in the prompt, the harder the model has to work to extract the actual signal. For the technical mechanics see [A-26016: Causal Masking and Attention Mechanics — Implications for Prompt Format](architecture/evidence/analyses/A-26016_causal_masking_attention_mechanics_for_prompt_engineering.md).
    - [Token Economics of Prompt Delivery](/ai_system_layers/3_prompts/token_economics_of_prompt_delivery.ipynb) — the empirical companion: BPE tokenizer mechanics (space+word merging, indentation cost, punctuation merging), measured token costs across four formats on a production prompt, cross-tokenizer validation (cl100k\_base, o200k\_base, Qwen-72B).
    - [Appendix: YAML Serializer Variance](/ai_system_layers/3_prompts/appendix_yaml_serializer_variance.ipynb) — the unexpected finding: PyYAML and yq produce semantically equivalent YAML from the same JSON source yet differ by 100+ tokens on a 150-line production prompt, and the YAML Literal vs. Pretty JSON ranking **flips** depending on the serializer. Token cost is `f(format, serializer, tokenizer)` — three variables, not one. Validated across 5 prompt files.

    Three analyses ground the series in reviewed evidence:
    - [A-26016: Causal Masking and Attention Mechanics — Implications for Prompt Format](architecture/evidence/analyses/A-26016_causal_masking_attention_mechanics_for_prompt_engineering.md) — grounds the "attention anchors" and "reasoning capacity" claims in transformer architecture
    - [A-26017: YAML Serializer Variance — Token Economics of Format Choice](architecture/evidence/analyses/A-26017_yaml_serializer_variance_token_economics.md) — verifies the three-variable finding with independent measurements across serializers
    - [A-26018: XML Tags as Scope Boundaries — Prompt Architecture and Injection Resistance](architecture/evidence/analyses/A-26018_xml_tags_scope_isolation_prompt_architecture.md) — covers the hybrid YAML+XML pattern and the JSON-list injection boundary technique

*   **[check_frontmatter.py](/tools/scripts/check_frontmatter.py) — Frontmatter Enforcement** (work in progress; 67 tests, 97% coverage on implemented scope):
    Validates document frontmatter against the composable schema from [ADR-26042: Common Frontmatter Standard](architecture/adr/adr_26042_common_frontmatter_standard.md). Resolves the hub-spoke config chain dynamically — one validator, all document types. Two pre-commit hooks: `check-frontmatter` (validates on stage) and `test-check-frontmatter` (runs the test suite on script/config changes). Architecture analysis [A-26015: Frontmatter Validator Architecture](architecture/evidence/analyses/A-26015_frontmatter_validator_architecture.md) evaluated three approaches; Approach C (module+CLI) selected.

### Updates in Existing Files

*   **[ai_brainstorming_colleague.json](/ai_system_layers/3_prompts/consultants/ai_brainstorming_colleague.json) (v0.2.0)**: Refocused as the first stage of a two-stage workflow. Removed stack-specific defaults. Added `interaction_rules` (technical language, no filler, falsifiable claims only) and `handoff_target: ai_systems_consultant_hybrid`. Overhauled output structure with Critical Diagnosis and Root Cause Analysis steps. When it detects validation-intent keywords, it executes the handoff protocol instead of attempting formal review.

*   **Governance Config Migration** (`.vadocs/`): All configs migrated from YAML to JSON. Deleted: `conf.yaml`, `adr_config.yaml`, `architecture.config.yaml`, `evidence.config.yaml`. New layout: `conf.json` + `conf.schema.json` (hub) → `types/adr.conf.json`, `types/evidence.conf.json` (spokes). New shared modules: `git.py` (repo root detection, staged files) and `paths.py` (convention-based config discovery via `get_config_path()`). `pyproject.toml` gains `[tool.vadocs]` entry point.

### Existing Files Moved or Renamed

| Original Path | New Path |
| :--- | :--- |
| `.vadocs/conf.yaml` | `.vadocs/conf.json` (+ `conf.schema.json`) |
| `architecture/adr/adr_config.yaml` | `.vadocs/types/adr.conf.json` |
| `architecture/evidence/evidence.config.yaml` | `.vadocs/types/evidence.conf.json` |
| `architecture/architecture.config.yaml` | Absorbed into `.vadocs/conf.json` (hub) |

## release v2.7.0 "The Context Engineering Pivot"

### Summary of Changes

v2.6.0 explored an ambitious vision — agents as operating systems that discover and compose skills at runtime. That research produced valuable insights (4 analyses, 11 source artifacts, 7 ADRs), but the key finding was simpler than the vision: **what matters is not how many agents you have, but what each agent sees.** v2.7.0 distills this into a strategic pivot — context engineering replaces the Agentic OS paradigm as the ecosystem's core design principle.

Simultaneously, this release lays the **infrastructure blueprint** for what comes next. Seven new ADRs define the technical stack needed to deploy a working AI application: one database (pgvector), one container runtime (Podman), one metadata schema (composable frontmatter), one governance package (vadocs). The goal: `podman play kube` + API key = running mentor agent.

This is also the ecosystem's **first consolidation release**: 4 ADRs promoted to accepted standards, 3 rejected with their insights absorbed. After two releases of pure exploration, the ecosystem is now making commitments.

Three strategic themes define v2.7.0:

1. **Context Engineering Pivot** — v2.6.0's Agentic OS exploration (ADR-26032, ADR-26033, ADR-26034) asked how agents should organize knowledge. The [Compass analysis](architecture/evidence/analyses/A-26009_compass_realistic_state_of_agentic_ai_2026.md) — a comprehensive review of the state of agentic AI in early 2026 — showed that multi-agent swarms (systems where independent agents negotiate with each other) suffer from context isolation: each agent makes decisions without the other's knowledge. [ADR-26038](architecture/adr/adr_26038_context_engineering_as_core_design_principle.md) adopts a simpler model: one agent loads skills as injected instructions on demand, and the primary engineering challenge is managing the context window — what the agent sees, not how many agents there are. The boundary between skill injection and subagent delegation (as used by production tools like Claude Code) remains an open research question that will be analyzed in future releases.

2. **Ecosystem Infrastructure Blueprint** — Seven proposed ADRs define the technical stack: [ADR-26039](architecture/adr/adr_26039_pgvector_as_ecosystem_database_standard.md) (pgvector — one Postgres for structured data and vector embeddings), [ADR-26040](architecture/adr/adr_26040_podman_kube_yaml_as_deployment_standard.md) (Podman Kube YAML — one manifest from dev to prod), [ADR-26041](architecture/adr/adr_26041_client_side_logic_with_server_side_retrieval.md) (Python owns logic, SQL owns retrieval), [ADR-26042](architecture/adr/adr_26042_common_frontmatter_standard.md) (composable frontmatter with 10 document types), [ADR-26043](architecture/adr/adr_26043_ecosystem_package_boundary.md) (vadocs as an installable governance package). Together they answer a practical question: what does the ecosystem need to deploy its first application?

3. **Evidence-Driven Architecture** — The release demonstrates the Architecture Knowledge Base (ADR-26035) as a proven workflow: 4 new analyses ([A-26006](architecture/evidence/analyses/A-26006_agent_runtime_architecture_rag_infrastructure.md) through [A-26009](architecture/evidence/analyses/A-26009_compass_realistic_state_of_agentic_ai_2026.md)) grounded 5 ADRs in empirical evidence. Source artifacts were created, their insights extracted into analyses, and the sources deleted — the three-commit lifecycle model works. The SVA constraint framework (ADR-26037) was formalized from an informal guideline into six canonical constraints.

### Architecture Decisions

*   **[ADR-26038: Context Engineering as Core Design Principle](architecture/adr/adr_26038_context_engineering_as_core_design_principle.md) — The Pivot**:
    The most significant decision of the release. Instead of building an "Agentic OS" with tiered memory, tag-filtered registries, and runtime skill discovery, the ecosystem adopts a simpler model: one agent, skills loaded as injected instructions on demand (progressive disclosure), and context window budget as the first-class constraint. The Compass analysis (A-26009) shows that multi-agent swarms — systems where independent agents negotiate with each other — suffer from context isolation between agents. The ecosystem avoids this by keeping everything in one conversation: skills inject instructions into the agent's context rather than spawning separate agents. However, production tools like Claude Code use subagent patterns (forked child processes with their own LLM calls) that don't fit neatly into either category. The boundary between skill injection and subagent delegation is an open research question scheduled for future analysis.

*   **[ADR-26039: pgvector as Ecosystem Database Standard](architecture/adr/adr_26039_pgvector_as_ecosystem_database_standard.md), [ADR-26041: Client-Side Logic with Server-Side Retrieval](architecture/adr/adr_26041_client_side_logic_with_server_side_retrieval.md) — Data Infrastructure**:
    One Postgres instance serves the entire ecosystem — structured data and vector embeddings in the same database, isolated by schema-per-project. ADR-26041 complements this with the Logic-in-View pattern: Python owns orchestration logic, SQL functions own retrieval. Since LLM inference dominates latency (seconds), the millisecond advantage of server-side logic is irrelevant.

*   **[ADR-26040: Podman Kube YAML as Deployment Standard](architecture/adr/adr_26040_podman_kube_yaml_as_deployment_standard.md) — Deployment**:
    Kube YAML manifests are the single deployment artifact. `podman-kube@.service` systemd template manages lifecycle. Rootless by default, no Docker daemon, no Compose — the same manifest runs locally and in production.

*   **[ADR-26042: Common Frontmatter Standard](architecture/adr/adr_26042_common_frontmatter_standard.md), [ADR-26043: Ecosystem Package Boundary](architecture/adr/adr_26043_ecosystem_package_boundary.md) — Governance Infrastructure**:
    ADR-26042 defines a composable frontmatter schema with three blocks (identity, discovery, lifecycle) and 10 document types. Hub-and-spoke configuration ensures consistency across repositories. ADR-26043 draws the boundary for vadocs: 15 governance scripts organized by concern (core, docs, git, init), with a CLI that mirrors the structure. Together, they prepare the ecosystem for multi-repository governance.

*   **ADR Rejections — [ADR-26031](architecture/adr/adr_26031_prefixed_namespace_system_for_architectural_records.md), [ADR-26034](architecture/adr/adr_26034_agentic_os_paradigm_skills_as_composable_applications.md), [ADR-26003](architecture/adr/adr_26003_adoption_of_gitlint_for_tiered_workflow.md)**:
    ADR-26031 (prefixed namespaces) rejected — string prefix approach is weaker than the Postgres namespace model from A-26005. ADR-26034 (Agentic OS paradigm) rejected — the grand OS framing is replaced by context engineering; valid concepts (skills, procedural/declarative split) are absorbed into ADR-26038. ADR-26003 (gitlint) rejected — commit validation is solved by custom `validate_commit_msg.py` (ADR-26024); branch naming will be addressed in a future vadocs-git plugin.

### Accepted ADRs (Promoted in This Release)

Four ADRs promoted from proposed to accepted, marking the transition from exploration to commitment:

| ADR | Title | Rationale |
| :--- | :--- | :--- |
| [ADR-26011](architecture/adr/adr_26011_formalization_of_mandatory_script_suite.md) | Mandatory Script Suite Workflow | Triad (script + tests + docs) enforced via pre-commit hooks |
| [ADR-26024](architecture/adr/adr_26024_structured_commit_bodies_for_automated_changelog.md) | Structured Commit Bodies for Automated CHANGELOG | validate_commit_msg.py + generate_changelog.py operational |
| [ADR-26038](architecture/adr/adr_26038_context_engineering_as_core_design_principle.md) | Context Engineering as Core Design Principle | Core principle driving ADR rejections and ecosystem direction |
| [ADR-26040](architecture/adr/adr_26040_podman_kube_yaml_as_deployment_standard.md) | Podman Kube YAML as Deployment Standard | Production templates exist, CLAUDE.md mandates Podman |

### Open RFCs (Proposed ADRs)

All infrastructure ADRs introduced in this release are in **proposed** status — they define the target architecture but await implementation validation before promotion.

| ADR | Title | Theme |
| :--- | :--- | :--- |
| [ADR-26039](architecture/adr/adr_26039_pgvector_as_ecosystem_database_standard.md) | pgvector as Ecosystem Database Standard | Data Infrastructure |
| [ADR-26041](architecture/adr/adr_26041_client_side_logic_with_server_side_retrieval.md) | Client-Side Logic with Server-Side Retrieval | Data Infrastructure |
| [ADR-26042](architecture/adr/adr_26042_common_frontmatter_standard.md) | Common Frontmatter Standard | Governance |
| [ADR-26043](architecture/adr/adr_26043_ecosystem_package_boundary.md) | Ecosystem Package Boundary | Governance |
| [ADR-26032](architecture/adr/adr_26032_tiered_cognitive_memory_procedural_skills.md) | Tiered Cognitive Memory | Skills Architecture |
| [ADR-26033](architecture/adr/adr_26033_virtual_monorepo_via_package_driven_dependency_management.md) | Virtual Monorepo | Skills Architecture |

### New Features and Articles Added

*   **Evidence Pipeline Maturation**:
    Four new analyses (A-26006 through A-26009) demonstrate the Architecture Knowledge Base as a working system: raw dialogues formalized as sources, insights extracted into analyses, analyses grounding ADRs. The Compass analysis (A-26009) — a comprehensive assessment of the realistic state of agentic AI in 2026 — directly drove the rejection of the Agentic OS paradigm and the adoption of context engineering. Evidence source artifacts (S-26006 through S-26011) were created, extracted, and deleted per the three-commit workflow, proving the lifecycle model.

*   **SVA Constraint Framework (ADR-26037)**:
    The Smallest Viable Architecture principle, previously an informal guideline, is now formalized as six canonical constraints (C1–C6) derived from first principles (UNIX, YAGNI, Twelve-Factor, SRE, GitOps, ISO 29148). Consultant prompts updated to reference the canonical framework.

*   **Post-Commit Changelog Preview**:
    A new post-commit hook runs `generate_changelog.py` on the just-created commit, showing the CHANGELOG entry immediately after commit. This provides instant feedback on how structured body bullets will appear in the release — catching formatting issues before they accumulate.

### Updates in Existing Files

*   **format_string.py (v0.3.0)**: Gained argparse CLI (replacing sys.argv), optional truncation (`--trunc`, `--trunc-len`), en-dash support, and file extension stripping (.pdf, .epub, .tar.gz, etc.). Full triad update: 42 tests with contract-based docstrings, instruction doc with grouped examples.

*   **generate_changelog.py (v1.2.0)**: Fixed orphan commit bug — commits with all bullets excluded by patterns now drop entirely from output instead of rendering as subject-only stubs. Gained exclusion patterns from `pyproject.toml`, bold markdown section headers, `--verbose` flag for debugging, and blank-line separator in `--prepend` mode. 78 tests total.

*   **Architecture Decision Workflow Guide**: Gained Valid Status Transitions section referencing `adr_config.yaml` as SSoT, with transition rules (proposed → accepted/rejected only, terminal states locked).

*   **AI Systems Consultant Prompt (Hybrid)**: Refined specialization, updated tooling lists, replaced ad-hoc SVA constraints with canonical C1–C6 from ADR-26037.

### Existing Files Moved or Renamed

| Original | New |
| :--- | :--- |
| `architecture/evidence/sources/S-26007_compass*.md` | Promoted to `architecture/evidence/analyses/A-26009_compass*.md` |
| `architecture/evidence/sources/S-26001` through `S-26005` | Deleted (extracted into analyses) |
| `architecture/evidence/sources/S-26006` through `S-26011` | Deleted (extracted into ADRs and analyses) |

## release v2.6.0 "The Cognitive Architecture"

### Summary of Changes

This release shifts focus from infrastructure governance (v2.4.0–v2.5.0) to **architectural vision**: how should an AI-backed ecosystem think, remember, and organize itself? Six new ADRs answer this question by defining a three-tier cognitive model — procedural skills, declarative RAG, and composable agent applications — and by establishing the infrastructure to support it: namespaced decision records, a virtual monorepo, and stateless context injection.

Simultaneously, the release introduces a formal **Architecture Knowledge Base** — a taxonomy and validation toolchain for the architectural artifacts (analyses, sources, retrospectives) that feed the decision-making process. The ecosystem is now introspective: it documents how it documents.

Three strategic themes define v2.6.0:

1. **Skills Architecture** — Three interconnected ADRs ([ADR-26032](architecture/adr/adr_26032_tiered_cognitive_memory_procedural_skills.md), [ADR-26033](architecture/adr/adr_26033_virtual_monorepo_via_package_driven_dependency_management.md), [ADR-26034](architecture/adr/adr_26034_agentic_os_paradigm_skills_as_composable_applications.md)) define a coherent vision for AI agent operation: tiered cognitive memory separates fast procedural skills from slow declarative retrieval; a virtual monorepo connects ecosystem projects without coupling them; and the Agentic OS paradigm treats skills as composable applications that agents discover and execute at runtime. This is the conceptual leap of the release — from "what tools do we use" to "how should AI agents organize knowledge and capabilities."
2. **Architecture Knowledge Base** — [ADR-26035](architecture/adr/adr_26035_architecture_knowledge_base_taxonomy.md) and [ADR-26036](architecture/adr/adr_26036_config_file_location_and_naming_conventions.md) formalize how architectural knowledge itself is classified and stored. A new `check_evidence.py` validator (75 config-driven tests) enforces the taxonomy automatically. Evidence artifacts — analyses, sources, retrospectives — are now first-class citizens with naming conventions, required metadata, and validation gates. The knowledge base that informs architectural decisions is now as governed as the decisions themselves.
3. **Ecosystem Scaling** — [ADR-26030](architecture/adr/adr_26030_stateless_jit_context_injection_for_agentic_git_workflow.md) formalizes stateless JIT context injection, eliminating context accumulation across agent sessions and reducing token costs. [ADR-26031](architecture/adr/adr_26031_prefixed_namespace_system_for_architectural_records.md) introduces prefixed namespaces for architectural records, so that ADR identifiers remain unique and unambiguous as the ecosystem grows across multiple repositories. Together, they prepare the infrastructure for a multi-repo ecosystem where each spoke can maintain its own decision history without collision.

### Architecture Decisions

*   **[ADR-26032: Tiered Cognitive Memory](architecture/adr/adr_26032_tiered_cognitive_memory_procedural_skills.md), [ADR-26033: Virtual Monorepo](architecture/adr/adr_26033_virtual_monorepo_via_package_driven_dependency_management.md), [ADR-26034: Agentic OS Paradigm](architecture/adr/adr_26034_agentic_os_paradigm_skills_as_composable_applications.md) — Skills Architecture**:
    The most significant conceptual contribution of this release. ADR-26032 separates agent memory into three tiers: procedural skills (fast, always-loaded), declarative RAG (slow, on-demand retrieval), and episodic context (session-specific). ADR-26033 proposes a virtual monorepo where ecosystem packages share conventions without physical coupling — a package-driven dependency model that avoids the complexity of a real monorepo. ADR-26034 crowns the vision: agents operate like an OS, discovering and composing skills at runtime through tag-filtered registries. Together, these three ADRs chart the path from today's tool-specific automation to tomorrow's composable AI workforce.

*   **[ADR-26035: Architecture Knowledge Base Taxonomy](architecture/adr/adr_26035_architecture_knowledge_base_taxonomy.md)**:
    Before this ADR, analyses and source transcripts were unstructured files in ad-hoc locations. ADR-26035 introduces a formal taxonomy: **analyses** (A-prefixed, structured conclusions from sources), **sources** (S-prefixed, raw evidence like dialogue transcripts), and **retrospectives** (R-prefixed, post-hoc evaluations). Each type has naming conventions, required metadata, and a defined lifecycle. This makes the evidence base machine-queryable — an AI agent can now distinguish a raw Gemini transcript from a curated architectural analysis.

*   **[ADR-26036: Config File Location and Naming Conventions](architecture/adr/adr_26036_config_file_location_and_naming_conventions.md)**:
    As the number of config files grew (adr_config.yaml, evidence.config.yaml, architecture.config.yaml), inconsistent naming and placement created confusion. ADR-26036 standardizes the pattern: `<domain>.config.yaml` files live in their domain directory, with a `parent_config` pointer for shared vocabulary. This is the config counterpart to ADR-26029 (pyproject.toml for tool config) — together they establish a complete configuration hierarchy.

*   **[ADR-26030: Stateless JIT Context Injection](architecture/adr/adr_26030_stateless_jit_context_injection_for_agentic_git_workflow.md)**:
    Agent sessions that accumulate context over time become expensive and brittle — stale instructions mix with current state, token budgets grow unboundedly. ADR-26030 formalizes the stateless observer pattern: each agent invocation receives exactly the context it needs, assembled just-in-time from repository state. No session memory, no accumulated drift. This is the architectural foundation for scalable agent workflows.

*   **[ADR-26031: Prefixed Namespace System for Architectural Records](architecture/adr/adr_26031_prefixed_namespace_system_for_architectural_records.md)**:
    As the ecosystem spawns spoke repositories (vadocs, research monorepo), ADR numbering will collide — ADR-26001 in the hub means something different from ADR-26001 in a spoke. This ADR proposes prefix-based namespacing so that each repository's decisions are globally unique and cross-referenceable.

### Accepted ADRs (Promoted in This Release)

No ADRs were promoted from proposed to accepted in this release. All 7 new ADRs enter as proposed — the ecosystem is in an exploratory phase, accumulating RFCs that will be validated by practice before promotion.

### Open RFCs (Proposed ADRs)

All architectural decisions introduced in this release are in **proposed** status — they are living RFCs, open for analysis and feedback. They become binding standards only after passing the promotion gate (ADR-26025).

| ADR | Title | Theme |
| :--- | :--- | :--- |
| [ADR-26030](architecture/adr/adr_26030_stateless_jit_context_injection_for_agentic_git_workflow.md) | Stateless JIT Context Injection for Agentic Git Workflows | Ecosystem Scaling |
| [ADR-26031](architecture/adr/adr_26031_prefixed_namespace_system_for_architectural_records.md) | Prefixed Namespace System for Architectural Records | Ecosystem Scaling |
| [ADR-26032](architecture/adr/adr_26032_tiered_cognitive_memory_procedural_skills.md) | Tiered Cognitive Memory: Procedural Skills vs. Declarative RAG | Skills Architecture |
| [ADR-26033](architecture/adr/adr_26033_virtual_monorepo_via_package_driven_dependency_management.md) | Virtual Monorepo via Package-Driven Dependency Management | Skills Architecture |
| [ADR-26034](architecture/adr/adr_26034_agentic_os_paradigm_skills_as_composable_applications.md) | Agentic OS Paradigm: Skills as Composable Applications | Skills Architecture |
| [ADR-26035](architecture/adr/adr_26035_architecture_knowledge_base_taxonomy.md) | Architecture Knowledge Base Taxonomy | Knowledge Base |
| [ADR-26036](architecture/adr/adr_26036_config_file_location_and_naming_conventions.md) | Config File Location and Naming Conventions | Knowledge Base |

### New Features and Articles Added

*   **Evidence Artifact Validation (`check_evidence.py`)**:
    A new validation script that enforces the Architecture Knowledge Base taxonomy. It validates evidence artifacts against `evidence.config.yaml` — checking naming patterns, required frontmatter fields, date formats, and artifact type classification. The script follows the established Script Suite convention (ADR-26011): script + 75 config-driven tests + instruction document. Integrated into pre-commit hooks and the CI quality pipeline.

*   **Architecture Knowledge Base Infrastructure**:
    The `architecture/evidence/` directory gains formal structure: `evidence.config.yaml` defines the validation schema with common required fields and date format as SSoT; `architecture.config.yaml` provides shared architectural vocabulary (tags) as a parent config; `sources/README.md` documents the source lifecycle and git archaeology guide.

*   **A-26002: Agentic OS Analysis**:
    A comprehensive analysis extracting 11 architectural insights from the Gemini dialogue S-26001 — covering the Agentic OS paradigm, three-tier cognitive memory, tag-filtered skill discovery, package-driven virtual monorepo, builder/runtime separation, and the evolution from prompt engineering to software engineering. This analysis directly informed ADR-26032, ADR-26033, and ADR-26034.

*   **S-26001: Gemini Dialogue on Skills Architecture**:
    The raw source transcript of a Gemini 3.0 Flash consultation on skills architectures, cognitive memory tiers, and package-driven infrastructure. Preserved as evidence per ADR-26035 taxonomy — the source that seeded the skills architecture vision.

### Updates in Existing Files

*   **Commit Convention Cleanup**: Removed the backtick wrapping requirement from structured commit body bullets across ADR-26024, git workflow docs, validation script docs, and CHANGELOG format docs. The commit convention in `pyproject.toml` is now the single source of truth — added `adr` type, removed `test` type.

*   **format_string.py**: Added dash (`—`) to the list of special symbols replaced during string formatting. Corresponding documentation updated.

*   **Pre-commit & CI**: Added `check-evidence` and `test-check-evidence` hooks to `.pre-commit-config.yaml`; added `evidence-validation` job to `quality.yml` with logic/docs triggers.

### Existing Files Moved or Renamed

| Original | New |
| :--- | :--- |
| *(no file moves in this release)* | |

## release v2.5.0 "The Self-Documenting System"

### Summary of Changes

This release closes the loop on commit governance: the system now **validates its own commits, generates its own CHANGELOG, and installs its own hooks**. What began in v2.4.0 as metadata-driven ADR governance now extends to the entire commit lifecycle — from message validation at commit time to automated CHANGELOG generation from structured commit history.

The release also crystallizes the project's identity. The **Documentation-as-Code Manifesto** (`architecture/manifesto.md`) declares what this project has been converging toward since v1.0: documentation is source code for AI systems — versioned, tested, lifecycle-managed, and machine-readable. The README was rewritten around this principle.

Three strategic themes define v2.5.0:

1. **Automated Commit Governance** — `validate_commit_msg.py` enforces conventional commit format with structured body bullets at commit time; `generate_changelog.py` transforms that structured history into hierarchical CHANGELOG entries; `configure_repo.py` auto-installs the commit-msg hook during setup. Together, they form a self-documenting commit lifecycle where no manual CHANGELOG curation is needed.
2. **Tool-Agnostic Architecture** — [ADR-26004: Agentic RAG](architecture/adr/adr_26004_implementation_of_agentic_rag_for_autonom.md) through [ADR-26008: Reasoning-Class Models for Abstract Synthesis](architecture/adr/adr_26008_reasoning_class_models_for_abstract_synt.md) were written around specific tools (Aider, Gemini Flash). As the project matured, it became clear that cognitive roles matter more than tool names. [ADR-26027: Model Taxonomy](architecture/adr/adr_26027_model_taxonomy_reasoning_vs_agentic_class.md) and [ADR-26028: Tool-Agnostic Phase 0](architecture/adr/adr_26028_tool_agnostic_phase_0_intent_synthesis.md) replace them with tool-independent definitions: reasoning-class models for synthesis, agentic-class for execution. The `aidx` framework was rewritten as the generic Multi-Phase AI Pipeline.
3. **Ecosystem Consolidation** — Research projects that added noise to the main repo were extracted to a dedicated monorepo ([ADR-26026: Dedicated Research Monorepo](architecture/adr/adr_26026_dedicated_research_monorepo_for_volatile.md)). The RFC-to-ADR promotion gate ([ADR-26025: RFC→ADR Workflow Formalization](architecture/adr/adr_26025_rfc_adr_workflow_formalization.md)) prevents premature decisions from becoming authoritative. `pyproject.toml` was formalized as the single source of truth for tool configuration ([ADR-26029: pyproject.toml as Tool Config Hub](architecture/adr/adr_26029_pyproject_toml_as_tool_config_hub.md)), eliminating scattered config files.

### Architecture Decisions

*   **[ADR-26025: RFC→ADR Workflow Formalization](architecture/adr/adr_26025_rfc_adr_workflow_formalization.md) — Promotion Gate**:
    Without a formal gate, proposed ADRs could be silently accepted without review. This ADR formalizes the workflow where proposed ADRs serve as living RFCs, and `check_adr.py` enforces promotion criteria before a status change is allowed. The feature was dogfooded during this very release: the promotion gate validated its own ADR-26025 alongside 5 other ADRs being promoted from proposed to accepted.

*   **[ADR-26027: Model Taxonomy](architecture/adr/adr_26027_model_taxonomy_reasoning_vs_agentic_class.md), [ADR-26028: Tool-Agnostic Phase 0](architecture/adr/adr_26028_tool_agnostic_phase_0_intent_synthesis.md) — Tool-Agnostic Model Taxonomy**:
    The original ADRs (26004–26008) named specific tools — Aider as the editor, Gemini Flash as the architect model. This coupling meant every tool change required an ADR amendment. ADR-26027 defines cognitive roles instead: reasoning-class models handle synthesis and planning, agentic-class models handle execution and structure. ADR-26028 redefines Phase 0 (Intent Synthesis) as tool-agnostic human-led discovery. The tools change; the cognitive model stays.

*   **[ADR-26029: pyproject.toml as Tool Configuration Hub](architecture/adr/adr_26029_pyproject_toml_as_tool_config_hub.md)**:
    Tool configuration was scattered across individual config files. ADR-26029 formalizes `pyproject.toml [tool.X]` sections as the canonical location for machine-readable tool configuration, loaded via `tomllib` (stdlib). This is the SSoT for commit conventions, validation rules, and script parameters.

*   **[ADR-26026: Dedicated Research Monorepo](architecture/adr/adr_26026_dedicated_research_monorepo_for_volatile.md)**:
    Research projects (e.g., `slm_from_scratch`) added volatility and noise to the main repository. This ADR extracts them to a dedicated monorepo — only distilled insights are retained in the hub.

*   **ADR Triage (26004–26008)**:
    [ADR-26004: Agentic RAG](architecture/adr/adr_26004_implementation_of_agentic_rag_for_autonom.md) and [ADR-26005: Aider as Primary Orchestrator](architecture/adr/adr_26005_formalization_of_aider_as_primary_agentic.md) rejected — too tool-specific for an evolving ecosystem. [ADR-26006: Agentic-Class Models for Architect Phase](architecture/adr/adr_26006_agentic_class_models_for_architect_phase.md), [ADR-26007: Phase 0 Intent Synthesis](architecture/adr/adr_26007_formalization_of_phase_0_intent_synthesi.md), [ADR-26008: Reasoning-Class Models for Abstract Synthesis](architecture/adr/adr_26008_reasoning_class_models_for_abstract_synt.md) superseded by ADR-26027 and ADR-26028, preserving the cognitive model while removing tool coupling.

*   **ADR Promotions**:
    6 ADRs promoted from proposed to accepted — [ADR-26015: Mandatory Sync-Guard & Diff Suppression](architecture/adr/adr_26015_mandatory_sync_guard_and_diff_suppression.md), [ADR-26017: ADR Format Validation Workflow](architecture/adr/adr_26017_adr_format_validation_workflow.md), [ADR-26020: Hub-and-Spoke Ecosystem](architecture/adr/adr_26020_hub_spoke_ecosystem_documentation.md), [ADR-26021: Content Lifecycle Policy](architecture/adr/adr_26021_content_lifecycle_policy_for_rag_consumed.md), [ADR-26022: GitHub Pages Hosting](architecture/adr/adr_26022_standardization_of_public_documentation_hosting.md), [ADR-26025: RFC→ADR Workflow](architecture/adr/adr_26025_rfc_adr_workflow_formalization.md) — marking the transition from exploratory proposals to authoritative architecture.

### New Features and Articles Added

*   **Documentation-as-Code Manifesto**:
    `architecture/manifesto.md` — the foundational document that articulates what this project is: a system where documentation is the primary input for AI agents, and therefore must be treated with the same engineering rigor as production code. This is not a new idea — it is the formalization of the principle the project has been building toward since v1.0. The README was fully rewritten to reflect this identity.

*   **Automated Commit Validation & CHANGELOG Generation**:
    Before this release, commit messages were unstructured and CHANGELOG was manually curated — a process that doesn't scale and produces inconsistent results. `validate_commit_msg.py` enforces conventional commit format with structured body bullets as a commit-msg hook (68 tests). `generate_changelog.py` parses that structured history into hierarchical, grouped CHANGELOG entries (56 tests). Both read configuration from `pyproject.toml [tool.commit-convention]`, making the commit convention machine-readable and centrally managed.

*   **Format-as-Architecture v0.2.0**:
    The original article established that serialization format affects LLM attention budget. v0.2.0 adds empirical evidence: runnable `{code-cell}` blocks measuring actual BPE token costs across 4 formats with `cl100k_base` and `o200k_base` tokenizers. Now the claims are verifiable, not theoretical.

*   **ADR Section Whitelist Enforcement**:
    As the ADR count grew, inconsistent section naming crept in (e.g., "Rationale" vs. "Decision Rationale"). The whitelist (defined in `adr_config.yaml`) enforces a canonical set of section names, with conditional support (e.g., "Rejection Rationale" only for rejected ADRs) and code-fence awareness to avoid false positives on example sections inside fenced blocks.

*   **HTML/MHTML Text Extraction**:
    Working with AI models means accumulating web chat transcripts (Gemini, Qwen, ChatGPT sessions saved as HTML/MHTML). `extract_html_text.py` extracts clean text from these files — a token-saving mechanism that lets you feed conversation history to another model without the HTML overhead (36 tests, 85% coverage).

*   **Superseded Annotation in ADR Index**:
    When [ADR-26006: Agentic-Class Models](architecture/adr/adr_26006_agentic_class_models_for_architect_phase.md) is superseded by [ADR-26027: Model Taxonomy](architecture/adr/adr_26027_model_taxonomy_reasoning_vs_agentic_class.md), the generated index now shows this relationship explicitly. Without this, readers had to open each ADR to discover its status — breaking the "index as overview" contract.

### Updates in Existing Files

*   **check_adr.py**: Gains section whitelist validation, conditional section checks, duplicate section detection, and promotion gate enforcement (154 tests, 96% coverage). The most significant evolution of this script since its creation in v2.4.0.

*   **configure_repo.py**: Now auto-installs the commit-msg hook via `--hook-type commit-msg` during repository setup. This ensures new contributors get commit validation from the first commit — no manual hook installation required.

*   **README.md**: Full structural rewrite with Documentation-as-Code framing, Architectural Governance section, Hub-and-Spoke Ecosystem description, and tool-agnostic Methodology. All tool/model name references removed in favor of cognitive-role language.

*   **CLAUDE.md**: Updated with new scripts (`validate_commit_msg.py`, `generate_changelog.py`), tool configuration conventions ([ADR-26029: pyproject.toml as Tool Config Hub](architecture/adr/adr_26029_pyproject_toml_as_tool_config_hub.md)), ADR index management rules, and de-emphasized tool-specific references.

*   **CI/CD**: `deploy.yml` gated to `main` branch only — previously, pushes to any branch could trigger deployment. `quality.yml` gains dedicated test jobs for `validate_commit_msg.py` and `generate_changelog.py`.

### Existing Files Moved or Renamed

| Original | New |
| :--- | :--- |
| `ai_system/4_orchestration/workflows/aidx_industrial_ai_orchestration_framework.md` | `multi_phase_ai_pipeline.md` (rewritten as tool-agnostic) |
| `misc/research/slm_from_scratch/` | Extracted to dedicated research monorepo ([ADR-26026: Dedicated Research Monorepo](architecture/adr/adr_26026_dedicated_research_monorepo_for_volatile.md)) |
| `BROKEN_LINKS_EXCLUDE_DIRS` (in `paths.py` + 10 files) | `VALIDATION_EXCLUDE_DIRS` |
| [ADR-26004: Agentic RAG](architecture/adr/adr_26004_implementation_of_agentic_rag_for_autonom.md), [ADR-26005: Aider as Primary Orchestrator](architecture/adr/adr_26005_formalization_of_aider_as_primary_agentic.md) | Rejected (tool-agnostic shift) |
| [ADR-26006: Agentic-Class Models](architecture/adr/adr_26006_agentic_class_models_for_architect_phase.md), [ADR-26007: Phase 0 Intent Synthesis](architecture/adr/adr_26007_formalization_of_phase_0_intent_synthesi.md), [ADR-26008: Reasoning-Class Models](architecture/adr/adr_26008_reasoning_class_models_for_abstract_synt.md) | Superseded by [ADR-26027: Model Taxonomy](architecture/adr/adr_26027_model_taxonomy_reasoning_vs_agentic_class.md), [ADR-26028: Tool-Agnostic Phase 0](architecture/adr/adr_26028_tool_agnostic_phase_0_intent_synthesis.md) |

## release v2.4.0 "The Governed Architecture"

### Summary of Changes

This release shifts the project from a curated knowledge base to a **self-governing documentation ecosystem**. Every architectural decision now carries machine-readable metadata, enabling automated quality gates, RAG-aware lifecycle management, and reproducible validation — the same rigor we apply to production code, now applied to the knowledge base itself.

Three strategic themes define v2.4.0:

1. **Governance** — 7 new ADRs (26016–26022) and a full migration of all existing records establish a metadata-driven lifecycle where decisions are queryable, filterable, and auditable by both humans and AI agents.
2. **Ecosystem extraction** — The vadocs validation engine graduated from an in-repo prototype to a standalone package, proving the hub-spoke model where this repo serves as the standards hub and extracted tools become independent spokes.
3. **Content quality** — A formal content lifecycle policy now ensures that outdated articles are retired rather than left to mislead RAG pipelines, while two new companion articles deepen the Context layer.

### New Features and Articles Added

*   **Machine-Readable ADR Governance**:
    Every ADR now carries YAML frontmatter with status, date, and tags — making the entire decision history searchable by AI agents and filterable in RAG pipelines. The new `check_adr.py` enforces this standard automatically, catching formatting drift before it reaches the main branch.

*   **Content Lifecycle Policy (ADR-26021)**:
    Superseded articles are now deleted rather than accumulating as stale context. This directly improves RAG retrieval quality — AI agents no longer surface outdated patterns when querying the knowledge base. Git history serves as the archive.

*   **Hub-Spoke Ecosystem (ADR-26020)**:
    Establishes this repository as the architectural standards hub. Extracted packages (like vadocs) maintain their own implementation decisions while inheriting ecosystem-wide conventions. This enables teams to adopt individual tools without importing the entire monorepo.

*   **vadocs — Documentation Validation Engine**:
    Completed its full lifecycle within this release: designed, scaffolded, tested, and [extracted to its own repository](https://github.com/lefthand67/vadocs). Validates ADR structure, frontmatter completeness, and MyST cross-references — the same checks that protect this repo, now available to any documentation project.

*   **GitHub Pages Hosting (ADR-26022)**:
    Replaces the self-hosted Podman/Traefik/Nginx stack with GitHub Pages. Eliminates infrastructure maintenance, improves uptime, and simplifies the deployment pipeline to a single `myst build --html` step in CI.

*   **Layer 5 — Context (New Articles)**:
    *   `reflected_metadata_pattern.md` — Explains why custom YAML fields vanish from the published site and how the reflected-metadata pattern preserves them for both humans and machines.
    *   `yaml_frontmatter_for_ai_enabled_engineering.md` — Practical guide to designing frontmatter schemas that serve documentation builds, RAG retrieval, and CI validation simultaneously.

*   **Layer 2 — Model (Rewrite)**:
    *   `choosing_model_size.md` rewritten as a VRAM budgeting guide — now covers KV Cache sizing, quantization trade-offs, and production deployment patterns (Verifier Cascade, Hybrid Routing) aligned with the `aidx` pipeline and Jan 2026 model landscape.

### Updates in Existing Files

*   **ADR Migration**: All 17 existing ADRs standardized with YAML frontmatter and consistent formatting. The ADR index is now partitioned by status (Active Architecture vs. Evolutionary Proposals), making it easier to distinguish proven decisions from proposals under evaluation.

*   **Cross-Reference Integrity**: Fixed broken MyST `{term}` references across 14 files. These caused silent build errors — terms like `ADR 26001` failed to resolve because the glossary uses hyphenated `ADR-26001`. The new `--check-terms` flag prevents future regressions.

*   **ADR-26019 Corrected**: The original decision described an HTML-anchor mechanism that was never implemented. Rewritten to formalize the positional pattern already in use across 20+ articles — documenting what actually works rather than aspirational infrastructure.

*   **CI/CD Pipeline**: Updated for the `check_adr_index.py` → `check_adr.py` transition. `misc/` excluded from broken-link validation to prevent false positives on planning documents.

*   **Development Standards (CLAUDE.md)**: Strengthened TDD guidance (tests-first, Red → Green → Refactor) and added non-brittle test quality standards — test the contract, not the implementation.

*   **Onboarding**: Updated with metadata conventions section so new contributors understand the frontmatter requirements from day one.

### Existing Files Moved or Renamed

| Original Path | New Path |
| :--- | :--- |
| `tools/scripts/check_adr_index.py` | `tools/scripts/check_adr.py` (Rewritten) |
| `tools/tests/test_check_adr_index.py` | `tools/tests/test_check_adr.py` (Rewritten) |
| `tools/docs/scripts_instructions/check_adr_index_py_script.md` | `tools/docs/scripts_instructions/check_adr_py_script.md` (Rewritten) |
| `packages/vadoc/*` | *Extracted to [github.com/lefthand67/vadocs](https://github.com/lefthand67/vadocs)* |
| `ai_system/4_orchestration/patterns/llm_usage_patterns.md` | *Deleted per ADR-26021 content lifecycle policy* |

## release v2.3.0 "The Validated Ecosystem"

### Summary of Changes

This release introduces a rigorous **"Semantic Notebook Versioning"** strategy, fundamentally changing how we handle Jupyter notebooks to make them AI-friendly and git-diff clean.

We have formalized the **"Script Suite"** concept (Code + Test + Doc) with automated enforcement to prevent documentation drift. Additionally, core tooling (`prepare_prompt`, `configure_repo`) has been refactored from Bash to Python for cross-platform reliability and better testability.

We also introduce **Just-in-Time prompt transformation** script to keep our repository clean of derivative artifacts, ensuring a Single Source of Truth (SSoT) for our prompt infrastructure.

### New Features and Articles Added

*   **Architecture & Standards**:
  *   **Semantic Notebook Pairing**: Adopted Jupytext to pair `.ipynb` files with `.md` files. This allows for clean git diffs and efficient LLM processing while preserving execution state. See `architecture/adr/adr_26014_semantic_notebook_pairing_strategy.md`.
  *   **Mandatory Script Suite**: Formalized the requirement that every utility script must have a corresponding test and documentation file, enforcedby CI. See `architecture/adr/adr_26011_formalization_of_mandatory_script_suite.md`.
  *   **JIT Prompt Transformation**: Moved from storing YAML prompts to generating them on-the-fly from JSON source of truth to prevent artifact drift. See `architecture/adr/adr_26013_just_in_time_prompt_transformation.md`.
  *   **Docs Validation Engine**: Proposed extraction of validation logic into a standalone package for reuse. See `architecture/adr/adr_26012_extraction_of_docs_validation_engine.md`.

*   **Performance & Execution**:
  *   Added `1_execution/hybrid_cpu_gpu_execution_and_kv_cache_offloading.md` for advanced optimization strategies.

*   **Tooling Ecosystem Overhaul**:
  *   `check_script_suite.py`: A new validator that enforces the 1:1:1 rule (Script, Test, Doc) and ensures documentation is co-staged with code changes.
  *   `check_adr_index.py`: Automates the maintenance of `architecture/adr_index.md`, ensuring all ADRs are indexed, ordered, and correctly linked.
  *   `check_link_format.py`: Enforces the rule that Markdown files should link to `.ipynb` files (not `.md`) when a pair exists, ensuring correct rendering in the documentation site.
  *   `prepare_prompt.py`: A Python rewrite of the prompt preparation tool, now supporting JSON, YAML, TOML, and Markdown inputs with auto-detection.
  *   `configure_repo.py`: A Python rewrite of the setup script, adding dry-run capabilities and better error handling for environment provisioning.
  *   `jupytext_sync.py` & `jupytext_verify_pair.py`: Updated to fully support the Semantic Notebook Pairing strategy, ensuring consistent synchronization and staging of paired files.

*   **Documentation**:
  *   Added comprehensive instructions for all new and refactored scripts in `tools/docs/scripts_instructions/`, including `prepare_prompt.py`, `configure_repo.py`, `check_script_suite.py`, `check_adr_index.py`, `check_link_format.py`, `jupytext_sync.py`, and `jupytext_verify_pair.py`.
  *   Added `docs_validation_engine_development_plan.md` outlining the roadmap for tooling extraction.

### Updates in Existing Files

*   **CI/CD & Quality**:
  *   Updated `.pre-commit-config.yaml` and `quality.yml` to include the new validators (`check_script_suite`, `check_adr_index`, `check_link_format`)and enhance existing checks.
  *   Enhanced `check_api_keys.py` with file exclusion lists to prevent false positives in test files.
  *   Updated `check_broken_links.py` to scan all Markdown files in CI, preventing regression when files are renamed.
  *   **Dependency Management**: Updated `pyproject.toml` and `uv.lock` to reflect new and updated project dependencies.

*   **Project Configuration**:
  *   Updated `CONVENTIONS.md` and `CLAUDE.md` to reflect the new MyST, Jupytext, and Script Suite guidelines, providing clearer instructions for AI assistants and developers.
  *   Updated `0_intro/00_onboarding.md` to streamline the setup process and reference the new `configure_repo.py` script.
  *   Refactored `ai_system/3_prompts/README.md` to align with the "Prompts-as-Infrastructure" approach, detailing the use of structured prompt files and the `prepare_prompt.py` script.
  *   Updated `tools/docs/jupyter_and_markdown/semantic_notebook_versioning_ai_ready_jupyter_docs.md` with detailed guidance on the new notebook pairing strategy, Git attributes, and pre-commit sync guards.
  *   Updated `tools/docs/scripts_instructions/README.md` to provide an overview of the new script suite and how to use the refactored Python scripts.

### Existing Files Moved or Renamed

| Original Path | New Path |
| :--- | :--- |
| `security/password_management/*` | `misc/in_progress/security/password_management/*` |
| `tools/docs/scripts_instructions/precommit_ci_validation_system.md` | `tools/docs/git/03_precommit_ci_validation_system.md` |
| `ai_system/3_prompts/prepare_prompt.sh` | `tools/scripts/prepare_prompt.py` (Refactored) |
| `tools/scripts/configure_repo.sh` | `tools/scripts/configure_repo.py` (Refactored) |

## v2.2.0 "The Hardened Foundation"

### Summary of Changes

This release focuses on 
- security hardening, 
- CI/CD infrastructure improvements, and 
- repository reorganization.

Key updates include:
- the introduction of automated API key and JSON validation, 
- comprehensive documentation for secret management (including Ansible Vault and Shamir's Secret Sharing), and 
- the adoption of Ansible and Molecule for infrastructure automation.

Research materials and prompt consultants have been relocated to better align with the project's layered architecture.

### New Features and Articles Added

* **Security & Secret Management**:
    * Added `security/password_management/` containing guides on Ansible Vault setup, Shamir's Secret Sharing for digital safes, and AES-256 standards (polish needed, though).
* **Automated Validation Tooling**:
    * Introduced `tools/scripts/check_api_keys.py` to detect and prevent secret leakage.
    * Introduced `tools/scripts/check_json_files.py` to ensure configuration file integrity.
    * Added comprehensive documentation and test suites for both new validation scripts.
* **Infrastructure as Code**:
    * Added `architecture/adr/adr_26009_adoption_of_ansible_for_idempotent_confi.md`.
    * Added `architecture/adr/adr_26010_adoption_of_molecule_for_automated_ansib.md`.
* **Prompt Infrastructure**:
    * Added `ai_system/3_prompts/layer_3_prompts_as_infrastructure.md` and `ai_system/3_prompts/prepare_prompt.sh` for automated prompt sanitization.

### Updates in Existing Files

* **CI/CD Pipeline**: Refactored `.github/workflows/quality.yml` into modular jobs with file-change detection and added Jupytext synchronization validation.
* **Onboarding**: Updated `0_intro/00_onboarding.md` with a high-level architectural overview and documentation structure reference.
* **Link Validation**:
    * Updated `tools/scripts/check_broken_links.py` to resolve the git root as a basename for cleaner reporting.
    * `.md` files are default now.
* **Conventions**: Updated `CONVENTIONS.md` to mandate atomic commits.
* **Documentation Rendering**: Updated `myst.yml` to exclude research files from the main documentation build.

### Existing Files Moved or Renamed

| Original Path | New Path |
| :--- | :--- |
| `research/slm_from_scratch/` | `misc/research/slm_from_scratch/` |
| `tools/prompt_helpers/` | `ai_system/3_prompts/consultants/` |
| `tools/templates/Release_Notes.tmpl` | `ai_system/4_orchestration/workflows/release_notes_generation/Release_Notes.tmpl` |
| `tools/scripts/release_notes_data.sh` | `ai_system/4_orchestration/workflows/release_notes_generation/release_notes_data.sh` |
| `tools/scripts/sync_and_verify.py` | *Removed (replaced by jupytext_sync.py)* |

## v2.1.0 "The Agentic Architect"

### **Summary of Changes**

The update includes

* a new naming convention for Architecture Decision Records (ADRs),
* enhanced automated linting for MyST include directives via `tools/scripts/check_broken_links.py`, and
* comprehensive documentation for connecting to LLMs via free-tier API keys.

One of the **major advancements** is the presentation of the `ai_system/4_orchestration/workflows/aidx_industrial_ai_orchestration_framework.md` called `aidx` ("aider extended"), transitioning toward a formal "Architect/Editor" model selection strategy where the Architect is a capable cloud model and the editor is the small local model.

Significant work was also done on repository stabilization, including fixing broken link detection and refining pre-commit hook logic in `.pre-commit-config.yaml`.

### **New Features and Articles Added**

The new ADRs are aimed at equipping the developer with the right tools for effective development workflow backed by AI tools.

* **Architecture Decision Records (ADRs)** in  `architecture/adr/`:
    * `adr_26004`: Implementation of Agentic RAG for Autonomous Knowledge Retrieval.
    * `adr_26005`: Formalization of Aider as the primary agentic editor.
    * `adr_26006`: Mandating Agentic-Class models (e.g., Gemini 3 Flash) for the Architect Phase.
    * `adr_26007`: Formalization of Phase 0: Intent Synthesis.
    * `adr_26008`: Selection of Reasoning-Class models for Abstract Synthesis.
    * `adr_index.md`: Created a centralized index for all architectural decisions.

The new articles support ADRs:

* **Model Selection & Orchestration** in `ai_system/`:
    * Added `2_model/selection/general_purpose_vs_agentic_models.md` article to guide model selection for Requirements Engineering vs. Implementation.
    * Added the `4_orchestration/workflows/aidx_industrial_ai_orchestration_framework.md` documentation, detailing the Research-Apply pipeline.

Other articles covering daily work of the developer:

* **Documentation & AI Tools** in `tools/docs/ai_agents/`:
    * New guide: `03_vim_ollama_llm_tab_completion_nuances.md` covering LLM-based tab completion.
    * New guide: `04_connect_to_capable_llms_using_api_keys.md` providing detailed setup and usage limits for Gemini, GROQ, and OpenRouter.

* **Tooling**:
    * Added `tools/templates/Release_Notes.tmpl` for standardized release documentation.
    * Added Aider-specific configuration files `tools/configs/aider.conf.yml`. This config is now added to `.gitignore` and is installed locally to the dev working tree via `tools/scripts/configure_repo.sh`.
    * Added `misc/pr/tg_channel_ai_learning/2026_01_12_release_announcement_v2_0_0.md` for external communications.

### **Updates in Existing Files**

* **Onboarding**: Updated `0_intro/00_onboarding.md` to include references to the new ADR structure and renamed sections to emphasize essential reading and AI tool proficiency.
* **Broken Link Script**:
    * Updated `tools/scripts/check_broken_links.py` to support MyST `{include}` directive validation.
    * Fixed nested directory exclusion logic and improved verbose logging in `tools/tests/test_check_broken_links.py`.
    * Integrated a global check in `.pre-commit-config.yaml` to ensure renamed files don't break external references.

* **Aider Handout**: Updated `tools/docs/ai_agents/02_aider_commands_handout.md` with OpenRouter integration, updated model flags, and usage limit tables.
* **Configurations**:
    * `pyproject.toml`: Added `pytest-cov` library.
    * `.aider.conf.yml`: Set `map-tokens: 2048` to optimize repository map limits.
    * `myst.yml`: Updated to exclude specific Aider convention files.
    * `uv.lock`: Updated dependencies.

### Existing Files Moved or Renamed

| Original Path | New Path |
| --- | --- |
| `aider.CONVENTIONS` | `CONVENTIONS.md` |
| `architecture/adr/adr_0001_use_of_python_and_oop_for_git_hook_scripts.md` | `architecture/adr/adr_26001_use_of_python_and_oop_for_git_hook_scripts.md` |
| `architecture/adr/adr_0002_adoption_of_pre_commit_framework.md` | `architecture/adr/adr_26002_adoption_of_pre_commit_framework.md` |
| `architecture/adr/adr_0003_adoption_of_gitlint_for_tiered_workflow.md` | `architecture/adr/adr_26003_adoption_of_gitlint_for_tiered_workflow.md` |
| `architecture/adr/0001-template.md` | `architecture/adr/adr_template.md` |


## v2.0.0

### Summary of Changes

This release focuses on a major architectural restructuring to improve the separation of concerns between core AI system documentation and the operational processes surrounding it. 

A primary **ai_system** directory has been established to house the layered documentation (Execution, Model, Infrastructure, etc.). 

Additionally, this update introduces enhanced CI/CD quality gates, improved repository configuration for local development, and formalizes the project's licensing structure.

### Major Structural Changes

#### File Tree Refactor (REFACTOR-MIGRATION)

* **AI Layered Docs Migration**: The core architectural layers have been moved to the `ai_system/` directory to decouple the "what" (AI logic) from the "how" (process/tooling).
    * `1_execution/` → `ai_system/1_execution/`
* **Operational Tooling Consolidation**: The developer's tools, helper prompts, internal scripts and tests have been reorganized under `tools/`.

All less important stuff like drafts and public relations materials moved to `misc/`.

### MLOps and Repository Tooling

#### CI/CD and Quality Assurance

* **Pre-commit Hooks**: Added local hooks for broken link validation and script testing .
* **GitHub Actions:**
    * **New Workflow**: `quality.yml` introduced to automate broken link checks on pull requests and commits using `pytest` and custom scripts .
    * **Deployment Improvements**: The `deploy.yml` workflow now includes mandatory environment integrity checks using `uv` and notebook synchronization verification with `jupytext` .

#### Developer Experience

* **Aider Handout Expanded:** "Aider Integration with LLMs Using API Keys" workflow introduced in [Aider Commands Handout](/ai_agents/guides/aider/aider_commands_handout.md).
* **Aider Configuration**: New `.aider.conf.yml` to automate Jupytext synchronization during AI-assisted coding sessions .
* **Deps updates**: New environment dependency added - `tiktoken` for analyzing token efficiency of our system prompts. 

### Changes to Existing Files

#### Licensing

* **LICENSE.md**: Updated to clarify the split-licensing model—GPLv3 for software/scripts and CC-BY-SA 4.0 for documentation/articles.


## v1.4.0

### Summary of Changes

This release significantly expands the **1_execution** and **4_orchestration** layers with deep-dives into high-performance computing standards (GEMM) and advanced MLOps architectural patterns. It also introduces a formal grounding of AI disciplines in alignment with ACM/IEEE curricula. A new GitHub Actions deployment workflow has been implemented to automate documentation builds using MyST.

### New Features and Articles Added

#### Foundation and Grounding

* **Directory**: `0_intro`
* **Articles**:
  *  `ai_systems_grounding_in_computing_disciplines.md`: Maps the AI lifecycle to global computing curricula standards.
  *  `ai_systems_grounding_in_computing_disciplines_diagram.png`: Visual representation of AI as a convergent layer of engineering and science.

#### Execution Layer (HPC Standards)

* **Directory**: `1_execution`
* **Articles**:
  *  `algebra_gemm_engineering_standard.md`:
    * Defines GEMM as the foundational standard for Deep Learning and HPC.
    * Includes detailed analysis of arithmetic intensity, tiling, and hardware-specific optimizations like Tensor Cores.

#### Orchestration and MLOps Workflows

* **Directory**: `4_orchestration/workflows`
* **Articles**:
  * `slm_backed_release_documentation_pipeline_architecture.md`: Describes modular processing and generation blocks for automated documentation.
  * `post-mortem_slm_non-determinism_in_commit_generation.md`: A critical analysis of why Small Language Models (1B-3B) struggle with high-frequency structured tasks in production.
  * `requirements_engineering_in_the_ai_era_the_gated_velocity.md`: Introduces the "Gated Velocity" pipeline for AI-assisted requirement flows.

#### Infrastructure and Tooling

* **Deployment**: Added `.github/workflows/deploy.yml` to automate MyST HTML builds and RSYNC deployment to production servers.
* **Scripts**: Added `md_check_broken_links.py` to maintain documentation integrity across the repository.

### Articles Moved or Renamed

To align with the new thematic structure, several files were reorganized:

| Original Path | New Path |
| --- | --- |
| `tools/vim/ai_tools_in_vim.md` | `tools/ai_agents/ai_tools_in_vim.md` |
| `tools/vim/handout_aider.md` | `tools/ai_agents/handout_aider.md` |
| `tools/python314_parallelism_game_changer.md` | `tools/languages/python314_parallelism_game_changer.md` |

### Improvements to Existing Content

* **ai_further_reading.md**: Updated with new sections for Small Language Models (SLMs) and modern agentic tools like CrewAI and Aider.
* **README.md**: Updated tree structure to reflect new specialized subdirectories in `tools/` and `4_orchestration/`.
* **Security Documentation**: Enhanced sections on OWASP Top-10 for LLMs and prompt injection mitigation.


## v1.3.0

### Summary of Changes
This release introduces several new articles and directories to enhance the documentation on MLOps workflows and Vim tools for AI-driven tasks. Additionally, it moves several existing articles to more appropriate locations.

### New Features and Articles Added

#### MLOps Workflows

- **Directory**: `mlops/workflows`
- **Articles**:
  - `git_three_major_workflows.md`: Provides a detailed comparison of three major Git workflows: Integration Manager, Gitflow, and GitHub Flow.

#### AI Tools for Vim

- **Directory**: `tools/vim`
- **Articles**:
  - `ai_tools_in_vim.md`: Describes how to set up Vim for AI-driven tasks using plugins like `gergap/vim-ollama` and CLI tools like Aider.
  - `handout_aider.md`: Provides a handout of essential Aider commands and usage instructions.

### Articles Moved

| Original Path | New Path |
| :--- | :--- |
| `2_model/training/python314_parallelism_game_changer.md` | `tools/python314_parallelism_game_changer.md` |
| `2_model/training/right_tool_for_right_layer.md` | `tools/right_tool_for_right_layer.md` |
| `2_model/training/why_rust_for_tokenizers.md` | `tools/why_rust_for_tokenizers.md` |
| `4_orchestration/patterns/llm_usage_patterns_p1.md` | `4_orchestration/patterns/llm_usage_patterns.md` |
| `4_orchestration/patterns/llm_usage_patterns_p2.md` | `2_model/selection/choosing_model_size.md` |

### Changes to Existing Files

#### README.md
- **Updated Structure**: The repository structure has been updated to reflect the new articles and directories added in version 1.3.0.

#### CHANGELOG
- **New Release Entry**: Added an entry for release 1.3.0 detailing the new articles, moved articles, and directory additions.


## v1.2.0

### Summary of Changes
This release introduces several new articles and directories to enhance the documentation on general AI systems, introductory materials, and orchestration patterns.

### New Features and Articles Added

#### General and Introductory Materials
- **Directory**: `0_intro`
- **Articles**:
  - `ai_systems_multilayer_approach.md`: Describes a multi-layered approach to building AI systems with DevSecOps considerations.

#### Orchestration Patterns
- **Directory**: `4_orchestration/patterns`
- **Articles**:
  - `llm_usage_patterns_p1.md`: Discusses the core distinctions between chats, workflows, and agents in AI.
  - `llm_usage_patterns_p2.md`: Explores model size considerations for chats, workflows, and agents, including Schema-Guided Reasoning (SGR).

### Changes to Existing Files

#### README.md
- **Updated Structure**: The repository structure has been updated to reflect the new articles and directories added in version 1.2.0.

#### CHANGELOG
- **New Release Entry**: Added an entry for release 1.2.0 detailing the new articles, moved articles, and directory additions.


## v1.1.0

### New Features and Articles Added

#### Model Training
- **Directory**: `2_model/training`
- **Articles**:
  - `custom_tokenizer_and_embedding.md`: Guide on creating custom tokenizers and embeddings.
  - `why_rust_for_tokenizers.md`: Discusses the benefits of using Rust for tokenizers.
  - `right_tool_for_right_layer.md`: Provides guidance on choosing the right tools for different layers in AI stack.
  - `python314_parallelism_game_changer.md`: Highlights the improvements in Python 3.14 for parallelism.


## v1.0.0

### Initial Release
- **Tree Structure Prepared**: The repository structure was prepared to accommodate new articles.
- **Articles Added**:
  - `nvidia_gpu_optimization.md` under `1_execution`.
  - `embeddings_for_small_llms.md` under `2_model`.


## v2.1.0

### **Summary of Changes**

The update includes

* a new naming convention for Architecture Decision Records (ADRs),
* enhanced automated linting for MyST include directives via `tools/scripts/check_broken_links.py`, and
* comprehensive documentation for connecting to LLMs via free-tier API keys.

One of the **major advancements** is the presentation of the `ai_system/4_orchestration/workflows/aidx_industrial_ai_orchestration_framework.md` called `aidx` ("aider extended"), transitioning toward a formal "Architect/Editor" model selection strategy where the Architect is a capable cloud model and the editor is the small local model.

Significant work was also done on repository stabilization, including fixing broken link detection and refining pre-commit hook logic in `.pre-commit-config.yaml`.

### **New Features and Articles Added**

The new ADRs are aimed at equipping the developer with the right tools for effective development workflow backed by AI tools.

* **Architecture Decision Records (ADRs)** in  `architecture/adr/`:
    * `adr_26004`: Implementation of Agentic RAG for Autonomous Knowledge Retrieval.
    * `adr_26005`: Formalization of Aider as the primary agentic editor.
    * `adr_26006`: Mandating Agentic-Class models (e.g., Gemini 3 Flash) for the Architect Phase.
    * `adr_26007`: Formalization of Phase 0: Intent Synthesis.
    * `adr_26008`: Selection of Reasoning-Class models for Abstract Synthesis.
    * `adr_index.md`: Created a centralized index for all architectural decisions.

The new articles support ADRs:

* **Model Selection & Orchestration** in `ai_system/`:
    * Added `2_model/selection/general_purpose_vs_agentic_models.md` article to guide model selection for Requirements Engineering vs. Implementation.
    * Added the `4_orchestration/workflows/aidx_industrial_ai_orchestration_framework.md` documentation, detailing the Research-Apply pipeline.

Other articles covering daily work of the developer:

* **Documentation & AI Tools** in `tools/docs/ai_agents/`:
    * New guide: `03_vim_ollama_llm_tab_completion_nuances.md` covering LLM-based tab completion.
    * New guide: `04_connect_to_capable_llms_using_api_keys.md` providing detailed setup and usage limits for Gemini, GROQ, and OpenRouter.

* **Tooling**:
    * Added `tools/templates/Release_Notes.tmpl` for standardized release documentation.
    * Added Aider-specific configuration files `tools/configs/aider.conf.yml`. This config is now added to `.gitignore` and is installed locally to the dev working tree via `tools/scripts/configure_repo.sh`.
    * Added `misc/pr/tg_channel_ai_learning/2026_01_12_release_announcement_v2_0_0.md` for external communications.

### **Updates in Existing Files**

* **Onboarding**: Updated `0_intro/00_onboarding.md` to include references to the new ADR structure and renamed sections to emphasize essential reading and AI tool proficiency.
* **Broken Link Script**:
    * Updated `tools/scripts/check_broken_links.py` to support MyST `{include}` directive validation.
    * Fixed nested directory exclusion logic and improved verbose logging in `tools/tests/test_check_broken_links.py`.
    * Integrated a global check in `.pre-commit-config.yaml` to ensure renamed files don't break external references.

* **Aider Handout**: Updated `tools/docs/ai_agents/02_aider_commands_handout.md` with OpenRouter integration, updated model flags, and usage limit tables.
* **Configurations**:
    * `pyproject.toml`: Added `pytest-cov` library.
    * `.aider.conf.yml`: Set `map-tokens: 2048` to optimize repository map limits.
    * `myst.yml`: Updated to exclude specific Aider convention files.
    * `uv.lock`: Updated dependencies.

### Existing Files Moved or Renamed

| Original Path | New Path |
| --- | --- |
| `aider.CONVENTIONS` | `CONVENTIONS.md` |
| `architecture/adr/adr_0001_use_of_python_and_oop_for_git_hook_scripts.md` | `architecture/adr/adr_26001_use_of_python_and_oop_for_git_hook_scripts.md` |
| `architecture/adr/adr_0002_adoption_of_pre_commit_framework.md` | `architecture/adr/adr_26002_adoption_of_pre_commit_framework.md` |
| `architecture/adr/adr_0003_adoption_of_gitlint_for_tiered_workflow.md` | `architecture/adr/adr_26003_adoption_of_gitlint_for_tiered_workflow.md` |
| `architecture/adr/0001-template.md` | `architecture/adr/adr_template.md` |


## v2.0.0

### Summary of Changes

This release focuses on a major architectural restructuring to improve the separation of concerns between core AI system documentation and the operational processes surrounding it. 

A primary **ai_system** directory has been established to house the layered documentation (Execution, Model, Infrastructure, etc.). 

Additionally, this update introduces enhanced CI/CD quality gates, improved repository configuration for local development, and formalizes the project's licensing structure.

### Major Structural Changes

#### File Tree Refactor (REFACTOR-MIGRATION)

* **AI Layered Docs Migration**: The core architectural layers have been moved to the `ai_system/` directory to decouple the "what" (AI logic) from the "how" (process/tooling).
    * `1_execution/` → `ai_system/1_execution/`
* **Operational Tooling Consolidation**: The developer's tools, helper prompts, internal scripts and tests have been reorganized under `tools/`.

All less important stuff like drafts and public relations materials moved to `misc/`.

### MLOps and Repository Tooling

#### CI/CD and Quality Assurance

* **Pre-commit Hooks**: Added local hooks for broken link validation and script testing .
* **GitHub Actions:**
    * **New Workflow**: `quality.yml` introduced to automate broken link checks on pull requests and commits using `pytest` and custom scripts .
    * **Deployment Improvements**: The `deploy.yml` workflow now includes mandatory environment integrity checks using `uv` and notebook synchronization verification with `jupytext` .

#### Developer Experience

* **Aider Handout Expanded:** "Aider Integration with LLMs Using API Keys" workflow introduced in [Aider Commands Handout](/ai_agents/guides/aider/aider_commands_handout.md).
* **Aider Configuration**: New `.aider.conf.yml` to automate Jupytext synchronization during AI-assisted coding sessions .
* **Deps updates**: New environment dependency added - `tiktoken` for analyzing token efficiency of our system prompts. 

### Changes to Existing Files

#### Licensing

* **LICENSE.md**: Updated to clarify the split-licensing model—GPLv3 for software/scripts and CC-BY-SA 4.0 for documentation/articles.


## v1.4.0

### Summary of Changes

This release significantly expands the **1_execution** and **4_orchestration** layers with deep-dives into high-performance computing standards (GEMM) and advanced MLOps architectural patterns. It also introduces a formal grounding of AI disciplines in alignment with ACM/IEEE curricula. A new GitHub Actions deployment workflow has been implemented to automate documentation builds using MyST.

### New Features and Articles Added

#### Foundation and Grounding

* **Directory**: `0_intro`
* **Articles**:
  *  `ai_systems_grounding_in_computing_disciplines.md`: Maps the AI lifecycle to global computing curricula standards.
  *  `ai_systems_grounding_in_computing_disciplines_diagram.png`: Visual representation of AI as a convergent layer of engineering and science.

#### Execution Layer (HPC Standards)

* **Directory**: `1_execution`
* **Articles**:
  *  `algebra_gemm_engineering_standard.md`:
    * Defines GEMM as the foundational standard for Deep Learning and HPC.
    * Includes detailed analysis of arithmetic intensity, tiling, and hardware-specific optimizations like Tensor Cores.

#### Orchestration and MLOps Workflows

* **Directory**: `4_orchestration/workflows`
* **Articles**:
  * `slm_backed_release_documentation_pipeline_architecture.md`: Describes modular processing and generation blocks for automated documentation.
  * `post-mortem_slm_non-determinism_in_commit_generation.md`: A critical analysis of why Small Language Models (1B-3B) struggle with high-frequency structured tasks in production.
  * `requirements_engineering_in_the_ai_era_the_gated_velocity.md`: Introduces the "Gated Velocity" pipeline for AI-assisted requirement flows.

#### Infrastructure and Tooling

* **Deployment**: Added `.github/workflows/deploy.yml` to automate MyST HTML builds and RSYNC deployment to production servers.
* **Scripts**: Added `md_check_broken_links.py` to maintain documentation integrity across the repository.

### Articles Moved or Renamed

To align with the new thematic structure, several files were reorganized:

| Original Path | New Path |
| --- | --- |
| `tools/vim/ai_tools_in_vim.md` | `tools/ai_agents/ai_tools_in_vim.md` |
| `tools/vim/handout_aider.md` | `tools/ai_agents/handout_aider.md` |
| `tools/python314_parallelism_game_changer.md` | `tools/languages/python314_parallelism_game_changer.md` |

### Improvements to Existing Content

* **ai_further_reading.md**: Updated with new sections for Small Language Models (SLMs) and modern agentic tools like CrewAI and Aider.
* **README.md**: Updated tree structure to reflect new specialized subdirectories in `tools/` and `4_orchestration/`.
* **Security Documentation**: Enhanced sections on OWASP Top-10 for LLMs and prompt injection mitigation.


## v1.3.0

### Summary of Changes
This release introduces several new articles and directories to enhance the documentation on MLOps workflows and Vim tools for AI-driven tasks. Additionally, it moves several existing articles to more appropriate locations.

### New Features and Articles Added

#### MLOps Workflows

- **Directory**: `mlops/workflows`
- **Articles**:
  - `git_three_major_workflows.md`: Provides a detailed comparison of three major Git workflows: Integration Manager, Gitflow, and GitHub Flow.

#### AI Tools for Vim

- **Directory**: `tools/vim`
- **Articles**:
  - `ai_tools_in_vim.md`: Describes how to set up Vim for AI-driven tasks using plugins like `gergap/vim-ollama` and CLI tools like Aider.
  - `handout_aider.md`: Provides a handout of essential Aider commands and usage instructions.

### Articles Moved

| Original Path | New Path |
| :--- | :--- |
| `2_model/training/python314_parallelism_game_changer.md` | `tools/python314_parallelism_game_changer.md` |
| `2_model/training/right_tool_for_right_layer.md` | `tools/right_tool_for_right_layer.md` |
| `2_model/training/why_rust_for_tokenizers.md` | `tools/why_rust_for_tokenizers.md` |
| `4_orchestration/patterns/llm_usage_patterns_p1.md` | `4_orchestration/patterns/llm_usage_patterns.md` |
| `4_orchestration/patterns/llm_usage_patterns_p2.md` | `2_model/selection/choosing_model_size.md` |

### Changes to Existing Files

#### README.md
- **Updated Structure**: The repository structure has been updated to reflect the new articles and directories added in version 1.3.0.

#### CHANGELOG
- **New Release Entry**: Added an entry for release 1.3.0 detailing the new articles, moved articles, and directory additions.


## v1.2.0

### Summary of Changes
This release introduces several new articles and directories to enhance the documentation on general AI systems, introductory materials, and orchestration patterns.

### New Features and Articles Added

#### General and Introductory Materials
- **Directory**: `0_intro`
- **Articles**:
  - `ai_systems_multilayer_approach.md`: Describes a multi-layered approach to building AI systems with DevSecOps considerations.

#### Orchestration Patterns
- **Directory**: `4_orchestration/patterns`
- **Articles**:
  - `llm_usage_patterns_p1.md`: Discusses the core distinctions between chats, workflows, and agents in AI.
  - `llm_usage_patterns_p2.md`: Explores model size considerations for chats, workflows, and agents, including Schema-Guided Reasoning (SGR).

### Changes to Existing Files

#### README.md
- **Updated Structure**: The repository structure has been updated to reflect the new articles and directories added in version 1.2.0.

#### CHANGELOG
- **New Release Entry**: Added an entry for release 1.2.0 detailing the new articles, moved articles, and directory additions.


## v1.1.0

### New Features and Articles Added

#### Model Training
- **Directory**: `2_model/training`
- **Articles**:
  - `custom_tokenizer_and_embedding.md`: Guide on creating custom tokenizers and embeddings.
  - `why_rust_for_tokenizers.md`: Discusses the benefits of using Rust for tokenizers.
  - `right_tool_for_right_layer.md`: Provides guidance on choosing the right tools for different layers in AI stack.
  - `python314_parallelism_game_changer.md`: Highlights the improvements in Python 3.14 for parallelism.


## v1.0.0

### Initial Release
- **Tree Structure Prepared**: The repository structure was prepared to accommodate new articles.
- **Articles Added**:
  - `nvidia_gpu_optimization.md` under `1_execution`.
  - `embeddings_for_small_llms.md` under `2_model`.
