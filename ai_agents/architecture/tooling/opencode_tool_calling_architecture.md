---
title: OpenCode Tool Calling Architecture Analysis
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: 2026-05-06
description: Source-level analysis of the tool calling system in OpenCode (upstream
  for KiloCode), focusing on Effect-based validation, Vercel AI SDK integration, and
  role-based permission rules.
tags:
- agents
- architecture
options:
  type: guide
  birth: 2026-05-06
  version: 1.1.0
  token_size: 1510
---
# OpenCode Tool Calling Architecture Analysis

This analysis examines the tool calling implementation in OpenCode, which serves as the architectural foundation for KiloCode.

## 1. Tool Definitions

**Claim**: Tools are defined using a `Def` interface for type-safe parameter validation and are managed by a central `ToolRegistry` that aggregates built-in and plugin tools.

**Path**: `ai_agents/research/ai_coding_agents/opencode/packages/opencode/src/tool/tool.ts`

**Snippet**:
```typescript
export interface Def<
  Parameters extends Schema.Decoder<unknown> = Schema.Decoder<unknown>,
  M extends Metadata = Metadata,
> {
  id: string
  description: string
  parameters: Parameters
  execute(args: Schema.Schema.Type<Parameters>, ctx: Context): Effect.Effect<ExecuteResult<M>>
  formatValidationError?(error: unknown): string
}
```

**Explanation**: The `Def` interface ensures that every tool provides a unique ID, a description for the LLM, and a `Schema.Decoder` for rigorous input validation. The `ToolRegistry` aggregates these definitions from built-in tools and dynamically discovered plugins to provide a unified toolset to the session.

## 2. LLM Integration

**Claim**: OpenCode uses the Vercel AI SDK to map internal `Effect` schemas to LLM-compatible JSON schemas via the `resolveTools` function.

**Path**: `ai_agents/research/ai_coding_agents/opencode/packages/opencode/src/session/prompt.ts`

**Snippet**:
```typescript
const schema = ProviderTransform.schema(input.model, EffectZod.toJsonSchema(item.parameters))
tools[item.id] = tool({
  description: item.description,
  inputSchema: jsonSchema(schema),
  execute(args, options) {
    return run.promise(
      Effect.gen(function* () {
        const ctx = context(args, options)
        // ... execution logic
      }),
    )
  },
})
```

**Explanation**: The `resolveTools` function iterates over registered tools and converts their `Effect` schemas into JSON Schema 7 using `EffectZod.toJsonSchema`. These are then wrapped in the `tool` helper from the AI SDK, ensuring the LLM receives precise argument specifications.

## 3. Tool Invocation and Permissions

**Claim**: Tool execution is wrapped in an `Effect` runtime that enforces agent-specific permission rules via `ctx.ask()` before invocation.

**Path**: `ai_agents/research/ai_coding_agents/opencode/packages/opencode/src/session/prompt.ts`

**Snippet**:
```typescript
// In the context builder within resolveTools:
ask: (req) =>
  permission
    .ask({
      ...req,
      sessionID: input.session.id,
      tool: { messageID: input.processor.message.id, callID: options.toolCallId },
      ruleset: Permission.merge(input.agent.permission, input.session.permission ?? []),
    })
    .pipe(Effect.orDie),

// In the tool execution loop (e.g., for MCP tools):
yield* ctx.ask({ permission: key, metadata: {}, patterns: ["*"], always: ["*"] })
```

**Explanation**: Before a tool's `execute` logic is triggered, the system invokes `ctx.ask()`. This checks the merged `Permission.Ruleset` (combining agent defaults and session overrides) to determine if the action is permitted, implementing a "Default-Deny" security model.

## 4. The Three-Tier Steering Model

OpenCode employs a highly structured steering approach, utilizing synthetic prompt injections and strict permission-gated modalities.

### Tier 1: Tool-Level Steering (Semantic)
OpenCode uses **Template-Based Steering**, where tool descriptions are not static strings but are generated based on the current environment.

- **Mechanism**: Tool descriptions can be injected with runtime data (OS, shell type, environment variables) to reduce LLM hallucinations.
- **Pattern**: Descriptions are treated as dynamic templates that are resolved at the moment of prompt assembly.
- **Role**: Ensures the LLM understands the exact environmental constraints of the tool it is about to call.

### Tier 2: Operational Steering (Modality)
Operational steering is implemented via high-priority `<system-reminder>` blocks.

- **Mechanism**: The `insertReminders` function appends `synthetic` text parts to the prompt to enforce strict mode constraints.
- **Path**: `ai_agents/research/ai_coding_agents/opencode/packages/opencode/src/session/prompt.ts`

**Snippet**:
```typescript
const part = yield* sessions.updatePart({
  id: PartID.ascending(),
  messageID: userMessage.info.id,
  sessionID: userMessage.info.sessionID,
  type: "text",
  text: `<system-reminder>
Plan mode is active. The user indicated that they do not want you to execute yet -- you MUST NOT make any edits (with the exception of the plan file mentioned below), run any non-readonly tools (including changing configs or making commits), or otherwise make any changes to the system. This supersedes any other instructions you have received.

## Plan File Info:
${exists ? `A plan file already exists at ${plan}. You can read it and make incremental edits using the edit tool.` : `No plan file exists yet. You should create your plan at ${plan} using the write tool.`}
...
</system-reminder>`,
  synthetic: true,
})
```

- **Evidence**: The snippet shows how a `<system-reminder>` blocks the agent from making edits or running non-readonly tools when Plan mode is active.
- **Role**: Overrides previous instructions to force the agent into a specific operational loop (e.g., Plan $\rightarrow$ Execute).

### Tier 3: Contextual Steering (Conventions)
Contextual steering is managed through the `Permission.Ruleset` and agent-specific configurations.

- **Mechanism**: Merging of agent-level defaults with session-specific permission overrides.
- **Pattern**: **Permission-Gated Steering**. By explicitly denying a tool at the API level (e.g., denying edit tools for a 'planner' persona), the agent is steered toward a specific role without relying solely on prompt-based guidance.
- **Role**: Enforces strict isolation between different agent personas and privilege levels.

## 5. Summary of Steering Patterns

| Pattern | Implementation in OpenCode | Primary Goal |
| :--- | :--- | :--- |
| **Template-Based** | Dynamic resolution of `description` strings | Environmental Accuracy |
| **System Reminders**| Synthetic `<system-reminder>` blocks | Absolute Modality Control |
| **Permission-Gated**| `ctx.ask()` against `Permission.Ruleset` | Strict Role Isolation |
