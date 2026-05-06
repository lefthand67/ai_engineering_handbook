---
title: Claude Code Tool Calling Architecture Analysis
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: 2026-05-06
description: Source-level analysis of the tool calling system in Claude Code, focusing
  on Zod-based validation, deferred tool loading, and distributed negative constraints.
tags:
- agents
- architecture
options:
  type: guide
  birth: 2026-05-06
  version: 1.1.0
  id: A-26057
  status: accepted
  token_size: 1699
---
# Claude Code Tool Calling Architecture Analysis

This analysis examines the tool calling mechanism in Claude Code, emphasizing its focus on type safety and token efficiency.

## 1. Tool Definitions

**Claim**: Tools are defined using a strict `Tool` interface that enforces a Zod-based input schema, a `call` method for execution, and metadata for discovery and UI rendering.

**Path**: `ai_agents/research/ai_coding_agents/claude-code-main/src/Tool.ts`

**Snippet**:
```typescript
export type Tool<
  Input extends AnyObject = AnyObject,
  Output = unknown,
  P extends ToolProgressData = ToolProgressData,
> = {
  // ... (metadata fields)
  call(
    args: z.infer<Input>,
    context: ToolUseContext,
    canUseTool: CanUseToolFn,
    parentMessage: AssistantMessage,
    onProgress?: ToolCallProgress<P>,
  ): Promise<ToolResult<Output>>
  description(
    input: z.infer<Input>,
    options: {
      isNonInteractiveSession: boolean
      toolPermissionContext: ToolPermissionContext
      tools: Tools
    },
  ): Promise<string>
  readonly inputSchema: Input
  // ... (rendering and validation methods)
}
```

**Claim**: Individual tools (e.g., `BashTool`) implement this interface by defining a specific `inputSchema` and a `call` handler that interacts with the system shell.

**Path**: `ai_agents/research/ai_coding_agents/claude-code-main/src/tools/BashTool/BashTool.tsx`

**Snippet**:
```typescript
const fullInputSchema = lazySchema(() => z.strictObject({
  command: z.string().describe('The command to execute'),
  timeout: semanticNumber(z.number().optional()).describe(`Optional timeout in milliseconds (max ${getMaxTimeoutMs()})`),
  description: z.string().optional().describe(`Clear, concise description of what this command does...`),
  run_in_background: semanticBoolean(z.boolean().optional()).describe(`Set to true to run this command in the background...`),
  dangerouslyDisableSandbox: semanticBoolean(z.boolean().optional()).describe('Set this to true to dangerously override sandbox mode...`),
  _simulatedSedEdit: z.object({
    filePath: z.string(),
    newContent: z.string()
  }).optional().describe('Internal: pre-computed sed edit result from preview')
}));

// ... inside buildTool definition
async call(input: BashToolInput, toolUseContext, _canUseTool?: CanUseToolFn, parentMessage?: AssistantMessage, onProgress?: ToolCallProgress<BashProgress>) {
  if (input._simulatedSedEdit) {
    return applySedEdit(input._simulatedSedEdit, toolUseContext, parentMessage);
  }
  // ... (shell execution logic via runShellCommand)
}
```

**Explanation**: The `Tool` interface ensures consistency across the agent's capabilities. By using Zod schemas, the agent can programmatically validate LLM-generated arguments before execution.

## 2. LLM Integration and Deferred Loading

**Claim**: Tools are converted from Zod schemas to JSON schemas compatible with the Anthropic API, with support for "deferred loading" to manage prompt token budgets.

**Path**: `ai_agents/research/ai_coding_agents/claude-code-main/src/utils/api.ts`

**Snippet**:
```typescript
export async function toolToAPISchema(
  tool: Tool,
  options: {
    // ...
    deferLoading?: boolean
    // ...
  },
): Promise<BetaToolUnion> {
  // ...
  const base = {
    name: tool.name,
    description: await tool.prompt({ /* ... */ }),
    input_schema,
  }
  // ...
  const schema: BetaToolWithExtras = { ...base }
  if (options.deferLoading) {
    schema.defer_loading = true
  }
  return schema as BetaTool
}
```

**Claim**: The system dynamically determines which tools to defer based on their type (e.g., LSP tools) or discovery status in the conversation history.

**Path**: `ai_agents/research/ai_coding_agents/claude-code-main/src/services/api/claude.ts`

**Snippet**:
```typescript
function shouldDeferLspTool(tool: Tool): boolean {
  if (!('isLsp' in tool) || !tool.isLsp) {
    return false
  }
  const status = getInitializationStatus()
  return status.status === 'pending' || status.status === 'not-started'
}

// ... inside queryModel
const willDefer = (t: Tool) =>
  useToolSearch && (deferredToolNames.has(t.name) || shouldDeferLspTool(t))
```

**Explanation**: By marking tools as `defer_loading: true`, the agent avoids flooding the system prompt with every possible tool schema. The model must first use a `ToolSearch` tool to "discover" and load the specific schema it needs.

## 3. Tool Invocation Pipeline

**Claim**: Tool execution follows a strict validation pipeline: Zod type parsing $\rightarrow$ semantic validation $\rightarrow$ permission checking $\rightarrow$ execution.

**Path**: `ai_agents/research/ai_coding_agents/claude-code-main/src/services/tools/toolExecution.ts`

**Snippet**:
```typescript
async function checkPermissionsAndCallTool(...) {
  // 1. Zod parse
  const parsedInput = tool.inputSchema.safeParse(input)
  if (!parsedInput.success) {
    // return InputValidationError
  }

  // 2. Semantic validation
  const isValidCall = await tool.validateInput?.(
    parsedInput.data,
    toolUseContext,
  )
  if (isValidCall?.result === false) {
    // return validation error
  }

  // 3. Permission check (delegated to canUseTool/permission system)
  // ... logic calling checkPermissions() and potentially prompting the user
}
```

**Explanation**: This multi-stage pipeline prevents malformed or dangerous requests from reaching the system shell. The Zod layer catches type errors, `validateInput` catches logical errors (e.g., "blocked sleep patterns"), and the permission layer handles security boundaries.

## 4. Negative Steering and Constraints

**Claim**: High-risk tools include negative constraints (instructions on what to "NEVER" do) within their prompt descriptions to steer the LLM away from destructive or incorrect patterns.

**Path**: `ai_agents/research/ai_coding_agents/claude-code-main/src/tools/FileEditTool/prompt.ts`

**Snippet**:
```typescript
return `Performs exact string replacements in files.
...
- ALWAYS prefer editing existing files in the codebase. NEVER write new files unless explicitly required.
...
- Never include any part of the line number prefix in the old_string or new_string.`
```

**Path**: `ai_agents/research/ai_coding_agents/claude-code-main/src/tools/FileWriteTool/prompt.ts`

**Snippet**:
```typescript
return `Writes a file to the local filesystem.
...
- NEVER create documentation files (*.md) or README files unless explicitly requested by the User.
- Only use emojis if the user explicitly requests it. Avoid writing emojis to files unless asked.`
```

**Explanation**: Because the LLM is the primary driver of tool use, the "instructions" for the tool act as a final guardrail. Constraints like "NEVER write new files" in the `Edit` tool prevent the model from accidentally creating duplicate files when it should be modifying existing ones.
