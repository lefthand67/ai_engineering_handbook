
---
title: Subagents Realization Report
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: '2026-05-02'
description: A technical synthesis of how various AI agent frameworks implement subagent
  delegation, context isolation, and orchestration.
tags:
- architecture
- agents
options:
  type: guide
  birth: '2026-04-26'
  version: 1.0.1
  token_size: 2872
---
# Subagents Realization Report

## Methodological Note: Defining "Subagent" Realization

Before analyzing specific implementations, it is critical to establish a taxonomy of what constitutes a "subagent." In the current AI engineering landscape, the term "subagent" is used loosely to describe any form of task delegation. However, the architectural reality varies significantly across three distinct paradigms of realization.

To maintain technical rigor, this report distinguishes between **Physical**, **Logical**, and **Asynchronous** isolation.

### 1. Physical Isolation (The "Fork" Pattern)
**Realization**: The creation of a separate API session, a new context window, or a distinct process.
- **Mechanism**: The primary agent calls a "spawn" or "fork" tool that initializes a new LLM call with a curated subset of the parent's context.
- **Key Characteristic**: **State Boundary**. The subagent has its own history; mutations in the subagent's state do not automatically affect the parent until a final result is returned.
- **Trade-off**: High token overhead (context duplication) and higher latency, but maximum isolation and prevention of "context pollution."
- **Examples**: Claude Code, Qwen Code, Gemini CLI.

### 2. Logical Isolation (The "Persona" Pattern)
**Realization**: A role-shift within the same continuous API session.
- **Mechanism**: The agent modifies its own system prompt or prepends a "persona" instruction (e.g., "You are now the Spec Reviewer") to the current conversation.
- **Key Characteristic**: **State Continuity**. There is no separate session; the "subagent" is a virtual construct defined by the active prompt.
- **Trade-off**: Zero token overhead for session initialization and zero latency, but low isolation. The agent may struggle to "forget" its previous role, leading to persona leakage.
- **Examples**: Superpowers (Subagent-Driven Development).

### 3. Asynchronous Isolation (The "Headless" Pattern)
**Realization**: Execution decoupled from the main interaction loop, often triggered by system-level events.
- **Mechanism**: A system hook (e.g., a bash script or a middleware interceptor) triggers a background process that operates autonomously without the user's immediate visibility.
- **Key Characteristic**: **Temporal Decoupling**. The "subagent" runs in parallel to the main agent or triggers after the main agent's turn ends.
- **Trade-off**: Zero-token overhead in the main chat window and non-interruptive execution, but requires external orchestration (OS hooks/queues) and lacks real-time steering from the user.
- **Examples**: MemPalace (Background Bookkeeping).

---

## Comparative Analysis of Implementations

### 1. Physical Isolation: The "Fork" and "Worker" Patterns

Coding agents (Claude Code, Qwen Code, Gemini CLI) predominantly use Physical Isolation to ensure that sub-tasks do not corrupt the main session's state or introduce unstable mutations.

#### A. Calling Mechanisms and Routing
AI coding agents use a declarative tool-based dispatcher, but their routing strategies vary based on the desired level of session continuity:
- **The Fork (Claude Code, Qwen Code)**: The subagent is a "clone" of the parent. It inherits the current conversation history and system prompt to maintain high continuity.
- **The Supervisor (Gemini CLI)**: The primary agent acts as a dispatcher, routing tasks to a registry of predefined agents (`Local`, `Remote`, or `Browser`) via a `DelegateInvocation` factory.
- **The Recursive Session (OpenCode)**: Spawns sessions linked by a `parentID` in the database, enabling a strict hierarchical tree of delegation.
- **The Coordinator (OpenClaude)**: Manages subagents as asynchronous tasks in a central `AppState` registry, supporting fluid foreground/background transitions.
- **The Gateway Router (OpenClaw)**: Encodes hierarchy directly into session keys (e.g., `:subagent:`) and routes requests through a centralized Gateway using dedicated internal channels.

