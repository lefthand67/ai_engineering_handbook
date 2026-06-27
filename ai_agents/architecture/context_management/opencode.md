---
title: Context Management — OpenCode
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Deep dive into OpenCode's reactive compaction — SQLite-backed message
  storage, dedicated compaction agent with structured summaries, and tool output pruning.
tags:
- architecture
- agents
date: '2026-04-05'
options:
  version: 1.0.0
  birth: '2026-04-05'
  type: guide
  token_size: 2213
---
# Context Management — OpenCode

**Agent version:** v1.3.15 (commit `280eb16e`)
**Analysis date:** 2026-04-05

## Architecture Overview

OpenCode uses a **persistent SQLite database** with a Message/Part data model. Every conversation turn is stored immediately as it happens. Messages are NOT kept in memory across API calls — they are persisted to SQLite after every step and streamed back on demand.

### Storage Schema

- `MessageTable` — stores message metadata (role, agent, model, tokens, cost, finish reason) as JSON in the `data` column
- `PartTable` — stores individual parts (text, tool calls, tool results, reasoning, compaction markers, snapshots) as JSON in the `data` column

**Key file:** `packages/opencode/src/session/session.sql.ts` (lines 45–72)

## History Transmission

Messages are streamed from disk in **reverse chronological order** (newest first) with pagination (page size 50), then reversed. On every API call iteration, the main loop reads ALL non-compacted messages via `MessageV2.filterCompactedEffect(sessionID)`, converts them to model format, and sends the full set.

```typescript
let msgs = yield* MessageV2.filterCompactedEffect(sessionID)
const modelMsgs = yield* Effect.promise(() => MessageV2.toModelMessages(msgs, model))
const result = yield* handle.process({
  messages: [...modelMsgs, ...],  // full history
  // ...
})
```

**Key file:** `packages/opencode/src/session/prompt.ts` (lines 1345, 1505, 1510–1514)

### Compaction Boundaries: `filterCompacted`

The `filterCompacted` function streams messages from the database in reverse order and **stops** when it hits a compaction boundary:

```typescript
export function filterCompacted(msgs: Iterable<MessageV2.WithParts>) {
  const result = [] as MessageV2.WithParts[]
  const completed = new Set<string>()
  for (const msg of msgs) {
    result.push(msg)
    if (
      msg.info.role === "user" &&
      completed.has(msg.info.id) &&
      msg.parts.some((part) => part.type === "compaction")
    )
      break  // stops including history before this compaction point
    if (msg.info.role === "assistant" && msg.info.summary && msg.info.finish && !msg.info.error)
      completed.add(msg.info.parentID)
  }
  result.reverse()
  return result
}
```

After compaction, the next API call only receives:
- The compaction summary (as a user message)
- Any messages after the compaction point

**Key file:** `packages/opencode/src/session/message-v2.ts` (lines 903–918)

## Token Counting

`isOverflow()` in `overflow.ts`:

```typescript
const COMPACTION_BUFFER = 20_000

export function isOverflow(input: { cfg; tokens; model }) {
  if (input.cfg.compaction?.auto === false) return false
  const context = input.model.limit.context
  if (context === 0) return false

  const count = input.tokens.total ||
    input.tokens.input + input.tokens.output + input.tokens.cache.read + input.tokens.cache.write

  const reserved = input.cfg.compaction?.reserved ??
    Math.min(COMPACTION_BUFFER, ProviderTransform.maxOutputTokens(input.model))
  const usable = input.model.limit.input
    ? input.model.limit.input - reserved
    : context - ProviderTransform.maxOutputTokens(input.model)
  return count >= usable
}
```

