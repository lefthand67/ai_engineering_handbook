---
title: OpenClaude Tool Calling Architecture Analysis
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: 2026-05-06
description: Source-level analysis of tool calling in OpenClaude, focusing on Zod
  validation, tool orchestration for concurrency, and role-based allowlists.
tags:
- agents
- architecture
options:
  type: guide
  birth: 2026-05-06
  version: 1.1.0
  id: A-26059
  status: accepted
  token_size: 2200
---
# OpenClaude Tool Calling Architecture Analysis

This analysis examines the tool calling system in OpenClaude, which inherits and extends patterns from Claude Code.

## 1. Tool Definitions

**Claim**: OpenClaude defines a rigorous `Tool` interface that enforces structural consistency for all tools, including concurrency safety, read-only status, and deferred loading capabilities.

**Path**: `ai_agents/research/ai_coding_agents/openclaude/src/Tool.ts`

**Snippet**:
```typescript
export type Tool<
  Input extends AnyObject = AnyObject,
  Output = unknown,
  P extends ToolProgressData = ToolProgressData,
> = {
  aliases?: string[]
  searchHint?: string
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
  readonly inputJSONSchema?: ToolInputJSONSchema
  outputSchema?: z.ZodType<unknown>
  inputsEquivalent?(a: z.infer<Input>, b: z.infer<Input>): boolean
  isConcurrencySafe(input: z.infer<Input>): boolean
  isEnabled(): boolean
  isReadOnly(input: z.infer<Input>): boolean
  isDestructive?(input: z.infer<Input>): boolean
  interruptBehavior?(): 'cancel' | 'block'
  isSearchOrReadCommand?(input: z.infer<Input>): {
    isSearch: boolean
    isRead: boolean
    isList?: boolean
  }
  isOpenWorld?(input: z.infer<Input>): boolean
  requiresUserInteraction?(): boolean
  isMcp?: boolean
  isLsp?: boolean
  readonly shouldDefer?: boolean
  readonly alwaysLoad?: boolean
  mcpInfo?: { serverName: string; toolName: string }
  readonly name: string
  maxResultSizeChars: number
  readonly strict?: boolean
  // ... (remaining methods)
}
```

**Claim**: Tools are implemented as structured definitions using a `buildTool` helper, separating the logic (call), metadata (description), and validation (inputSchema).

**Path**: `ai_agents/research/ai_coding_agents/openclaude/src/tools/FileReadTool/FileReadTool.ts`

**Snippet**:
```typescript
export const FileReadTool = buildTool({
  name: FILE_READ_TOOL_NAME,
  searchHint: 'read files, images, PDFs, notebooks',
  maxResultSizeChars: Infinity,
  strict: true,
  async description() {
    return DESCRIPTION
  },
  async prompt() {
    // ... (prompt construction)
  },
  get inputSchema(): InputSchema {
    return inputSchema()
  },
  get outputSchema(): OutputSchema {
    return outputSchema()
  },
  userFacingName,
  getToolUseSummary,
  getActivityDescription(input) {
    const summary = getToolUseSummary(input)
    return summary ? `Reading ${summary}` : 'Reading file'
  },
  isConcurrencySafe() {
    return true
  },
  isReadOnly() {
    return true
  },
  // ... (remaining implementation)
  async call(
    { file_path, offset = 1, limit = undefined, pages },
    context,
    _canUseTool?,
    parentMessage?,
  ) {
    // ... (read logic)
  },
})
```

**Explanation**: `FileReadTool` exemplifies the implementation pattern: it marks itself as `isConcurrencySafe` and `isReadOnly`, allowing the orchestrator to run it in parallel with other read operations.

## 2. LLM Integration and Deferred Loading

**Claim**: OpenClaude utilizes a `queryModel` generator to manage the LLM request-response cycle, incorporating dynamic tool filtering and deferred loading to optimize the context window.

**Path**: `ai_agents/research/ai_coding_agents/openclaude/src/services/api/claude.ts`

**Snippet**:
```typescript
async function* queryModel(
  messages: Message[],
  systemPrompt: SystemPrompt,
  thinkingConfig: ThinkingConfig,
  tools: Tools,
  signal: AbortSignal,
  options: Options,
): AsyncGenerator<
  StreamEvent | AssistantMessage | SystemAPIErrorMessage,
  void
> {
  // ...
  let useToolSearch = await isToolSearchEnabled(
    options.model,
    tools,
    options.getToolPermissionContext,
    options.agents,
    'query',
  )

  const deferredToolNames = new Set<string>()
  if (useToolSearch) {
    for (const t of tools) {
      if (isDeferredTool(t)) deferredToolNames.add(t.name)
    }
  }

  let filteredTools: Tools

  if (useToolSearch) {
    const discoveredToolNames = extractDiscoveredToolNames(messages)

    filteredTools = tools.filter(tool => {
      if (!deferredToolNames.has(tool.name)) return true
      if (toolMatchesName(tool, TOOL_SEARCH_TOOL_NAME)) return true
      return discoveredToolNames.has(tool.name)
    })
  } else {
    filteredTools = tools.filter(
      t => !toolMatchesName(t, TOOL_SEARCH_TOOL_NAME),
    )
  }
  // ...
}
```

