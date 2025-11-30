# Small LLM-Backed Release Documentation Pipeline: Architecture

-----

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.1.0  
Birth: 2025-12-01  
Last Modified: 2025-12-01

-----

## 1\. Introduction: Architecture Driven by Resource Constraint

This handbook defines the **specific technical architecture** we use to generate official project documentation (Changelogs, Release Notes) leveraging our local, resource-constrained **Small Language Models (SLLMs)** (1B to 14B parameters).

The key distinction from larger, cloud-hosted LLMs (like GPT-4 or Gemini) is the **resource scarcity** typical of local, commodity AI engineering stacks (e.g., VRAM pools of **12GiB to 48GiB**). This necessitates a highly optimized, modular approach.

### The Core Principle: Decoupling $\to$ Efficiency

We implement a **Decoupled Documentation Pipeline**. This is our architectural standard. We explicitly avoid the common anti-pattern of passing massive, raw data (like a complete `git diff` output) to the SLLM in one monolithic prompt. This anti-pattern causes VRAM saturation, OOM errors, and non-deterministic latency.

Instead, we shift the heavy lifting (parsing, filtering, aggregation) to lightweight, non-LLM tools and use the SLLM *only* for the final, low-context, high-value step of **transformation and summarization**.

### Target Audience

This document is mandatory for all MLOps Engineers, Architects, and Senior Developers responsible for managing release automation and maintaining our local AI tooling stack (`aider`, `ollama`, HuggingFace).

-----

## 2\. The Staged Documentation Flow and Dependency

Our process is defined by three distinct, independent stages. The architecture's robustness is entirely predicated on the strict enforcement of the **Conventional Commit Standard** (defined in the *Production Git Workflow: Standards* handbook).

### 2.1 The Architectural Flow Diagram (Refined)

The following diagram illustrates how the enforced commit standard is processed through the stages to produce the final release artifacts. Note that **Stage 1** is primarily a **Developer** task, optionally **assisted** by an SLLM.

```mermaid
---
config:
  layout: dagre
  theme: default
---
flowchart TD

  A[Create a Topic Branch]

  subgraph id1 [AI-Assisted Documentation Flow]
    direction LR

    %% 1. Input / Development
    B[Commit Code & Enforce Format
    - Generate Structured Commit Message
    - *pre-commit hook + SLLM: 1B*
    - *Manual Review & Edit*]

    %% 2. Transformation / Documentation
    D[Generate CHANGELOG.md
    - *SLLM: 7B-14B*
    - *Manual Review & Edit*]
    
    B --> D

    %% 3. Release Stage
    E[Generate Release Notes
    - *SLLM: 7B-14B*
    - *Manual Review & Edit*]

    D --> E
    
  end
  
  G[Publish Final Release Notes]

  A --> id1
  id1 -->  G

  %% Styling for visual hierarchy
  classDef stage fill:#f0f9ff,stroke:#0077b6,stroke-width:2px;
  class A,B,C,D,E,G stage;
  
  %% Style for the Human Gate
  classDef humanGate fill:#e8f5e9,stroke:#4caf50,stroke-width:2px;
  class F humanGate;
```

```mermaid
---
config:
  layout: dagre
  theme: default
---
flowchart TD

  subgraph MLOps Documentation Pipeline
    direction LR

    %% 1. Input / Development (SLLM only ASSISTS)
    B[Stage 1: Commit & Format Enforcement
    - *Input:* Code Diff
    - *Processor:* Developer or SLLM-assisted 1B-3B
    - *Output:* Structured Commit Message Tier 2/3
    - *Gate:* Pre-Commit Hook Validation]
    
    %% 2. Transformation / Documentation (CRITICAL ENABLER)
    D[Stage 2: Changelog Aggregation
    - *Input:* History of Structured Commits
    - *Processor:* Non-LLM Tool e.g., conventional-changelog-cli
    - *Output:* CHANGELOG.md Markdown
    - *Gate:* Human Review & Validation]
    
    B --> D

    %% 3. Release Stage
    E[Stage 3: Release Notes Transformation
    - *Input:* Relevant CHANGELOG.md Section
    - *Processor:* SLLM 7B-14B
    - *Output:* Formatted Release Notes Audience-specific
    - *Gate:* Architect/Peer Review]

    D --> E
    
  end

  classDef sllm1 fill:#e0f7fa,stroke:#0097a7,stroke-width:2px;
  classDef sllm2 fill:#c8e6c9,stroke:#388e3c,stroke-width:2px;
  classDef tool fill:#ffe0b2,stroke:#ff9800,stroke-width:2px;

  class B sllm1;
  class D tool;
  class E sllm2;
```

