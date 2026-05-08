---
title: Qwen Code Tool-Calling Architecture
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: 2026-05-06
description: Deep-dive into the technical implementation of tool steering, selection,
  and execution in Qwen Code, combining source-level evidence with architectural synthesis.
tags:
- agents
- architecture
options:
  type: guide
  birth: 2026-05-06
  version: 1.1.0
  token_size: 1588
---
# Qwen Code Tool-Calling Architecture

This document analyzes how Qwen Code implements its tool-calling system, focusing on the mechanism of "steering"—the process of guiding an LLM to select the correct tool and use it according to project and session constraints.

## 1. The Tool-Calling Loop

Qwen Code implements a classic **Reason $\rightarrow$ Act $\rightarrow$ Observe** loop orchestrated by `AgentCore`.

### 1.1 Cycle Execution
The core logic resides in `AgentCore._runReasoningLoopInner`:
1. **Prompting**: The model is sent a prompt containing the conversation history and the current task.
2. **Tool Selection**: The model produces either a text response or one or more `FunctionCall` requests.
3. **Orchestration**: `AgentCore.processFunctionCalls` validates the requests against the available toolset.
4. **Execution**: `CoreToolScheduler` executes the tools, handling permissions, user approvals, and concurrency.
5. **Observation**: Tool outputs are fed back into the chat history as `functionResponse` parts, and the loop repeats.

**Evidence**: `/packages/core/src/agents/runtime/agent-core.ts`
```typescript
// 1. Send message with tools list
const responseStream = await chat.sendMessageStream(model, messageParams, promptId);

// 2. Process function calls from LLM response
if (response.functionCalls) {
  await this.processFunctionCalls(response.functionCalls);
}
```

## 2. Tool Definition & Discovery

### 2.1 Declarative Tool Surface
Qwen Code uses a declarative approach to tool definition via `BaseDeclarativeTool`. This ensures that the "surface" presented to the LLM is always in sync with the underlying implementation.

- **Type Safety**: Zod schemas are used to define parameter types.
- **Semantic Mapping**: Every tool provides a `description` and `displayName`, which serve as the primary signals for the LLM's semantic matching during selection.

**Evidence**: `/packages/core/src/tools/tools.ts`
```typescript
export abstract class BaseDeclarativeTool extends DeclarativeTool {
  // Defines tool metadata and the JSON schema for LLM consumption
  abstract get name(): string;
  abstract get description(): string;
  abstract get parameterSchema(): ZodSchema;
}
```

### 2.2 Registry & Filtering
Tools are managed by a `ToolRegistry`. `AgentCore.prepareTools()` determines the final set of tools available to a specific agent instance:
- **Inheritance**: By default, agents inherit all registered tools.
- **Explicit Config**: `ToolConfig` can restrict the agent to a specific subset of tools.
- **Subagent Constraints**: To prevent recursive spawning and session instability, certain tools are hard-coded as `EXCLUDED_TOOLS_FOR_SUBAGENTS` (e.g., the `AgentTool` and `Cron` tools).
- **Blocklisting**: `disallowedTools` allows for fine-grained removal of tools or MCP server-level patterns.

**Evidence**: `/packages/core/src/tools/tool-registry.ts`
```typescript
export class ToolRegistry {
  // Aggregates function declarations from all registered tools
  getFunctionDeclarations(): FunctionDeclaration[] {
    return Array.from(this.tools.values()).map(tool => tool.schema);
  }
}
```

## 3. The Three-Tier Steering Model

A key architectural insight in Qwen Code is the separation of steering into three distinct tiers. This prevents the system prompt from becoming a cluttered "list of rules" and instead organizes constraints by their scope.

### Tier 1: Tool-Level Steering (Semantic)
**Scope**: Specific Tool $\rightarrow$ Selection Logic.
- **Mechanism**: Embedded directly in the `description` field of the `BaseDeclarativeTool`.
- **Pattern**: **Negative Steering**. By explicitly stating what a tool *cannot* do, the model is steered away from common pitfalls.
- **Example**: The `ShellTool` description explicitly forbids file operations, steering the model toward the `ReadTool` or `EditTool`.

**Evidence**: `/packages/core/src/tools/shell.ts`
```typescript
// Part of the ShellTool description
"IMPORTANT: This tool is for terminal operations like git, npm, docker, etc. DO NOT use it for file operations (reading, writing, editing, searching, finding files) - use the specialized tools for this instead."
```

### Tier 2: Operational Steering (Modality)
**Scope**: Session $\rightarrow$ Behavioral Mode.
- **Mechanism**: Dynamic suffixes appended to the system prompt in `AgentCore.buildChatSystemPrompt`.
- **Pattern**: **Modality-Based Constraints**. The system adjusts the "rules of engagement" based on whether the agent is interactive or headless.
- **Example**: In non-interactive mode, the prompt is appended with: *"You operate in non-interactive mode: do not ask the user questions; proceed with available context."*

### Tier 3: Contextual Steering (Conventions)
**Scope**: Project $\rightarrow$ Architectural Identity.
- **Mechanism**: Integration of "User Memory" (e.g., the content of `QWEN.md`) as a final block in the system prompt.
- **Pattern**: **Convention Injection**. This ensures that the agent's tool use adheres to the specific coding standards of the repository.
- **Example**: Guidance on using `pathlib.Path` instead of `os` is delivered via this tier, ensuring that the `ShellTool` or `EditTool` calls generate idiomatic code.

## 4. Execution & Scheduling

The transition from "Model Intent" to "System Effect" is managed by the `CoreToolScheduler`.

### 4.1 Validation Pipeline
Qwen Code prevents "hallucinated" tool arguments by validating them against the tool's JSON schema before execution.

**Evidence**: `/packages/core/src/core/coreToolScheduler.ts`
```typescript
// Validates arguments using the tool's internal schema validator
const invocation = tool.build(args);
// If validation fails, an error is returned to the LLM instead of executing the tool
```

### 4.2 Runtime Concurrency and Safety
The system enforces a safety check to prevent race conditions during tool execution.

**Evidence**: `/packages/core/src/core/coreToolScheduler.ts`
```typescript
// Checks if the tool can be run in parallel with others
if (!tool.isConcurrencySafe()) {
  // Logic to handle sequential execution or blocking
}
```

## Summary Table: Steering Architecture

| Tier | Target | Location | Primary Goal | Example |
| :--- | :--- | :--- | :--- | :--- |
| **Tool** | Tool Selection | `Tool.description` | Accuracy / Prevention | "DO NOT use Shell for file edits" |
| **Operational** | Agent Behavior | `buildChatSystemPrompt` | Modality / Loop Control | "Do not ask user questions" |
| **Contextual** | Code Quality | `UserMemory` (`QWEN.md`) | Idiomaticity / Standards | "Use `pathlib.Path`" |
