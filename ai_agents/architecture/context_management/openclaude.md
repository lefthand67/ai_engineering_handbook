
---
title: Context Management — OpenClaude
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: '2026-04-08'
description: Deep dive into OpenClaude's context management — 5-tier system inherited
  from Claude Code with multi-provider support, session memory, and cache-aware compaction.
tags:
- architecture
- agents
options:
  version: 1.0.0
  birth: '2026-04-08'
  type: guide
  token_size: 2822
---
# Context Management — OpenClaude

**Agent version:** 0.1.8
**Analysis date:** 2026-04-08

## Architecture Overview

OpenClaude is a fork of Claude Code that extends it to support 200+ LLM providers (OpenAI, Gemini, Ollama, Codex, Grok, etc.) while retaining Claude Code's core architecture. It inherits the same 5-tier context management system with adaptations for multi-provider compatibility.

OpenClaude maintains an in-memory `Message[]` array that is rebuilt and sent to the LLM on every API call. There is no persistent server-side session — context lives in memory for the duration of the process, with optional JSONL history persistence.

Message types (`src/types/message.ts`):
- `UserMessage` — user input (text, tool_results, pasted content)
- `AssistantMessage` — model output (text, tool_use, thinking blocks)
- `SystemMessage` — system prompts and metadata
- `AttachmentMessage` — system-injected context (git status, CLAUDE.md, skills, MCP instructions)
- `HookResultMessage` — output from pre/post-compact hooks

Before sending, messages are normalized through `normalizeMessagesForAPI()`:
1. Reorders attachments to bubble them up
2. Strips virtual/display-only messages
3. Merges consecutive user messages (API compatibility)
4. Strips tool_reference blocks for unavailable tools
5. Strips images/documents that caused "too large" errors
6. Filters progress and synthetic error messages

**Key file:** `src/utils/messages.ts` — `normalizeMessagesForAPI()`

## Context Prefix

System context is constructed from two memoized functions:
- `getSystemContext()` — git status (truncated to 2000 chars), cache-breaker injection
- `getUserContext()` — CLAUDE.md files, current date

Both are memoized via `lodash-es/memoize` and cached for the conversation duration.

**Key file:** `src/context.ts`

## Token Counting

OpenClaude uses a **hybrid approach** that avoids double-counting drift:

```typescript
export function tokenCountWithEstimation(
  messageNumberAndTokens: MessageNumberAndTokens,
  allMessages: Message[],
): number {
  // Find the most recent message with real API usage data
  let highestNumber = -1
  let bestInputTokens = 0
  for (const [num, tokens] of messageNumberAndTokens) {
    if (tokens?.input && num > highestNumber) {
      highestNumber = num
      bestInputTokens = tokens.input
    }
  }

  if (highestNumber === -1) {
    // No API response yet — fall back to pure estimation
    return allMessages.reduce((sum, msg) => sum + estimateTokens(msg), 0)
  }

  // Use real API usage as the anchor, estimate only for messages added since
  const messagesSinceLastApiCall = allMessages.slice(highestNumber + 1)
  const estimatedSinceLast = messagesSinceLastApiCall.reduce(
    (sum, msg) => sum + estimateTokens(msg),
    0,
  )
  return bestInputTokens + estimatedSinceLast
}
```

The `estimateTokens()` helper uses 4 bytes/token (2 for JSON):

```typescript
export function estimateTokens(text: string): number {
  const bytesPerToken = text.trim().startsWith('{') ? 2 : 4
  return new TextEncoder().encode(text).length / bytesPerToken
}
```

This avoids the cumulative counter drift that plagues agents that sum estimates on every turn — each API response resets the anchor to ground truth.

For accurate counting, OpenClaude also supports:
- **API-based counting** (`countMessagesTokensWithAPI`) — calls provider's token count endpoint directly
- **Haiku fallback** (`countTokensViaHaikuFallback`) — uses a small/fast model when API count is unavailable

**Key files:** `src/services/tokenEstimation.ts`, `src/utils/tokens.ts`

## The 5-Tier System

