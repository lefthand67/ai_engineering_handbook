
---
title: OpenCode/KiloCode Subagent Orchestration Analysis
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: 2026-04-26
description: Technical analysis of the subagent delegation and session isolation mechanism
  in OpenCode (and its fork KiloCode)
tags:
- architecture
- agents
options:
  type: guide
  birth: 2026-04-26
  version: 1.1.0
  token_size: 1285
---
# OpenCode/KiloCode Subagent Orchestration Analysis

OpenCode implements a hierarchical agent delegation system where a primary agent can spawn specialized subagents via the `Task` tool. This creates a recursive session model where subagents operate in isolated contexts but share the same physical workspace.

## 1. Delegation Mechanism: The `Task` Tool

The primary mechanism for spawning subagents is the `TaskTool`, implemented in `/packages/opencode/src/tool/task.ts`.

### 1.1 Tool Parameters
The delegation is triggered by a structured tool call with the following schema:

```typescript
// /packages/opencode/src/tool/task.ts
export const Parameters = Schema.Struct({
  description: Schema.String.annotate({ description: "A short (3-5 words) description of the task" }),
  prompt: Schema.String.annotate({ description: "The task for the agent to perform" }),
  subagent_type: Schema.String.annotate({ description: "The type of specialized agent to use for this task" }),
  task_id: Schema.optional(Schema.String).annotate({
    description: "This should only be set if you mean to resume a previous task...",
  }),
  command: Schema.optional(Schema.String).annotate({ description: "The command that triggered this task" }),
})
```

### 1.2 Execution Flow
When `TaskTool.execute` is called, the following sequence occurs:

1. **Agent Resolution**: The system resolves the specialized agent using `Agent.Service`.
   ```typescript
   const next = yield* agent.get(params.subagent_type)
   ```
2. **Session Instantiation**: A new session is created and linked to the primary session via `parentID`.
   ```typescript
   const nextSession =
     session ??
     (yield* sessions.create({
       parentID: ctx.sessionID,
       title: params.description + ` (@${next.name} subagent)`,
       // ... permissions
     }))
   ```
3. **Recursive Loop Trigger**: The `TaskTool` invokes the `prompt` operation from `TaskPromptOps`, which triggers a new LLM loop for the subagent.
   ```typescript
   const result = yield* ops.prompt({
     messageID,
     sessionID: nextSession.id,
     model: { modelID: model.modelID, providerID: model.providerID },
     agent: next.name,
     tools: { ... },
     parts,
   })
   ```

## 2. Session Isolation and Security

### 2.1 Context Isolation
Isolation is achieved through the `Session` model. Each subagent gets a unique `sessionID`, ensuring:
- **Independent Message History**: Subagents do not see the primary agent's full history unless explicitly passed in the `prompt`.
- **Recursive State**: The `parentID` linkage allows the system to track the lineage of delegation.

### 2.2 Permission Gating (Default-Deny)
OpenCode employs a strict permission model to prevent subagents from escalating privileges. In `/packages/opencode/src/tool/task.ts`, the system explicitly checks for `todowrite` and `task` (delegation) permissions.

If the resolved `next` agent does not explicitly possess these permissions, they are forcefully denied in the subagent's session configuration:

```typescript
// /packages/opencode/src/tool/task.ts
const canTask = next.permission.some((rule) => rule.permission === id)
const canTodo = next.permission.some((rule) => rule.permission === "todowrite")

// ... inside sessions.create
permission: [
  ...(canTodo
    ? []
    : [{ permission: "todowrite" as const, pattern: "*" as const, action: "deny" as const }]),
  ...(canTask
    ? []
    : [{ permission: id, pattern: "*" as const, action: "deny" as const }]),
  // ...
]
```

## 3. Orchestration Loop

The recursive nature of the system is managed in `/packages/opencode/src/session/prompt.ts`.

The `SessionPrompt.Service` provides the `prompt` method used by `TaskTool`. When a subagent is invoked, it enters a `runLoop` (via `SessionPrompt.runner`), which can in turn call the `TaskTool` again, enabling N-level deep delegation.

### 3.1 Result Integration
Once the subagent's loop terminates, the `TaskTool` wraps the result in a specific XML-like tag to signal the primary agent:

```typescript
return {
  // ...
  output: [
    `task_id: ${nextSession.id} (for resuming to continue this task if needed)`,
    "",
    "<task_result>",
    result.parts.findLast((item) => item.type === "text")?.text ?? "",
    "</task_result>",
  ].join("\n"),
}
```

## Architectural Summary

| Feature | Implementation Detail | File Reference |
| :--- | :--- | :--- |
| **Delegation Tool** | `TaskTool` (via `TaskPromptOps`) | `/packages/opencode/src/tool/task.ts` |
| **Session Linkage** | `parentID` in `sessions.create` | `/packages/opencode/src/tool/task.ts` |
| **Isolation** | Unique `SessionID` per subagent | `/packages/opencode/src/session/schema.ts` |
| **Permission Model** | Explicit `deny` rules for `todowrite`/`task` | `/packages/opencode/src/tool/task.ts` |
| **Recursion** | `SessionPrompt.prompt` $\rightarrow$ `runLoop` $\rightarrow$ `TaskTool` | `/packages/opencode/src/session/prompt.ts` |