-----

## 3\. SLLM Allocation and Resource Strategy

The core design choice is assigning the **smallest viable model** to the most frequent tasks. This ensures optimal **latency** and predictable, minimal **VRAM consumption** across our heterogeneous local stack.

### 3.1 Stage 1: Commit Message Generation

| Parameter | Specification | Rationale |
| :--- | :--- | :--- |
| **SLLM Size** | **1 Billion to 3 Billion** | Task is highly constrained: adherence to a format and summarization of a small, local diff. **Minimal VRAM is required** for near-instant inference, supporting high-frequency use. |
| **Input Context** | Low. Single commit diff + the concise prompt template. | **Maximally low token count.** Prevents VRAM pressure during high-frequency development use. |
| **Tooling** | `aider` (CLI agent) with **`--no-apply`** or equivalent flag, controlled by a System Prompt. | The tool is used **only for drafting text output**, preventing code mutation and ensuring process idempotency. |

### 3.2 Stage 2: Changelog Aggregation (The Non-LLM Gate)

This stage is primarily handled by standard, non-LLM command-line tools. This is the **Critical Architectural Choice** that removes the complex, high-cost, and non-deterministic **context-saturation risk** entirely.

| Parameter | Specification | Rationale |
| :--- | :--- | :--- |
| **SLLM Size** | **Not Used.** | **Computational Efficiency & Cost Avoidance.** Using an SLLM for deterministic parsing is computationally inefficient. Lightweight, non-LLM tools execute this process near-instantly on the CPU, avoiding the VRAM load, latency, and token costs associated with even a short LLM prompt. |
| **Tooling** | `conventional-changelog-cli` (or similar). | These tools use simple regex and parsing logic to reliably aggregate the structured commit history into the standard `CHANGELOG.md` format. |

### 3.3 Stage 3: Release Notes Transformation

This is the final, high-value task where the largest SLLM is justified. The goal is to transform the *developer-focused* Markdown into an *audience-focused* narrative (e.g., executive summary, customer email).

| Parameter | Specification | Rationale |
| :--- | :--- | :--- |
| **SLLM Size** | **7 Billion to 14 Billion** | Requires complex linguistic capabilities (tone, style, summarization, abstraction). The higher parameter count is necessary for quality, as the task is **less frequent** (only at release). |
| **Input Context** | **Low-to-Medium.** **Only** the relevant, clean section (e.g., the `## vX.Y.Z` block) from `CHANGELOG.md` is provided. | Context is short, clean, and pre-categorized. The prompt asks the SLLM to act as a **text transformer**, not a complex parser. |
| **Prompt Focus** | **Instructional/Transformative Prompt.** | The prompt explicitly details the target audience (e.g., "Write this for a non-technical manager") and the required tone. |

-----

## 4\. Resource Pitfalls and Technical Debt

New engineers must understand the specific constraints that mandate this architecture. Deviating from these constraints *will* result in production failures.

### 4.1 Hidden Debt: Context Window Inflation