#### B. State Isolation and Mutation Guarding
To prevent subagents from accidentally altering the parent's environment, these systems implement various isolation guards:
- **Mutation Stubs (Claude Code)**: State-altering callbacks (e.g., `setAppState`) are replaced with no-op functions during the fork.
- **Execution Guards (Qwen Code)**: Uses `AsyncLocalStorage` (ALS) to mark the execution context, rejecting recursive forks to prevent infinite loops.
- **Permission Gating (OpenCode)**: Implements a "Default-Deny" model where subagents are explicitly denied sensitive permissions (like `todowrite`) unless granted by the parent.
- **Contextual Isolation (Gemini CLI)**: Wraps each invocation in a distinct `ToolInvocation` context.
- **Traffic/Resource Isolation (OpenClaw)**: Uses `INTERNAL_MESSAGE_CHANNEL` to separate internal monologue from user dialogue, and `AGENT_LANE_SUBAGENT` to apply independent rate limits.

#### C. Prompt Cache Optimization
A critical engineering constraint for physical subagents is the token cost of duplicating the parent's context. Claude Code and Qwen Code solve this through **Verbatim Prefix Mirroring**:
- **Mechanism**: By ensuring the system prompt, tool declarations, and message prefix are identical to the parent's, they maximize hits on API prompt caches (Anthropic / DashScope).
- **Evidence**: Qwen Code's `AgentTool` explicitly mirrors the parent's `systemInstruction` and `toolDecls` to minimize Time to First Token (TTFT).

#### D. Observability and Steering
The "black box" nature of separate sessions is mitigated through structured telemetry:
- **Sidechains (Claude Code)**: Subagent dialogues are recorded as "sidechain transcripts" in separate storage.
- **Activity Bridges (Gemini CLI)**: Internal agent events (e.g., `THOUGHT_CHUNK`) are streamed through a bridge to the UI.
- **XML Notifications (OpenClaude)**: Background tasks communicate terminal states via structured XML notifications enqueued into the primary session.
- **Recursive Cascade Kill (OpenClaw)**: Implements a "Cascade Kill" mechanism that identifies and terminates all descendant runs in the delegation tree.
- **Dynamic Steering (Gemini CLI, OpenClaw)**: Both support "steering," allowing the controller to interrupt a subagent and restart it with new instructions.

#### E. Context Management and Pollution
Physical isolation provides the strongest guarantee against pollution:
- **The State Boundary**: Because the subagent exists in a separate session, its "thinking" (chain-of-thought), errors, and iterative attempts never enter the parent's message history.
- **The "Token Tax"**: The cost of this isolation is the duplication of the system prompt and initial context. This is why **Verbatim Prefix Mirroring** is not just a performance optimization, but an economic necessity for this paradigm.
- **Result-only Integration**: Pollution is avoided by returning only the final synthesized result to the parent, rather than the full subagent transcript.

| Feature | Claude Code | Qwen Code | Gemini CLI | OpenCode | OpenClaude | OpenClaw |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Realization** | Forked Agent | Hybrid (Fork+Spec) | Supervisor | Recursive | Coordinator | Gateway |
| **Isolation** | No-op stubs | ALS Guard | `ToolInvocation` | Permission Gate | Task Registry | Lanes/Channels |
| **Caching** | Mirroring | Mirroring | Registry | SessionID | Disk-backed | Session-Key |
| **Observability** | Sidechains | Event-UI | Activity Bridge | `task_result` | XML Notify | Session-Keys |
| **Steering** | Result-based | Result-based | Injections | Resume Task | Backgrounding | Steer/Cascade |
### 2. Logical Isolation: The "Persona" Pattern

Unlike Physical Isolation, Logical Isolation does not create a new session. Instead, it shifts the agent's operational mode within the same continuous dialogue.

#### A. Virtual Subagents (Superpowers)
Superpowers implements a **3-role subagent orchestration pipeline** (Implementer $\rightarrow$ Spec Reviewer $\rightarrow$ Code Quality Agent).
- **Mechanism**: The "Controller" (host agent) dispatches virtual subagents by providing them with specific prompt templates (e.g., `implementer-prompt.md`) and a curated subset of context.
- **Realization**: It is a **Logical Shift**. The "subagent" is a virtual construct created by the controller's prompt engineering. As noted in the `subagent-driven-development` skill, it explicitly operates in the **same session** to avoid context-switch overhead.
- **Trade-off**: Zero token overhead for session initialization and zero latency, but it is susceptible to **persona leakage** and requires the controller to meticulously manage the prompt to prevent the subagent from inheriting the full session history (context pollution).

