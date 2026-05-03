
---
title: Context Management — Claude Code
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: '2026-04-05'
description: Deep dive into Claude Code's 5-tier context management system — microcompact,
  API-level cache editing, session memory, full compaction, and PTL retry truncation.
tags:
- architecture
- agents
options:
  version: 1.0.0
  birth: '2026-04-05'
  type: guide
  token_size: 2246
---
# Context Management — Claude Code

**Agent version:** (no tag) — commit `3da7e321`
**Analysis date:** 2026-04-05

## Architecture Overview

Claude Code maintains an in-memory `Message[]` array that is rebuilt and sent to the LLM on every API call. There is no persistent server-side session — context lives in memory for the duration of the process.

Message types (`src/types/message.ts`):
- `UserMessage` — user input (text, tool_results, pasted content)
- `AssistantMessage` — model output (text, tool_use, thinking blocks)
- `SystemMessage` — system prompts and metadata
- `AttachmentMessage` — system-injected context (git status, CLAUDE.md, skills, MCP instructions)
- `HookResultMessage` — output from pre/post-compact hooks

Before sending, messages are normalized through `normalizeMessagesForAPI()`:
1. Reorders attachments to bubble them up
2. Strips virtual/display-only messages
3. Merges consecutive user messages (Bedrock API requirement)
4. Strips tool_reference blocks for unavailable tools
5. Strips images/documents that caused "too large" errors
6. Filters progress and synthetic error messages

**Key file:** `src/utils/messages.ts` — `normalizeMessagesForAPI()` (line ~1989)

## Context Prefix

System context is constructed from two cached functions:
- `getSystemContext()` — git status (truncated to 2000 chars), cache-breaker injection
- `getUserContext()` — CLAUDE.md files, current date

Both are memoized and cached for the conversation duration.

**Key file:** `src/context.ts`

## Token Counting

`tokenCountWithEstimation()` (`src/utils/tokens.ts`) uses a **hybrid approach** that avoids double-counting drift:

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
  // 4 bytes per token for prose, 2 for JSON/structured content
  const bytesPerToken = text.trim().startsWith('{') ? 2 : 4
  return new TextEncoder().encode(text).length / bytesPerToken
}
```

This avoids the cumulative counter drift that plagues agents that sum estimates on every turn — each API response resets the anchor to ground truth.

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

### Tier 4: Full Compaction (Fallback)

**Key file:** `src/services/compact/compact.ts`

When session memory is insufficient, a **full summarization** approach:

1. Sends ALL messages to a forked agent with the compact prompt
2. The LLM produces a structured 9-section summary: Primary Request, Key Concepts, Files/Code, Errors/Fixes, Problem Solving, All User Messages, Pending Tasks, Current Work, Next Steps
3. The `<analysis>` scratchpad is stripped; only `<summary>` is kept
4. After compaction, post-compact attachments are re-injected:
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
3. Model capability registry
4. Beta header `context-1m-2025-07-21` + model supports 1M
5. Sonnet 4.6 experimental treatment
6. Falls back to `MODEL_CONTEXT_WINDOW_DEFAULT = 200,000`

## Circuit Breaker

After 3 consecutive auto-compact failures, the circuit breaker trips and auto-compact is permanently disabled for that session.

**Key file:** `src/services/compact/autoCompact.ts` — `MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES = 3`

## Key Files

| File | Role |
|------|------|
| `src/utils/messages.ts` | `normalizeMessagesForAPI()` — final message normalization |
| `src/utils/tokens.ts` | `tokenCountWithEstimation()` — hybrid token counting |
| `src/utils/context.ts` | `getContextWindowForModel()` — context window resolution |
| `src/services/api/claude.ts` | `queryModelWithStreaming()` — API client |
| `src/services/compact/microCompact.ts` | Tool result clearing (cached + time-based) |
| `src/services/compact/apiMicrocompact.ts` | API-level `context_management` beta |
| `src/services/compact/sessionMemoryCompact.ts` | Prefix-preserving compaction via session memory |
| `src/services/compact/compact.ts` | Full conversation compaction (summarization) |
| `src/services/compact/autoCompact.ts` | Auto-compact trigger logic and thresholds |
| `src/services/compact/prompt.ts` | Compact prompt templates (full, partial variants) |
| `src/services/SessionMemory/sessionMemory.ts` | Background session memory extraction |
