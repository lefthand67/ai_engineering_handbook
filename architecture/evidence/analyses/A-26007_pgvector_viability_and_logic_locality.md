
---
title: pgvector Viability Assessment and Logic Locality Decision
date: 2026-03-09
tags:
- architecture
- context_management
- devops
options:
  token_size: 1930
  id: A-26007
  status: active
  sources:
  - S-26011
  produces:
  - ADR-26039
  type: analysis
  version: 1.0.0
  birth: '2026-03-09'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: ADR-26039 proposes pgvector as the ecosystem database standard.
---
# A-26007: pgvector Viability Assessment and Logic Locality Decision

## Problem Statement

ADR-26039 proposes pgvector as the ecosystem database standard. Before accepting, two questions require independent validation:

1. **Is the pgvector decision sound?** Are the claims about scalability, schema isolation, and migration paths verified or merely plausible?
2. **Where should agent logic run?** Python client-side or PL/pgSQL server-side? This determines the architecture of every agent in the ecosystem.

`S-26011: Gemini — pgvector Viability Analysis and Client vs Server Logic Locality` provides external peer review of ADR-26039 and a structured analysis of the logic locality question.

## Key Insights

### 1. pgvector Viability — Verified with Caveats

S-26011 uses a WRC (Weighted Response Confidence) scoring methodology specific to the Gemini consultation. The scores are not an ecosystem standard but provide a useful structured assessment. The breakdown for unified pgvector:

- **Empirical (0.92)**: Timescale and Supabase benchmarks show near-parity with specialized vector DBs for <10M vectors
- **Adoption (0.95)**: Industry standard across AWS, Azure, and Vercel for production RAG pipelines
- **Performance (0.90)**: Fits the Python/SQL/Podman stack with minimal complexity overhead

The core reframing: pgvector solves **referential drift** — the root cause of most RAG system failures, where vector stores and metadata databases fall out of sync. ACID guarantees within one database eliminate this category of bugs entirely.

**Verified claims from ADR-26039:**
- `halfvec` reduces RAM by 2x — verified via pgvector 0.7.0+ release notes
- SQL joins outperform metadata filtering in specialized vector DBs — verified; relational engines optimize complex predicates better than K-V filters

**Unverified claims requiring future validation:**
- Migration to Qdrant/Milvus is "straightforward" — requires a validated ETL specification, not just a claim
- Schema isolation handles HNSW scaling at >1M vectors — plausible but requires index-level performance profiling

### 2. The VACUUM Trap — Operational Risk

S-26011 identifies a hidden operational risk not covered in ADR-26039: vector updates create PostgreSQL "dead tuples." Without aggressive autovacuum tuning on vector tables, index scans degrade over time.

**Mitigation path**: The schema-per-project model helps — `DROP SCHEMA CASCADE` avoids gradual bloat from incremental deletes. For high-churn tables (e.g., session history with frequent updates), autovacuum parameters need explicit tuning.

### 3. Embedding Model Versioning Gap

ADR-26039 identifies the dimension lock-in risk but lacks a **Versioned Embedding Strategy**. If the ecosystem switches from `nomic-embed-text` (768d) to a different model, every table must be re-indexed. S-26011 also warns that litellm can return different dimensions depending on the provider — a strict dimension check at the application layer before INSERT is required.

### 4. Logic Locality — Client-Side Python with Server-Side Views

S-26011 frames this as a choice between:
- **Fat-Client/Thin-DB**: Python handles all logic, DB is passive storage
- **Thin-Client/Fat-DB**: PL/pgSQL handles context operations, Python is a thin wrapper

The WRC comparison:

| Approach | WRC | Best For |
|---|---|---|
| Client-Side (Python) | 0.938 | Default for AI agents — ecosystem tooling, testability, Git-native |
| Server-Side (PL/pgSQL) | 0.72 | Complex data aggregations, but vendor lock-in and debugging pain |
| Hybrid (Logic-in-View) | 0.89 | Production RAG — DB handles heavy retrieval, Python handles orchestration |

