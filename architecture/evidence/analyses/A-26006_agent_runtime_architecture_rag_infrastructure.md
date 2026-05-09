
---
title: Agent Runtime Architecture and RAG Infrastructure Decisions
date: 2026-03-08
tags:
- architecture
- context_management
- model
options:
  token_size: 2925
  id: A-26006
  status: active
  sources:
  - S-26008
  - S-26009
  - S-26010
  produces: []
  type: analysis
  version: 1.0.0
  birth: '2026-03-08'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: The ecosystem roadmap (`misc/plan/implemented/plan_20260308_ecosystem_roadmap_vadocs_to_mentor.md`)
  defines a three-phase path from governance tooling (vadocs) to a production mentor
  agent.
---
# A-26006: Agent Runtime Architecture and RAG Infrastructure Decisions

## Problem Statement

The ecosystem roadmap (`misc/plan/implemented/plan_20260308_ecosystem_roadmap_vadocs_to_mentor.md`) defines a three-phase path from governance tooling (vadocs) to a production mentor agent. Phase 2 (Runtime) requires concrete decisions about agent architecture, RAG infrastructure, and tool integration. Three Gemini dialogues (S-26008, S-26009, S-26010) provide external validation and implementation patterns for these decisions. This analysis extracts the actionable insights that inform Phase 2 ADRs and implementation.

## Key Insights

### 1. The Master Loop Pattern — Production Agent Architecture

S-26008 documents Claude Code's internal architecture, codenamed the "n0" master loop:

```python
while True:
    response = llm.completion(messages=messages, tools=tools)
    if not response.tool_calls:
        return response.content  # Done — no more tool calls
    for tool_call in response.tool_calls:
        result = execute(tool_call)
        messages.append(tool_result)
    # Loop: LLM sees tool output and decides next action
```

Key architectural properties:
- **Single-threaded**: One agent, one loop, no multi-agent coordination
- **Flat context**: Direct message history, not chained abstractions
- **Tool-driven exit**: The loop runs while the LLM calls tools; it stops when the LLM returns text
- **Context compaction**: When history grows too long, older parts are summarized (not discarded)
- **Note-taking**: The agent maintains a separate "scratchpad" of goals alongside the message history

This validates [ADR-26038](/architecture/adr/adr_26038_context_engineering_as_core_design_principle.md) — single-agent with skill dispatch is exactly how Claude Code ($1B run-rate) works. The "skills" in Claude Code are filesystem-based directories containing SKILL.md + executable scripts, read on demand via standard Bash commands.

**Implication for mentor_generator**: The existing three-stage pipeline (collect → create → compile) should evolve into a master loop where skills are loaded on demand. The loop structure is: prompt user → LLM decides which skill/tool to invoke → execute → feed result back → repeat.

### 2. litellm + MCP — The Tool Integration Stack

S-26008 recommends the combination of litellm (model abstraction) + MCP (tool standardization):

- **litellm** replaces LangChain for model connectivity. The mentor_generator already uses litellm — this is validated as production-grade
- **MCP via FastMCP** wraps custom scripts as standardized tool servers. Instead of hardcoding tool definitions, each tool becomes an MCP server with auto-generated JSON schemas
- **Configuration-based registration**: Tools are defined in a config YAML, not in code. The master loop discovers tools from config at startup

This means the mentor_generator's tools (RAG retriever, web search, file I/O) should be wrapped as MCP servers. The master loop calls litellm with tools registered from MCP config. This achieves the separation of concerns: the loop is generic, the skills are pluggable.

**Counterpoint**: [A-26009 (Compass)](/architecture/evidence/analyses/A-26009_compass_realistic_state_of_agentic_ai_2026.md) warns that MCP has real security vulnerabilities (CVE-2025-6514, 36% skill flaw rate). For local-first deployment this is less critical (no remote servers), but the permission model should still be considered.

### 3. pgvector Architecture — Schema-Per-Repo Design

S-26009 provides the concrete RAG architecture that feeds ADR-26039 (pgvector as ecosystem standard):

