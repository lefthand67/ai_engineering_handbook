---
title: Context Management — Agent Comparison
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Side-by-side comparison of context management across 7 coding agents
  — history transmission, detection methods, compaction strategies, and unique innovations.
tags:
- architecture
- agents
date: '2026-05-01'
options:
  version: 1.1.1
  birth: '2026-04-05'
  type: guide
  token_size: 2027
---
# Context Management — Agent Comparison

*All analyses based on source code inspection dated 2026-04-08.*

## Decision Guide: Which Agent for Which Use Case

| Need | Best Fit | Why |
|------|----------|-----|
| Long sessions, large repos | Claude Code | 5-tier system + 1M context option + server-side editing |
| Multi-provider flexibility | OpenClaude | 200+ LLM providers with same 5-tier system |
| Git-centric workflow | Aider | Git history as session record, commit-per-change |
| Privacy (local-only) | OpenClaw | Configurable sliding window, no cloud dependency |
| Multi-session work | KiloCode | Agent Manager with VS Code panel + git worktrees |
| Fast startup, simple | OpenCode | Reactive compaction, clean SQLite storage |
| Gemini/GCP ecosystem | Qwen-Code | Deep Gemini integration, JSONL crash recovery |

## Version Tracking

| Agent | Version | Commit |
|-------|---------|--------|
| [Aider](aider.md) | v0.86.3.dev | `bdb4d9ff` |
| [Claude Code](claude_code.md) | (no tag) | `3da7e321` |
| [OpenClaude](openclaude.md) | 0.1.8 | (fork) |
| [OpenClaw](openclaw.md) | v2026.4.2 | `2781897d` |
| [OpenCode](opencode.md) | v1.3.15 | `280eb16e` |
| [KiloCode](kilocode.md) | v7.1.20 | `cb0c58c0` |
| [Qwen-Code](context_management_qwen_code.md) | v0.14.0 | `e8552294` |

## Universal Pattern: Full History Every Call

All 7 agents send the **full conversation history** on every API call. There is no chunking, no delta updates, no server-side session persistence. The entire message array is serialized and sent with each `chat.completions.create()` request.

| Agent | History Sent | Evidence |
|-------|-------------|----------|
| Qwen-Code | Full curated `Content[]` | `geminiChat.ts`: `contents: requestContents` |
| Aider | Full assembled context | `base_coder.py`: `format_chat_chunks()` → `all_messages()` |
| OpenClaw | Full sanitized history | `attempt.ts`: sanitize → validate → `limitHistoryTurns()` → send |
| OpenCode | Full non-compacted history | `prompt.ts`: `filterCompactedEffect()` → `toModelMessages()` |
| KiloCode | Full non-compacted history | `prompt.ts`: `filterCompacted()` → `toModelMessages()` |
| Claude Code | Full normalized history | `messages.ts`: `normalizeMessagesForAPI()` → `queryModelWithStreaming()` |
| OpenClaude | Full normalized history | `messages.ts`: `normalizeMessagesForAPI()` → multi-provider routing |

## Context Window Defaults

| Agent | Default | Max | Source |
|-------|---------|-----|--------|
| Qwen-Code | 128K | 1M (Qwen3-coder-plus) | Regex matching on model name (`tokenLimits.ts`) |
| Aider | From LiteLLM registry | Varies by model | LiteLLM `model_prices_and_context_window.json` |
| OpenClaw | 200K | Configurable per-model | `DEFAULT_CONTEXT_TOKENS` constant |
| OpenCode | From model config | Varies by model | `model.limit.context` field |
| KiloCode | From model config | Varies by model | `model.limit.context` field |
| Claude Code | 200K | 1M (`[1m]` suffix) | `MODEL_CONTEXT_WINDOW_DEFAULT`, env var override |
| OpenClaude | 200K | 1M (`[1m]` suffix + 200+ providers) | `MODEL_CONTEXT_WINDOW_DEFAULT`, OpenAI registry |

## Overflow Detection

