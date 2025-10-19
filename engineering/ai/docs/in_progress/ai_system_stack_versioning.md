# 🤖 AI System Stack Versioning Policy (Models, Prompts, Schemas, Pipelines)

-----

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.1.0  
Creation Date: 06.10.2025  
Modification Date: 19.10.2025

-----

When dealing with complex AI systems like multi-agent pipelines, versioning the whole stack—model, prompt, schema, and the pipeline logic—is crucial for **reproducibility** and **auditability**.

See [Semantic Versioning 2.0.0](https://semver.org/) for the core standard.

## Version Format:

`<MAJOR>.<MINOR>.<PATCH>`

Example Asset Name:
`summarization_pipeline_2.1.0`

## 1\. Version Components and When to Increment

The core principle is: if a change forces a **downstream consumer** (like another agent, a service, or the final application) to change its code or data handling, it's a **MAJOR** version bump.

| Component | Version Segment | Meaning | When to Increment | Example |
|---|---|---|---|---|
| **Pipeline** | **MAJOR** | **Breaking change in the overall workflow.** | Altering the required input/output format of the entire pipeline, removing a required step, or changing the core business logic. | `1.0.0` → **`2.0.0`** (e.g., changes from one input document to a batch of documents) |
| | **MINOR** | **New, backward-compatible features.** | Adding an optional step, enabling a new optional parameter, or refactoring the internal flow without affecting external APIs. | `1.0.0` → **`1.1.0`** (e.g., introducing an optional pre-processing step) |
| | **PATCH** | **Fixes and internal tuning.** | Fixing a bug in step orchestration, improving error handling, or minor performance tweaks. | `1.1.0` → **`1.1.1`** (e.g., fixing a race condition in the step queue) |
| **Model** | **MINOR** | **Model Retraining/Update (Significant Improvement).** | Replacing the model with a new version (e.g., `gpt-4o` to `gpt-4o-2025-05-13`) or a fine-tuned model that provides **significant, non-breaking** quality improvements. | `1.0.0` → **`1.1.0`** (e.g., updating to a new LLM point-release or a major finetuning run) |
| | **PATCH** | **Minor Model Update (Hotfix/Tuning).** | Small hotfixes, adjustments to quantization, or minor platform updates that don't change core behavior. | `1.1.0` → **`1.1.1`** |
| **Prompt** | **MAJOR** | **Breaking change in prompt I/O.** | Changing the name/format of **placeholders** (`{old_name}` to `{new_name}`), or altering the **required output format** (e.g., switching from a plain string to a required JSON structure). | `1.0.0` → **`2.0.0`** (e.g., output schema requires a new mandatory field) |
| | **MINOR** | **New functionality, backward compatible.** | Adding an **optional placeholder** or an **optional parameter** (e.g., tone control) to the prompt template. | `1.0.0` → **`1.1.0`** (e.g., adding an optional `{user_context}` placeholder) |
| | **PATCH** | **Typo fixes, grammar, and tuning.** | Adjusting system instructions, fixing misspellings, or tweaking few-shot examples that do not change I/O. | `1.1.0` → **`1.1.1`** (e.g., changing `temperature` from $0.7$ to $0.6$) |
| **Schema** | **MAJOR** | **Breaking change in data structure.** | Removing a field, renaming a field, or changing the data type of an existing field. | `1.0.0` → **`2.0.0`** (e.g., changing `summary_text` from `string` to `array<string>`) |
| | **MINOR** | **New, backward-compatible fields.** | Adding an **optional** field to a JSON/Pydantic output schema. | `1.0.0` → **`1.1.0`** (e.g., adding an optional `keywords` array) |
| | **PATCH** | **Schema documentation or constraint fixes.** | Fixing a typo in a description or tightening a regex constraint on an existing field. | `1.1.0` → **`1.1.1`** |

-----

## 2\. Metadata and Tracking Requirements

To ensure full reproducibility, every component **MUST** be tracked, and the **Pipeline** itself must link to the specific versions of its dependencies.

### A. Component Metadata

Every individual asset (Prompt, Schema, Model config) **MUST** contain basic tracking metadata (similar to Section 2 of the original policy).

```json
{
  "id": "summarizer_prompt",
  "version": "X.Y.Z",
  "component_type": "PROMPT", // New required field
  "description": "...",
  // ... other fields (author, created_at, template/definition, etc.)
}
```

### B. Pipeline Manifest (The Stack Snapshot)

The **Pipeline** definition file **MUST** contain a manifest that locks the versions of all its dependencies.

```json
{
  "id": "summarization_pipeline",
  "version": "2.1.0",
  "description": "Full workflow for summarizing input documents.",
  "dependencies": [
    {
      "component_id": "document_reader_prompt",
      "version": "1.0.5", // Locked Prompt version
      "type": "PROMPT"
    },
    {
      "component_id": "summary_output_schema",
      "version": "2.0.1", // Locked Schema version
      "type": "SCHEMA"
    },
    {
      "component_id": "large_language_model",
      "version": "1.1.0", // Locked Model/Config version
      "type": "MODEL"
    }
    // ... all other steps, agents, and their respective versions
  ],
  "workflow": [ /* The actual orchestration logic */ ]
}
```

-----

## 3\. Change Documentation and Audit

  - **Changelog:** Each component's version bump **MUST** have a corresponding changelog entry detailing the change, motivation, and impact.
  - **Pipeline Release Notes:** Pipeline release notes **MUST** explicitly list the internal component versions that were updated, even if the Pipeline's own major version didn't change.

Example Pipeline Changelog Entry:

```
2.1.0 - FEATURE: Added new step for metadata extraction.
    - Updated component: 'document_reader_prompt' from 1.0.5 to 1.1.0 (added optional 'source' placeholder).
    - Updated component: 'summary_output_schema' from 2.0.0 to 2.0.1 (fixed description typo).
```

-----

## 4\. Automation and Governance

1.  **Atomic Commits:** Any change to a component (prompt, schema, pipeline definition) **MUST** be committed and reviewed as a self-contained unit that results in a version bump for *that* specific component.
2.  **Validation:** Use tools (e.g., **JSON Schemas** for data, **Pydantic** for Python code) to validate that prompt inputs/outputs match the defined Schemas, and that the Pipeline Manifest successfully resolves all dependent versions.
3.  **CI/CD Checks:** The CI/CD process must:
      * Verify that any change to a component results in a SemVer-compliant version increment.
      * For the Pipeline, verify that its version number is updated if any dependency version it uses is updated.
4.  **Rollback:** The use of a manifest ensures that rolling back the entire stack is as simple as deploying the **previous stable Pipeline version** file, which automatically points to the correct, older versions of all Prompts, Models, and Schemas. This provides a single point of control for full system state rollback.