**Schema design**:
```sql
CREATE EXTENSION vector;
-- One schema per repo (logical isolation, independent indexing)
CREATE SCHEMA ai_engineering_book;
CREATE TABLE ai_engineering_book.doc_vectors (
    id serial PRIMARY KEY,
    file_path TEXT,
    content TEXT,
    commit_sha TEXT,
    embedding vector(768)  -- nomic-embed-text dimensions
);
```

**Why schema-per-repo over one table**:
- **Isolated re-indexing**: Rebuilding the HNSW index for one repo doesn't lock or affect others
- **Instant cleanup**: `DROP SCHEMA repo_x CASCADE;` physically removes data and indexes immediately (no VACUUM bloat)
- **RBAC**: Agent can be restricted to specific schemas via standard Postgres roles
- **Cross-repo search**: Remove the `WHERE` clause to search across all repos

**Scalability reality (2026)**:
- The "1M vector limit" is per-index, not per-database. With schema-per-repo, each index stays lean
- `halfvec` (half-precision) cuts RAM usage by 2x without significant recall loss
- `pgvectorscale` (Rust extension) now allows Postgres to outperform Qdrant in QPS at 99% recall
- Postgres handles 50M+ vectors in production with these optimizations
- The real bottleneck: embedding model latency (~300ms via Ollama) dwarfs vector search (~5ms)

**Migration path**: If pgvector is ever outgrown (>10M vectors per repo), exporting to Qdrant/Milvus is a straightforward ETL — the data is clean SQL, not a proprietary format.

**Embedding model**: S-26009 recommends `nomic-embed-text` — an open-source embedding model by Nomic AI that produces 768-dimensional vectors and runs locally via Ollama. It was trained for long-context text and code retrieval. This recommendation needs independent verification against current alternatives (e.g., Snowflake Arctic, BGE-M3, Jina) before standardization. For API-based embedding, litellm can abstract the provider.

### 4. Auto-Updating RAG — Git-Triggered Sync

S-26009 describes the sync mechanism for keeping the vector store current:

- **Watchdog pattern**: A background process monitors the repo for file changes (git hooks or `watchdog` library)
- **Incremental updates**: Only re-chunks and re-embeds modified files, not the entire repo
- **Git commit tracking**: Each vector row stores `commit_sha` to detect what's changed since last sync
- **Hybrid search**: pgvector similarity (`<=>` cosine distance) + `tsvector` keyword search in one SQL query

**Implication for the ecosystem**: The RAG sync can be triggered by:
1. A post-commit git hook (immediate, per-commit)
2. A Podman sidecar container running a watcher (continuous)
3. A CLI command (`vadocs index` or similar) for manual re-indexing

### 5. JIT Context Injection — Stateless Agent Pattern

S-26010 validates the JIT (Just-In-Time) context injection pattern formalized in [ADR-26030](/architecture/adr/adr_26030_stateless_jit_context_injection_for_agentic_git_workflow.md):

- **Zero chat history**: The agent session is destroyed after every invocation
- **State from SSoT**: The prompt is assembled fresh from `git status --short` + `git diff --cached` + `pyproject.toml [tool.commit-convention]`
- **Token economy**: 70-90% reduction versus stateful sessions (O(n) vs O(n^2) token growth)
- **Pure function model**: `f(Git State, Config) → Structured Commit` — deterministic, traceable, reproducible

This pattern is specific to git operations (where the "state" is fully captured by git CLI output), but the principle generalizes to the mentor agent:

- The **interview skill** is JIT: prompt assembled from question config + previous answers
- The **research skill** is JIT: prompt assembled from topic + search results
- The **generation skill** is JIT: prompt assembled from template + answers + research context
- The **mentor skill** is stateful (needs session continuity) but with JIT context injection from RAG + course_history

The JIT pattern is the default; statefulness is the exception that requires justification — consistent with [ADR-26038](/architecture/adr/adr_26038_context_engineering_as_core_design_principle.md).

