---
title: MemPalace — AI Memory System
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: 2026-05-06
description: Analysis of the MemPalace AI memory system, its hierarchical structure,
  and retrieval performance.
tags:
- agents
- architecture
options:
  type: guide
  birth: 2026-05-06
  version: 1.0.0
  token_size: 3939
---
# MemPalace — AI Memory System

## Overview

MemPalace ([milla-jovovich/mempalace](https://github.com/milla-jovovich/mempalace), v3.0.0) is a local-only AI memory system that scored 96.6% R@5 on the LongMemEval benchmark — the highest result published, free or paid. It stores conversations verbatim in ChromaDB and organizes them into a hierarchical "memory palace" structure (wings, halls, rooms, drawers) that enables structured retrieval on top of semantic search.

Runs entirely on your machine. Zero API calls. No cloud. Open-source (MIT license).

## How It Works

### The Palace Structure

Inspired by the ancient Greek memory palace technique — orators placed ideas in rooms of an imaginary building, then walked through to retrieve them. MemPalace applies the same principle to AI conversations:

```
  ┌─────────────────────────────────────────────────────────────┐
  │  WING: Person or Project                                    │
  │                                                            │
  │    ┌──────────┐  ──hall──  ┌──────────┐                    │
  │    │  Room A  │            │  Room B  │                    │
  │    └────┬─────┘            └──────────┘                    │
  │         │                                                  │
  │         ▼                                                  │
  │    ┌──────────┐      ┌──────────┐                          │
  │    │  Closet  │ ───▶ │  Drawer  │                          │
  │    └──────────┘      └──────────┘                          │
  └─────────────────────────────────────────────────────────────┘
```

| Element | Role | Example |
|---------|------|---------|
| **Wing** | Person or project | `ai_engineering_book`, `mentor_generator`, `vadocs` |
| **Hall** | Memory type (fixed set, same in every wing) | `hall_facts` (decisions), `hall_events` (sessions), `hall_discoveries` (breakthroughs), `hall_preferences` (habits), `hall_advice` (recommendations) |
| **Room** | Specific topic within a wing | `chunking-strategy`, `pgvector-decision`, `config-migration` |
| **Closet** | Summary pointing to original content | Auto-generated during mining |
| **Drawer** | The original verbatim file | Exact conversation text, never summarized |
| **Hall** (cross-wing) | Connections between related rooms in same wing | Auth room in project wing linked to auth room in security hall |
| **Tunnel** | Connections between the same topic across different wings | `config-migration` room exists in vadocs wing, mentor_generator wing, and ai_engineering_book wing — tunnel connects all three |

When the same room name appears in different wings, a **tunnel** is created automatically. This is the retrieval advantage: search once, get connected context across all your projects.

### Retrieval Performance

The palace structure is not cosmetic — it measurably improves search accuracy:

| Search Mode | R@10 | Improvement |
|-------------|------|-------------|
| Search all closets (flat) | 60.9% | baseline |
| Search within wing | 73.1% | +12% |
| Search wing + hall | 84.8% | +24% |
| Search wing + room | 94.8% | +34% |

Tested on 22,000+ real conversation memories. The structure narrows the search space before the embedding model runs, reducing noise.

### Under the Hood: ChromaDB + Embeddings

MemPalace uses ChromaDB for vector storage. The default embedding model is `all-MiniLM-L6-v2` — a ~80MB transformer running locally on CPU, producing 384-dimensional vectors. The pipeline:

```
Query text → MiniLM embedding → 384-dim vector → cosine similarity → top-K results
```

No LLM involved in the retrieval step. The embedding model converts your query to a vector, finds the closest stored vectors, returns the original text they represent.

### AAAK Compression (Experimental)

AAAK is a lossy abbreviation dialect — entity codes, structural markers, sentence truncation — designed to reduce token count for repeated entities at scale. It is readable by any LLM without a decoder.

**Honest status (April 2026):**
- AAAK is **lossy**, not lossless
- Does **not** save tokens at small scales (overhead exceeds savings)
- **Regresses** LongMemEval vs raw verbatim mode: 84.2% vs 96.6%
- The 96.6% headline number comes from **raw mode**, not AAAK
- Storage default is raw verbatim text — AAAK is a separate compression layer

The authors are iterating. Track progress in [Issue #43](https://github.com/milla-jovovich/mempalace/issues/43).

### Knowledge Graph

Temporal entity-relationship triples stored in SQLite (like Zep's Graphiti, but local and free):

```python
from mempalace.knowledge_graph import KnowledgeGraph

kg = KnowledgeGraph()
kg.add_triple("Kai", "works_on", "Orion", valid_from="2025-06-01")
kg.add_triple("Maya", "assigned_to", "auth-migration", valid_from="2026-01-15")

# What's true right now?
kg.query_entity("Kai")

# What was true in January?
kg.query_entity("Maya", as_of="2026-01-20")

# Invalidate when no longer true
kg.invalidate("Kai", "works_on", "Orion", ended="2026-03-01")
```

Facts have validity windows. When something stops being true, invalidate it. Historical queries still work.

## Usage Modes

### Manual Mode (CLI — You Drive)

You run commands in the terminal. No LLM involved. Results printed to stdout.

```bash
# Initialize palace for a project
mempalace init ~/projects/myapp

# Mine conversation exports
mempalace mine ~/chats/claude_exports/ --mode convos --wing driftwood
mempalace mine ~/projects/myapp/ --mode projects               # code, docs, notes
mempalace mine ~/chats/ --mode convos --extract general         # auto-classify

# Search
mempalace search "why did we switch to GraphQL"
mempalace search "auth decisions" --wing driftwood --room auth-migration

# Status and taxonomy
mempalace status              # Palace overview with counts
mempalace list_wings          # All wings with drawer counts
mempalace get_taxonomy        # Full tree: wing → halls → rooms → counts

# Load context for local model
mempalace wake-up > context.txt   # ~170 tokens of critical facts
```

**When to use:** Quick lookup, exploration, debugging, one-off questions. You read the results yourself.

### Agentic Mode (MCP — AI Drives)

MemPalace exposes 19 tools via the Model Context Protocol (MCP). Your AI assistant calls them automatically when your questions require historical context.

**One-time setup:**

```bash
# For Claude Code
claude mcp add mempalace -- python -m mempalace.mcp_server

# For Qwen Code — add to settings.json:
{
  "mcpServers": {
    "mempalace": {
      "command": "python",
      "args": ["-m", "mempalace.mcp_server"],
      "cwd": "/path/to/your/project"
    }
  }
}
```

**19 MCP tools available to the AI:**

| Category | Tools | What They Do |
|----------|-------|-------------|
| **Palace (read)** | `mempalace_status`, `mempalace_list_wings`, `mempalace_list_rooms`, `mempalace_get_taxonomy`, `mempalace_search`, `mempalace_check_duplicate`, `mempalace_get_aaak_spec` | Browse structure, search with filters, check before filing |
| **Palace (write)** | `mempalace_add_drawer`, `mempalace_delete_drawer` | File verbatim content, remove by ID |
| **Knowledge Graph** | `mempalace_kg_query`, `mempalace_kg_add`, `mempalace_kg_invalidate`, `mempalace_kg_timeline`, `mempalace_kg_stats` | Query entity relationships, add/remove facts, view timelines |
| **Navigation** | `mempalace_traverse`, `mempalace_find_tunnels`, `mempalace_graph_stats` | Walk the graph across wings, find cross-topic connections |
| **Agent Diary** | `mempalace_diary_write`, `mempalace_diary_read` | Write/read AAAK diary entries for specialist agents |

**How it works in practice:**

```
You: "What did we decide about auth last month?"
  → AI calls mempalace_search("auth decisions", wing="project", hall="hall_facts")
  → MemPalace returns verbatim conversation snippets
  → AI reads snippets and answers you with the actual decision

You: "Did we debug this Podman issue before?"
  → AI calls mempalace_search("Podman permission rootless")
  → MemPalace finds February 28 session
  → AI: "Yes — the fix was adding securityContext.runAsNonRoot: false"
```

**Auto-save hooks (Claude Code only):** Two hooks fire during work sessions — every 15 messages (structured save) and before context compression (emergency save). Qwen Code does not have equivalent hooks yet — manual mining required.

**When to use:** Daily development. The AI searches your past conversations automatically. You never type `mempalace search` again.

### Python API (Programmatic)

```python
from mempalace.searcher import search_memories

results = search_memories(
    "auth decisions",
    palace_path="~/.mempalace/palace",
    wing="driftwood",
    room="auth-migration"
)

for r in results:
    print(r.content)  # verbatim conversation text
    print(r.score)    # similarity score
```

Use this when building custom integration — e.g., a script that mines Qwen Code JSONL sessions and feeds results into MemPalace.

## Specialist Agents

Create agents that focus on specific areas. Each agent gets its own wing and diary in the palace:

```
~/.mempalace/agents/
  ├── reviewer.json    # code quality, patterns, bugs
  ├── architect.json   # design decisions, tradeoffs
  └── ops.json         # deploys, incidents, infra
```

Each agent has a focus, keeps a diary (written in AAAK, persists across sessions), and builds expertise by reading its own history. The AI discovers agents from the palace at runtime — your config stays the same size regardless of how many agents you add.

## Known Issues (April 2026)

The authors publicly acknowledged problems after community feedback:

- **AAAK token example was incorrect** — used rough heuristic instead of real tokenizer. Being rewritten
- **"30x lossless compression" overstated** — AAAK is lossy, scores 84.2% vs raw 96.6%
- **"+34% palace boost" misleading** — metadata filtering is standard ChromaDB, not novel retrieval
- **Contradiction detection** (`fact_checker.py`) not wired into knowledge graph operations
- **"100% with Haiku rerank"** — real result files exist but rerank pipeline not in public benchmark scripts
- **Shell injection vulnerability** in hooks (Issue #110)
- **macOS ARM64 segfault** (Issue #74)
- **ChromaDB version not pinned** (Issue #100)

The 96.6% raw mode score remains reproducible — independently verified on M2 Ultra in under 5 minutes with 500 questions.

## Comparison: MemPalace vs. Frontmatter 3-Tier System

Both systems use the same architectural pattern — hierarchical metadata filter narrows scope, then semantic/text search finds matches within that scope. They differ in content domain and operational constraints.

| Dimension | MemPalace | Frontmatter 3-Tier |
|-----------|-----------|-------------------|
| **Content** | Conversations (mined, ephemeral → captured) | Documents (authored, intentional → persisted) |
| **Structure** | Wing → Hall → Room → Closet → Drawer | Type → Status → Tag → Document |
| **Metadata source** | Auto-detected during mining | Intentional YAML during authoring |
| **Storage** | ChromaDB (SQLite binary + vectors) | Git (plain text + YAML frontmatter) |
| **Search** | Embedding-based (MiniLM → cosine similarity) | Text/keyword (BM25, grep, full-text) |
| **Validation** | None at ingest | Pre-commit + JSON Schema (`.vadocs/conf.json`) |
| **Versioning** | No commit tracking | Git-native — every change tracked, diffable |
| **Provenance** | None — can't detect stale content | `commit_sha` implicitly tracked via Git |
| **Retrieval proven** | 60.9% → 94.8% R@10 (22k conversations) | Not benchmarked |
| **Runtime** | Requires ChromaDB process | Zero runtime — files on disk |
| **Consumer** | LLM via MCP (agentic) or CLI (manual) | Human reader + scripts (`check_adr.py`, etc.) |
| **WRC** | 0.688 (PoC-only for document use) | 0.796 (Production-adaptable) |

### When Each Is the Right Tool

| Scenario | Use | Why |
|----------|-----|-----|
| "What did we decide about chunking in that Gemini session?" | MemPalace | Captures reasoning that didn't make it into the ADR |
| "Show me all accepted ADRs about devops" | Frontmatter | Validated schema, Git-native, zero runtime |
| "Find the Podman debugging conversation from February" | MemPalace | Verbatim conversation with error messages and attempts |
| "What's the current status of the pgvector decision?" | Frontmatter | ADR has the decision, status field tells you if it's final |
| "Cross-reference config migration across vadocs, mentor, and the book" | MemPalace | Tunnels connect same-named rooms across wings |
| "Generate the ADR index for the documentation site" | Frontmatter | `check_adr.py --fix` reads frontmatter, builds index |

### The Pattern Is the Same, the Instances Differ

```
Hierarchical metadata filter (narrow the universe)
        ↓
Search within narrowed set (find the needle)
```

MemPalace fills this pattern with ChromaDB embeddings and auto-mined conversation structure. The frontmatter system fills it with Git-tracked YAML and intentional authoring. Neither is "better" — they are the same mechanism applied to different content.

**Conversations are mined, not authored.** They emerge from debugging sessions, design debates, and failed experiments. The right system captures them verbatim and makes them findable — that's MemPalace.

**Documents are authored, not mined.** They are intentional artifacts with lifecycle states, validation rules, and governance requirements. The right system validates structure, tracks provenance, and enables lifecycle management — that's the frontmatter system.

## Where MemPalace Fits in This Ecosystem

The clean split:

| What | Where | Rationale |
|------|-------|-----------|
| Development conversations | MemPalace (ChromaDB, local) | Captures the reasoning behind decisions — what didn't make it into ADRs |
| Formal decisions | `architecture/adr/` (Git) | SSoT, validated via `check_adr.py`, versioned, diffable |
| Course reference materials | pgvector (Postgres) | Structure-aware chunking, `commit_sha` tracking, hybrid search (ADR-26039) |
| Student session state | Mentor package (JSON files) | Structured state, not verbatim search |
| Skills / prompts | Skills directory (Git) | Procedural knowledge, deterministic, validated via vadocs |

MemPalace is **development memory** — the conversations that happen before the ADR is written, before the code is committed, before the decision is made. It captures the messy reasoning process that structured artifacts intentionally exclude.

It is **not application memory** — course materials, student history, and curriculum graphs belong in the mentor package or pgvector. MemPalace was designed for conversational recall, not educational content delivery. The mining pipeline is tuned for conversations, not structured documents with chapters, figures, and speaker attributions.

## Integration with Qwen Code

MemPalace integrates with Qwen Code via MCP. Add to your project-level `.qwen/settings.json` or global `~/.qwen/settings.json`:

```json
{
  "mcpServers": {
    "mempalace": {
      "command": "python",
      "args": ["-m", "mempalace.mcp_server"],
      "cwd": "/path/to/your/project"
    }
  }
}
```

After setup, Qwen Code has 19 MemPalace tools available. When you ask about past decisions, it searches automatically. No manual commands needed.

**Current limitation:** Qwen Code does not have auto-save hooks equivalent to Claude Code's Stop/PreCompact hooks. New conversations must be mined manually or via custom extraction scripts that convert Qwen Code's JSONL session files (`~/.qwen/tmp/projects/<hash>/chats/*.jsonl`) into a format MemPalace understands.
