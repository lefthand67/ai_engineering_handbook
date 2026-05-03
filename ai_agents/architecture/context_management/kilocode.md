
---
title: Context Management — KiloCode
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: '2026-04-05'
description: 'KiloCode is a fork of OpenCode — identical context management architecture
  with the addition of Agent Manager for multi-session orchestration. Full technical
  breakdown: [OpenCode](opencode.md).'
tags:
- architecture
- agents
options:
  version: 1.0.0
  birth: '2026-04-05'
  type: guide
  token_size: 734
---
# Context Management — KiloCode

**Agent version:** v7.1.20 (commit `cb0c58c0`)
**Analysis date:** 2026-04-05

:::{note}
KiloCode is a fork of OpenCode. The context management architecture is **identical** — same SQLite storage, same compaction agent, same pruning constants, same `filterCompacted` boundary detection. See [OpenCode deep dive](opencode.md) for the full technical breakdown with code evidence.
:::

## What's Different: Agent Manager

KiloCode adds an **Agent Manager** (VS Code extension) for multi-session orchestration:

- Each session gets its own **git worktree**
- The extension coordinates `kilo serve` processes via HTTP + SSE
- Each session has its own independent SQLite database and context budget
- The Agent Manager is a panel in VS Code that manages multiple concurrent sessions

This doesn't change the per-session context management algorithm — each session still uses the same `filterCompacted` → `toModelMessages` → `isOverflow` → compaction pipeline as OpenCode. But it adds a **multi-session layer** that OpenCode doesn't have: users can work on multiple files/branches simultaneously, each with independent context budgets.

### Key File: Agent Manager location

The Agent Manager lives in the VS Code extension portion of the monorepo, separate from the core `packages/opencode/` runtime. It manages session lifecycle (create, pause, resume, delete) and coordinates the underlying `kilo serve` processes.

## Shared Architecture with OpenCode

The following are inherited directly from OpenCode (no code changes):

| Component | Behavior |
|-----------|----------|
| Storage | SQLite (MessageTable + PartTable) |
| History retrieval | `filterCompacted` — stops at compaction markers |
| Token counting | `isOverflow()` — context − 20K buffer |
| Compaction | Dedicated agent (no tools) with structured summary |
| Pruning | `PRUNE_MINIMUM = 20_000`, `PRUNE_PROTECT = 40_000` |
| Tool truncation | `MAX_LINES = 2000`, `MAX_BYTES = 50KB` |
| Media handling | Stripped during compaction |
| Overflow detection | Provider error pattern matching |

All code paths are in `packages/opencode/src/` — the same package as OpenCode.

## Key Files

| File | Role |
|------|------|
| `packages/opencode/src/session/prompt.ts` | Main loop — identical to OpenCode |
| `packages/opencode/src/session/message-v2.ts` | `filterCompacted` — identical to OpenCode |
| `packages/opencode/src/session/compaction.ts` | Compaction agent — identical to OpenCode |
| VS Code extension (Agent Manager) | Multi-session orchestration — **KiloCode unique** |
