---
id: 26041
title: Client-Side Logic with Server-Side Retrieval
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Separates agent logic (client) from data retrieval (server) to minimize latency and token overhead.
tags:
- architecture
date: 2026-03-09
options:
  type: adr
  birth: '2026-03-09'
  version: 1.0.0
  token_size: 1963
  status: proposed
  superseded_by: null
---
<!-- Quality guidelines: /architecture/architecture_decision_workflow_guide.md -->

# ADR-26041: Client-Side Logic with Server-Side Retrieval

## Date
2026-03-09

## Status

proposed

## Context

[ADR-26039: pgvector as Ecosystem Database Standard](/architecture/adr/adr_26039_pgvector_as_ecosystem_database_standard.md) establishes PostgreSQL with pgvector as the single database for all ecosystem storage. [ADR-26038: Context Engineering as Core Design Principle](/architecture/adr/adr_26038_context_engineering_as_core_design_principle.md) defines the agent as a single-agent context manager that orchestrates retrieval, reasoning, and action.

With the database chosen, the next architectural question is: **where should the agent's logic execute?** Three options exist:

1. **Fat-Client / Thin-DB**: Python handles everything — query construction, retrieval orchestration, scoring, and ranking. The database is passive storage.
2. **Thin-Client / Fat-DB**: PL/pgSQL stored procedures handle context operations — hybrid search, scoring, ranking, session management. Python is a thin wrapper.
3. **Hybrid (Logic-in-View)**: Python handles orchestration (agent loop, LLM calls, context budgeting). SQL stored functions handle computationally expensive retrieval (vector search, hybrid scoring).

This decision impacts every agent in the ecosystem, starting with the mentor_generator application.

### Existing Infrastructure

The ecosystem already has a `postgres_connector` module — a psycopg-based Python library used across database projects. It provides connection management, safe query construction via `psycopg.sql`, table lifecycle operations (create, drop, dump), and CRUD helpers with SQL injection prevention. The module operates on the `public` schema and does not yet support schema-per-project isolation or pgvector operations, but it validates the client-side Python pattern as the ecosystem's established approach to database interaction.

### Evidence

[A-26007: pgvector Viability Assessment and Logic Locality Decision](/architecture/evidence/analyses/A-26007_pgvector_viability_and_logic_locality.md) provides a structured comparison based on `S-26011` (Gemini 3 Flash Thinking analysis):

- **Client-Side Python** scores highest for ecosystem fit (testability, Git-native code, compatibility with pytest/litellm/pre-commit tooling)
- **Server-Side PL/pgSQL** scores highest for data-local computation but introduces vendor lock-in, debugging complexity, and version control friction
- **Hybrid Logic-in-View** captures most of the server-side performance benefit while keeping orchestration logic in Python

The critical falsification from S-26011: if the agent loop is "read once, think for 30 seconds, write once" — which matches the LLM call pattern — the PL/pgSQL latency advantage vanishes. LLM inference time dominates by orders of magnitude over database round-trip savings.

[A-26006: Agent Runtime Architecture and RAG Infrastructure Decisions](/architecture/evidence/analyses/A-26006_agent_runtime_architecture_rag_infrastructure.md) establishes the master loop pattern where the agent's cycle is: retrieve context → inject into prompt → call LLM → act on response. The retrieval step is the only database-intensive operation; the rest is Python orchestration.

## Decision

We adopt the **Logic-in-View pattern**: Python handles all agent orchestration, and SQL stored functions encapsulate computationally expensive retrieval operations.

### 1. Python Owns the Agent Loop

All orchestration logic — context budgeting, LLM calls, skill dispatch, session management, error handling — lives in Python application code. This code is version-controlled in Git, tested with pytest, and follows ecosystem conventions (pathlib, top-down design, TDD).

### 2. SQL Functions Encapsulate Retrieval