### 6. Why Not LangChain

S-26008 provides a clear rejection rationale for LangChain that strengthens the Alternatives section of ADR-26038:

- Big companies (Anthropic, OpenAI) do not use high-level LangChain for flagship products
- The "Black Box" problem: framework internals strip context or format prompts in non-transparent ways
- 45% of LangChain users never deployed to production (corroborated by [A-26009](/architecture/evidence/analyses/A-26009_compass_realistic_state_of_agentic_ai_2026.md) Adaline analysis)
- litellm replaces LangChain's model abstraction without the orchestration overhead
- LangGraph (low-level sibling) is production-viable but adds complexity the ecosystem doesn't need

The validated stack: **litellm (models) + FastMCP (tools) + custom master loop (orchestration) + pgvector (memory)**.

## Approach Evaluation

### What These Sources Mean for the Roadmap

| Roadmap Step | Source Evidence | Decision |
|---|---|---|
| **2.1 Skill dispatcher** | S-26008: n0 master loop pattern | Master loop with litellm + MCP tool registration |
| **2.2 Context management** | S-26010: JIT injection, S-26008: context compaction | JIT default, stateful exception; token counting via litellm |
| **2.3 pgvector + Podman** | S-26009: schema-per-repo, halfvec, pgvectorscale | Single Postgres, schema-per-repo, nomic-embed-text |
| **2.4 RAG indexer** | S-26009: watchdog sync, incremental updates | Git hook or sidecar watcher, commit_sha tracking |
| **2.5 Tool integration** | S-26008: FastMCP server wrapping | Wrap tools as MCP servers, register in config |

### Open Questions

1. **MCP security for local deployment**: [A-26009](/architecture/evidence/analyses/A-26009_compass_realistic_state_of_agentic_ai_2026.md) documents serious MCP vulnerabilities. For local-first Podman deployment, the attack surface is smaller, but we should still design a permission model for tool access. Defer to Phase 2 implementation.

2. **Embedding model choice**: `nomic-embed-text` is recommended for local Ollama setups. For API-based embedding (when using capable cloud LLMs), litellm can abstract the provider. The choice should be configurable per deployment — local users get nomic, API users get model-native embeddings.

3. **RAG sync granularity**: Should the indexer chunk by file, by function/class, or by semantic section? Code-aware splitting (by function/class) requires language-specific parsers. Document-aware splitting (by `##` headers) is simpler for the documentation-heavy ecosystem. Start with document-level, evolve to code-level when needed.

## References

### Internal
- [ADR-26038: Context Engineering as Core Design Principle](/architecture/adr/adr_26038_context_engineering_as_core_design_principle.md)
- [ADR-26030: Stateless JIT Context Injection for Agentic Git Workflows](/architecture/adr/adr_26030_stateless_jit_context_injection_for_agentic_git_workflow.md)
- `misc/plan/plan_20260308_ecosystem_roadmap_vadocs_to_mentor.md` — Phase 2 decisions
- [A-26005: Agentic OS Filesystem Architecture](/architecture/evidence/analyses/A-26005_doc_type_interfaces_unified_validation.md) — Postgres namespace model
- [Format as Architecture: Signal-to-Noise in Prompt Delivery](/ai_system_layers/3_prompts/format_as_architecture_signal_noise_in_prompt_delivery.ipynb)
- `S-26008: Gemini — LangChain vs Production Agent Architecture`
- `S-26009: Gemini — Local Git Repo RAG Setup with pgvector`
- `S-26010: Gemini — Stateless JIT Context Injection for Agentic Git Workflows`

### External
- Claude Code "n0" master loop — Anthropic technical disclosures
- Model Context Protocol (MCP) — Anthropic, now under Linux Foundation AAIF
- FastMCP — High-level MCP server library
- pgvector — PostgreSQL vector similarity search extension
- pgvectorscale — TimescaleDB Rust-based pgvector acceleration
- nomic-embed-text — Nomic AI embedding model (Ollama-native)
- litellm — Universal LLM API abstraction
