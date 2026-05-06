
---
title: pgvector as Ecosystem Database Standard
date: 2026-03-08
tags:
- context_management
- devops
options:
  token_size: 2741
  id: 26039
  status: proposed
  superseded_by: null
  type: adr
  version: 1.0.0
  birth: '2026-03-08'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: '<!-- Quality guidelines: /architecture/architecture_decision_workflow_guide.md
  -->.'
---
<!-- Quality guidelines: /architecture/architecture_decision_workflow_guide.md -->

# ADR-26039: pgvector as Ecosystem Database Standard

## Date
2026-03-08

## Status

proposed

## Context

[ADR-26038: Context Engineering as Core Design Principle](/architecture/adr/adr_26038_context_engineering_as_core_design_principle.md) establishes three-tier memory as the primary abstraction: working memory (context window), episodic memory (session history), and semantic memory (long-term knowledge in a vector store). The semantic and episodic tiers require a concrete storage decision: which database, how projects share it, and how vector and structured data coexist.

[ADR-26032: Tiered Cognitive Memory: Procedural Skills vs. Declarative RAG](/architecture/adr/adr_26032_tiered_cognitive_memory_procedural_skills.md) separates procedural knowledge (skills — high-density logic injected into the context window) from declarative knowledge (RAG — low-density facts retrieved on demand). The declarative tier needs a persistent store that supports semantic search. Pure RAG for everything is rejected there because vector search is probabilistic — but for declarative knowledge (books, articles, historical logs), RAG is the right retrieval strategy. This ADR decides where that RAG data lives.

The ecosystem comprises multiple projects — documentation hubs, agent applications, generated repositories, and future tools — that need persistent storage. Today these projects use ad-hoc file-based storage (JSON, YAML). There is no shared database, which means no cross-project search, no transactional guarantees, and no consistent data lifecycle.

### Evidence

`S-26009: Gemini — Local Git Repo RAG Setup with pgvector` documents a progression from simple RAG options (Open WebUI's built-in ChromaDB, Aider's repo map) to a server-side pgvector setup. The key finding: pgvector unifies structured and vector data in one database with ACID guarantees, SQL joins for metadata filtering, and schema-based isolation.

[A-26006: Agent Runtime Architecture and RAG Infrastructure Decisions](/architecture/evidence/analyses/A-26006_agent_runtime_architecture_rag_infrastructure.md) synthesizes this into a schema-per-project design and provides the scalability analysis:

- The pgvector performance ceiling commonly cited as "1M vectors" is per-index, not per-database — schema isolation keeps each index lean
- `halfvec` (half-precision vectors) cuts RAM usage by 2x without significant recall loss (verified via pgvector 0.7.0+ release notes per S-26011)
- `pgvectorscale` (Rust extension by TimescaleDB) improves Postgres vector search throughput at high recall levels
- Migration path to specialized vector DBs (Qdrant, Milvus) is possible via standard SQL export, though a validated ETL specification is needed for large-scale transfers

[A-26007: pgvector Viability Assessment and Logic Locality Decision](/architecture/evidence/analyses/A-26007_pgvector_viability_and_logic_locality.md) provides external peer review (S-26011, Gemini 3 Flash Thinking) confirming the approach as production-ready. The critical reframing: pgvector solves **referential drift** — the root cause of most RAG system failures, where vector stores and metadata databases fall out of sync. ACID guarantees within one database eliminate this category of bugs entirely.

[A-26005: Agentic OS Filesystem Architecture](/architecture/evidence/analyses/A-26005_doc_type_interfaces_unified_validation.md) establishes the Postgres namespace model: schemas map to logical namespaces (like filesystem mount points), providing isolation without the operational overhead of multiple database instances.

## Decision

We adopt **PostgreSQL with pgvector as the single database for all ecosystem storage needs**. One Postgres instance serves both structured data (session history, metadata, configuration) and vector data (document embeddings for RAG). This ADR is deployment-agnostic — Postgres may run as a system package (`apt`/`dnf`) or in a container; the deployment method is a separate decision.

### 1. Schema-Per-Project Isolation

Each ecosystem project gets its own Postgres schema:

```sql
CREATE EXTENSION vector;

-- Each project = one schema (logical namespace)
CREATE SCHEMA hub;           -- ai_engineering_book
CREATE SCHEMA project_alpha; -- any agent-created project

-- Document vectors for RAG
CREATE TABLE hub.doc_vectors (
    id serial PRIMARY KEY,
    file_path TEXT NOT NULL,
    content TEXT NOT NULL,
    commit_sha TEXT,
    embedding vector(768)  -- dimension matches embedding model
);

-- Structured data (session history, metadata) in the same database
CREATE TABLE project_alpha.session_history (
    id serial PRIMARY KEY,
    session_id UUID NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT now(),
    role TEXT NOT NULL,
    content TEXT NOT NULL
);
```

Schema isolation provides: independent HNSW index rebuilds per project, instant cleanup via `DROP SCHEMA CASCADE`, RBAC per project via Postgres roles, and cross-project search by querying across schemas.

### 2. Hybrid Search as Default Retrieval

RAG queries combine vector similarity and keyword matching in a single SQL query:

```sql
SELECT file_path, content,
       1 - (embedding <=> $1::vector) AS similarity,
       ts_rank(to_tsvector('english', content), plainto_tsquery('english', $2)) AS keyword_rank
FROM hub.doc_vectors
WHERE to_tsvector('english', content) @@ plainto_tsquery('english', $2)
ORDER BY 0.7 * (1 - (embedding <=> $1::vector))
       + 0.3 * ts_rank(to_tsvector('english', content), plainto_tsquery('english', $2)) DESC
LIMIT 10;
```