### Tier 1: Microcompact (Before Every Call)

**Key file:** `src/services/compact/microCompact.ts`

Two paths:

**Cached microcompact** — Uses Anthropic's `cache_edits` API to delete old tool results **server-side** without invalidating the cached prefix. Messages are returned unchanged locally — deletions happen at the API layer. Triggered by count-based thresholds from GrowthBook config.

**Time-based microcompact** — When 60+ minutes have passed since the last assistant message, replaces old tool result content with `"[Old tool result content cleared]"`. This triggers because the server-side prompt cache (1h TTL) has already expired, so the full prefix will be rewritten regardless.

Compactable tools: file read, shell, grep, glob, web search, web fetch, file edit, file write.

### Tier 2: API Context Management (Server-Side Editing)

**Key file:** `src/services/compact/apiMicrocompact.ts`

Uses Anthropic's `context_management` API beta (`clear_tool_uses_20250919` and `clear_thinking_20251015` strategies):

```typescript
const DEFAULT_MAX_INPUT_TOKENS = 180_000    // trigger when prompt exceeds this
const DEFAULT_TARGET_INPUT_TOKENS = 40_000  // keep the last 40K tokens
```

The API request includes `context_management: contextManagement`. This is **server-side** — the API itself removes old tool results and thinking blocks without client-side summarization.

### Tier 3: Session Memory Compaction (First Auto-Compact Attempt)

**Key file:** `src/services/compact/sessionMemoryCompact.ts`

A **prefix-preserving** compaction that uses a persistently-maintained markdown file as the summary:

1. Uses `.claude/session-memory.md` (maintained by a background forked agent) as the summary
2. Calculates which messages to keep starting from `lastSummarizedMessageId`
3. Expands backwards to meet minimum thresholds (10K tokens, 5 text-block messages) with max cap of 40K tokens
4. Ensures tool_use/tool_result pairs and thinking blocks are not split
5. Preserves all messages after the calculated start index verbatim

The session memory runs as a post-sampling hook (`src/services/SessionMemory/sessionMemory.ts`), continuously updating the markdown file as the conversation progresses. When compaction is needed, the summary already exists — no extra API call required.

Config defaults:
```typescript
export const DEFAULT_SM_COMPACT_CONFIG: SessionMemoryCompactConfig = {
  minTokens: 10_000,
  minTextBlockMessages: 5,
  maxTokens: 40_000,
}
```

### Tier 4: Full Compaction (Fallback)

**Key file:** `src/services/compact/compact.ts`

When session memory is insufficient, a **full summarization** approach:

1. Strips images from messages (not needed for summarization)
2. Strips reinjected attachments (skill discovery/listing)
3. Executes pre-compact hooks
4. Sends ALL messages to a forked agent with the compact prompt
5. The LLM produces a structured 9-section summary: Primary Request, Key Concepts, Files/Code, Errors/Fixes, Problem Solving, All User Messages, Pending Tasks, Current Work, Next Steps
6. Handles `prompt_too_long` errors by truncating oldest API-round groups and retrying (up to `MAX_PTL_RETRIES = 3`)
7. The `<analysis>` scratchpad is stripped; only `<summary>` is kept
8. After compaction, post-compact attachments are re-injected:
   - File read state (up to 5 files, 50K token budget, 5K per file)
   - Skill invocations (25K token budget, 5K per skill)
   - Plan attachment, tool/MCP instruction deltas, hook outputs

### Tier 5: PTL Retry Truncation (Emergency Escape Hatch)

When the compact request itself hits prompt-too-long, `truncateHeadForPTLRetry()` drops the oldest API-round groups:
- If the token gap is parseable: drops groups until the gap is covered
- Otherwise: drops 20% of groups as a fallback
- Always keeps at least one group to summarize
- Prepends `[earlier conversation truncated for compaction retry]`
- Retries up to 3 times (`MAX_PTL_RETRIES = 3`)

## Thresholds

