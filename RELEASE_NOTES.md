# Release Notes

## release v3.1.0 "The Industrialization of Intelligence"

Since v3.0.0, the repository has transitioned from content establishment to **governed engineering and verifiable rigor.** The focus of v3.1.0 is the elimination of "casual" engineering in favor of governed, verifiable standards.

### 🛠️ The Primary Shift: AI-Native Development ("Code as Docs")
We've collapsed the gap between documentation and implementation by adopting the principle of **Code as Primary Documentation**.

*   **Contract Docstrings:** We replaced entire directories of separate instruction files with mandatory contract docstrings within every source file. 
*   **The Logic:** Since agents read code as fluently as prose, co-locating the "contract" (scope, public interface, design decisions) within the file ensures that documentation is CI-verified and refactoring-safe. This removes the "context window tax" of redundant prose and prevents agents from operating on stale instructions.

### 🧠 The Intelligence Layer: From Heuristics to Tradecraft
To move beyond the limitations of raw LLM generation, we integrated formal intelligence analysis techniques into our system prompts and orchestration.

*   **Heuer Intelligence Tradecraft:** To counter "autoregressive momentum"—the tendency of AI to converge on the first plausible hypothesis and simply agree with itself—we integrated Richard Heuer's methodology. By mandating the **Analysis of Competing Hypotheses (ACH)** and **disconfirmation**, we force the system to explore divergent paths and identify "linchpin" assumptions before reaching a conclusion.
*   **The WRC Metric (Self-Discipline Trigger):** We replaced "vibes-based" evaluation with the **Weighted Response Confidence (WRC)** metric. Rather than an external tool, WRC is a self-discipline trigger embedded in the generation phase. It forces the model to calculate confidence based on a weighted formula ($\text{WRC} = 0.35 \cdot \text{Evidence} + 0.25 \cdot \text{Alignment} + 0.40 \cdot \text{Probability}$), ensuring that high confidence is earned through evidence and adherence to constraints, not just linguistic fluency.

### 🏗️ The Governance Foundation: The Frontmatter Standard
We overhauled the repository's metadata system, moving from a fragmented, directory-based approach to a **Self-Describing Composable Block Standard**.

*   **The "Why":** Previously, validation scripts had to "guess" a file's type based on its folder. We replaced this with a system where documents define themselves using additive blocks: **Identity** (who/what), **Discovery** (intent/tags/cost), and **Lifecycle** (version/birth/date).
*   **Enabling Progressive Disclosure:** This structural shift is the prerequisite for **AI-Readability**. By isolating the "Discovery block," we enable agents to parse a file's intent and context cost without reading the entire document—a critical optimization for managing the attention budget.
*   **The Guardrail:** This standard is enforced by the `check_frontmatter.py` validation engine, acting as a Git guardrail that prevents metadata decay.
*   **The "Hidden" Win:** The massive effort of migrating hundreds of files to this standard served as a systemic audit. Forcing every metadata-touching script to handle the new schema revealed and purged dozens of latent bugs in YAML parsing and path handling, effectively **hardening our toolchain**.

### 🛡️ Operational Guardrails: Hard Constraints
As the system's complexity grew, we introduced "Hard Constraints" to eliminate high-impact, avoidable errors.

*   **Scripts as Instructors (JIT Feedback):** We transformed our validation scripts from simple "pass/fail" checks into active instructors. Instead of generic error messages, the scripts now provide **Just-In-Time (JIT) instructions**—telling the agent exactly what is wrong and how to fix it. This eliminates the costly "diagnostic loop" where agents waste time and tokens repeatedly reading the same files to figure out an error, often spiraling into cycles that require user intervention. By enforcing **Precise Targeting**, we ban dangerous "global cleanups" and require agents to map every single error to a specific fix and a specific file pair. This workflow improvement was rigorously tested on `gemma-4-31b-it` as part of our "no-vendor-lock-in" initiative, proving that governed instructions can compensate for lower-tier model reasoning.
*   **Safety Bans:** To protect the integrity of the Git history and CI/CD pipeline, we explicitly banned high-risk tools (`sed`, `git reset`) and the use of the `--no-verify` flag.

---
---

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

v2.6.0 explored an ambitious vision — agents as operating systems that discover and compose skills at runtime. That research produced valuable insights (4 analyses, 11 source artifacts, 7 ADRs), but the key finding was simpler than the vision: **what matters is not how many agents you have, but what each agent sees.** v2.7.0 distills this into a strategic pivot — context enginee... [truncated]