#### B. Context Management and Pollution
In a single-session model, pollution is a constant risk:
- **The Persona Leakage**: Since the LLM sees the entire history, a "Reviewer" subagent may be biased by the "Implementer's" previous justifications, leading to a "confirmation bias" where the reviewer simply agrees with the implementer.
- **The Controller's Burden**: To fight pollution, the Controller must act as a context filter. Instead of relying on the session history, the Controller explicitly provides a "Fresh Context" block in the prompt: *"Ignore previous discussion on X; focus only on this specific task Y."*
- **The "Forgetting" Problem**: As the session grows, the role-shift instructions can be pushed out of the active attention window, causing the subagent to revert to the default host persona.

### 3. Asynchronous Isolation: The "Headless" Pattern

Asynchronous isolation decouples the subagent's execution from the main user-agent interaction loop.

#### A. Headless Bookkeeping (MemPalace)
MemPalace implements subagent-like behavior through an **Agentic MCP Server**.
- **Mechanism**: While the primary agent interacts with the user, MemPalace operates as a "headless" utility that manages a hierarchical "memory palace."
- **Realization**: It uses a **background-process trigger** (OS hooks in Claude Code) to trigger mining and indexing of conversations.
- **Specialist Agents**: MemPalace supports "Specialist Agents" (e.g., Architect, Reviewer) that each maintain their own **Wing** and **Diary** in the palace. These agents operate autonomously to organize knowledge without occupying tokens in the primary chat window.
- **Trade-off**: Maximum efficiency (zero-token impact on the main loop) and temporal decoupling, but it lacks the real-time steering capabilities of physical or logical subagents.

#### B. Context Management and Pollution
Asynchronous subagents avoid pollution through temporal and structural decoupling:
- **Out-of-Band Execution**: Because the subagent runs in a separate process/server, it is physically impossible for its intermediate reasoning to pollute the main chat's KV cache.
- **Structural Filtering**: MemPalace uses a "Wing $\rightarrow$ Hall $\rightarrow$ Room" hierarchy. This ensures that a specialist agent only "sees" the context relevant to its wing, preventing noise from other projects or unrelated conversations.
- **The Synchronization Gap**: The primary pollution risk here is not "noise" but "staleness." Since the subagent runs asynchronously, its internal state (the Palace) may be slightly behind the real-time conversation, requiring explicit "mining" cycles to sync.

## Summary: Taxonomy of Subagent Realizations

| Paradigm | Realization | Isolation Level | Overhead | Primary Example | Key Trade-off |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Physical** | New Session / Fork | High (State Boundary) | High (Tokens/Latency) | Claude Code / Qwen Code | Prevents pollution $\leftrightarrow$ Expensive |
| **Logical** | Role-Shift / Prompt | Low (Shared State) | Zero | Superpowers | Instant $\leftrightarrow$ Persona Leakage |
| **Asynchronous** | Background / Headless | Medium (Temporal) | Zero (Main Loop) | MemPalace | Invisible $\leftrightarrow$ No real-time steering |

## References

For detailed technical walk-throughs and implementation patterns, refer to the following guides:

- [Claude Code Subagents Guide](/ai_agents/architecture/orchestration/claude_code_subagents.md)
- [Qwen Code Subagents Guide](/ai_agents/architecture/orchestration/qwen_code_subagents.md)
- [Gemini CLI Subagents Guide](/ai_agents/architecture/orchestration/gemini_cli_subagents.md)
- [OpenClaw Subagents Guide](/ai_agents/architecture/orchestration/openclaw_subagents.md)
- [OpenClaude Subagents Guide](/ai_agents/architecture/orchestration/openclaude_subagents.md)
- [OpenCode Subagents Guide](/ai_agents/architecture/orchestration/opencode_subagents.md)
