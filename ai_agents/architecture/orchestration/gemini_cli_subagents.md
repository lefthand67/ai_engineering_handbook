
---
title: Gemini CLI Subagents Analysis
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: '2026-05-02'
description: Technical analysis of the subagent orchestration and activity streaming
  in Gemini CLI
tags:
- architecture
- agents
options:
  type: guide
  birth: '2026-04-26'
  version: 1.0.1
  token_size: 1277
---
# Gemini CLI Subagents Analysis

Gemini CLI implements a **Supervisor-Worker** pattern where the primary agent orchestrates sub-tasks via a unified `AgentTool`. The system emphasizes real-time observability through a structured activity bridge.

## 1. Calling Mechanism

### 1.1 The `AgentTool` Dispatcher
Subagents are invoked through a declarative tool that handles definition lookup and invocation routing.

**Evidence**: `AgentTool` and `DelegateInvocation` in `packages/core/src/agents/agent-tool.ts`.
```typescript
// packages/core/src/agents/agent-tool.ts
export class AgentTool extends BaseDeclarativeTool<
  { agent_name: string; prompt: string },
  ToolResult
> {
  // ...
  protected createInvocation(
    params: { agent_name: string; prompt: string },
    messageBus: MessageBus,
    // ...
  ): ToolInvocation<{ agent_name: string; prompt: string }, ToolResult> {
    const registry = this.context.config.getAgentRegistry();
    const definition = registry.getDefinition(params.agent_name);
    // ...
    return new DelegateInvocation(
      params,
      mappedInputs,
      messageBus,
      definition,
      this.context,
      // ...
    );
  }
}
```

**Explanation**: The `AgentTool` acts as a factory. It retrieves the agent's definition from a registry and wraps the execution in a `DelegateInvocation`, which then selects the concrete execution strategy (`LocalSubagentInvocation`, `RemoteAgentInvocation`, or `BrowserAgentInvocation`) based on the agent's `kind`.

### 1.2 Smart Parameter Mapping
The system automatically maps the general `prompt` string to the subagent's specific input schema.

**Evidence**: `mapParams` method in `AgentTool` (`packages/core/src/agents/agent-tool.ts`).
```typescript
// packages/core/src/agents/agent-tool.ts
private mapParams(prompt: string, schema: unknown): AgentInputs {
  // ...
  const properties = schemaObj['properties'];
  if (isRecord(properties)) {
    const keys = Object.keys(properties);
    if (keys.length === 1) {
      return { [keys[0]]: prompt };
    }
  }
  return { prompt };
}
```

**Explanation**: If the target subagent's input schema defines exactly one property, the `prompt` is mapped to that key. This allows the supervisor to use a consistent tool interface while supporting subagents with specialized input schemas.

## 2. Execution and Observability

### 2.1 Real-time Activity Bridge
Gemini CLI bridges the internal events of the `LocalAgentExecutor` to the user interface and internal logging.

**Evidence**: `onActivity` callback in `LocalSubagentInvocation.execute` (`packages/core/src/agents/local-invocation.ts`).
```typescript
// packages/core/src/agents/local-invocation.ts
const onActivity = (activity: SubagentActivityEvent): void => {
  if (!updateOutput) return;

  switch (activity.type) {
    case 'THOUGHT_CHUNK': {
      // ... sanitize and append to recentActivity
      recentActivity.push({
        id: randomUUID(),
        type: 'thought',
        content: sanitizeThoughtContent(text),
        status: 'running',
      });
      // ...
    }
    case 'TOOL_CALL_START': {
      // ... pushes 'tool_call' activity with args
    }
    // ...
  }
  // ... updateOutput(progress);
};
```

**Explanation**: The `LocalSubagentInvocation` creates a bridge that transforms internal agent events (like `THOUGHT_CHUNK` or `TOOL_CALL_START`) into `SubagentActivityItem` objects. These are then streamed via `updateOutput` (for the UI) and `MessageBus` (for internal policy/logging).

### 2.2 User Steering via Injections
The system supports "steering" remote subagents by injecting user-provided hints into the prompt.

**Evidence**: `withUserHints` method in `DelegateInvocation` (`packages/core/src/agents/agent-tool.ts`).
```typescript
// packages/core/src/agents/agent-tool.ts
private withUserHints(agentArgs: AgentInputs): AgentInputs {
  if (this.definition.kind !== 'remote') {
    return agentArgs;
  }

  const userHints = this.context.config.injectionService.getInjectionsAfter(
    this.startIndex,
    'user_steering',
  );
  const formattedHints = formatUserHintsForModel(userHints);
  // ... appends formattedHints to the primary input key
}
```

**Explanation**: For remote agents, the `DelegateInvocation` queries the `injectionService` for `user_steering` hints that occurred after the tool call was initiated. These hints are prepended to the subagent's prompt, allowing the user to refine the subagent's direction without restarting the process.

## Architectural Summary

| Feature | Implementation Detail | File Reference |
| :--- | :--- | :--- |
| **Routing** | `AgentTool` $\rightarrow$ `DelegateInvocation` $\rightarrow$ `Local/Remote/BrowserInvocation` | `agent-tool.ts` |
| **Input Mapping** | Single-property schema auto-mapping | `agent-tool.ts` |
| **Observability** | Event-driven activity bridge $\rightarrow$ `MessageBus` | `local-invocation.ts` |
| **Steering** | `user_steering` injection for remote agents | `agent-tool.ts` |
| **State** | Isolated registries per subagent | `local-invocation.ts` |
| **UI Feedback** | Streaming `SubagentProgress` updates | `local-invocation.ts` |
