
---
title: 'How Subagents Actually Work: The Myth of Process Spawning'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: '2026-04-26'
description: 'Debunks the misconception that subagent spawning = OS fork/exec. Explains
  the three actual paradigms: Physical, Logical, and Asynchronous isolation.'
tags:
- architecture
- agents
- prompts
options:
  version: 1.1.0
  birth: '2026-04-08'
  type: guide
  token_size: 1317
---
# How Subagents Actually Work: The Myth of Process Spawning

## The Misconception

When developers hear "subagent spawning," they think of OS-level `fork()` or `child_process.spawn()`. **This is wrong.** In almost every major AI coding agent analyzed (Claude Code, OpenCode, Qwen Code, OpenClaw, Superpowers), "spawning a subagent" is **not a process operation** — it is a **prompt engineering and session management pattern**.

The term "forked agent" (used in Claude Code's source code) does not mean a forked OS process. It means a **separate LLM API call** with a different system prompt and a curated state boundary.

## The Three Realization Paradigms

Depending on the goals of the system (isolation vs. speed), "subagents" are realized in one of three ways:

### 1. Physical Isolation (The "Fork" Pattern)

The subagent is realized as a **separate API session** or a new context window. It has its own history and its own "thinking" space.

**Used by:** Claude Code, Qwen Code, Gemini CLI, OpenCode, OpenClaw.

**How it works:**
The primary agent uses a tool to "spawn" a subagent. The runtime then makes a **new API call** using:
- A **different system prompt** (e.g., "You are a compaction agent").
- A **curated subset of the parent's context** (to save tokens).
- **Verbatim Prefix Mirroring**: To avoid the "token tax" of duplicating the system prompt, the subagent's prefix is kept identical to the parent's to maximize prompt cache hits (e.g., Anthropic/DashScope caches).

**Key characteristic: The State Boundary.** 
Mutations in the subagent's history (its internal reasoning, errors, and attempts) **do not** pollute the parent's conversation. The parent only receives the final, synthesized result.

### 2. Logical Isolation (The "Persona" Pattern)

The subagent is a **virtual construct** realized as a role-shift within the same continuous API session.

**Used by:** Superpowers (Subagent-Driven Development).

**How it works:**
There is no separate session. Instead, the agent is instructed to adopt a different persona (e.g., "You are now the Spec Reviewer"). This is achieved by:
- Prepending a "persona" instruction to the current conversation.
- Using a specific prompt template (e.g., `spec-reviewer-prompt.md`) to frame the task.

**Key characteristic: State Continuity.** 
There is zero token overhead and zero latency for initialization. However, the system suffers from **Persona Leakage** — the "Reviewer" may be biased by the "Implementer's" previous logic because they share the same history. The "Controller" must act as a manual context filter to fight this pollution.

### 3. Asynchronous Isolation (The "Headless" Pattern)

The subagent is realized as a **decoupled process** that operates out-of-band, often triggered by system hooks.

**Used by:** MemPalace (Background Bookkeeping).

**How it works:**
Instead of a turn-based interaction, a "headless" agent runs in the background (e.g., via an MCP server or an OS hook). It mines the conversation history and updates a structured knowledge base (the "Palace") without occupying any tokens in the main chat window.

**Key characteristic: Temporal Decoupling.** 
The subagent runs in parallel to the user's interaction. It avoids context pollution entirely because its execution is physically separate from the main loop, but it lacks the real-time steering of the other two patterns.

## The Universal Substrate: Request-Response Statelessness

Regardless of the pattern, all these systems sit on the same fundamental API reality: **The LLM is stateless.**

Every "subagent" call follows this structure:
```
API Request:
├─ System Prompt (Exactly ONE per call)
├─ Context/History (The "State")
└─ Instruction (The "Task")
```

When a subagent is "spawned," the runtime is simply constructing a **new request**. Whether that request uses a new session (Physical), a modified prompt in the same session (Logical), or a background trigger (Asynchronous), it is still just a stateless API call. The "intelligence" of the subagent comes from the **curation of the context** and the **specificity of the system prompt**, not from any magical OS process spawning.

## Summary Table

| Paradigm | Mechanism | Isolation | Overhead | Example | Key Trade-off |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Physical** | New Session / Fork | High | High | Claude Code | No pollution $\leftrightarrow$ Expensive |
| **Logical** | Role-Shift / Prompt | Low | Zero | Superpowers | Instant $\leftrightarrow$ Persona Leakage |
| **Asynchronous** | Background / Headless | Medium | Zero | MemPalace | Invisible $\leftrightarrow$ No steering |

## Key Takeaway

**"Subagent spawning" is almost always a misnomer.** In 95% of cases, it is simply a **strategically constructed API call**. 

If you want to understand the deep technical implementation of these patterns — including how to handle state boundaries, mutation guards, and prompt cache mirroring — see the [Subagents Realization Report](/ai_agents/architecture/orchestration/subagents_realization_report.md) and the corresponding implementation guides.
