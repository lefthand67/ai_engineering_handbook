
---
title: Context Management — Qwen-Code
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: '2026-05-01'
description: Deep dive into Qwen-Code's context management — autocompact buffer, /compress
  command, token limits registry, and JSONL-backed session history reconstruction.
tags:
- architecture
- agents
options:
  version: 1.1.0
  birth: '2026-04-05'
  type: guide
  token_size: 2572
---
# Context Management — Qwen-Code

**Agent version:** v0.14.0 (commit `e8552294`)
**Analysis date:** 2026-04-05

:::{note}
This document focuses on Qwen-Code's **context window management** — the `/compress` mechanism, autocompact buffer, token limits, and history reconstruction. For the JSONL session format, file storage, and session management mechanics, see [Session History in Qwen Code](/ai_agents/architecture/session_history_management/session_history_in_qwen_code.md).
:::

## Architecture Overview

Qwen-Code maintains a `Content[]` history array in memory. On every API call, the **full curated history** is sent via `generateContentStream()`. There is no chunking, no delta-based updates, and no server-side session persistence.

The flow:
1. User message added to history
2. `getHistory(true)` returns the **curated history** — cleaned version with invalid/empty model outputs filtered out
3. Full history sent via `generateContentStream()` with `contents: requestContents`

**Key file:** `packages/core/src/core/geminiChat.ts` (lines ~340–365)

## History Curation: `extractCuratedHistory`

```typescript
function extractCuratedHistory(comprehensiveHistory: Content[]): Content[] {
  const curatedHistory: Content[] = []
  const length = comprehensiveHistory.length
  let i = 0
  while (i < length) {
    if (comprehensiveHistory[i].role === 'user') {
      curatedHistory.push(comprehensiveHistory[i])
      i++
    } else {
      const modelOutput: Content[] = []
      let isValid = true
      while (i < length && comprehensiveHistory[i].role === 'model') {
        modelOutput.push(comprehensiveHistory[i])
        if (isValid && !isValidContent(comprehensiveHistory[i])) {
          isValid = false
        }
        i++
      }
      if (isValid) {
        curatedHistory.push(...modelOutput)
      }
    }
  }
  return curatedHistory
}
```

Filters out invalid/empty model outputs, keeps clean user messages.

**Key file:** `packages/core/src/core/geminiChat.ts` (lines ~170–195)

## Context Window Sizes

Context windows defined via regex pattern matching on model names:

- Qwen3-coder-plus/flash: 1M tokens
- Qwen3-coder-*: 256K tokens
- Claude: 200K tokens
- GPT-5: 272K input (400K total − 128K output)
- Default fallback: 131,072 (128K)

```typescript
export const DEFAULT_TOKEN_LIMIT: TokenCount = 131_072  // 128K (power-of-two)
```

These are also overridable per-model in settings (`contextWindowSize` config field).

**Key file:** `packages/core/src/core/tokenLimits.ts`

## The Autocompact Buffer

```typescript
const DEFAULT_COMPRESSION_THRESHOLD = 0.7  // triggers compression at 70%

const autocompactBuffer = Math.round((1 - compressionThreshold) * contextWindowSize)
```

This reserves ~30% of the context window as a buffer to prevent the model from hitting the hard limit.

**Key file:** `packages/cli/src/ui/commands/contextCommand.ts` (lines ~33, ~219)

## Context Overhead Accounting

The `/context` command breaks down usage into categories:

1. **System prompt** tokens
2. **Tool declarations** (all tools: built-in, MCP, skills) — JSON schema tokens
3. **Memory files** (user memory content)
4. **Skills** (tool definition + loaded skill bodies)
5. **Messages** (conversation history tokens = total − overhead)
6. **Free space** = contextWindowSize − totalTokens − autocompactBuffer

## Compression: `/compress` Command

**Key file:** `packages/core/src/services/chatCompressionService.ts`

### Constants

```typescript
COMPRESSION_TOKEN_THRESHOLD = 0.7    // triggers at 70%
COMPRESSION_PRESERVE_THRESHOLD = 0.3 // keeps last 30%
MIN_COMPRESSION_FRACTION = 0.05      // minimum compressible content
```

### Implementation Analysis

**Claim**: Compression is triggered when the history token count exceeds 70% of the model's context window.
**Evidence**: `packages/core/src/services/chatCompressionService.ts`
```typescript
export const COMPRESSION_TOKEN_THRESHOLD = 0.7;
// ...
if (!force) {
  const contextLimit = config.getContentGeneratorConfig()?.contextWindowSize ?? DEFAULT_TOKEN_LIMIT;
  if (originalTokenCount < threshold * contextLimit) {
    return { ..., compressionStatus: CompressionStatus.NOOP };
  }
}
```
**Explanation**: The service uses a configurable threshold (defaulting to 0.7) to determine if the current `originalTokenCount` warrants an automatic compression cycle.

**Claim**: The history is split to preserve the most recent 30% of the conversation while summarizing the older 70%.
**Evidence**: `packages/core/src/services/chatCompressionService.ts`
```typescript
export const COMPRESSION_PRESERVE_THRESHOLD = 0.3;
// ...
const splitPoint = findCompressSplitPoint(
  historyForSplit,
  1 - COMPRESSION_PRESERVE_THRESHOLD,
);
const historyToCompress = historyForSplit.slice(0, splitPoint);
const historyToKeep = historyForSplit.slice(splitPoint);
```
**Explanation**: `findCompressSplitPoint` calculates a split index based on character counts, ensuring that the trailing 30% of the conversation is kept as-is to maintain immediate context.

