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
  id: 26062
  status: accepted
  token_size: 2992
---
# AI Agent Tooling Architecture Patterns

This document synthesizes the architectural patterns found in the tool-calling systems of various AI coding agents (Qwen Code, Claude Code, Aider, OpenCode, OpenClaude, OpenClaw, Superpowers, and Open WebUI). It moves from the cognitive process of tool selection to a generalized map of how LLMs discover, invoke, and are constrained in their use of tools.

## 1. The Cognitive Mechanism of Tool Selection

The ability of an LLM to "know" when to call a tool is not a single feature, but a synergy between training-time capabilities and runtime context. It can be likened to the difference between knowing *how to use a toolkit* and knowing *which specific tool in the box fits the current bolt*.

### 1.1 Behavioral Intuition (Fine-Tuning)
Tool-calling is primarily driven by specialized fine-tuning on tool-calling trajectories. Models are not just trained on static text, but on sequences that mirror the "Reason $\rightarrow$ Act $\rightarrow$ Observe" loop:

**Example Trajectory:**
- **User**: "Find all occurrences of 'auth' in the codebase."
- **Model (Internal Thought)**: *I cannot see the files directly. I have a tool called `grep_search` that does exactly this.*
- **Model (Call)**: `call: grep_search(pattern="auth")`
- **System (Result)**: `[Returns a list of 15 files]`
- **Model (Response)**: "I found 15 occurrences of 'auth' in the following files..."

This instills a behavioral pattern: when the model identifies a gap in its internal knowledge (e.g., "I don't know what's in `main.py`"), its first instinct is to trigger a tool call rather than hallucinating an answer.

### 1.2 Semantic Mapping (The Catalog)
At runtime, the LLM treats the tool registry as a semantic catalog. This is akin to reading the labels on tools in a box to find the right match. The process follows a specific cognitive pipeline:
1. **Intent Analysis**: The model decomposes the user request to identify the core objective (e.g., "The user needs to search for text").
2. **Catalog Scan**: It performs a semantic match between the objective and the `description` fields of available tools.
3. **Constraint Evaluation**: It checks for negative steering (e.g., "DO NOT use this tool for X") to refine the selection.
4. **Call Generation**: It maps the required arguments to the tool's `parameterSchema`.

### Summary: Cognitive Tool-Calling Components

| Component | Role | Analogy |
| :--- | :--- | :--- |
| **Fine-Tuning** | Teaches the concept of tool use and the syntax of calling them. | Learning how to use a toolkit in general. |
| **System Prompt** | Provides the specific list of available tools and their purposes. | Reading the labels on the tools in the current box. |
| **Descriptions** | Provides the logic for when to pick one tool over another. | The "User Manual" explaining which wrench fits which bolt. |
| **Guardrails** | Ensures the execution is safe and the arguments are valid. | A safety inspector checking the tool isn't broken before it's used. |

---

## 2. Tool Definition Strategies

There are three primary ways agents define the "surface" of their capabilities:

### 2.1 Declarative Type-Safe Definitions (The "Engineering" Approach)
Used by **Qwen Code**, **Claude Code**, **OpenClaude**, and **Open WebUI**. Tools are defined using structured metadata—either via explicit schema objects or inferred from language constructs.

- **Pattern**: `(Zod Schema OR Python Type-Hints/Docstrings)` $\rightarrow$ `JSON Schema` $\rightarrow$ `LLM Prompt`.
- **Advantage**: Ensures structural correctness. The agent can programmatically validate arguments before they reach the execution logic.
- **Evidence**: Claude Code's `Tool` interface and Qwen Code's `BaseDeclarativeTool` use Zod; Open WebUI uses `inspect` and Pydantic to derive schemas from function docstrings and type hints.

### 2.2 Schema-Driven Dictionaries (The "Flexible" Approach)
Used by **Aider**. Tools are defined as raw JSON schema dictionaries.

- **Pattern**: `Python Dict (JSON Schema)` $\rightarrow$ `LLM Prompt`.
- **Advantage**: High flexibility and provider-agnosticism. Easier to dynamically generate or modify schemas at runtime without redefining classes.
- **Evidence**: Aider's `EditBlockFunctionCoder` defines tools as a list of dictionaries containing `name`, `description`, and `parameters`.

