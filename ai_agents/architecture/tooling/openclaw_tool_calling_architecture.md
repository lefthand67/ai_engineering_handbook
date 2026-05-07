---
title: OpenClaw Tool Calling Architecture Analysis
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: 2026-05-06
description: Source-level analysis of tool calling in OpenClaw, focusing on TypeBox
  schemas, scoped tool surfaces, and the hierarchical steering model.
tags:
- agents
- architecture
options:
  type: guide
  birth: 2026-05-06
  version: 1.2.0
  id: 26060
  status: accepted
  token_size: 2004
---
# OpenClaw Tool Calling Architecture Analysis

This analysis examines the tool calling system in OpenClaw, focusing on its unique approach to scoped tool surfaces, policy-driven filtering, and hierarchical steering.

## 1. Tool Definitions

**Claim**: OpenClaw uses a standardized `AnyAgentTool` interface to define tool capabilities, and implements specialized tool factories to encapsulate tool-specific logic and schemas.

**Path**: `ai_agents/research/ai_coding_agents/openclaw/src/agents/tools/common.ts`

**Snippet**:
```typescript
export type AnyAgentTool = Omit<AgentTool<TSchema, unknown>, "execute"> &
  ErasedAgentToolExecute & {
    ownerOnly?: boolean;
    displaySummary?: string;
  };
```

**Path**: `ai_agents/research/ai_coding_agents/openclaw/src/agents/tools/nodes-tool.ts`

**Snippet**:
```typescript
export function createNodesTool(options?: {
  agentSessionKey?: string;
  agentChannel?: GatewayMessageChannel;
  agentAccountId?: string;
  currentChannelId?: string;
  currentThreadTs?: string | number;
  config?: OpenClawConfig;
  modelHasVision?: boolean;
  allowMediaInvokeCommands?: boolean;
}): AnyAgentTool {
  const agentId = resolveSessionAgentId({
    sessionKey: options?.agentSessionKey,
    config: options?.config,
  });
  const imageSanitization = resolveImageSanitizationLimits(options?.config);
  return {
    label: "Nodes",
    name: "nodes",
    ownerOnly: isOpenClawOwnerOnlyCoreToolName("nodes"),
    description:
      "Discover and control paired nodes (status/describe/pairing/notify/camera/photos/screen/location/notifications/invoke).",
    parameters: NodesToolSchema,
    execute: async (_toolCallId, args) => {
      // ... implementation ...
    },
  };
}
```

**Explanation**: The `AnyAgentTool` type provides a consistent contract for tool metadata and execution. Factories like `createNodesTool` allow the system to inject session-specific context (e.g., `agentSessionKey`) and runtime configurations (e.g., `modelHasVision`) into the tool's execution logic.

## 2. LLM Integration: Scoped Tool Surfaces

**Claim**: OpenClaw employs a "Scoped Tool Surface" approach, resolving available tools based on session identity and filtering them through a multi-step policy pipeline before providing them to the LLM.

**Path**: `ai_agents/research/ai_coding_agents/openclaw/src/gateway/tool-resolution.ts`

**Snippet**:
```typescript
export function resolveGatewayScopedTools(params: {
  // ... params ...
}) {
  // ... policy resolution ...
  const allTools = createOpenClawTools({
    // ... context injection ...
  });

  const policyFiltered = applyToolPolicyPipeline({
    tools: allTools,
    toolMeta: (tool: AnyAgentTool) => getPluginToolMeta(tool),
    warn: logWarn,
    steps: [
      ...buildDefaultToolPolicyPipelineSteps({
        // ... policies ...
      }),
      { policy: subagentPolicy, label: "subagent tools.allow" },
    ],
  });
  // ... gateway filtering ...
}
```

**Path**: `ai_agents/research/ai_coding_agents/openclaw/src/agents/tool-policy-pipeline.ts`

**Snippet**:
```typescript
export function applyToolPolicyPipeline(params: {
  tools: AnyAgentTool[];
  toolMeta: (tool: AnyAgentTool) => { pluginId: string } | undefined;
  warn: (message: string) => void;
  steps: ToolPolicyPipelineStep[];
}): AnyAgentTool[] {
  // ...
  let filtered = params.tools;
  for (const step of params.steps) {
    if (!step.policy) {
      continue;
    }
    // ... policy expansion and filtering ...
    const expanded = expandPolicyWithPluginGroups(policy, pluginGroups);
    filtered = expanded ? filterToolsByPolicy(filtered, expanded) : filtered;
  }
  return filtered;
}
```

