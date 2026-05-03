
---
title: OpenClaude Subagent Orchestration Analysis
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: 2026-04-26
description: Technical analysis of the Coordinator pattern and asynchronous task management
  in OpenClaude
tags:
- architecture
- agents
options:
  type: guide
  birth: 2026-04-26
  version: 1.1.0
  token_size: 1266
---
# OpenClaude Subagent Orchestration Analysis

OpenClaude utilizes a **Coordinator Pattern**, where a central application state manages a registry of asynchronous tasks. Subagents are implemented as `local_agent` tasks that can run either in the foreground (blocking/interactive) or the background.

## 1. Task Lifecycle and State Management

All subagents are governed by a unified task system defined in `/src/Task.ts`.

### 1.1 Task Statuses
A subagent's lifecycle is tracked via a finite set of statuses:

```typescript
// /src/Task.ts
export type TaskStatus =
  | 'pending'
  | 'running'
  | 'completed'
  | 'failed'
  | 'killed'
```

### 1.2 State Structure
Each agent task maintains a `LocalAgentTaskState`, which includes tracking for tokens, tool usage, and visibility:

```typescript
// /src/tasks/LocalAgentTask/LocalAgentTask.tsx
export type LocalAgentTaskState = TaskStateBase & {
  type: 'local_agent';
  agentId: string;
  prompt: string;
  isBackgrounded: boolean; // False = foreground, True = background
  retain: boolean;         // Prevents GC when the user is viewing the task
  // ...
};
```

## 2. Foreground vs. Background Execution

OpenClaude features a fluid transition between foreground and background execution, allowing the user to "background" a long-running agent.

### 2.1 Foreground Registration
When an agent starts, it is registered in the foreground:

```typescript
// /src/tasks/LocalAgentTask/LocalAgentTask.tsx
export function registerAgentForeground({ ... }) {
  // ...
  const taskState: LocalAgentTaskState = {
    // ...
    isBackgrounded: false,
  };
  // ...
}
```

### 2.2 The Backgrounding Signal
The transition to the background is handled via a promise-based signal. When `backgroundAgentTask` is called, the system resolves a `backgroundSignal` to interrupt the current agent loop and mark the task as backgrounded:

```typescript
// /src/tasks/LocalAgentTask/LocalAgentTask.tsx
export function backgroundAgentTask(taskId: string, getAppState: () => AppState, setAppState: SetAppState): boolean {
  // ...
  setAppState(prev => ({
    ...prev,
    tasks: { ...prev.tasks, [taskId]: { ...prevTask, isBackgrounded: true } }
  }));

  const resolver = backgroundSignalResolvers.get(taskId);
  if (resolver) {
    resolver(); // Signal the agent loop to yield/background
    backgroundSignalResolvers.delete(taskId);
  }
  return true;
}
```

## 3. Inter-Agent Communication: XML Notifications

When a background subagent reaches a terminal state (`completed`, `failed`, or `killed`), it does not simply return a value. Instead, it enqueues an XML-formatted notification into the primary session's message queue.

### 3.1 Notification Structure
The notification is constructed in `enqueueAgentNotification` to provide the primary agent with structured metadata:

```typescript
// /src/tasks/LocalAgentTask/LocalAgentTask.tsx
const message = `<${TASK_NOTIFICATION_TAG}>
<${TASK_ID_TAG}>${taskId}</${TASK_ID_TAG}>${toolUseIdLine}
<${OUTPUT_FILE_TAG}>${outputPath}</${OUTPUT_FILE_TAG}>
<${STATUS_TAG}>${status}</${STATUS_TAG}>
<${SUMMARY_TAG}>${summary}</${SUMMARY_TAG}>${resultSection}${usageSection}${worktreeSection}
</${TASK_NOTIFICATION_TAG}>`;
```

This allows the primary agent to identify which task finished and where to find the detailed output file (`outputFile`) on disk.

## 4. Resource Isolation

### 4.1 Disk-Backed Transcripts
Unlike some agents that keep history in memory, OpenClaude writes subagent transcripts to disk. The output path is resolved via `getTaskOutputPath(id)`, ensuring that subagent logs are persisted and can be "retained" or "evicted" from memory without losing data.

### 4.2 Lifecycle Cleanup
Each task is assigned an `AbortController` and a cleanup registration. When a task is killed or completes, the system triggers these handlers to ensure no orphaned processes remain:

```typescript
// /src/tasks/LocalAgentTask/LocalAgentTask.tsx
export function killAsyncAgent(taskId: string, setAppState: SetAppState): void {
  updateTaskState<LocalAgentTaskState>(taskId, setAppState, task => {
    // ...
    task.abortController?.abort();
    task.unregisterCleanup?.();
    return { ...task, status: 'killed' };
  });
}
```

## Architectural Summary

| Feature | Implementation Detail | File Reference |
| :--- | :--- | :--- |
| **Orchestration Pattern** | Coordinator (Central `AppState` Registry) | `/src/Task.ts` |
| **Lifecycle States** | `pending` $\rightarrow$ `running` $\rightarrow$ `terminal` | `/src/Task.ts` |
| **Execution Mode** | Dynamic Foreground $\leftrightarrow$ Background | `/src/tasks/LocalAgentTask/LocalAgentTask.tsx` |
| **Communication** | XML Notifications (`TASK_NOTIFICATION_TAG`) | `/src/tasks/LocalAgentTask/LocalAgentTask.tsx` |
| **Isolation** | Disk-backed transcripts + `AbortController` | `/src/utils/task/diskOutput.ts` |