Compaction triggers when cumulative tokens reach `usable = context - reserved` where `reserved` defaults to 20,000 tokens (or the model's max output, whichever is smaller).

Token estimation for pruning uses a rough heuristic: `chars / 4` tokens.

**Key file:** `packages/opencode/src/session/overflow.ts`

## Compaction: Dedicated Agent

When overflow is detected, a dedicated **compaction agent** is invoked:

1. Takes the full message history up to that point
2. Strips media from messages (`stripMedia: true`)
3. Appends a structured summarization prompt
4. The compaction agent has **all tools denied** — it is a pure summarization agent

### Structured Summary Prompt

```
Provide a detailed prompt for continuing our conversation above.
Focus on information that would be helpful for continuing the conversation,
including what we did, what we're doing, which files we're working on,
and what we're going to do next.

Stick to this template:
---
## Goal
[What goal(s) is the user trying to accomplish?]

## Instructions
- [What important instructions did the user give you?]

## Discoveries
[What notable things were learned during this conversation?]

## Accomplished
[What work has been completed, in progress, and left?]

## Relevant files / directories
[Construct a structured list of relevant files.]
---
```

### Compaction Agent Definition

```typescript
compaction: {
  name: "compaction",
  mode: "primary",
  native: true,
  hidden: true,
  prompt: PROMPT_COMPACTION,
  permission: Permission.merge(defaults, Permission.fromConfig({ "*": "deny" }), user),
  options: {},
}
```

All tools denied — pure summarization.

**Key file:** `packages/opencode/src/session/compaction.ts` (lines 99–293, 183–203)
**Key file:** `packages/opencode/src/agent/agent.ts` (lines 188–203)

## Pruning Old Tool Outputs

Before compaction, a "pruning" step removes old tool call outputs:

```typescript
export const PRUNE_MINIMUM = 20_000
export const PRUNE_PROTECT = 40_000
const PRUNE_PROTECTED_TOOLS = ["skill"]
```

The algorithm walks backwards through parts, accumulating token count until it hits the protect zone:

```typescript
let tokensSinceLastProtection = 0
const toPrune: Part[] = []

for (const part of partsInReverse) {
  if (part.type === "tool" && !PRUNE_PROTECTED_TOOLS.includes(part.toolName)) {
    if (tokensSinceLastProtection >= PRUNE_PROTECT) {
      toPrune.push(part)
    } else {
      tokensSinceLastProtection += estimateTokens(part.state.output)
    }
  }
}

// Only commit if we found enough to prune
if (toPrune.reduce((sum, p) => sum + estimateTokens(p.state.output), 0) > PRUNE_MINIMUM) {
  for (const part of toPrune) {
    part.state.time.compacted = Date.now()
    await Session.updatePart(part)
  }
}
```

When a tool part is marked with `time.compacted`, its output is replaced with `"[Old tool result content cleared]"` during `toModelMessagesEffect`.

**Key file:** `packages/opencode/src/session/compaction.ts` (lines 93–141)

## Tool Output Truncation

Individual tool outputs are truncated to prevent excessively large results:

```typescript
export const MAX_LINES = 2000
export const MAX_BYTES = 50 * 1024  // 50 KB
```

When tool output exceeds these limits, the first 2000 lines (or 50KB) are kept, and a hint is appended directing the agent to read the full output from a saved file if needed.

**Key file:** `packages/opencode/src/tool/truncate.ts`

## Overflow Error Detection

Comprehensive error pattern matching for 15+ providers:

```typescript
const OVERFLOW_PATTERNS = [
  /prompt is too long/i,                     // Anthropic
  /input is too long for requested model/i,  // Amazon Bedrock
  /exceeds the context window/i,             // OpenAI
  /input token count.*exceeds the maximum/i, // Google Gemini
  /maximum context length is \d+ tokens/i,  // OpenRouter, DeepSeek, vLLM
  /context window exceeds limit/i,           // MiniMax
  /model_context_window_exceeded/i,          // z.ai
]
```

When a context overflow error is caught, `needsCompaction = true` is set and the stream stops. If compaction also fails, the session is marked as error and stops.

**Key file:** `packages/opencode/src/provider/error.ts` (lines 10–29)

## Media Stripping During Compaction

When compacting, media (images, PDFs) are stripped and replaced with placeholders:

```typescript
[Attached ${part.mime}: ${part.filename ?? "file"}]
```

**Key file:** `packages/opencode/src/session/message-v2.ts` (lines 660–664)

## Key Files

| File | Role |
|------|------|
| `packages/opencode/src/session/prompt.ts` | Main loop — `filterCompactedEffect`, `toModelMessages`, LLM call |
| `packages/opencode/src/session/message-v2.ts` | `filterCompacted`, `toModelMessagesEffect` — history reconstruction |
| `packages/opencode/src/session/compaction.ts` | Compaction agent, pruning, structured summary prompt |
| `packages/opencode/src/session/overflow.ts` | `isOverflow()` — token count vs. context threshold |
| `packages/opencode/src/session/session.sql.ts` | SQLite schema (MessageTable + PartTable) |
| `packages/opencode/src/session/processor.ts` | Stream processing, overflow error handling |
| `packages/opencode/src/tool/truncate.ts` | Per-tool output truncation (2000 lines / 50KB) |
| `packages/opencode/src/provider/error.ts` | Context overflow pattern matching (15+ providers) |
| `packages/opencode/src/agent/agent.ts` | Compaction agent definition (all tools denied) |
