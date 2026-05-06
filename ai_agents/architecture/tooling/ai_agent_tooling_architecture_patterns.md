---
title: AI Agent Tooling Architecture Patterns
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: 2026-05-06
description: Synthesis of tool-calling architectures across multiple AI coding agents,
  identifying recurring patterns in definition, discovery, execution, and constraint.
tags:
- agents
- architecture
options:
  type: guide
  birth: 2026-05-06
  version: 1.0.0
  id: A-26062
  status: accepted
  token_size: 1751
---
# AI Agent Tooling Architecture Patterns

This document synthesizes the architectural patterns found in the tool-calling systems of various AI coding agents (Qwen Code, Claude Code, Aider, OpenCode, OpenClaude, OpenClaw, Superpowers, and Open WebUI). It moves from individual agent analyses to a generalized map of how LLMs discover, invoke, and are constrained in their use of tools.

## 1. Tool Definition Strategies

There are three primary ways agents define the "surface" of their capabilities:

### 1.1 Declarative Type-Safe Definitions (The "Engineering" Approach)
Used by **Qwen Code**, **Claude Code**, **OpenClaude**, and **Open WebUI**. Tools are defined using structured metadata—either via explicit schema objects or inferred from language constructs.

- **Pattern**: `(Zod Schema OR Python Type-Hints/Docstrings)` $\rightarrow$ `JSON Schema` $\rightarrow$ `LLM Prompt`.
- **Advantage**: Ensures structural correctness. The agent can programmatically validate arguments before they reach the execution logic.
- **Evidence**: Claude Code's `Tool` interface and Qwen Code's `BaseDeclarativeTool` use Zod; Open WebUI uses `inspect` and Pydantic to derive schemas from function docstrings and type hints.

### 1.2 Schema-Driven Dictionaries (The "Flexible" Approach)
Used by **Aider**. Tools are defined as raw JSON schema dictionaries.

- **Pattern**: `Python Dict (JSON Schema)` $\rightarrow$ `LLM Prompt`.
- **Advantage**: High flexibility and provider-agnosticism. Easier to dynamically generate or modify schemas at runtime without redefining classes.
- **Evidence**: Aider's `EditBlockFunctionCoder` defines tools as a list of dictionaries containing `name`, `description`, and `parameters`.

### 1.3 Behavioral "Prompt-Tools" (The "Instructional" Approach)
Used by **Superpowers**. Tools are not functions, but behavioral contexts (Skills).

- **Pattern**: `SKILL.md` $\rightarrow$ `Metadata (Discovery)` $\rightarrow$ `Markdown Body (Behavioral Logic)`.
- **Advantage**: Allows the agent to switch "operational modes" rather than just performing a discrete action.
- **Evidence**: Superpowers uses `SKILL.md` files to inject high-discipline workflows (e.g., Brainstorming) into the LLM's context.

---

## 2. Tool Discovery and Context Management

Managing the "token budget" of the system prompt is a critical constraint in tool design.

### 2.1 The Central Registry (Static Discovery)
Used by **Qwen Code** and **OpenCode**. All available tools are registered in a central hub and injected into every request.

- **Pattern**: `ToolRegistry` $\rightarrow$ `List<FunctionDeclaration>` $\rightarrow$ `System Prompt`.
- **Trade-off**: Simple to implement, but leads to "prompt bloat" as the number of tools increases.

### 2.2 Deferred Loading (Dynamic Discovery)
Used by **Claude Code** and **OpenClaude**. The agent only loads a minimal "discovery" toolset initially.

- **Pattern**: `Minimal Toolset` $\rightarrow$ `ToolSearch()` $\rightarrow$ `Load Specific Schema` $\rightarrow$ `Invoke Tool`.
- **Advantage**: Drastically reduces prompt tokens. The LLM must "discover" the tool it needs before it can use it.
- **Evidence**: Claude Code's `defer_loading: true` flag in `toolToAPISchema` prevents the schema from being sent unless specifically requested.