The weight balance (0.7 vector / 0.3 keyword) is a starting default, tunable per use case. Postgres's built-in `tsvector` provides keyword search without an additional service.

### 3. Configurable Embedding Model

The vector dimension (768 in examples) is tied to the embedding model. The ecosystem does not mandate a specific model:

- **Local (Ollama)**: `nomic-embed-text` (768 dimensions) — recommended starting point per S-26009
- **API-based**: provider-native embeddings via litellm abstraction
- **Constraint**: all vectors in a given table must share the same dimension; changing the model requires re-indexing that table. A dimension check at the application layer before INSERT is required to catch mismatches early (A-26007)

## Consequences

### Positive

- **Eliminates referential drift**: structured metadata and vector embeddings share the same transactional boundary — no orphaned vectors or inconsistent state after a crash (A-26007)
- **Single operational target**: one database to back up, monitor, and maintain — not a zoo of ChromaDB, SQLite, and JSON files across projects
- **SQL-native metadata**: unlike specialized vector DBs with limited "payload" fields, pgvector allows unlimited SQL joins, aggregations, and filtering alongside vector search. A single query can combine vector similarity with structured filters (date ranges, file types, project membership)
- **Schema isolation matches the ecosystem model**: each project maps to a Postgres schema, mirroring the namespace model from A-26005. Adding a new project is `CREATE SCHEMA`, not provisioning a new database
- **Clear migration path**: if any project outgrows pgvector, data exports to Qdrant/Milvus via standard SQL. The application code changes only the retrieval layer, not the storage schema

### Negative / Risks

- **Postgres operational knowledge required**: running Postgres requires understanding of VACUUM, WAL management, and backup strategies. **Mitigation**: the schema-per-project model means `DROP SCHEMA CASCADE` avoids VACUUM bloat from mass deletes. For high-churn vector tables, autovacuum parameters need explicit tuning (A-26007 identifies this as "The VACUUM Trap")
- **Single point of failure**: one database means one failure domain for all projects. **Mitigation**: for the local-first, single-user deployment model this is acceptable. `pg_dump` backups are standard practice. HA (replication, failover) is out of scope for the current ecosystem scale
- **HNSW index build time**: building the initial HNSW index on large document collections can take minutes. **Mitigation**: index creation is a one-time cost per table; incremental inserts update the index in real-time. As a project's schema exceeds 1M vectors, IVFFlat or pgvectorscale can reduce memory pressure (A-26007)
- **Embedding model lock-in per table**: changing the embedding model requires re-indexing all vectors in that table (dimension mismatch). **Mitigation**: schema isolation limits the blast radius — re-indexing one project doesn't affect others. A versioned embedding strategy is needed but deferred to implementation

## Alternatives

- **ChromaDB (embedded vector store).** Lightweight, zero-config, runs as a Python library. **Rejection Reason**: no structured data support — would require a separate database for session history and metadata, doubling operational complexity and reintroducing referential drift. No SQL joins for hybrid queries. Limited to <1M vectors with no clear scaling path.

- **Qdrant / Milvus (specialized vector databases).** Purpose-built for high-volume vector search with sub-10ms tail latency at billion-scale. **Rejection Reason**: overkill for the current ecosystem scale (thousands to low millions of vectors). Adds a separate service to maintain alongside whatever structured database we'd still need for non-vector data. Remains the migration target if pgvector is outgrown.

- **SQLite + sqlite-vss (embedded, no server).** Zero-deployment vector search in a file. **Rejection Reason**: no concurrent access from multiple projects/processes. No RBAC. No hybrid search with `tsvector`. Poor fit for a shared ecosystem database that multiple agents and tools connect to simultaneously.

- **Separate databases per project.** Each project runs its own Postgres instance. **Rejection Reason**: multiplied operational overhead (N backups, N monitoring targets, N upgrade cycles). No cross-project search. Schema isolation within one instance provides the same logical separation with a fraction of the maintenance cost.

- **ElasticSearch (document store with vector support).** Best-in-class keyword/BM25 search with mature vector capabilities. **Rejection Reason**: massive Java overhead for a local-first deployment. Complex vector configuration. The ecosystem needs SQL joins and ACID, not a search engine (A-26007).

## References

- [ADR-26038: Context Engineering as Core Design Principle](/architecture/adr/adr_26038_context_engineering_as_core_design_principle.md) — establishes three-tier memory model requiring semantic memory infrastructure
- [ADR-26032: Tiered Cognitive Memory: Procedural Skills vs. Declarative RAG](/architecture/adr/adr_26032_tiered_cognitive_memory_procedural_skills.md) — RAG as persistent store for declarative knowledge
- [A-26007: pgvector Viability Assessment and Logic Locality Decision](/architecture/evidence/analyses/A-26007_pgvector_viability_and_logic_locality.md) — external peer review confirming production-readiness, referential drift analysis, security constraints
- [A-26006: Agent Runtime Architecture and RAG Infrastructure Decisions](/architecture/evidence/analyses/A-26006_agent_runtime_architecture_rag_infrastructure.md) — schema-per-project design, scalability analysis, hybrid search pattern
- `S-26009: Gemini — Local Git Repo RAG Setup with pgvector` — primary evidence for pgvector selection
- `S-26011: Gemini — pgvector Viability Analysis and Client vs Server Logic Locality` — viability peer review
- [A-26005: Agentic OS Filesystem Architecture](/architecture/evidence/analyses/A-26005_doc_type_interfaces_unified_validation.md) — Postgres namespace model (schemas as logical mount points)
- {term}`ADR-26037` — Smallest Viable Architecture Constraint Framework (one DB, not many)

## Participants

1. Vadim Rudakov
2. Claude Opus 4.6
