
---
title: Context Management — OpenClaw
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: '2026-04-05'
description: Deep dive into OpenClaw's sliding window approach and auto-compaction
  — how it limits history turns, sizes context budgets, and delegates to the pi-coding-agent
  library.
tags:
- architecture
- agents
options:
  version: 1.0.0
  birth: '2026-04-05'
  type: guide
  token_size: 2002
---
# Context Management — OpenClaw

**Agent version:** v2026.4.2 (commit `2781897d`)
**Analysis date:** 2026-04-05

## Architecture Overview

OpenClaw uses a `SessionManager` from the external `@mariozechner/pi-coding-agent` library, which persists conversation state to a **JSONL session file** on disk. The full message history is kept in memory (`activeSession.messages`) and written to this file after each turn.

## History Transmission

OpenClaw sends the **full sanitized history** to the LLM on each call, not chunks. Each API call goes through a processing pipeline:

1. **`sanitizeSessionHistory`** — cleans images, drops thinking blocks, sanitizes tool calls, repairs tool_use/tool_result pairing, strips stale usage data
2. **`validateReplayTurns`** — provider-specific validation (Gemini/Anthropic turn ordering)
3. **`limitHistoryTurns`** — truncates to last N user turns (configurable per DM session)
4. **`sanitizeToolUseResultPairing`** — repairs any orphaned tool_results caused by truncation
5. **`contextEngine.assemble`** — optional plugin-based context assembly (pluggable, defaults to pass-through)
6. Messages sent to LLM API

**Key file:** `src/agents/pi-embedded-runner/run/attempt.ts` (line ~1140–1185)

## Sliding Window: `limitHistoryTurns`

```typescript
export function limitHistoryTurns(
  messages: AgentMessage[],
  limit: number | undefined,
): AgentMessage[] {
  if (!limit || limit <= 0 || messages.length === 0) return messages

  let userCount = 0
  let lastUserIndex = messages.length

  for (let i = messages.length - 1; i >= 0; i--) {
    if (messages[i].role === "user") {
      userCount++
      if (userCount > limit) return messages.slice(lastUserIndex)
      lastUserIndex = i
    }
  }
  return messages
}
```

This is a **sliding window over user turns** — it keeps the most recent N user messages and all associated assistant/tool responses. The limit is configured per-provider/per-DM via `dmHistoryLimit` and `historyLimit` in the config.

**Key file:** `src/agents/pi-embedded-runner/history.ts` (lines 17–32)

## Context Window Resolution

Priority chain:
1. Per-model config (`models.providers.<provider>.models[].contextTokens` or `contextWindow`)
2. Model metadata (`model.contextTokens` or `model.contextWindow`)
3. Agent-level cap (`agents.defaults.contextTokens`) — acts as a ceiling
4. Default fallback: `DEFAULT_CONTEXT_TOKENS = 200,000`

The resolved value becomes `contextTokenBudget` passed to each attempt.

**Key file:** `src/agents/pi-embedded-runner/run/setup.ts` (lines 102–150)

### Guardrails

```typescript
CONTEXT_WINDOW_HARD_MIN_TOKENS = 16_000   // blocks below this
CONTEXT_WINDOW_WARN_BELOW_TOKENS = 32_000 // warns below this
```

**Key file:** `src/agents/context-window-guard.ts`

## Compaction: pi-coding-agent Auto-Compaction

OpenClaw delegates auto-compaction to the `@mariozechner/pi-coding-agent` library (external dependency). The library has built-in auto-compaction:

- `subscription.isCompacting()` — tracks compaction state
- `getCompactionCount()` — counts compactions per attempt
- `waitForCompactionRetryWithAggregateTimeout()` — waits for compaction with timeout

### Compaction Constants

```typescript
SUMMARIZATION_OVERHEAD_TOKENS = 4_096
```

Reserved for summarization prompt, system prompt, previous summary, and serialization wrappers.

### Adaptive Strategy

The pi-coding-agent library uses three compaction strategies that escalate on failure:

| Strategy | When Used | How It Works |
|----------|-----------|-------------|
| **Full summarization** | Normal case | Summarize all history into one summary message |
| **Partial summarization** | Some messages too large | Exclude oversized messages, summarize the rest |
| **Staged summarization** (`summarizeInStages`) | Even partial fails | Split messages by token share, summarize each chunk, merge summaries |