### 2.3 Scoped Tool Surfaces (Identity-Based Discovery)
Used by **OpenClaw**. The available toolset is a function of the user's identity and the current session role.

- **Pattern**: `Identity` $\rightarrow$ `Policy Pipeline` $\rightarrow$ `Filtered Toolset` $\rightarrow$ `LLM Prompt`.
- **Advantage**: Implements security boundaries (e.g., subagents cannot access high-privilege coordinator tools).
- **Evidence**: OpenClaw's `applyToolPolicyPipeline` iteratively filters tools based on a hierarchy of Profile $\rightarrow$ Global $\rightarrow$ Agent policies.

---

## 3. Execution and Orchestration

The gap between the LLM's "request to call" and the actual "system effect" is managed through different orchestration patterns.

### 3.1 The Reason $\rightarrow$ Act $\rightarrow$ Observe Loop
The standard pattern used by nearly all agents (**Qwen Code**, **Aider**, **OpenCode**).

- **Pattern**: `LLM (Decision)` $\rightarrow$ `Orchestrator (Execution)` $\rightarrow$ `System (Result)` $\rightarrow$ `LLM (Reasoning)`.
- **Key Detail**: The orchestrator treats the tool output as a new message in the conversation history, forcing the LLM to reason about the result before the next turn.

### 3.2 Concurrency Partitioning (Safe vs. Mutating)
Used by **OpenClaude** and **Qwen Code**. Tools are categorized by their side-effects.

- **Pattern**: `ReadOnly/Safe` $\rightarrow$ `Parallel Execution` | `Mutating/Unsafe` $\rightarrow$ `Sequential Execution`.
- **Advantage**: Increases performance by running independent read operations (e.g., reading 5 files) in parallel while preventing race conditions on writes.
- **Evidence**: OpenClaude's `partitionToolCalls` groups tools by their `isConcurrencySafe` flag.

### 3.3 Decoupled Gateway Execution
Used by **OpenClaw**. The LLM doesn't call the tool; it requests the gateway to do it.

- **Pattern**: `LLM` $\rightarrow$ `Gateway (StopReason: tool_calls)` $\rightarrow$ `HTTP Invoke Handler` $\rightarrow$ `Result`.
- **Advantage**: Allows tool execution to happen in separate environments or languages, isolated from the LLM's main loop.

---

## 4. Safety, Validation, and Steering

To prevent hallucinations and destructive actions, agents employ multi-layered guardrails.

### 4.1 The Validation Pipeline
The transition from "string arguments" to "system execution" is guarded by a pipeline.

- **Pattern**: `Zod Parse (Type Check)` $\rightarrow$ `Semantic Validation (Logic Check)` $\rightarrow$ `Permission Check (Security Check)`.
- **Evidence**: Claude Code's `checkPermissionsAndCallTool` implements this exact three-stage sequence.

### 4.2 Negative Steering (Description-Level Constraints)
Used by **Qwen Code** and **Claude Code**. Constraints are embedded in the tool's identity.

- **Pattern**: `Tool Description` $\rightarrow$ `"NEVER use this for X, ALWAYS use tool Y for X"`.
- **Advantage**: Forces the LLM to evaluate the constraint at the moment of tool selection.
- **Evidence**: Qwen Code's `ShellTool` explicitly forbids file operations in its description to steer the LLM toward `ReadTool`/`EditTool`.

---

## Summary Comparison Table

| Pattern | Representative Agent | Core Mechanism | Primary Goal |
|-----------|-------------------|------------------|----------------|
| **Declarative** | Qwen Code, OpenClaude | Zod $\rightarrow$ JSON Schema | Type Safety |
| **Deferred** | Claude Code | `ToolSearch` $\rightarrow$ Load | Token Efficiency |
| **Scoped** | OpenClaw | Policy Pipeline $\rightarrow$ Filter | Security/Isolation |
| **Partitioned** | OpenClaude | Safe vs. Mutating batches | Performance/Integrity |
| **Steered** | Claude Code, Qwen Code | "NEVER" in descriptions | Correct Tool Selection |
