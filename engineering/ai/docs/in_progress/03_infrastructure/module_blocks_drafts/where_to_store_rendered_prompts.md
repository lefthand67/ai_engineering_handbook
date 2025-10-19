# Where to store final prompts?

**You should *not* store the final, rendered prompts in your version-controlled `infrastructure` directory.** That directory is for **templates and source code**, not for **build artifacts**.

The rendered prompt is an **output** or a **build artifact** of your system. Storing it in the same place as your templates would be like storing compiled binaries (`*.o` files) in your source code directory—it creates clutter and breaks the separation of concerns.

Here are the correct places to store them, depending on their purpose:

---

### Option 1: For Audit Trail & Peer Review (Recommended)

The most logical place is within the **`/projects/`** directory structure. This creates a direct association between a project's input (the brief) and the output (the rendered requirements).

```
ai/
├── 3_infrastructure/                 # Source Code: The templates
│   └── templates/
│       └── agent_prompts/
│           └── business_analyst/     # Contains the *template* v1.0.0
│               ├── system_prompt.yaml
│               └── user_prompt_template.yaml
│
└── projects/                         # Project Data & Outputs
    └── project_phoenix/              # The specific project
        ├── input/                    # Inputs that generated the artifact
        │   └── project_brief.md
        ├── outputs/                  # The Build Artifacts
        │   └── phase_1_requirements/ # e.g., The output of the Business Analyst agent
        │       ├── rendered_prompt_v1.0.0.yaml  # <- RENDERED PROMPT HERE
        │       ├── requirements_spec.yaml       # <- THE AI'S OUTPUT
        │       └── chat_log.json                # Full conversation log for audit
        └── README.md
```

**Why this is best:**
*   **Auditability:** It directly links the output to the input that created it.
*   **Reproducibility:** You can exactly recreate any analysis by referring to the project directory.
*   **Peer Review:** The rendered prompt is saved alongside the requirements spec it generated, making it easy for reviewers to see the exact input that led to the output.

---

### Option 2: For CI/CD & Automated Deployment

If the rendered prompt is meant to be deployed directly to a production system (e.g., as a config file for an API), it should be treated as a **build artifact** and stored in a dedicated artifact repository.

*   **Examples:** Amazon S3, Azure Blob Storage, Google Cloud Storage, Artifactory, or even a dedicated `/build-artifacts/` directory that is **not** versioned in Git.
*   **The workflow would be:**
    1.  CI/CD pipeline takes the template from `3_infrastructure/templates/...`
    2.  It renders the prompt with the correct parameters.
    3.  It saves the output to the artifact storage.
    4.  It deploys the artifact from that storage to the production environment.

```
# Example CI/CD pseudo-code
- step:
    name: "Render and Deploy Prompt"
    commands:
      - render-prompt --template infrastructure/templates/agent_prompts/business_analyst/system_prompt.yaml --output /tmp/rendered_prompt.yaml
      - aws s3 cp /tmp/rendered_prompt.yaml s3://my-artifact-bucket/prompts/project_phoenix/v1.0.0.yaml
      - aws ecs update-service ... # Deploy service using the new prompt
```

---

### Option 3: For Runtime Context (Ephemeral)

Often, the rendered prompt is **ephemeral**. It is created on-the-fly by an orchestration script, sent to the LLM, and then discarded. Its only purpose is to generate the final output (the requirements spec).

In this case, you **don't need to store it at all**. The only thing that matters is the final, validated output.

*   **What to store:** Only the final `requirements_spec.yaml` in the `/projects/` directory.
*   **Why:** Storing every intermediate step can lead to artifact bloat. The template is the source of truth; if you have that, you can always recreate the rendered prompt.

---

### Summary and Recommendation

For your use case, **Option 1 (storing in `/projects/`) is strongly recommended.**

**Do this:**
*   **`/3_infrastructure/templates/`**: Stores the **source code** (the templates). This is what you version and peer-review.
*   **`/projects/<project_name>/outputs/`**: Stores the **build artifacts** (the rendered prompts + the AI's output). This is for audit trails, reproducibility, and hand-off to the next phase.

This clear separation keeps your core infrastructure clean and manageable while providing full traceability for every project you run.
