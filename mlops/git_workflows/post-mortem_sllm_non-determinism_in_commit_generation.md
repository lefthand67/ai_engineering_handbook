# Post-Mortem Report: SLM Non-Determinism in Stage 1

-----

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.1.1  
Birth: 2025-12-02  
Last Modified: 2025-12-06

-----

## 1. Executive Summary and Architectural Mandate

This report documents the architectural failure observed during the deployment of the **Small Language Model (SLM)** (1B-3B parameter class) for the highly frequent and highly constrained task of generating structured Conventional Commit messages (Pipeline **Stage 1**).

> See [Production Git Workflow Standards](./git_production_workflow_standards.md)

The underlying architectural decision to use the SLM was based on achieving efficiency at the edge. However, subsequent analysis revealed a critical mismatch between the **task requirement (100% deterministic, low-context output)** and the **model's capability (non-deterministic synthesis)**.

| Metric | Detail | Status |
| :--- | :--- | :--- |
| **Issue Title** | Failure of 1B-3B SLM to reliably generate structured Conventional Commit messages. | **CLOSED** |
| **Impact** | Non-deterministic output, violation of mandatory ArchTag rules, failure to adhere to the core formatting standard (e.g., imperative mood). | **CRITICAL** |
| **Root Cause** | **Low Instruction Fidelity and Synthesis Limitation** in small (1B-3B) SLMs. The model could not maintain complex, simultaneous constraints (parsing raw diff, applying multiple rules, generating structured JSON) while conserving VRAM. | **Architectural** |
| **Mandated Solution** | **Replace the LLM** in Stage 1 with a **Deterministic CLI Tool** (`gitlint`) to enforce the format. Limit the SLM role to the final, high-context Stage 3 transformation. | **MANDATORY** |

> See [Tools: Commit & Changelog Tooling for Release Pipelines](./tools_commit_and_changelog_tooling_for_release_pipelines.md)

## 2. Introduction: Failure of a High-Frequency SLM Application

Our testing confirmed that **Small Language Models (1B-3B) are not suitable for mandatory, high-frequency, structured parsing and generation tasks in a production MLOps pipeline.** Their inherent low **Instruction Fidelity** and difficulty maintaining complex, simultaneous constraints (e.g., 50-character limit, imperative mood, conditional ArchTag insertion) leads to non-deterministic, unreliable output.

* **Result:** The SLM-generated commit messages failed to pass mandatory CI/CD gates, leading to a direct violation of the **[Production Git Workflow: Standards](./production_git_workflow_standards.md)**.
* **Action:** We are immediately retiring the SLM from **Stage 1** of the pipeline. The function will be replaced by a deterministic, non-LLM CLI tool to enforce compliance via an interactive workflow.

This report reinforces the architectural principle that **LLMs must only be applied to generative, low-constraint transformation tasks, not deterministic parsing or rule-based enforcement.**

## 3. Technical Diagnosis and Failure Analysis

The failure was a direct result of mismatching the task complexity with the model's resource constraints. We attempted to use the SLM for a task that requires **high deterministic parsing capability** and **strict adherence to multiple rules**, a domain better suited to traditional software logic.

**The Two Points of Failure**

| Failure Type | Description | Observed SLM Error |
| :--- | :--- | :--- |
| **Instruction Fidelity Breakdown** | The model's low parameter count led to confusion between the JSON system prompt and the required text output format. | **Hallucination of keys**, **ignoring imperative mood**, **omitting mandatory ArchTags**. |
| **Synthesis and Context Overload** | The model had to hold the complex prompt rules (20+ lines) in context while simultaneously synthesizing a title/body from the large, noisy `git diff`. | **Ignoring the content of the diff** (e.g., using boilerplate text instead of synthesizing the actual change). **Failure to check the 50-character limit.** |

## 4. Final Mandate: Stage 1 Reversion and New Workflow

To guarantee **industrial-grade reliability** and compliance with the **Production Git Workflow: Standards**, we implement the following mandated architectural change:

1.  **Eliminate the LLM Role in Stage 1:** The 1B-3B SLM is explicitly **retired** from the commit message generation task.
2.  **Enforce Format Deterministically:** All developers must use a dedicated, non-LLM command-line utility for creating commit messages.
    * **Tool:** `gitlint` or a similar interactive CLI.
