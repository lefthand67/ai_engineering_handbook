
---
title: 'Claude Code: Subagent Implementation Analysis'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: '2026-04-26'
description: Technical analysis of the forked agent mechanism and subagent isolation
  in Claude Code
tags:
- agents
- architecture
- development
options:
  type: guide
  birth: '2026-04-26'
  version: 1.0.0
  token_size: 1445
---
# Claude Code: Subagent Implementation Analysis

Claude Code implements a **Forked Agent** pattern to execute isolated sub-tasks. This mechanism allows the primary agent to delegate work to specialized workers without polluting the main session history or inducing unstable state mutations.

## 1. Calling Mechanism

### 1.1 Initiation via `runForkedAgent`
Subagents are initiated through a specialized query loop that clones a snapshot of the parent's context.

```typescript
// /src/utils/forkedAgent.ts
export async function runForkedAgent({
  promptMessages,
  cacheSafeParams,
  // ...
}: ForkedAgentParams): Promise<ForkedAgentResult> {
  // ...
  const isolatedToolUseContext = createSubagentContext(
    toolUseContext,
    overrides,
  )
  // ...
  for await (const message of query({
    // ...
    toolUseContext: isolatedToolUseContext,
    // ...
  })) {
    // ...
  }
}
```

**Explanation**: The `runForkedAgent` function encapsulates the entire lifecycle of a subagent, from context isolation via `createSubagentContext` to the execution of the `query` loop.

## 2. Context Isolation and State Management

### 2.1 Mutable State Isolation
Claude Code prevents subagents from accidentally modifying the parent's state by replacing mutation callbacks with no-ops.

```typescript
// /src/utils/forkedAgent.ts
export function createSubagentContext(
  parentContext: ToolUseContext,
  overrides?: SubagentContextOverrides,
): ToolUseContext {
  return {
    // ...
    readFileState: cloneFileStateCache(
      overrides?.readFileState ?? parentContext.readFileState,
    ),
    // ...
    setAppState: overrides?.shareSetAppState
      ? parentContext.setAppState
      : () => {},
    setResponseLength: overrides?.shareSetResponseLength
      ? parentContext.setResponseLength
      : () => {},
    // ...
  }
}
```

**Explanation**: 
- **File State**: `readFileState` is cloned using `cloneFileStateCache`, ensuring the subagent has its own view of the file system cache.
- **Mutation Callbacks**: `setAppState` and `setResponseLength` are set to `() => {}` by default. This ensures that any state updates attempted by the subagent are ignored unless `shareSetAppState` or `shareSetResponseLength` is explicitly enabled in the `SubagentContextOverrides`.

### 2.2 Abort Propagation
Subagents use a linked `AbortController` hierarchy.

```typescript
// /src/utils/forkedAgent.ts
const abortController =
    overrides?.abortController ??
    (overrides?.shareAbortController
      ? parentContext.abortController
      : createChildAbortController(parentContext.abortController))
```

**Explanation**: By using `createChildAbortController(parentContext.abortController)`, Claude Code ensures that aborting the parent agent automatically triggers the abort of all active subagents, while aborting a subagent remains local to that fork.

## 3. Performance and Observability

### 3.1 Prompt Cache Optimization
To minimize latency and cost, subagents are designed to hit the Anthropic API prompt cache by mirroring the parent's request prefix.

```typescript
// /src/utils/forkedAgent.ts
export type CacheSafeParams = {
  systemPrompt: SystemPrompt
  userContext: { [k: string]: string }
  systemContext: { [k: string]: string }
  toolUseContext: ToolUseContext
  forkContextMessages: Message[]
}
```

**Explanation**: The `CacheSafeParams` structure captures the exact parameters required to maintain the API cache key. By passing these identical parameters to the subagent's `query` call, the system ensures that the parent's already-cached prefix is reused.

### 3.2 Sidechain Logging
Subagent interactions are recorded as "sidechains" rather than being appended to the main conversation.

```typescript
// /src/utils/forkedAgent.ts
if (agentId) {
  await recordSidechainTranscript(initialMessages, agentId).catch(err =>
    logForDebugging(`Forked agent [${forkLabel}] failed to record initial transcript: ${err}`),
  )
}
```

**Explanation**: Using `recordSidechainTranscript` allows the system to store the subagent's full dialogue history in a separate storage bucket, keeping the primary session transcript clean and focused on the user's high-level goals.

### 3.3 Telemetry and Metrics
Subagent efficiency is tracked via a specific analytics event.

```typescript
// /src/utils/forkedAgent.ts
function logForkAgentQueryEvent({
  forkLabel,
  // ...
  totalUsage,
  // ...
}: { ... }): void {
  const totalInputTokens =
    totalUsage.input_tokens +
    totalUsage.cache_creation_input_tokens +
    totalUsage.cache_read_input_tokens
  const cacheHitRate =
    totalInputTokens > 0
      ? totalUsage.cache_read_input_tokens / totalInputTokens
      : 0

  logEvent('tengu_fork_agent_query', {
    forkLabel,
    // ...
    cacheHitRate,
    // ...
  })
}
```

**Explanation**: The `logForkAgentQueryEvent` function calculates the `cacheHitRate` (cache read tokens vs total input tokens) and logs it as `tengu_fork_agent_query`, providing visibility into the effectiveness of the `CacheSafeParams` strategy.

## Architectural Summary

| Feature | Implementation Detail | File Reference |
| :--- | :--- | :--- |
| **Orchestration** | Forked Query Loop (`runForkedAgent`) | `/src/utils/forkedAgent.ts` |
| **State Isolation** | Clone-on-Fork + No-op mutation stubs | `/src/utils/forkedAgent.ts` |
| **Lifecycle** | Parent-linked `AbortController` | `/src/utils/forkedAgent.ts` |
| **Caching** | `CacheSafeParams` mirror | `/src/utils/forkedAgent.ts` |
| **History** | Sidechain recording (`recordSidechainTranscript`) | `/src/utils/forkedAgent.ts` |
| **Telemetry** | `tengu_fork_agent_query` event | `/src/utils/forkedAgent.ts` |
