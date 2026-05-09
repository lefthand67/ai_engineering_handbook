
---
title: MemPalace Role Clarification — Development Memory vs. Application Memory
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: 'MemPalace is unsuitable for mentor_generator application memory (WRC
  0.290) but valuable as development conversation memory. The clean ecosystem split:
  pgvector for course materials, ADRs for decisions, MemPalace for the reasoning that
  didn''t make it into formal artifacts.'
tags:
- context_management
- architecture
date: '2026-04-08'
options:
  type: analysis
  birth: '2026-04-08'
  version: 1.0.0
  token_size: 2132
  id: A-26023
  status: active
  sources:
  - S-26022
  produces: []
---
# MemPalace Role Clarification — Development Memory vs. Application Memory

**Analysis date:** 2026-04-08
**Source:** `S-26022_mempalace_framework_assessment.md`

## Problem Statement

The user encountered MemPalace in `ai_agents/agents_source_code/` and asked whether it could serve as the context management system for mentor_generator — specifically for storing books, articles, and video lecture transcripts that mentors retrieve from during sessions.

Through 10 exchanges, the dialogue evolved through four distinct phases:
1. Understanding what MemPalace is and how it works
2. Recognizing the structural similarity to the existing frontmatter 3-tier system
3. Assessing MemPalace for mentor_generator (WRC 0.290 — PoC-only)
4. Assessing the local-vs-cloud split (MemPalace local / pgvector cloud — WRC 0.465 for local)

The session concluded with a clear resolution: MemPalace is for **development memory** (capturing the reasoning behind decisions), not **application memory** (course materials, student history).

## Key Insights

### 1. Two Orthogonal Problems, One Mechanism

MemPalace and the frontmatter 3-tier system use the same architectural pattern — hierarchical metadata filter → semantic search — applied to completely different content domains:

| Dimension | MemPalace | Frontmatter 3-Tier |
|-----------|-----------|-------------------|
| Content | Conversations (mined, ephemeral → captured) | Documents (authored, intentional → persisted) |
| Metadata source | Auto-detected rooms from conversation topics | Intentional YAML during authoring |
| Storage | ChromaDB (SQLite binary) | Git (plain text) |
| Validation | None at ingest | Pre-commit + JSON Schema via `.vadocs/` |
| Consumer | LLM via MCP | Human reader + scripts |
| Retrieval proven | 60.9% → 94.8% R@10 (22k conversations) | Not benchmarked |

The pattern is the same. The instantiation differs because the content differs. This is not a "one size fits all" decision — it's a "same pattern, different instance" decision.

### 2. The Unified Engine Conclusion

For mentor_generator's reference materials (books, articles, transcripts), the correct architecture is **single pgvector engine, two deployment topologies**:

- **Local:** Podman sidecar on user's machine (rootless, `systemctl --user`, same Kube YAML)
- **Cloud:** Shared Postgres cluster with schema-per-user

This avoids the double-validation burden of maintaining two storage engines. The local deployment is not "serverless" — it's "single-tenant server." The ecosystem already uses Podman via `systemctl --user` (ADR-26040), so the infrastructure exists.

**Why the MemPalace-local / pgvector-cloud split fails:**
- Two chunking pipelines to validate (conversation mining vs. document chunking)
- Two embedding model configurations to maintain
- No `commit_sha` tracking in MemPalace — can't detect stale vectors
- Mining pipeline tuned for conversations, not structured documents with chapters/sections/speakers
- SVA violations: C2 (portability), C3 (git-native), C5 (reuse) — WRC drops from 0.883 to 0.465

### 3. MemPalace's Actual Place in the Ecosystem

The clean split:

| What | Where | Rationale |
|------|-------|-----------|
| Development conversations | MemPalace (ChromaDB) | Captures reasoning that didn't make it into ADRs |
| Formal decisions | `architecture/adr/` (Git) | SSoT, validated, versioned |
| Course reference materials | pgvector (Postgres) | Structure-aware chunking, commit_sha tracking |
| Student session state | Mentor package (JSON) | Structured state, not verbatim search |
| Skills / prompts | Skills directory (Git) | Procedural knowledge, deterministic |

