
---
title: OpenClaw Subagent Orchestration Analysis
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: 2026-04-26
description: Technical analysis of the session-key routed subagent system in OpenClaw
tags:
- architecture
- agents
options:
  type: guide
  birth: 2026-04-26
  version: 1.0.0
  token_size: 1350
---
# OpenClaw Subagent Orchestration Analysis

OpenClaw implements a highly structured subagent system based on **Session Key Routing**. Rather than using object-oriented parent-child links, it encodes the agent hierarchy directly into the session keys.

## 1. Session Key Routing and Hierarchy

The system uses a colon-delimited string to represent the agent's position in the delegation tree.

### 1.1 Key Structure
Subagent sessions follow a pattern like `agent:<agentId>:subagent:<subagentId>`. This allows the system to determine the delegation depth mathematically.

```typescript
// /src/sessions/session-key-utils.ts
export function getSubagentDepth(sessionKey: string | undefined | null): number {
  const raw = normalizeOptionalLowercaseString(sessionKey);
  if (!raw) {
    return 0;
  }
  return raw.split(":subagent:").length - 1;
}
```

### 1.2 Identification
The `isSubagentSessionKey` function identifies whether a session belongs to a subagent by checking for the `:subagent:` marker in either the raw key or the parsed agent session rest.

```typescript
// /src/sessions/session-key-utils.ts
export function isSubagentSessionKey(sessionKey: string | undefined | null): boolean {
  // ...
  if (normalizeOptionalLowercaseString(raw)?.startsWith("subagent:")) {
    return true;
  }
  const parsed = parseAgentSessionKey(raw);
  return normalizeOptionalLowercaseString(parsed?.rest)?.startsWith("subagent:") === true;
}
```

## 2. Execution and Control

### 2.1 Gateway-Based Execution
Unlike agents that run as local processes or direct function calls, OpenClaw subagents are invoked via a centralized **Gateway**. This architecture decouples the coordinator's logic from the physical execution of the subagent.

```typescript
// /src/agents/subagent-control.ts
const response = await subagentControlDeps.callGateway({
  method: "agent",
  params: {
    // ...
    channel: INTERNAL_MESSAGE_CHANNEL,
    lane: AGENT_LANE_SUBAGENT,
    timeout: 0,
  },
  timeoutMs: 10_000,
});
```

This mechanism provides two layers of isolation:

1.  **Traffic Isolation (`INTERNAL_MESSAGE_CHANNEL`)**: By routing subagent requests through a dedicated internal channel, the system separates the "internal monologue" (coordinator $\leftrightarrow$ subagent) from the "external dialogue" (user $\leftrightarrow$ coordinator). This prevents the client-side interface from being flooded with intermediate subagent outputs and reduces unnecessary data transfer over the user's connection.
2.  **Resource Isolation (`AGENT_LANE_SUBAGENT`)**: The "lane" represents a specialized processing queue within the gateway. Segregating subagents into the `AGENT_LANE_SUBAGENT` allows the infrastructure to apply distinct Quality of Service (QoS) policies—such as independent rate limits or priority scheduling—ensuring that recursive subagent chains do not starve the primary user chat of resources.

### 2.2 Control Scopes and Permissions
Subagents are assigned a `controlScope`. Only agents with a scope of `"children"` can control or steer other subagents.

```typescript
// /src/agents/subagent-control.ts
export type ResolvedSubagentController = {
  // ...
  controlScope: "children" | "none";
};

// Enforcement check
if (params.controller.controlScope !== "children") {
  return {
    status: "forbidden",
    error: "Leaf subagents cannot control other sessions.",
  };
}
```

## 3. Advanced Orchestration Patterns

### 3.1 Steer Mechanism
OpenClaw implements "steering," which allows a controller to interrupt a subagent and restart it with a new instruction. This involves:
1. Aborting the existing run via `abortEmbeddedPiRun`.
2. Clearing the session queue.
3. Triggering a new `agent` call to the gateway with the new message.

```typescript
// /src/agents/subagent-control.ts
export async function steerControlledSubagentRun(params: { ... }) {
  // ...
  if (sessionId) {
    const runtime = await resolveSubagentControlRuntime();
    runtime.abortEmbeddedPiRun(sessionId);
  }
  const runtime = await resolveSubagentControlRuntime();
  const cleared = runtime.clearSessionQueues([params.entry.childSessionKey, sessionId]);
  // ... trigger new gateway call
}
```

### 3.2 Cascade Killing
The system supports recursive termination. When a subagent is killed, the system identifies all its descendant runs and kills them in a cascade.

```typescript
// /src/agents/subagent-control.ts
async function cascadeKillChildren(params: { ... }) {
  // ...
  for (const run of childRuns) {
    // ... kill current child
    const cascade = await cascadeKillChildren({
      // ... recursive call
    });
    killed += cascade.killed;
  }
  return { killed, labels };
}
```

## Architectural Summary

| Feature | Implementation Detail | File Reference |
| :--- | :--- | :--- |
| **Hierarchy Model** | Session Key Strings (`:subagent:`) | `/src/sessions/session-key-utils.ts` |
| **Execution Path** | Gateway $\rightarrow$ `INTERNAL_MESSAGE_CHANNEL` | `/src/agents/subagent-control.ts` |
| **Depth Tracking** | Delimiter count (`split(":subagent:").length - 1`) | `/src/sessions/session-key-utils.ts` |
| **Control Model** | `controlScope` (children vs none) | `/src/agents/subagent-control.ts` |
| **Termination** | Recursive Cascade Kill | `/src/agents/subagent-control.ts` |
| **Interruption** | Steer (Abort $\rightarrow$ Clear $\rightarrow$ Re-spawn) | `/src/agents/subagent-control.ts` |