The adaptive chunk ratio (`computeAdaptiveChunkRatio`) dynamically adjusts how much history to summarize based on average message size — larger messages get a smaller chunk ratio to keep the summary request itself within bounds.

```typescript
// Reserved for summarization prompt, system prompt, previous summary, and wrappers
export const SUMMARIZATION_OVERHEAD_TOKENS = 4_096
```

**Key file:** `src/agents/compaction.ts` (lines 212–215)

## Overflow Recovery Loop

When the LLM API returns a context overflow error, OpenClaw enters a recovery loop:

1. **Detect overflow** via `isLikelyContextOverflowError()` — matches 40+ error patterns from providers (Anthropic, OpenAI, Groq, Gemini, Mistral, Cohere, Chinese proxies, etc.)
2. **Check if in-attempt compaction already ran** — if so, retry without additional compaction (avoid double-compaction)
3. **Explicit overflow compaction** — calls `contextEngine.compact()` with `force: true` and `compactionTarget: "budget"`
4. **Tool result truncation fallback** — if compaction cannot reduce enough, truncates oversized tool results
5. **Maximum retry attempts** — governed by `MAX_OVERFLOW_COMPACTION_ATTEMPTS`

### Overflow Detection

`isLikelyContextOverflowError()` uses a multi-stage filter that demonstrates how to handle 40+ provider-specific error formats:

```typescript
function isLikelyContextOverflowError(error: Error): boolean {
  // Stage 1: Exclude rate limit errors (not overflow)
  if (isRateLimitError(error)) return false
  // Stage 2: Exclude reasoning constraint errors
  if (isReasoningConstraintError(error)) return false
  // Stage 3: Exclude billing/quota errors
  if (isBillingError(error)) return false
  // Stage 4: Match explicit overflow patterns
  if (OVERFLOW_PATTERNS.some(p => p.test(error.message))) return true
  // Stage 5: Broad heuristic match
  return CONTEXT_OVERFLOW_HINT_RE.test(error.message)
}
```

It also extracts observed token counts from provider error messages via `extractObservedOverflowTokenCount()` for diagnostic and targeted compaction — parsing numbers from messages like `"maximum context length is 128000 tokens"` to know exactly how much to compact.

**Key file:** `src/agents/pi-embedded-helpers/errors.ts` (lines 258–295)

## Session File Truncation

After successful compaction, the session JSONL file is physically truncated to prevent unbounded file growth. This removes only the message entries that were actually summarized, preserving non-message session state (custom entries, model changes, labels, etc.) and re-parenting orphaned entries.

**Key file:** `src/agents/pi-embedded-runner/session-truncation.ts`

## Pluggable ContextEngine Architecture

OpenClaw defines a `ContextEngine` interface with pluggable implementations:

```typescript
interface ContextEngine {
  bootstrap()    // initialize engine state for a session
  ingest()       // add messages to the engine's store
  ingestBatch()  // bulk add
  assemble()     // build model context under a token budget
  compact()      // reduce token usage via summarization/pruning
  afterTurn()    // post-turn lifecycle hook
  maintain()     // transcript maintenance (safe rewrites)
}
```

The `LegacyContextEngine` is the default, which delegates to the existing pi-coding-agent compaction pipeline.

**Key file:** `src/context-engine/types.ts`

## Key Files

| File | Role |
|------|------|
| `src/agents/pi-embedded-runner/run/attempt.ts` | Main attempt loop, sanitization pipeline |
| `src/agents/pi-embedded-runner/history.ts` | `limitHistoryTurns()` — sliding window |
| `src/agents/pi-embedded-runner/run/setup.ts` | Context window resolution |
| `src/agents/pi-embedded-runner/run.ts` | Overflow recovery loop |
| `src/agents/compaction.ts` | Compaction constants, adaptive chunking |
| `src/agents/pi-embedded-helpers/errors.ts` | Overflow detection (40+ patterns) |
| `src/agents/context-window-guard.ts` | Hard minimum and warning thresholds |
| `src/context-engine/types.ts` | Pluggable `ContextEngine` interface |
| `src/agents/defaults.ts` | `DEFAULT_CONTEXT_TOKENS = 200,000` |