The most significant risk is a developer attempting to increase the SLLM's context size by modifying the system prompt or adding unnecessary input data at **Stage 3**.

  * **Risk:** Even a short, clean changelog list, if followed by an unnecessarily large or verbose system prompt, can push a mid-sized SLLM over the edge, causing latency spikes or Out-of-Memory (OOM) errors.
  * **Mitigation:** System prompts for SLLMs **MUST** be highly compact, using JSON or constrained Markdown templates instead of verbose prose. All prompts must be **version-controlled alongside model configs** to prevent drift between prompt behavior and model quantization performance. **Every token is a resource cost.**

### 4.2 The Anti-Pattern: Monolithic Processing

Avoid any attempt to use a single SLLM (even the 14B model) for both raw code analysis (Stage 1) and final summarization (Stage 2/3) simultaneously.

  * **Why it Fails:** If the SLLM is tasked with parsing raw code diffs *and* generating the final summary, the process becomes non-deterministic and fails under load.
  * **Proof:** The complexity of the Transformer Attention mechanism is $O(N^2)$, where $N$ is the context length. Doubling the input context length quadruples the VRAM and time requirements for the most demanding parts of the calculation, quickly exceeding capacity.

### 4.3 Mandatory Human Audit Gates

The "Manual Review & Edit" steps are **MANDATORY AUDIT GATES** against SLLM errors and parsing failures. They are not optional:

1.  **Stage 2 Audit:** Verify the non-LLM tool correctly grouped and categorized **all** relevant commits from the specified range.
2.  **Stage 3 Audit:** Verify the SLLM-generated release notes accurately reflect the facts in the changelog and use the correct professional tone. **Do not trust the SLLM's stylistic choices without review.**

-----

## 5\. Architectural Rationale: Monolithic vs. Decoupled

The choice of the **Decoupled Documentation Pipeline** is an architectural imperative driven by the **resource constraints** of our SLLM stack. This decision ensures high performance, reliability, and low operational cost, directly contrasting the brittle and resource-heavy "Monolithic" anti-pattern.

### The Monolithic Anti-Pattern

The monolithic approach attempts to use a single large prompt to feed raw, unparsed data (e.g., hundreds of lines of `git diff -p`) directly into the SLLM for processing and summarization.

### The Decoupled Solution (Our Standard)

We use lightweight tools to parse the structured **Conventional Commits** first, and only feed the clean, minimal context (i.e., the changelog entries) to the SLLM for the final transformation step.

| Architectural Dimension | Monolithic Anti-Pattern (Raw Diff $\to$ LLM) | Decoupled Solution (Commit $\to$ Tool $\to$ LLM) |
| :--- | :--- | :--- |
| **SLLM Role** | **Parser and Summarizer** (High-Cost Data Processing) | **Contextual Transformer** (Low-Cost Stylistic Adaptation) |
| **Input Context** | **Extremely High** (Raw diffs: hundreds of lines of code). | **Very Low** (Structured commit summaries: tens of lines of text). |
| **VRAM/RAM Load** | **Critical:** High risk of **Out-of-Memory (OOM)** error. $O(N^2)$ complexity on large $N$. | **Minimal:** Predictable, low-peak memory usage. |
| **Latency/Speed** | **High and Unpredictable** (Slow token generation). | **Fast and Predictable** (Rapid generation on short context). |
| **Failure Point** | **Brittle:** Single failure (OOM or prompt misinterpretation) breaks the entire release notes generation. | **Robust:** Failure in one stage is localized; the LLM stage is highly reliable due to clean input. |
| **Operational Cost** | **High** (GPU hours, retries, development complexity) | **Low** (CPU work + brief, predictable GPU burst) |
| **Applicability** | Only viable for large, cloud-hosted LLMs with massive memory pools. | **Mandatory** for resource-constrained local SLLMs (1B-14B). |

-----

## 6\. Next Steps for Implementation

1.  Finalize the concise, token-efficient System Prompt templates for the 1B-3B SLLM (Stage 1) and the 7B-14B SLLM (Stage 3).
2.  Implement and enforce the CI/CD pipeline gate to ensure **Stage 2** uses a non-LLM tool for aggregation before passing the output to **Stage 3**.