**Explanation**: The `queryModel` function implements deferred loading by filtering the tool pool. If `useToolSearch` is active, only non-deferred tools and tools explicitly "discovered" (referenced) in the conversation history are sent to the API, significantly reducing prompt tokens.

## 3. Tool Orchestration and Concurrency

**Claim**: Tool invocation is optimized via a partitioning strategy that separates "concurrency-safe" (read-only) tools from mutating tools, executing the former in parallel.

**Path**: `ai_agents/research/ai_coding_agents/openclaude/src/services/tools/toolOrchestration.ts`

**Snippet**:
```typescript
function partitionToolCalls(
  toolUseMessages: ToolUseBlock[],
  toolUseContext: ToolUseContext,
): Batch[] {
  return toolUseMessages.reduce((acc: Batch[], toolUse) => {
    const tool = findToolByName(toolUseContext.options.tools, toolUse.name)
    const parsedInput = tool?.inputSchema.safeParse(toolUse.input)
    const isConcurrencySafe = parsedInput?.success
      ? (() => {
          try {
            return Boolean(tool?.isConcurrencySafe(parsedInput.data))
          } catch {
            return false
          }
        })()
      : false
    if (isConcurrencySafe && acc[acc.length - 1]?.isConcurrencySafe) {
      acc[acc.length - 1]!.blocks.push(toolUse)
    } else {
      acc.push({ isConcurrencySafe, blocks: [toolUse] })
    }
    return acc
  }, [])
}
```

**Explanation**: `partitionToolCalls` groups consecutive tools that are marked `isConcurrencySafe`. The `runTools` function then processes these batches: safe batches are executed in parallel via `runToolsConcurrently`, while unsafe batches (mutating tools) are executed sequentially to prevent race conditions.

## 4. Execution Pipeline and Validation

**Claim**: The tool execution pipeline implements a multi-stage validation and permission check process before calling the tool's core logic.

**Path**: `ai_agents/research/ai_coding_agents/openclaude/src/services/tools/toolExecution.ts`

**Snippet**:
```typescript
async function checkPermissionsAndCallTool(
  tool: Tool,
  toolUseID: string,
  input: { [key: string]: boolean | string | number },
  toolUseContext: ToolUseContext,
  canUseTool: CanUseToolFn,
  assistantMessage: AssistantMessage,
  // ...
) {
  // 1. Zod Schema Validation
  const parsedInput = tool.inputSchema.safeParse(input)
  if (!parsedInput.success) {
    // ... return InputValidationError
  }

  // 2. Tool-specific Logical Validation
  const isValidCall = await tool.validateInput?.(
    parsedInput.data,
    toolUseContext,
  )
  if (isValidCall?.result === false) {
    // ... return ValidationError
  }

  // 3. Permission Check (handled via streamedCheckPermissionsAndCallTool -> checkPermissions)
  // ...
}
```

**Explanation**: The pipeline ensures that no tool is executed without first passing: (1) structural validation via Zod, (2) logical validation via `validateInput`, and (3) a security permission check.

## 5. Role-Based Constraints

**Claim**: OpenClaude enforces role-based tool restrictions using centralized allow-lists and deny-lists to prevent recursive loops and restrict coordinator capabilities.

**Path**: `ai_agents/research/ai_coding_agents/openclaude/src/constants/tools.ts`

**Snippet**:
```typescript
export const ALL_AGENT_DISALLOWED_TOOLS = new Set([
  TASK_OUTPUT_TOOL_NAME,
  EXIT_PLAN_MODE_V2_TOOL_NAME,
  ENTER_PLAN_MODE_TOOL_NAME,
  ASK_USER_QUESTION_TOOL_NAME,
  TASK_STOP_TOOL_NAME,
  ...(feature('WORKFLOW_SCRIPTS') ? [WORKFLOW_TOOL_NAME] : []),
])

export const COORDINATOR_MODE_ALLOWED_TOOLS = new Set([
  AGENT_TOOL_NAME,
  TASK_STOP_TOOL_NAME,
  SEND_MESSAGE_TOOL_NAME,
  SYNTHETIC_OUTPUT_TOOL_NAME,
])
```

**Explanation**: `ALL_AGENT_DISALLOWED_TOOLS` blocks subagents from accessing high-privilege tools (like `AgentTool` or `TaskStopTool`) to prevent infinite recursion and unauthorized session control. `COORDINATOR_MODE_ALLOWED_TOOLS` ensures that when the system is in coordinator mode, the agent is restricted to management and output tools only.