3.  **LLM Role Restriction:** The SLM's function is now strictly limited to **Stage 3: Release Notes Transformation**, where it processes short, pre-validated `CHANGELOG.md` excerpts.

This mandate shifts the compliance burden from the brittle SLM synthesis step to the **developer's interactive workflow**, guaranteeing a clean input for the subsequent automated stages.

## 5. Next Steps for Engineers: Mandatory Actions 🛠️

The following actions are mandatory to implement the new, deterministic architecture and align with the **Commit & Changelog Tooling Standard**. Compliance with these steps is enforced via the `pre-commit` hooks and CI/CD gates.

1.  **SLM Decommissioning (Stage 1 Retirement):** Remove all local configurations and system prompts related to the 1B-3B SLM assisting with commit message generation. This role is permanently retired.
2.  **Tool Installation:** All development environments **must** install and configure the mandated tooling stack:
    * **Enforcement:** **`gitlint`** (via `pre-commit` hook) for mandatory commit message validation.
    * **Generation:** **`git-chglog`** (single Go binary) for reproducible `CHANGELOG.md` creation.
3.  **Workflow Change (Manual Creation):** Developers **must** ensure their commit messages adhere to the Conventional Commit standard, as they will be validated by **`gitlint`** before being accepted into the Git history. No automated message creation is approved.
4.  **Training Material:** Training will be immediately deployed to outline the new manual yet validated commit workflow and the updated role of the SLM (now exclusively **Stage 3: Transformation**).

## Appendix A. Prompts Examples

**SLM Execution Sequence (Workflow)** - Expected

The developer initiates this sequence within the CLI agent (`aider`) to the local SLM.

1.  `/run git diff` and add output to context (110 lines changes in one file - a new file created)
1. `/add <prompt.json>`
1. `/ask generate commit message for git diff using instruction in <prompt.json>`
1.  **SLM Process:** The 1B-3B model reads the instructions and performs a two-step transformation:
      * **Step A (Classification):** It classifies the change type and determines if an `ArchTag` is mandatory.
      * **Step B (Summarization/Formatting):** It synthesizes the diff into the structured output.
1.  **Output:** The model returns the three lines of structured text, which the developer reviews and commits.

Tested in `aider` with models:

1. `deepseek-r1:1.5b-qwen-distill-q4_K_M`
2. `qwen2.5-coder:3b-instruct-q5_K_M`

### 1. The Prompt Template (Minimize Tokens)

We will use a fixed, minimal template with clear delimiters to maximize parsing speed and minimize unnecessary tokens.

````json
{
    "TASK": "GENERATE_COMMIT_MESSAGE",
    "CONTEXT": "You are a Git commit generator. Your sole function is to process the provided 'RAW_DIFF' and adherence to the mandatory 'OUTPUT_SCHEMA' and 'COMMIT_RULES'. Do not output any preamble, explanation, or code block fences (```).",
    "MANDATORY_OUTPUT_FORMAT": [
        "Commit Title: <type>(<scope>): <description> (Max 50 chars, imperative mood)",
        "ArchTag: <TAG-NAME> (Only for refactor/perf/remove, otherwise skip line)",
        "Commit Body: <detailed justification>"
    ],
    "COMMIT_RULES": {
        "TYPES": ["feat", "fix", "refactor", "perf", "docs", "test", "chore", "remove"],
        "SCOPE": "Use the affected component or area (e.g., core, api, ci). Omit if scope is global.",
        "ARCH_TAG_REQUIRED_FOR": ["refactor", "perf", "remove"],
        "ARCH_TAG_LIST": ["DEPRECATION-PLANNED", "TECHDEBT-PAYMENT", "REFACTOR-MIGRATION", "PERF-OPTIMIZATION"]
    }
}
````

### 2. The Minimalist Prompt