### 2.3 Behavioral "Prompt-Tools" (The "Instructional" Approach)
Used by **Superpowers**. Tools are not functions, but behavioral contexts (Skills).

- **Pattern**: `SKILL.md` $\rightarrow$ `Metadata (Discovery)` $\rightarrow$ `Markdown Body (Behavioral Logic)`.
- **Advantage**: Allows the agent to switch "operational modes" rather than just performing a discrete action.
- **Evidence**: Superpowers uses `SKILL.md` files to inject high-discipline workflows (e.g., Brainstorming) into the LLM's context.

---

## 3. Tool Discovery and Context Management

Managing the "token budget" of the system prompt is a critical constraint in tool design.

### 3.1 The Central Registry (Static Discovery)
Used by **Qwen Code** and **OpenCode**. All available tools are registered in a central hub and injected into every request.

- **Pattern**: `ToolRegistry` $\rightarrow$ `List<FunctionDeclaration>` $\rightarrow$ `System Prompt`.
- **Trade-off**: Simple to implement, but leads to "prompt bloat" as the number of tools increases.

### 3.2 Deferred Loading (Dynamic Discovery)
Used by **Claude Code** and **OpenClaude**. The agent only loads a minimal "discovery" toolset initially.

- **Pattern**: `Minimal Toolset` $\rightarrow$ `ToolSearch()` $\rightarrow$ `Load Specific Schema` $\rightarrow$ `Invoke Tool`.
- **Advantage**: Drastically reduces prompt tokens. The LLM must "discover" the tool it needs before it can use it.
- **Evidence**: Claude Code's `defer_loading: true` flag in `toolToAPISchema` prevents the schema from being sent unless specifically requested.

### 3.3 Scoped Tool Surfaces (Identity-Based Discovery)
Used by **OpenClaw**. The available toolset is a function of the user's identity and the current session role.

- **Pattern**: `Identity` $\rightarrow$ `Policy Pipeline` $\rightarrow$ `Filtered Toolset` $\rightarrow$ `LLM Prompt`.
- **Advantage**: Implements security boundaries (e.g., subagents cannot access high-privilege coordinator tools).
- **Evidence**: OpenClaw's `applyToolPolicyPipeline` iteratively filters tools based on a hierarchy of Profile $\rightarrow$ Global $\rightarrow$ Agent policies.

---

## 4. Execution and Orchestration

The gap between the LLM's "request to call" and the actual "system effect" is managed through different orchestration patterns.

### 4.1 The Reason $\rightarrow$ Act $\rightarrow$ Observe Loop
The standard pattern used by nearly all agents (**Qwen Code**, **Aider**, **OpenCode**).

- **Pattern**: `LLM (Decision)` $\rightarrow$ `Orchestrator (Execution)` $\rightarrow$ `System (Result)` $\rightarrow$ `LLM (Reasoning)`.
- **Key Detail**: The orchestrator treats the tool output as a new message in the conversation history, forcing the LLM to reason about the result before the next turn.

### 4.2 Concurrency Partitioning (Safe vs. Mutating)
Used by **OpenClaude** and **Qwen Code**. Tools are categorized by their side-effects.

- **Pattern**: `ReadOnly/Safe` $\rightarrow$ `Parallel Execution` | `Mutating/Unsafe` $\rightarrow$ `Sequential Execution`.
- **Advantage**: Increases performance by running independent read operations (e.g., reading 5 files) in parallel while preventing race conditions on writes.
- **Evidence**: OpenClaude's `partitionToolCalls` groups tools by their `isConcurrencySafe` flag.

### 4.3 Decoupled Gateway Execution
Used by **OpenClaw**. The LLM doesn't call the tool; it requests the gateway to do it.

- **Pattern**: `LLM` $\rightarrow$ `Gateway (StopReason: tool_calls)` $\rightarrow$ `HTTP Invoke Handler` $\rightarrow$ `Result`.
- **Advantage**: Allows tool execution to happen in separate environments or languages, isolated from the LLM's main loop.

---

## 5. Safety, Validation, and Steering

To prevent hallucinations and destructive actions, agents employ multi-layered guardrails.

### 5.1 Steering vs. Validation
A critical distinction in tool-calling architecture is the timing and purpose of constraints. This is the difference between a **User Manual** (guiding the choice) and a **Safety Inspector** (blocking the action).