```typescript
AUTOCOMPACT_BUFFER_TOKENS = 13_000       // triggers auto-compact
WARNING_THRESHOLD_BUFFER_TOKENS = 20_000 // shows warning to user
ERROR_THRESHOLD_BUFFER_TOKENS = 20_000   // shows error state
MANUAL_COMPACT_BUFFER_TOKENS = 3_000     // hard blocking limit
```

The auto-compact threshold: `effectiveContextWindow - 13_000`
For a 200K window: 187,000 tokens triggers auto-compact.

`getEffectiveContextWindowSize()` reserves space for the compaction summary:
```typescript
const MAX_OUTPUT_TOKENS_FOR_SUMMARY = 20_000
return contextWindow - min(getMaxOutputTokensForModel(model), MAX_OUTPUT_TOKENS_FOR_SUMMARY)
```

## Context Window Size Resolution

Priority chain in `getContextWindowForModel()`:
1. `CLAUDE_CODE_MAX_CONTEXT_TOKENS` env var override
2. `[1m]` suffix in model name — explicit 1,000,000 token opt-in
3. Model capability registry (Sonnet 4, Opus 4-6 → 1M via beta header)
4. OpenAI-compatible model lookup from `openaiContextWindows.ts` (gpt-4o=128K, gpt-5.4=1,050,000, etc.)
5. Falls back to `MODEL_CONTEXT_WINDOW_DEFAULT = 200,000`

## Circuit Breaker

After 3 consecutive auto-compact failures, the circuit breaker trips and auto-compact is permanently disabled for that session.

**Key file:** `src/services/compact/autoCompact.ts` — `MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES = 3`

## JSONL History Persistence

**Key file:** `src/history.ts`

OpenClaude adds optional JSONL history persistence to a global `history.jsonl` file (shared across projects):
- `MAX_HISTORY_ITEMS = 100` — maximum history items retained
- `MAX_PASTED_CONTENT_LENGTH = 1024` — pasted content above this size is stored by hash reference in an external paste store
- Supports reverse reading from disk (`readLinesReverse`)
- Pending entries buffered in memory before flush
- Lock-based concurrent writes
- Undo of the most recent entry (`removeLastFromHistory`)

This is separate from the in-memory context — it provides crash recovery and session replay capabilities.

## Configuration Overrides

OpenClaude supports extensive environment variable overrides:

| Variable | Purpose |
|----------|---------|
| `CLAUDE_CODE_MAX_CONTEXT_TOKENS` | Override effective context window |
| `CLAUDE_CODE_AUTO_COMPACT_WINDOW` | Override auto-compact window size |
| `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` | Set auto-compact threshold as percentage |
| `CLAUDE_CODE_BLOCKING_LIMIT_OVERRIDE` | Override the blocking limit |
| `DISABLE_COMPACT` / `DISABLE_AUTO_COMPACT` | Disable compaction |
| `CLAUDE_CODE_DISABLE_1M_CONTEXT` | Disable 1M context window |
| `CLAUDE_CONTEXT_COLLAPSE` | Enable context collapse feature |

## Key Files

| File | Role |
|------|------|
| `src/utils/messages.ts` | `normalizeMessagesForAPI()` — final message normalization |
| `src/utils/tokens.ts` | `tokenCountWithEstimation()` — hybrid token counting |
| `src/utils/context.ts` | `getContextWindowForModel()` — context window resolution |
| `src/services/tokenEstimation.ts` | API-based and fallback token estimation |
| `src/services/compact/microCompact.ts` | Tool result clearing (cached + time-based) |
| `src/services/compact/apiMicrocompact.ts` | API-level `context_management` beta |
| `src/services/compact/sessionMemoryCompact.ts` | Prefix-preserving compaction via session memory |
| `src/services/compact/compact.ts` | Full conversation compaction (summarization) |
| `src/services/compact/autoCompact.ts` | Auto-compact trigger logic and thresholds |
| `src/services/compact/prompt.ts` | Compact prompt templates (full, partial variants) |
| `src/services/SessionMemory/sessionMemory.ts` | Background session memory extraction |
| `src/history.ts` | JSONL history persistence with crash recovery |
| `src/context.ts` | System context construction (memoized) |