```json
{
  "TASK_MANDATE": "GENERATE_COMMIT_MESSAGE",
  "RULES": {
    "1_IMPERATIVE_MOOD": "Title must start with an imperative verb (e.g., 'Add', 'Fix', 'Refactor').",
    "2_TITLE_MAX_CHARS": "50",
    "3_ARCH_TAGS_REQD_FOR": "refactor, perf, remove",
    "4_VALID_TYPES": ["feat", "fix", "refactor", "perf", "docs", "test", "chore", "remove"],
    "5_VALID_TAGS": ["DEPRECATION-PLANNED", "TECHDEBT-PAYMENT", "REFACTOR-MIGRATION", "PERF-OPTIMIZATION"]
  },
  "OUTPUT_SCHEMA": {
    "type": "object",
    "properties": {
      "commit_title": {"description": "<type>(<scope>): <description>"},
      "arch_tag": {"description": "Omit key if not required (i.e., not refactor, perf, or remove)."},
      "commit_body": {"description": "Detailed justification of changes. Mandatory."}
    },
    "required": ["commit_title", "commit_body"]
  }
}
```

`/ask Based on the git diff output provided, output ONLY the JSON object defined in OUTPUT_SCHEMA. Do not include the git diff output in your response.`

### 3. Ultra-Detailed System Prompt for 3B SLM

```json
{
  "TASK_MANDATE": "GENERATE_COMMIT_MESSAGE",
  "RULES_XML": "<RULES>
    <CONSTRAINT_1>The Commit Title MUST adhere to the format: <type>(<scope>): <summary>. The summary MUST be in imperative mood (e.g., Add, Fix, Refactor).</CONSTRAINT_1>
    <CONSTRAINT_2>The Commit Title MUST NOT exceed 50 characters (excluding the type and scope prefix).</CONSTRAINT_2>
    <CONSTRAINT_3>The 'arch_tag' key MUST ONLY be present if the type is 'refactor', 'perf', or 'remove'.</CONSTRAINT_3>
    <CONSTRAINT_4>The 'arch_tag' value MUST be one of the capitalized VALID_TAGS (e.g., 'REFACTOR-MIGRATION').</CONSTRAINT_4>
    <CONSTRAINT_5>The commit_body MUST be a technical justification, NOT a summary of the change's contents. It MUST be minimal (max 3 sentences) and focused on *why* the change was necessary (e.g., 'Fixes CI deadlock issue 123', 'Improves maintainability by decoupling classes').</CONSTRAINT_5>
    <VALID_TYPES>feat, fix, refactor, perf, docs, test, chore, remove</VALID_TYPES>
    <VALID_TAGS>DEPRECATION-PLANNED, TECHDEBT-PAYMENT, REFACTOR-MIGRATION, PERF-OPTIMIZATION</VALID_TAGS>
    <OUTPUT_INSTRUCTION>Output ONLY the final JSON object defined in OUTPUT_SCHEMA. DO NOT include any preamble, XML tags, or code block fences (```).</OUTPUT_INSTRUCTION>
  </RULES>",
  "OUTPUT_SCHEMA": {
    "type": "object",
    "properties": {
      "commit_title": {"description": "<type>(<scope>): <summary of change>"},
      "arch_tag": {"description": "Omit this key if not mandatory (i.e., not refactor, perf, or remove)."},
      "commit_body": {"description": "Technical justification/rationale for the change. Max 3 sentences."}
    },
    "required": ["commit_title", "commit_body"]
  },
  "INPUT_DIFF_TO_PROCESS": "<INJECT RAW GIT DIFF HERE>"
}
```

### 4. The Pure Data Interface

**User Input (Per-Commit):**

```
>/ask You are a Git commit generator. Your sole output is a JSON object conforming to the schema I am about to give you. The rules are: (1) Title is max 50 chars, imperative mood. (2) ArchTag is mandatory only for `refactor`, `perf`, or `remove`. (3) Valid tags are: `DEPRECATION-PLANNED`, `TECHDEBT-PAYMENT`, `REFACTOR-MIGRATION`, `PERF-OPTIMIZATION`. **Acknowledge the rules by replying ONLY with the JSON schema below.*
>/ ask 
>/ ask ```json
>/ ask {
>/ ask   "commit_title": "<type>(<scope>): <description>",
>/ ask   "arch_tag": "string (optional)",
>/ ask   "commit_body": "string"
>/ ask }
>/ ask ``
>/ ask Analyze the following `git diff` and provide the JSON commit object according to the rules we established. Do not repeat the rules or include fences.
```
