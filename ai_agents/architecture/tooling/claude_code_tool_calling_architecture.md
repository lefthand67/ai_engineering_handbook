---
title: Claude Code Tool Calling Architecture Analysis
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: 2026-05-06
description: Source-level analysis of the tool calling system in Claude Code, focusing
  on Zod-based validation, deferred tool loading, and the hierarchical steering model.
tags:
- agents
- architecture
options:
  type: guide
  birth: 2026-05-06
  version: 1.2.0
  token_size: 1689
---
# Claude Code Tool Calling Architecture Analysis

This analysis examines the tool calling mechanism in Claude Code, emphasizing its focus on type safety, token efficiency, and hierarchical steering.

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
  dangerouslyDisableSandbox: semanticBoolean(z.boolean().optional()).describe('Set this to true to dangerously override sandbox mode...'),
  _simulatedSedEdit: z.object({
    filePath: z.string(),
    newContent: z.string()
  }).optional().describe('Internal: pre-computed sed edit result from preview')
}));
```

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

**Explanation**: By marking tools as `defer_loading: true`, the agent avoids flooding the system prompt with every possible tool schema. The model must first use a `ToolSearch` tool to "discover" and load the specific schema it needs.

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

## 4. The Three-Tier Steering Model

Claude Code employs a hierarchical steering architecture that separates global behavioral guardrails, tool-specific operational constraints, and project-level domain conventions.

### Tier 1: Tool-Level Steering (Semantic)
Claude Code uses **Distributed Steering**, where each tool is paired with a dedicated `prompt.ts` file to define imperative constraints.

- **Mechanism**: Imperative instructions ("ALWAYS", "NEVER", "MUST") are embedded in the tool's semantic description.
- **Evidence**: `/src/tools/FileEditTool/prompt.ts`
  - *"ALWAYS prefer editing existing files in the codebase. NEVER write new files unless explicitly required."*
- **Evidence**: `/src/tools/GrepTool/prompt.ts`
  - *"ALWAYS use ${GREP_TOOL_NAME} for search tasks. NEVER invoke grep or rg as a ${BASH_TOOL_NAME} command."*
- **Role**: Guides the model's selection of a specific tool based on the exact intent.

### Tier 2: Operational Steering (Modality)
Operational steering is managed through a modular system prompt assembly pipeline.

- **Mechanism**: The system prompt is constructed from memoized sections in `src/constants/systemPromptSections.ts` and assembled in `src/constants/prompts.ts`.
- **Blast Radius Steering**: A dedicated `# Executing actions with care` section steers the model to evaluate "reversibility and blast radius" before performing destructive operations.
- **Modality Adjustments**: The prompt is modified based on `outputStyleConfig` to change the agent's explanation and reasoning style.
- **Role**: Defines global behavioral rules and safety frameworks.

### Tier 3: Contextual Steering (Conventions)
Claude Code uses a layered discovery mechanism to inject project-specific rules without bloating the global prompt.

- **Mechanism**: Hierarchy of markdown files acting as "Project Memory".
- **Discovery Order**:
  1. `CLAUDE.md`: Project-wide conventions (committed).
  2. `CLAUDE.local.md`: User-specific overrides (git-ignored).
  3. `.claude/rules/*.md`: Scoped rules for specific sub-directories.
- **Lifecycle**: The `remember` skill allows the agent to promote ephemeral session memories into these persistent artifacts.
- **Role**: Aligns agent behavior with specific project architectural standards.
