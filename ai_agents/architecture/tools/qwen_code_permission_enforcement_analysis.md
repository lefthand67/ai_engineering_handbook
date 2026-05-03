
---
title: Qwen Code Permission Enforcement Analysis
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: 2026-04-27
description: Source-level analysis of the L3-L4-L5 permission flow and the 'Implicit
  Trust' risk in Qwen Code.
tags:
- architecture
- agents
- security
options:
  version: 1.2.0
  birth: 2026-04-27
  type: guide
  token_size: 2508
---
# Qwen Code Permission Enforcement Analysis

This document provides a source-level analysis of how Qwen Code enforces tool access and filesystem permissions.

## Roles in Permission Enforcement

Permission enforcement is a two-stage process involving a **Requestor** and a **Gatekeeper**.

### 1. The LLM (The Requestor)
The LLM decides **what** to do. It analyzes the task and decides which tool is appropriate and which target (file, directory, or command) should be used.
- **Autonomy**: The LLM can decide to access any path it believes is relevant to the goal.
- **Lack of Awareness**: The LLM generally does not "know" the specific permission rules of the wrapper; it simply issues a request.

### 2. The Agent Wrapper (The Gatekeeper)
The Agent Wrapper decides **if** the request is allowed. It intercepts every tool call before it reaches the system.
- **Enforcement**: It evaluates the request against the L3 $\rightarrow$ L4 $\rightarrow$ L5 flow.
- **Blindness to Intent**: The wrapper doesn't care *why* the LLM wants the file; it only checks if the tool and the path are permitted.

---

## The Conceptual Framework (L0 $\rightarrow$ L5)

To understand where permissions are enforced, we distinguish between the **Infrastructure Layers** (the plumbing) and the **Governance Layers** (the rules).

### Infrastructure Layers (L0 $\rightarrow$ L2)
These layers provide the capability to execute tools but do not make policy decisions about whether a tool *should* run.
- **L0: The OS / Kernel**: The final arbiter. If the OS user lacks permission to a file, no agent setting can override it.
- **L1: The Runtime / API**: The Node.js environment and system modules (e.g., `fs`) that translate code into system calls.
- **L2: The Agent Core**: The `CoreToolScheduler` and main loop that manage the lifecycle of a tool call.

### Governance Layers (L3 $\rightarrow$ L5)
These are the **Policy Filters** that sit between the Requestor and the Engine. This is where the "Permission Enforcement" actually happens.
- **L3 (Tool Policy)**: The tool's real-time risk assessment based on arguments.
- **L4 (User Policy)**: Explicit overrides defined in `settings.json`.
- **L5 (Mode Policy)**: The operational state (e.g., `YOLO` vs `PLAN`).

---

## The Permission Flow (L3 $\rightarrow$ L4 $\rightarrow$ L5)

When the LLM (Requestor) requests a tool call, the Agent Wrapper (Gatekeeper) evaluates it through the governance layers:

### Layer 3: Tool-Level Defaults (Dynamic Risk)
The wrapper checks the tool's implementation for its default risk level. Crucially, this is **not a static label** but a real-time calculation based on the tool's arguments.

For example, `read_file` does not have a single "default permission." Instead, it computes one based on the target path.

#### Tool Permission Reference Table
| Tool | L3 Dynamic Permission | Condition / Note |
| :--- | :--- | :--- |
| `read_file` | `allow` $\rightarrow$ `ask` | `allow` for workspace/temp/skills dirs; `ask` for all others. |
| `grep_search` | `allow` | Inherently read-only. |
| `glob` | `allow` | Inherently read-only. |
| `list_directory` | `allow` | Inherently read-only. |
| `write_file` | `ask` | Inherently destructive. |
| `edit` | `ask` | Inherently destructive. |
| `run_shell_command` | `allow` $\rightarrow$ `deny` | `allow` if AST is read-only; `ask` if state-changing; `deny` if command substitution is detected. |
| `web_fetch` | `ask` | Network access is treated as risky. |

### Layer 4: PermissionManager Override (User Settings)
The wrapper checks `settings.json` for explicit user rules.
- **Bare Rules**: e.g., `"Read"` (global grant/restriction).
- **Scoped Rules**: e.g., `"Read(/home/user/project/**)"` (path-specific).
- **No Match**: Returns `default`, deferring the decision to the Layer 3 dynamic default.

**Crucial Override Logic**: If a match is found in Layer 4, it **overrides** the L3 result. For example, if `read_file` computes `ask` for an external file (L3), but `settings.json` contains `"allow": [ "Read" ]` (L4), the final result is `allow`.

### Layer 5: Final Decision (Approval Mode)
The result is combined with the `ApprovalMode` (e.g., `YOLO`, `PLAN`).

| L3/L4 Result | Approval Mode | Final Outcome | Logic |
| :--- | :--- | :--- | :--- |
| `allow` | Any | **Execute Immediately** | Tool is inherently safe or explicitly allowed. |
| `deny` | Any | **Block Immediately** | Security violation or explicit deny. |
| `ask` | `YOLO` | **Execute Immediately** | User has opted into auto-approving risky tools. |
| `ask` | `PLAN` / `DEFAULT` | **Pause for User Confirmation** | Requires manual confirmation. |

---

## Implementation Evidence

To ground the above flow in reality, here are the core implementation patterns from the source code.