- **Steering (Pre-Call)**: These are instructions embedded in the tool's `description` or system prompts. Steering happens at the moment of tool selection, guiding the LLM's internal reasoning to pick the correct tool.
- **Validation (Post-Call)**: These are hard constraints enforced by the orchestrator after the LLM has already decided to call a tool. Validation (e.g., Zod schema checks) ensures the arguments are structurally and semantically sound before the system actually executes the function.

### 5.2 The Three-Tier Steering Model
Modern coding agents (Qwen Code, Claude Code, OpenClaw) implement a hierarchical approach to steering, organizing constraints by their scope to prevent prompt pollution.

- **Tier 1: Tool-Level Steering (Semantic)**
  - **Focus**: Tool selection accuracy.
  - **Mechanism**: Embedded in the `description` or dedicated tool-prompt files.
  - **Pattern**: **Negative Steering**. Explicitly stating what a tool *cannot* do (e.g., "DO NOT use Shell for file edits").
  - **Role**: Answers *"Which tool is the correct fit for this specific action?"*

- **Tier 2: Operational Steering (Modality)**
  - **Focus**: Agent behavior and loop control.
  - **Mechanism**: Dynamic system prompt suffixes or "Persona" switches (e.g., Architect vs. Editor).
  - **Pattern**: **Modality-Based Constraints**. Instructions like "do not ask the user questions" in non-interactive mode.
  - **Role**: Answers *"How should I behave during this specific session?"*

- **Tier 3: Contextual Steering (Conventions)**
  - **Focus**: Project-wide standards and identity.
  - **Mechanism**: Injection of project-specific artifacts (e.g., `QWEN.md`, `CLAUDE.md`, `SOUL.md`).
  - **Pattern**: **Convention Injection**. Ensuring the agent follows the architectural rules of the repository.
  - **Role**: Answers *"What are the architectural rules of the project I am working in?"*

### 5.3 Advanced Steering Patterns

| Pattern | Example Agent | Description | Primary Goal |
| :--- | :--- | :--- | :--- |
| **Coder Protocol** | Aider | Using strictly formatted output blocks (e.g., `SEARCH/REPLACE`) instead of native function calls. | Precision in editing |
| **Distributed Steering**| Claude Code | Pairing each tool with a dedicated `prompt.ts` for imperative constraints. | Reduced prompt bloat |
| **Sectional Composition**| OpenClaw | Using `PromptMode` to dynamically assemble the prompt from modular sections. | Scaling complexity |
| **Skill-Based Steering**| OpenClaude | Grouping tools into "Skills" with semantic `when_to_use` and `allowed-tools` metadata. | Tool-overload prevention |
| **Template-Based** | OpenCode | Injecting runtime environment data (OS, shell) into tool descriptions. | Reduced hallucinations |
| **Permission-Gated** | OpenCode | Enforcing modality via hard API-level tool restrictions (deny edit tools for 'planner'). | Strict isolation |
| **Structural Context** | Aider | Using graph-based ranking (RepoMap) to inject a structural "compass" of the project. | Large-repo navigation |

### 5.4 The Validation Pipeline
The transition from "string arguments" to "system execution" is guarded by a pipeline.

- **Pattern**: `Zod Parse (Type Check)` $\rightarrow$ `Semantic Validation (Logic Check)` $\rightarrow$ `Permission Check (Security Check)`.
- **Evidence**: Claude Code's `checkPermissionsAndCallTool` implements this exact three-stage sequence.

---

## Summary Comparison Table

| Pattern | Representative Agent | Core Mechanism | Primary Goal |
|-----------|-------------------|------------------|----------------|
| **Declarative** | Qwen Code, OpenClaude | Zod $\rightarrow$ JSON Schema | Type Safety |
| **Deferred** | Claude Code | `ToolSearch` $\rightarrow$ Load | Token Efficiency |
| **Scoped** | OpenClaw | Policy Pipeline $\rightarrow$ Filter | Security/Isolation |
| **Partitioned** | OpenClaude | Safe vs. Mutating batches | Performance/Integrity |
| **Steered** | Claude Code, Qwen Code | "NEVER" in descriptions | Correct Tool Selection |