**Claim**: The summary is generated by requesting a structured `<state_snapshot>` from the model using a specific system prompt.
**Evidence**: `packages/core/src/services/chatCompressionService.ts`
```typescript
const summaryResponse = await config.getContentGenerator().generateContent({
  model,
  contents: [
    ...historyToCompress,
    {
      role: 'user',
      parts: [{ text: 'First, reason in your scratchpad. Then, generate the <state_snapshot>.' }],
    },
  ],
  config: {
    systemInstruction: getCompressionPrompt(),
  },
});
```
**Explanation**: The agent is instructed to reason in a scratchpad before producing a structured XML-like snapshot, which reduces summarization drift.

**Claim**: Compression is aborted if the resulting compressed history is larger than the original.
**Evidence**: `packages/core/src/services/chatCompressionService.ts`
```typescript
} else if (newTokenCount > originalTokenCount) {
  return {
    newHistory: null,
    info: { ..., compressionStatus: CompressionStatus.COMPRESSION_FAILED_INFLATED_TOKEN_COUNT },
  };
}
```
**Explanation**: This guard prevents "token inflation" where a poor summary actually increases the context window usage.

### Compression Checkpoint in JSONL

**Claim**: Compression results are stored as immutable `system` records with `subtype: "chat_compression"` in the append-only JSONL log.
**Evidence**: Session log analysis (e.g., `57918f6e...jsonl`)
```json
{
  "type": "system",
  "subtype": "chat_compression",
  "systemPayload": {
    "info": { ... },
    "compressedHistory": [ ... ]
  }
}
```
**Explanation**: By appending a checkpoint rather than mutating existing records, the system ensures crash-safety and allows the original UI history to remain intact.

**Claim**: The compressed state is captured as a full `Content[]` snapshot in the `compressedHistory` field.
**Evidence**: Session log analysis
```json
"compressedHistory": [
  {
    "role": "user",
    "parts": [{ "text": "<state_snapshot>\n..." }]
  },
  {
    "role": "model",
    "parts": [{ "text": "Got it. Thanks for the additional context!" }]
  },
  ...
]
```
**Explanation**: The `compressedHistory` field stores exactly what the model should see as its starting history upon session resumption, including the summary and the preserved recent messages.

## API History Reconstruction

**Claim**: The model-facing history is reconstructed by identifying the latest `chat_compression` system record in the session history.
**Evidence**: `packages/core/src/services/sessionService.ts`
```typescript
messages.forEach((record, index) => {
  if (record.type === 'system' && record.subtype === 'chat_compression') {
    const payload = record.systemPayload as
      | ChatCompressionRecordPayload
      | undefined;
    if (payload?.compressedHistory) {
      lastCompressionIndex = index;
      compressedHistory = payload.compressedHistory;
    }
  }
});
```
**Explanation**: The `buildApiHistoryFromConversation` function scans the linear record set to find the most recent compression checkpoint, which serves as the state baseline.

**Claim**: If a compression checkpoint exists, the system initializes the history with the `compressedHistory` snapshot and appends all subsequent non-system messages.
**Evidence**: `packages/core/src/services/sessionService.ts`
```typescript
if (compressedHistory && lastCompressionIndex >= 0) {
  const baseHistory: Content[] = structuredClone(compressedHistory);

  // Append everything after the compression record (newer turns)
  for (let i = lastCompressionIndex + 1; i < messages.length; i++) {
    const record = messages[i];
    if (record.type === 'system') continue;
    if (record.message) {
      baseHistory.push(structuredClone(record.message as Content));
    }
  }
  return baseHistory;
}
```
**Explanation**: This mechanism ensures that the model receives the compressed summary of the old history while maintaining the full detail of the most recent turns.

**Claim**: If no compression checkpoint is found, the system falls back to a linear projection of all available message records.
**Evidence**: `packages/core/src/services/sessionService.ts`
```typescript
// Fallback: return linear messages as Content[]
const result = messages
  .map((record) => record.message)
  .filter((message): message is Content => message !== undefined)
  .map((message) => structuredClone(message));
```
**Explanation**: In the absence of compression, the entire reconstructed conversation is passed to the API.

## Orphaned Entry Stripping

When a model crashes or the user interrupts, `stripOrphanedUserEntriesFromHistory()` cleans up trailing user entries that have no model response.

## Thought Filtering

`stripThoughtsFromHistory()` removes model thinking/reasoning parts (`thought: true`) from history before sending, since those are not part of the actual response content.

## Rate Limit Retries

Up to 10 retries with 60s delays for throttling errors (`RATE_LIMIT_RETRY_OPTIONS`).

## Transient Stream Anomaly Retries

Up to 2 retries with incremental delays for streams that end without a finish reason or with no response text.

## Key Files

| File | Role |
|------|------|
| `packages/core/src/core/geminiChat.ts` | Main chat API — `sendMessageStream()`, `getHistory()`, curation |
| `packages/core/src/core/tokenLimits.ts` | Per-model context window sizes via regex matching |
| `packages/core/src/services/chatCompressionService.ts` | `/compress` command — split, summarize, replace |
| `packages/cli/src/ui/commands/contextCommand.ts` | `/context` command — overhead accounting, autocompact buffer |
| `packages/core/src/services/sessionService.ts` | Session listing, loading, API history reconstruction |
| `packages/core/src/services/chatRecordingService.ts` | JSONL record writing (append-only) |