**Recommended pattern**: Python for the "thinking" (agent loop, LLM calls, context budgeting) and SQL Views/Stored Procedures for the "retrieval" (heavy vector search, hybrid queries). This is called the **Logic-in-View** pattern:

```sql
-- Server-side: define retrieval as a function
CREATE FUNCTION get_relevant_context(
    query_vector vector(768),
    keyword_query TEXT,
    result_limit INT DEFAULT 10
) RETURNS TABLE (file_path TEXT, content TEXT, score FLOAT) AS $$
    SELECT file_path, content,
           0.7 * (1 - (embedding <=> query_vector))
         + 0.3 * ts_rank(to_tsvector('english', content), plainto_tsquery('english', keyword_query))
    FROM doc_vectors
    WHERE to_tsvector('english', content) @@ plainto_tsquery('english', keyword_query)
    ORDER BY 3 DESC
    LIMIT result_limit;
$$ LANGUAGE SQL STABLE;
```

```python
# Client-side: Python calls the function, handles orchestration
results = cursor.execute(
    "SELECT * FROM get_relevant_context(%s, %s, %s)",
    [query_embedding, keyword_query, 10]
).fetchall()
```

**Key falsification from S-26011**: If the agent loop is "read once, think for 30 seconds, write once" (which matches the LLM call pattern), the PL/pgSQL latency advantage vanishes — the LLM inference time dominates by orders of magnitude.

### 5. Security Constraints

Two security requirements for any agent connecting to pgvector:

1. **RBAC per schema**: Each agent connects via a restricted Postgres role with `GRANT USAGE ON SCHEMA project_x TO agent_x`. No superuser connections.
2. **RAG content as untrusted input**: Retrieved context from the vector store must be treated as untrusted input — it may contain prompt injection payloads stored during indexing. Application-layer sanitization is required.

## Approach Evaluation

### What S-26011 Means for the Roadmap

| Decision | S-26011 Evidence | Action |
|---|---|---|
| **pgvector selection** | WRC 0.919, Production-Ready | Confirms ADR-26039 |
| **Logic locality** | Python client + Logic-in-View pattern | Informs the planned server-side vs client-side ADR |
| **Embedding versioning** | Gap identified | Add to ADR-26039 Consequences or track as tech debt |
| **VACUUM management** | Operational risk | Document in operational runbooks |
| **Security model** | RBAC + input sanitization | Inform security ADR or add to ADR-26039 |

### Open Questions

1. **Dimensionality stress test**: S-26011 recommends deploying pgvector with the current ai_engineering_book content and measuring RAM delta between flat scan and HNSW index. This would provide real empirical data for the ecosystem's actual scale.

2. **Connection pooling**: For agents that make rapid DB calls, pgbouncer or a persistent psycopg pool is needed. This is an implementation detail, not an architectural decision — but it should be documented in the operational runbooks.

3. **Migration tooling**: The Logic-in-View pattern requires tracking SQL views/functions in Git. S-26011 suggests Alembic or yoyo-migrations. This needs evaluation against the ecosystem's existing tooling (uv, pre-commit hooks).

## References

### Internal
- [ADR-26039: pgvector as Ecosystem Database Standard](/architecture/adr/adr_26039_pgvector_as_ecosystem_database_standard.md)
- [ADR-26038: Context Engineering as Core Design Principle](/architecture/adr/adr_26038_context_engineering_as_core_design_principle.md)
- [A-26006: Agent Runtime Architecture and RAG Infrastructure Decisions](/architecture/evidence/analyses/A-26006_agent_runtime_architecture_rag_infrastructure.md)
- `S-26011: Gemini — pgvector Viability Analysis and Client vs Server Logic Locality`

### External
- pgvector — PostgreSQL vector similarity search extension, https://github.com/pgvector/pgvector
- The Case for Unified Databases in AI — Timescale, 2025, https://www.timescale.com/blog/postgresql-as-a-vector-database/
- Designing Data-Intensive Applications — Martin Kleppmann, 2017
- Psycopg 3 Documentation — https://www.psycopg.org/psycopg3/docs/