| Agent | Pre-emptive | Reactive |
|-------|-------------|----------|
| Qwen-Code | Token count ≥ 70% of window | Error retry (up to 10×, 60s delay) |
| Aider | Pre-send token count check | `ContextWindowExceededError` from LiteLLM |
| OpenClaw | `contextTokenBudget` comparison | 40+ provider error patterns matched |
| OpenCode | Token count ≥ context − 20K | 15+ provider error pattern regexes |
| KiloCode | Token count ≥ context − 20K | Provider error matching |
| Claude Code | Hybrid: real API usage + estimate | 15+ patterns + `ContextOverflowError` type |
| OpenClaude | Hybrid: real API usage + estimate | Multi-provider error matching + Haiku fallback |

## Compaction Strategy Comparison

| Agent | Primary Method | Trigger | Keeps |
|-------|---------------|---------|-------|
| Qwen-Code | AI summarization (separate LLM call) | 70% usage | Last 30% of conversation |
| Aider | Async LLM summarization of done_messages | > 1/16th of context (max 8192) | Tail messages (recent half) |
| OpenClaw | Sliding window + pi-coding-agent auto-compact | Configurable N turns + budget | Last N user turns |
| OpenCode | Dedicated compaction agent (no tools) | Token ≥ context − 20K | Everything after compaction marker |
| KiloCode | Dedicated compaction agent (no tools) | Token ≥ context − 20K | Everything after compaction marker |
| Claude Code | 5-tier: microcompact → API editing → session memory → full → PTL retry | Token ≥ context − 13K | Recent messages (prefix-preserving) |
| OpenClaude | 5-tier (Claude Code inherited) + JSONL persistence | Token ≥ context − 13K | Recent messages (prefix-preserving) |

## Tool Output Management

| Agent | Strategy | Limits |
|-------|----------|--------|
| Qwen-Code | No explicit truncation | None found |
| Aider | Repo map dynamic sizing | Budgeted from context window |
| OpenClaw | Tool result truncation (last resort) | Overflow recovery fallback |
| OpenCode | Per-output truncation + pruning | 2000 lines / 50KB; prune > 40K back |
| KiloCode | Per-output truncation + pruning | 2000 lines / 50KB; prune > 40K back |
| Claude Code | Server-side `cache_edits` + content clearing | Count-based thresholds from GrowthBook |
| OpenClaude | Server-side `cache_edits` + content clearing | Count-based thresholds from GrowthBook |

## Content Filtering

| Agent | Images/Documents/Thoughts |
|-------|-------------------------|
| Qwen-Code | `thought: true` parts stripped from history |
| Aider | N/A (code-focused, no image support) |
| OpenClaw | Strips images during sanitization |
| OpenCode | Stripped during compaction → `[Attached mime: filename]` |
| KiloCode | Stripped during compaction → `[Attached mime: filename]` |
| Claude Code | Stripped during compaction → `[image]` / `[document]` |
| OpenClaude | Stripped during compaction → `[image]` / `[document]` |

## Persistence

| Agent | Storage |
|-------|---------|
| Qwen-Code | Append-only JSONL event logs (`~/.qwen/tmp/...`) |
| Aider | JSONL session file + git history |
| OpenClaw | JSONL session file (SessionManager from pi-coding-agent) |
| OpenCode | SQLite (MessageTable + PartTable) |
| KiloCode | SQLite (MessageTable + PartTable) |
| Claude Code | In-memory `Message[]` array |
| OpenClaude | In-memory `Message[]` + global `history.jsonl` (cross-project) |

## Unique Innovations

| Agent | Innovation |
|-------|-----------|
| **Qwen-Code** | Tree-structured JSONL with `uuid`/`parentUuid` enabling branching and checkpointing |
| **Aider** | Background async summarization that doesn't block the main conversation loop |
| **OpenClaw** | Pluggable `ContextEngine` interface with legacy + custom implementations |
| **OpenCode** | Structured summary template (Goal/Instructions/Discoveries/Accomplished/Files) |
| **KiloCode** | Nearly identical to OpenCode (shared codebase — KiloCode is a fork) |
| **Claude Code** | Server-side cache editing via Anthropic API; background session memory agent that continuously maintains a summary file |
| **OpenClaude** | 200+ LLM provider support with same 5-tier system; cross-project JSONL history persistence |