MemPalace's four concrete use cases:
1. **Architecture decision memory** — mine Gemini/Claude sessions that produced ADRs. Get the reasoning that didn't survive formalization.
2. **Cross-repo development context** — wings for each repo, tunnels connecting related topics across repos.
3. **Post-mortem evidence capture** — auto-classify into hall_facts, hall_decisions, hall_advice. Still create formal ADRs, but never lose raw discussion.
4. **Solo developer cross-project memory** — design discussions about course structure, interview flows, format decisions.

### 4. Qwen Code Integration Workflow

MemPalace integrates with Qwen Code via MCP protocol:

**One-time setup:** install → init → mine → register in `~/.qwen/settings.json` as MCP server → verify.

**Daily use:** Ask questions about past decisions. Qwen Code calls MemPalace tools automatically via MCP. No manual search needed.

**Limitations:**
- No auto-save hook for Qwen Code (Claude Code has Stop + PreCompact hooks)
- Still requires manual mining of conversation exports
- Read-heavy — retrieval only, no generation assistance
- 96.6% benchmark is on conversations, not code-heavy development discussions

## Approach Evaluation

### The Local vs. Cloud Split Hypothesis

The user's intuition was: "Local should use MemPalace (zero server), cloud should use pgvector (scalability)." This is a common architectural instinct — different constraints, different tools.

**Why it's wrong here:** The retrieval contract is identical. Query → relevant passages from books/transcripts. The only variable is deployment topology (where the database runs), not the storage engine (what format the data is in). Choosing different engines means:
- Two chunking strategies to design and validate
- Two embedding model configs to maintain
- Two test matrices (R@10 for each engine × each content type)
- Two migration paths when embedding models change
- No way to move a local user's data to cloud without re-indexing

**The better split:** Same engine, different scale. Local = single-user Postgres via Podman. Cloud = multi-user Postgres cluster. The difference is configuration, not architecture.

### The "What About Local Users Without Podman?" Question

Some users won't have Podman. This is a real concern. But the answer is not "use a different vector store" — it's "make Podman setup easier." Options:
- Setup script that installs rootless Podman and runs `podman play kube`
- Include the Kube YAML in the mentor_generator repo
- Document the process in a getting-started guide

Adding ChromaDB as a "lighter alternative" saves ~200MB RAM at the cost of doubling the validation surface. Not a good trade.

### The Ecosystem Roadmap Impact

The ecosystem roadmap (`plan_20260308_ecosystem_roadmap_vadocs_to_mentor.md`) Phase 2 commits to pgvector. This analysis confirms that commitment and extends it to the local deployment case.

**What changes:** The roadmap should explicitly address local deployment topology — not as a separate engine, but as the same engine at different scale.

**What doesn't change:** The engine choice, the embedding model, the chunking strategy, the commit_sha tracking. All remain pgvector-first.

**New consideration:** Add a retrieval benchmark step to the roadmap — 50 questions about educational content, measure R@10 for different chunking strategies and search modes. This gives empirical E scores for WRC calculations on actual content, not assumptions.

## Appendix

### Open Questions

1. **Qwen Code session mining** — Qwen Code stores sessions as JSONL (`~/.qwen/tmp/projects/<hash>/chats/*.jsonl`). Can MemPalace mine these directly? The JSONL format is not a standard conversation export. A custom extraction step would be needed to convert JSONL to a format MemPalace's `mine` command understands.

2. **Book ingestion pipeline** — How do books, articles, and transcripts get into pgvector? The chunking strategy matters: chapter/section-aware for books, speaker-aware for transcripts. This is a separate tool to build.

3. **Retrieval benchmark design** — The immediate next step (build a benchmark for educational content) requires: a corpus (10 chapters + 5 transcripts), a question set (50 questions), ground truth answers, and R@10 measurement across three modes (ChromaDB default, pgvector structure-aware, pgvector hybrid).

## References

- S-26022 — Full dialogue (this session)
- ADR-26038 — Context Engineering as Core Design Principle
- ADR-26039 — pgvector as ecosystem standard
- ADR-26040 — Kube YAML via systemctl --user
- A-26002 — Agentic OS, Tiered Cognitive Memory
- A-26006 — Agent Runtime Architecture and RAG Infrastructure
- `plan_20260308_ecosystem_roadmap_vadocs_to_mentor.md` — Ecosystem roadmap
- [MemPalace](https://github.com/milla-jovovich/mempalace) — milla-jovovich/mempalace, v3.0.0, April 2026
