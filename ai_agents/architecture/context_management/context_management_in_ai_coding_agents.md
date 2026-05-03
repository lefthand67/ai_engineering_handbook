
---
title: Context Management in AI Coding Agents
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: '2026-05-01'
description: Overview of the universal 'full history' pattern — why agents accumulate
  millions of tokens despite bounded context windows, and the compaction taxonomy
  used across 7 agents.
tags:
- architecture
- agents
options:
  version: 1.1.1
  birth: '2026-04-05'
  type: guide
  token_size: 1218
---
# Context Management in AI Coding Agents

## The Core Insight: Context Window vs Cumulative Tokens

When working with AI coding agents, you'll see two very different numbers:

- **"You're using 10% of context"** — the agent's session-level working memory
- **"Total tokens: 2.5M"** — the cumulative sum across all API calls

These are **different things**. The context window (128K–1M tokens) is the **per-call ceiling** — how much text the LLM can process in a single request. The cumulative tokens metric is the **sum across all API calls** in your session.

## Why Millions of Tokens? The Universal Pattern

Every coding agent analyzed (Aider, Claude Code, OpenClaude, OpenClaw, OpenCode, KiloCode, Qwen-Code) follows the same fundamental pattern:

> **Each API call sends the full conversation history to the LLM.**

The LLM has no memory between calls. So every request rebuilds the entire context from scratch:

```
API Call N:
├─ System Prompt              (always present)
├─ Conversation History       (turns 1..N-1)  ← GROWS each turn
├─ Tool Results               (if any)
└─ User Message               (turn N)
```

Over a 20-turn session:

| Turn | Approx Tokens | What's Included |
|------|--------------|-----------------|
| 1 | 5K | System + your message |
| 5 | 25K | System + turns 1–4 + turn 5 |
| 10 | 50K | System + turns 1–9 + turn 10 |
| 20 | 100K | System + turns 1–19 + turn 20 |
| **Total** | **~1M+** | Sum across all calls |

The same content is counted repeatedly — once per API call it appears in.

## The Analogy

**Context window** = the size of your desk (how much you can work with at once).

**Cumulative tokens** = how many pages you've read through over the day (you re-read the same pages many times, so the total is much higher than your desk size).

## The Compaction Taxonomy

Since context grows unboundedly, every agent implements some form of **compaction** — reducing the history size. There are four main strategies:

| Strategy | How It Works | Agents |
|----------|-------------|--------|
| **AI Summarization** | LLM reads old messages, produces a summary that replaces them | Qwen-Code, Aider, OpenCode, KiloCode |
| **Sliding Window** | Keep only the last N turns, discard the rest | OpenClaw (configurable) |
| **Pruning** | Clear old tool outputs, keep conversation text | Claude Code, OpenCode, KiloCode |
| **Server-Side Editing** | Use provider APIs to delete content without invalidating cache | Claude Code (Anthropic `cache_edits`) |

### When Compaction Triggers

```
Before compaction:  [Turn 1] [Turn 2] ... [Turn 50]  = 100K tokens
After compaction:   [Summary of 1..40] [Turn 41..50]  = 15K tokens
```

Agents trigger compaction at varying thresholds — from 70% of the context window (Qwen-Code) down to a 13K-token buffer (Claude Code). See [/ai_agents/architecture/context_management/context_management_agent_comparison.md](/ai_agents/architecture/context_management/context_management_agent_comparison.md#compaction-strategy-comparison) for the full agent-by-agent breakdown.

## Key Takeaway

The "context window" is the **per-call limit**. The "cumulative tokens" is the **sum across all calls**, where the same content is counted repeatedly. Compaction is what prevents hitting the hard limit — but even with compaction, a long session accumulates millions of tokens because the model re-reads the compressed history on every subsequent call.

## Guide Structure

This guide covers context management across 7 agents:

- [/ai_agents/architecture/context_management/context_management_agent_comparison.md](/ai_agents/architecture/context_management/context_management_agent_comparison.md) — Side-by-side comparison of all agents
- [aider.md](aider.md) — Aider's async background summarization
- [claude_code.md](claude_code.md) — Claude Code's 5-tier system
- [openclaude.md](openclaude.md) — OpenClaude's multi-provider 5-tier system
- [openclaw.md](openclaw.md) — OpenClaw's sliding window + auto-compaction
- [opencode.md](opencode.md) — OpenCode's reactive compaction agent
- [kilocode.md](kilocode.md) — KiloCode's compaction agent
- [context_management_qwen_code.md](context_management_qwen_code.md) — Qwen-Code's autocompact buffer + /compress

All analyses are based on source code inspection. Version and commit hash are recorded in each file for traceability.