**Explanation**: `resolveGatewayScopedTools` acts as the orchestrator for tool discovery. It aggregates tools and then passes them through `applyToolPolicyPipeline`, which iteratively filters the toolset based on a hierarchy of policies (Profile $\rightarrow$ Global $\rightarrow$ Agent $\rightarrow$ Group $\rightarrow$ Subagent).

## 3. Tool Invocation

**Claim**: Tool execution is decoupled from the LLM response loop; the gateway detects tool call requests via `stopReason` and invokes them through a dedicated HTTP-based execution handler.

**Path**: `ai_agents/research/ai_coding_agents/openclaw/src/gateway/openresponses-http.ts`

**Snippet**:
```typescript
      const { stopReason, pendingToolCalls } = resolveStopReasonAndPendingToolCalls(meta);

      // If agent called a client tool, return function_call (and any assistant text) to caller
      if (stopReason === "tool_calls" && pendingToolCalls && pendingToolCalls.length > 0) {
        const functionCall = pendingToolCalls[0];
        // ... construct function_call response ...
```

**Path**: `ai_agents/research/ai_coding_agents/openclaw/src/gateway/tools-invoke-http.ts`

**Snippet**:
```typescript
    const result = await gatewayTool.execute?.(toolCallId, hookResult.params);
    sendJson(res, 200, { ok: true, result });
```

**Explanation**: In `openresponses-http.ts`, the system checks if the LLM stopped because it wants to call a tool (`stopReason === "tool_calls"`). If so, it returns the call to the client. The actual execution happens in `tools-invoke-http.ts`, where the corresponding `AnyAgentTool.execute` method is called after passing through security hooks.

## 4. The Three-Tier Steering Model

OpenClaw implements a high-granularity steering model that combines semantic tool descriptions, dynamic session-based modality, and complex identity policies.

### Tier 1: Tool-Level Steering (Semantic)
OpenClaw utilizes a normalized tool catalog where steering is embedded in the `description` field of the `AnyAgentTool`.

- **Mechanism**: Descriptions are used as semantic anchors for the LLM to differentiate between similar tools (e.g., differentiating between different "node" control tools).
- **Evidence**: `createNodesTool` implementation.
  - *"Discover and control paired nodes (status/describe/pairing/notify/camera/photos/screen/location/notifications/invoke)."*
- **Role**: Ensures correct tool selection based on the specific node action required.

### Tier 2: Operational Steering (Modality)
Operational steering is handled via **Sectional Composition** of the system prompt.

- **Mechanism**: The `PromptMode` system allows OpenClaw to dynamically assemble the prompt from modular sections based on the current interaction state.
- **Pattern**: The agent switches "Modality" by altering which prompt sections are injected (e.g., shifting from a discovery phase to an execution phase).
- **Role**: Adjusts behavioral constraints based on the operational phase of the agent.

### Tier 3: Contextual Steering (Conventions)
Contextual steering is enforced through a sophisticated **Identity-Based Policy Pipeline**.

- **Mechanism**: The `applyToolPolicyPipeline` filters available tools based on the user's identity, role, and associated plugin groups.
- **Evidence**: `src/gateway/tool-resolution.ts`
  - The pipeline resolves a hierarchy: `Profile` $\rightarrow$ `Global` $\rightarrow$ `Agent` $\rightarrow$ `Group` $\rightarrow$ `Subagent`.
- **Artifacts**: User-specific persona artifacts (like `SOUL.md` if present) can influence the policy resolution.
- **Role**: Ensures the agent only operates within the authorized and relevant architectural boundaries of the current session.

## 5. Security and Constraints

**Claim**: OpenClaw enforces strict security boundaries using a global "deny-list" for dangerous tools on HTTP surfaces and an `ownerOnly` property to restrict sensitive tools to authorized senders.

**Path**: `ai_agents/research/ai_coding_agents/openclaw/src/security/dangerous-tools.ts`

**Snippet**:
```typescript
export const DEFAULT_GATEWAY_HTTP_TOOL_DENY = [
  // ... list of dangerous tools ...
];
```

**Path**: `ai_agents/research/ai_coding_agents/openclaw/src/agents/tools/common.ts`

**Snippet**:
```typescript
export type AnyAgentTool = Omit<AgentTool<TSchema, unknown>, "execute"> &
  ErasedAgentToolExecute & {
    ownerOnly?: boolean;
    displaySummary?: string;
  };
```

**Explanation**: `DEFAULT_GATEWAY_HTTP_TOOL_DENY` provides a hardcoded safety floor for tools that should never be exposed via HTTP by default. The `ownerOnly` property allows individual tools to declare they require administrative privileges, which is then enforced during the tool resolution and execution phase.