### L3: Context-Aware Defaults
Tools implement `getDefaultPermission()` to define their risk level based on the target path.

```typescript
// packages/core/src/tools/read-file.ts

override async getDefaultPermission(): Promise<PermissionDecision> {
  const filePath = path.resolve(this.params.file_path);
  const workspaceContext = this.config.getWorkspaceContext();
  
  // L3 Logic: Allow if inside trusted boundaries (Workspace, Temp, etc.)
  if (
    workspaceContext.isPathWithinWorkspace(filePath) ||
    isSubpath(projectTempDir, filePath) ||
    isSubpath(globalTempDir, filePath) ||
    isSubpath(osTempDir, filePath) ||
    isSubpaths(userSkillsDirs, filePath) ||
    isSubpath(userExtensionsDir, filePath) ||
    isAutoMemPath(filePath, this.config.getTargetDir())
  ) {
    return 'allow';
  }
  // Otherwise, escalate to user confirmation
  return 'ask';
}
```

### L4: The Priority Cascade
The `PermissionManager` evaluates rules in a strict priority order to resolve the final decision.

```typescript
// packages/core/src/permissions/permission-manager.ts

private evaluateSingle(ctx: PermissionCheckContext): PermissionDecision {
  // ... (path context setup) ...

  const baseDecision: PermissionDecision = (() => {
    // Priority 1: deny rules (Session > Persistent)
    for (const rule of [...this.sessionRules.deny, ...this.persistentRules.deny]) {
      if (matchesRule(rule, ...matchArgs)) return 'deny';
    }
    // Priority 2: ask rules
    for (const rule of [...this.sessionRules.ask, ...this.persistentRules.ask]) {
      if (matchesRule(rule, ...matchArgs)) return 'ask';
    }
    // Priority 3: allow rules
    for (const rule of [...this.sessionRules.allow, ...this.persistentRules.allow]) {
      if (matchesRule(rule, ...matchArgs)) return 'allow';
    }
    return 'default';
  })();

  // ... (Virtual Operation mapping logic) ...
  return baseDecision;
}
```

### L5: Final Reconciliation
The `CoreToolScheduler` reconciles the L3/L4 decision with the current `ApprovalMode`.

```typescript
// Conceptual logic from packages/core/src/core/coreToolScheduler.ts

const finalDecision = await permissionManager.evaluate(ctx);

if (finalDecision === 'allow') {
  return executeTool(); // Immediate execution
}

if (finalDecision === 'deny') {
  return rejectTool(); // Immediate block
}

if (finalDecision === 'ask') {
  if (config.getApprovalMode() === 'yolo') {
    return executeTool(); // YOLO auto-approves 'ask'
  }
  return promptUserForConfirmation(); // Pause and wait for user
}
```

---

## The "Implicit Trust" Risk


:::{warning}
**The agent is not jailed by default.**
:::

The agent can access any file the OS user can if:
1. The tool computes `allow` (L3).
2. The user has explicitly allowed the tool category in `settings.json` (L4).
3. The agent is running in `YOLO` mode, which auto-approves any `ask` result (L5).

In any of these cases, the Gatekeeper grants the Requestor (LLM) **Implicit Trust**, allowing it to explore the entire filesystem unless a specific `deny` rule is in place.

:::{important}
**Global Permission Warning**
Adding a bare tool category (e.g., `"Read"`) to the `allow` list in `settings.json` grants the agent permission to use that tool across the **entire operating system**, effectively removing the workspace jail for all files the OS user can access.
:::

## Implementing a "Project Jail"

To restrict the LLM to a specific directory, you must configure the Gatekeeper to be strict.

### Strategy 1: The Strict Allowlist
Force the Gatekeeper to deny everything except the project path.

```json
"permissions": {
  "allow": [
    "Read(/absolute/path/to/project/**)"
  ],
  "deny": [
    "Read(**)"
  ]
}
```
*Since `deny` has higher priority than `allow`, the wrapper will block any path that doesn't match the specific allowed project path.*

### Strategy 2: Sensitive Directory Blacklist
Specifically block high-risk areas while leaving the rest open.

```json
"permissions": {
  "deny": [
    "Read(/home/user/.ssh/**)",
    "Read(/home/user/.aws/**)"
  ]
}
```

## Rule Priority and Hierarchy

When multiple rules match, the Gatekeeper follows this priority:

**`deny` $\rightarrow$ `ask` $\rightarrow$ `allow` $\rightarrow$ `default`**

### Session Lifecycle and Settings Reloading

:::{important}
**Settings changes are NOT hot-reloaded.**
:::

Permissions are loaded during the agent's initialization phase. If you modify `settings.json` while a session is active, the changes will **not** be applied to the current session's `PermissionManager`.

**To apply new permission rules, you must restart the agent/CLI session.**

This includes using the `--resume` flag. Because `--resume` starts a completely new OS process, it triggers a fresh `Config` initialization, which in turn calls `permissionManager.initialize()` and re-reads `settings.json` from disk.
## Virtual Operation Analysis

To prevent the LLM from bypassing the Gatekeeper by using `cat` in a shell instead of `read_file`, the wrapper analyzes shell commands. If it detects a "read-like" command, it maps it to the `"Read"` permission category, ensuring your `deny` rules remain effective across all tool interfaces.