Database-intensive operations — hybrid vector+keyword search, cross-schema queries, scored ranking — are defined as SQL stored functions. These functions are:
- Called from Python via `psycopg` (the ecosystem's Postgres driver per A-26007)
- Tracked in Git alongside application code
- Managed via a migration tool (implementation detail, deferred)

### 3. Boundary Rule

The boundary between Python and SQL follows one principle: **if the operation benefits from set-based processing close to the data, it belongs in a SQL function; everything else stays in Python.** Concretely:
- Vector similarity search with hybrid scoring → SQL function
- Context window token budgeting → Python
- Session history aggregation across schemas → SQL function
- LLM prompt construction and response parsing → Python
- RBAC enforcement → SQL (Postgres roles and grants)

## Consequences

### Positive

- **Testability**: agent logic is testable with standard Python tooling (pytest, mocks, fixtures) — no database required for unit tests of orchestration code
- **Ecosystem alignment**: Python code follows existing conventions (pathlib, TDD, pre-commit hooks) without introducing PL/pgSQL as a second development language
- **Performance where it matters**: hybrid search scoring executes inside Postgres, avoiding the transfer of raw vectors to the client for scoring — only ranked results cross the wire
- **Version-controlled SQL**: stored functions tracked in Git alongside the application code that calls them, maintaining the ecosystem's "everything in Git" principle
- **Debuggability**: Python orchestration is inspectable with standard debugging tools; SQL functions are independently testable via `psql`

### Negative / Risks

- **Migration tooling needed**: SQL stored functions must be versioned and applied consistently across environments. A migration tool (Alembic, yoyo-migrations, or raw SQL files) is needed but not yet selected. **Mitigation**: deferred to implementation phase; the pattern works regardless of which migration tool is chosen
- **Two languages in the codebase**: developers need SQL literacy for retrieval functions. **Mitigation**: the SQL surface is intentionally small — only retrieval functions, not business logic. The ecosystem already uses SQL in ADR-26039 examples
- **Function signature coupling**: Python callers depend on SQL function signatures. **Mitigation**: functions are versioned via migrations; signature changes require explicit migration steps, preventing silent breakage

## Alternatives

- **Pure Client-Side (Fat-Client).** All logic in Python, including query construction and scoring. **Rejection Reason**: transfers raw vectors to the client for scoring, increasing network overhead and memory usage. Hybrid search requires multiple round-trips (one for vector similarity, one for keyword ranking, then client-side merge). The performance cost is small at low scale but grows linearly with corpus size.

- **Pure Server-Side (Fat-DB).** All agent logic in PL/pgSQL stored procedures, including session management and context budgeting. **Rejection Reason**: PL/pgSQL is not designed for orchestration logic — no native HTTP client for LLM API calls, no package ecosystem for token counting, no integration with pytest or pre-commit. Creates vendor lock-in to PostgreSQL internals. Debugging stored procedures is significantly harder than debugging Python code. The latency advantage is irrelevant when LLM inference dominates (A-26007).

- **ORM-Mediated (SQLAlchemy / Django ORM).** Python ORM generates SQL queries, abstracting the database layer. **Rejection Reason**: ORMs add complexity without benefit for the ecosystem's use case. The SQL surface is small (a few stored functions), and direct `psycopg` calls provide more control over query execution plans. ORM-generated queries for hybrid vector+keyword search are often suboptimal compared to hand-tuned SQL.

## References

- [ADR-26039: pgvector as Ecosystem Database Standard](/architecture/adr/adr_26039_pgvector_as_ecosystem_database_standard.md) — establishes the database; this ADR decides how application code interacts with it
- [ADR-26038: Context Engineering as Core Design Principle](/architecture/adr/adr_26038_context_engineering_as_core_design_principle.md) — single-agent context management model that this ADR implements
- [A-26007: pgvector Viability Assessment and Logic Locality Decision](/architecture/evidence/analyses/A-26007_pgvector_viability_and_logic_locality.md) — primary evidence: WRC comparison, Logic-in-View pattern, LLM latency dominance falsification
- [A-26006: Agent Runtime Architecture and RAG Infrastructure Decisions](/architecture/evidence/analyses/A-26006_agent_runtime_architecture_rag_infrastructure.md) — master loop pattern, JIT context injection
- `S-26011: Gemini — pgvector Viability Analysis and Client vs Server Logic Locality` — source data for A-26007

## Participants

1. Vadim Rudakov
2. Claude Opus 4.6
