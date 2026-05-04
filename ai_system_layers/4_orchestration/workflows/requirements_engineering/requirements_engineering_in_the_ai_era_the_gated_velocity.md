---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.1
kernelspec:
  name: python3
  display_name: Python 3 (ipykernel)
  language: python
---

---
title: '📘 Requirements Engineering in the AI Era: The Gated Velocity Handbook'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: The definitive handbook for the Gated Velocity methodology, blending
  high-velocity LLM synthesis with deterministic SLM auditing and human Micro-Gating
  for NFR compliance.
tags:
- workflow
- architecture
date: '2026-05-02'
options:
  type: guide
  version: 0.2.4
  birth: '2025-12-07'
  token_size: 5120
---
# 📘 Requirements Engineering in the AI Era: The Gated Velocity Handbook
> INFO: *The handbook is optimized for environments supporting Mermaid.js diagrams. For static export, rasterized versions are available in Appendix A.*

Maximize LLM-driven velocity while enforcing Non-Functional Requirement (NFR) compliance via structured, low-friction human Micro-Gating.

## I. Foundational Philosophy: Micro-Gating vs. The Architectural Debt Trap

The legacy approach to Requirements Engineering (RE) is broken. Time wasted in lengthy document reviews, political negotiation, and ambiguous acceptance criteria has stalled the development cycle. Our methodology is designed to eliminate this inertia by delegating **synthesis and generation** to Large Language Models (LLMs) and delegating **verification and auditing** to Small Language Models (SLMs).

**The Critical Failure of POC-First Review**

A **Proof of Concept (POC)** is an evaluation of **functional feasibility** only. It is ***not*** a reliable criterion for production. By delaying human review until the POC is built, we risk committing to an architecture that is unviable for scaling, insecure, or too expensive.

**The Core Solution: The Gated Velocity Pipeline**

We enforce governance through **Gating Functions**—mandatory, auditable checkpoints where human experts review **SLM-generated audit reports**, not voluminous documents. This allows for high-speed LLM generation between gates while retaining executive control over **architectural risk**.

**The Engineer's Mindset: The WRC Formula**

Every engineer must evaluate decisions based on the trade-off between speed and viability. The **Weighted Risk Score (WRC)** is a conceptual framework guiding all architectural and design decisions in the AI-Augmented Gated Velocity Pipeline. It ensures that velocity is balanced against viability and future cost.

The WRC formalizes the architectural trade-off. We aim to maximize functional achievement and compliance while minimizing complexity and cost. A simplified, conceptual calculation is:
$$WRC = \frac{k_E E + k_A A}{k_C C}$$
Where $k$ values are project-specific weighting constants (e.g., $k_A$ is high for financial systems).

* **E (Effectiveness):** **Functional Achievement.** 
    - Measures if the solution meets core **Functional Requirements (FRs)** and user goals.
* **A (Accountability):** **Auditability and Compliance.** 
    - Measures if the artifact is fully **traceable, auditable, and compliant** with all established **Non-Functional Requirements (NFRs)**. This is the **non-negotiable** factor enforced by **Micro-Gating** (G1, G2, G3).
* **C (Complexity/Cost Penalty):** **Maintenance and Resource Overhead.** 
    - Measures the **Predicted Cost of Maintenance** and **Architectural Complexity Penalty**. High 'C' scores penalize manual overhead or non-standard tooling disproportionate to local **SLM stack** capabilities.

## II. The Model Allocation Strategy: LLM vs. SLM

We strategically allocate model resources based on their inherent strengths and organizational costs. This ensures **Efficiency**—we reserve high-cost, high-latency tools for high-value synthesis and use local, fast tools for deterministic checks.

### 1. Large Language Models (LLMs): The Synthesizers

| Dimension | **Large Language Models (LLMs)** | **Small Language Models (SLMs)** |
|:---|:---|:---|
| **Primary Role** | Synthesis, generation, ambiguity resolution | Verification, validation, deterministic transformation |
| **Typical Tasks** | Drafting user stories from BRs, refining specs | Schema validation, rule-based consistency checks |
| **Execution Environment** | Cloud-hosted / API (e.g., OpenRouter, Anthropic) | Local (CPU/GPU), containerized (Podman/Docker) |
| **Key Constraints** | Token cost, API latency, rate limits | RAM/VRAM budget, inference speed, reproducibility |
| **Change Frequency** | Low (used for initial high-entropy output) | High (integrated into CI/validation loops) |
| **Human Interaction Point** | Input formulation, output triage | Exception handling, audit escalation |
| **Example Models** | Claude 3.5, GPT-4o, Llama 3.1 70B | Deepseek-R1, Qwen2.5-Coder-7B, Gemma3N |

### 2. Human–AI Collaboration (HAIC)

The diagram below illustrates how the LLM and SLM roles are integrated into the lifecycle, with humans acting as **Gating Functions** at high-risk junctures. The goal is to maximize the time spent in the large automated blocks while minimizing the time spent in the human review gates.

```mermaid
---
config:
  layout: dagre
---
flowchart TB
 subgraph Legend["Legend"]
    direction LR
        L1["NFR: Non-Functional Requirements"]
        L2["LLM:Large Language Model - very capable"]
        L3["SLM: Small Language Model - Specialized"]
  end
    A["Raw Business Input
    (e.g., meeting notes, chat)"] --> B["**LLM**:
    Elicitation
    User Stories + NFR Manifest -> Store Requirements"]
    B --> G1{"G1: Architectural Viability Gate
    👔 Human Review"}
    G1 -- NO (Architectural Issues) --> B
    G1 -- YES (Viable Architecture) --> D["**LLM**:
    Technical Spec Generation
    + NFR Compliance JSON -> Store Spec"]
    D --> E["**SLM**:
    NFR Contract Validator (Specialized Check)"]
    E --> F["NFR Compliance Diff Report"]
    F --> G1{G1: Architectural Viability Gate} 
    D & E --> G["**LLM**:
    Code & Test Generation
    Based on Spec -> Stage in Git Branch"]
    
    %% --- Correction Made Here ---
    G --> G2{"G2: Code Integrity Gate
    🧑‍💻 Human Review"}
    G2 -- NO (Issues Found) --> G
    G2 -- YES (Code Cleared) --> I["**SLM**:
    Code Smells Auditor (Targeted Audit)"]
    
    I --> J["Audit Findings JSON"]
    J --> G2
    
    G2 -- "✅ CI + SLM Audit Passed" --> K["Deploy to Staging"]
    %% The deployment (K) now only occurs after G2 has successfully passed (via the audit loop)
    
    K --> L["**LLM**:
    Generate Gherkin Scenarios
    from User Stories"]
    L --> G3{"G3: Strategic Acceptance Gate
    📊 Product Owner"}
    G3 -- "REJECT (Requires Re-Scoping)" --> L
    G3 -- APPROVE (Accepted) --> N["**SLM**: Auto-generate
    Executable BDD Tests"]
    N --> O["GitOps Merge to Main
    (Traceable Artifact Chain)"]

     G1:::gate
     G2:::gate
     G3:::gate
    classDef gate fill:#f9f,stroke:#333,color:#000
    style B fill:#C8E6C9
    style G1 fill:#BBDEFB
    style D fill:#C8E6C9
    style E fill:#FFF9C4
    style G fill:#C8E6C9
    style G2 fill:#BBDEFB
    style I fill:#FFF9C4
    style L fill:#C8E6C9
    style G3 fill:#BBDEFB
    style N fill:#FFF9C4
````

> Figure 1: The Gated Velocity Pipeline. LLMs drive synthesis; SLMs enforce deterministic audits; humans gate only at high-risk decision points (G1–G3). **Note the critical feedback loop ("G1: Architectural Viability Gate") ensuring the LLM corrects its own blueprint.**

It aligns with the HAIC pattern validated in [arXiv:2511.01324v3](https://arxiv.org/html/2511.01324v3), where 54.4% of practitioners use AI as a collaborative partner—not an autonomous agent.

## III. The Three Micro-Gating Functions (G1, G2, G3)

Human expertise is reserved for these three gates. In all cases, the human reviewer is presented with a concise, auditable **SLM-generated summary** instead of raw documentation or code.

### G1: Architectural Viability Gate (Architect Sign-off)

This gate occurs immediately after the LLM generates the **Technical Specification**. It prevents the team from implementing a flawed, unviable blueprint.

* **Trigger:** Completion of the Technical Specification draft.
* **Human Role:** Architect/Lead Engineer.
* **SLM Action:** The **NFR Contract Validator** compares the proposed design choices in the Technical Specification against the non-negotiable constraints in the **NFR Manifest JSON**.
* **Output:** **NFR Compliance Diff Report** (Reject if 'FAIL'). The architect reviews only the failed justification lines and uses this report to **update the LLM prompt for Technical Spec Generation (D)** for iteration.

### G2: Code Integrity Gate (Security/Engineer Sign-off)

This gate occurs before the generated code is merged into the `main` branch, integrated directly into the **Pull Request (PR)** process. It combats **Generative Debt** (structural and security flaws).

* **Trigger:** LLM-generated code/tests are pushed to a feature branch.
* **Human Role:** Security/Lead Engineer.
* **SLM Action:** The **Code Smells Auditor** performs static analysis, checking for complexity, unapproved dependencies, and explicit security NFR violations.
* **Output:** **Audit Findings JSON Array** (Reject if Array is not empty). The engineer only reviews the specific lines of code flagged by the SLM.

### G3: Strategic Acceptance Gate (Business Sign-off)

This gate concludes the cycle, verifying that the *built system* meets the high-level business need.

* **Trigger:** System deployed to Staging/QA environment.
* **Human Role:** Product Owner/QA.
* **LLM Action:** The LLM is prompted to convert the initial User Stories into **Gherkin (Given-When-Then)** scenarios.
* **Output:** Approved Behavior-Driven Development (BDD) Scenarios (The final acceptance of the *behavior*).

## IV. The AI-Driven Artifact Chain and Governance

### 1. The NFR Manifest (JSON Contract)

This contract is the central mechanism for **architectural governance**. It is provided by the human **before** the LLM starts generation and is the primary input for the **G1 Validator**. The structured JSON format makes NFRs machine-readable and auditable, preventing them from being lost in prose.

### 2. The Traceability Mandate: Accountability in AI Engineering

To ensure **Accountability (A)**, every artifact must be traceable back to its origin and the human who approved it.

* **Mandate:** Every generated artifact (User Stories, Technical Spec, Code) **MUST** be tagged with its source:
    1.  The **LLM/SLM Model Name and Version** (e.g., `gemini-3-pro@v1.2`).
    2.  The **Git Commit Hash** of the System Prompt used to generate it.
* **Enforcement:** All artifacts must be stored under a **GitOps** model. The human G1/G2/G3 approvals are formalized as merge commits, creating a permanent, auditable record of the probabilistic output and the human decision.

## V. The Artifact Flow and Version Control: Stacked Diffs

The efficiency gained by offloading synthesis to LLMs must be preserved during code review and integration. The **LLM-generated artifacts** are naturally granular, small, and testable—making them ideal for the **Stacked Diffs** version control strategy. This strategy enforces small, atomic changes, accelerating human review and maintaining a clean, linear history.

> See [Stacked Diffs (and why you should know about them)](https://newsletter.pragmaticengineer.com/p/stacked-diffs)

### 1. The Atomic Change Mandate

Every **User Story** ("Elicitation") that proceeds to the Code Generation phase ("Code & Test Generation") must be treated as a candidate for a single, independent, verifiable **atomic commit**.

* **Definition of Atomic:** A change is atomic if it accomplishes a single, complete logical goal, passes all unit tests, and can be easily reviewed in isolation. *Example: Adding a single database column and updating the corresponding model definition is atomic. Adding the column, updating the model, and implementing a new complex query is not.*
* **LLM Guidance:** The LLM prompt for **Code Generation** must be constrained to address only the specific scope of the active atomic User Story. This prevents the LLM from creating large, multi-feature diffs.

### 2. The Stacked Submission Workflow

The developer's primary responsibility shifts from writing boilerplate code to organizing, reviewing, and submitting the LLM's output as a clean stack.

| Step | Action | Dependency | Artifact Created |
|:---|:---|:---|:---|
| **Initial Commit** | Base feature setup (e.g., project scaffolding). | None | Base `Diff 0` (Submitted/Merged) |
| **Generate Diff 1** | LLM (G) generates code for *User Story 1*. | Requires `Diff 0` | **`Diff 1`** (Stacked on `Diff 0`) |
| **Verify Diff 1** | Code passes **G2 (Code Integrity Gate)** and the **SLM Audit (I)**. | - | `Diff 1` is **Cleared** |
| **Generate Diff 2** | LLM (G) generates code for *User Story 2*. | Requires `Diff 1` | **`Diff 2`** (Stacked on `Diff 1`) |
| **Verify Diff 2** | Code passes **G2 (Code Integrity Gate)** and the **SLM Audit (I)**. | - | `Diff 2` is **Cleared** |

### 3. Review and Integration Benefits

The stacked methodology directly enhances the efficiency of the Gating Functions:

* **G2 Review Speed:** Instead of reviewing a single, large Pull Request (PR) spanning 1,000 lines of code (LoC), the human reviewer reviews a sequence of 10 small diffs, each with \~100 LoC. This dramatically reduces **reviewer fatigue** and improves **security vulnerability detection**.
* **Targeted Rebase:** If the SLM Audit (I) flags an issue in `Diff 1`, the developer only needs to modify `Diff 1` and rebase `Diff 2`, `Diff 3`, etc. The changes are surgically applied, preserving the integrity of the other diffs.
* **G3 Acceptance Alignment:** When the final stack is deployed to Staging (K), the Product Owner (G3) can trace the acceptance criteria back to the clean, atomic history. A rejection of a single feature only requires reverting or adjusting the associated **single diff** in the stack, not the entire branch.

This combination ensures that the velocity gained by AI generation is not lost in chaotic integration or slow, monolithic review processes.

## VI. Strategic Takeaways for the Engineer

### 1. Avoid the Architectural Complexity Penalty

The goal of the G1 gate is to enforce the **Simplest Viable Architecture (SVA)**. Engineers must actively mitigate complexity, as it directly impacts your **Cost Penalty (C)** score.

* **Penalty Definition:** A design choice receives a high complexity penalty if it requires a manual, high-effort operation on the local stack (e.g., compiling a custom library, deploying a third-party service just for a POC) that is disproportionate to the performance gain.
* **Guidance:** Favor solutions that can be easily managed by your local **1B-14B SLM stack** via CLI and standard Python tooling.

### 2. Final Traceability: Gherkin to Executable Code

The final link in the chain is automation. The SLM translates the human-approved BDD (G3) into executable tests, completing the chain and creating a **living requirement**.

* **Input (Approved by Human):** Gherkin Scenarios.
* **Transformation:** An SLM (**Qwen2.5-Coder** or **Deepseek-R1**) is prompted to write the Python step definition code, ensuring API calls and assertions are correct.
* **Result:** A fully automated acceptance test suite.

This process ensures that your requirements are not passive documents but **active, verifiable code assets**. The entire lifecycle is structured for maximum **Accountability** and **Velocity**.

## VII. Appendices (Mandatory Companion Documents)

The following structured templates are mandatory operational tools for this handbook. They provide the necessary constraints to ensure LLM output is auditable by SLMs.

* **Appendix C:** Template 1: Elicitation and User Story Generation Prompt
* **Appendix D:** Template 2: Technical Specification Generation Prompt
* **Appendix E:** Template 3: Acceptance Criteria Generation Prompt
* **Appendix F:** NFR Manifest (JSON) Schema

See [Apendices](https://www.google.com/search?q=./appendices_for_requirements_engineering_in_the_ai_era.md).

## Further Reading

1.  [Towards Human-AI Synergy in Requirements Engineering: A Framework and Preliminary Study](https://arxiv.org/html/2510.25016)
1.  [AI for Requirements Engineering: Industry Adoption and Practitioner Perspectives](https://arxiv.org/html/2511.01324v3)

## Appendix A. Figure 1: The Gated Velocity Pipeline

![](../images/gated_velocity_pipeline.png)

## Appendix B. Glossary of Terms

This glossary standardizes the terminology necessary for operating the **Gated Velocity Pipeline** and understanding its core architectural principles.

### I. Methodology & Architecture

| Term | Definition | Context/Rationale |
| :--- | :--- | :--- |
| **Gated Velocity Pipeline** | The end-to-end framework, comprising three human-in-the-loop (HITL) Micro-Gates (G1, G2, G3) that enforce NFR compliance at critical decision points to mitigate Generative Debt. | The name highlights the core goal: balancing speed (velocity) with quality control (gating). |
| **SVA (Smallest Viable Architecture)** | The principle that the **production system** and the **SLM validation stack** must favor local, CLI-driven, GitOps-native solutions (e.g., local SLMs via Ollama, structured JSON artifacts). | Minimizes architectural complexity and cost (zero C1-C4 penalties) by focusing external, high-cost LLMs only on initial synthesis, keeping the deployment stack simple. |
| **Generative Debt** | Architectural or technical debt created by LLM synthesis when the generated code or specification violates NFRs (e.g., high memory consumption, security flaws, high complexity). | The primary risk the entire Gated Velocity framework is designed to prevent. |
| **WRC (Weighted Response Confidence)** | The primary viability metric for the methodology, calculated based on the three factors: **Effectiveness (E), Accountability (A),** and the **Complexity/Cost Penalty (C)**. Must be $\mathbf{\ge 0.89}$ for Production-Ready. | The quantitative measure used for architectural decision-making, trading off speed for viability. |
| **Micro-Gating** | The term for the three low-friction, high-frequency human review steps (G1, G2, G3). | Emphasizes that reviews are small, fast, and highly targeted, contrasting with monolithic human review. |
| **BDD-First Hybrid Model** | The optimal elicitation approach where the human defines the **Gherkin Sketch**, and the LLM augments it into the complete **Gherkin Feature File**. | Maximizes both human quality assurance and LLM synthesis velocity. |

### II. Artifacts & Requirements

| Term | Definition | Context/Rationale |
| :--- | :--- | :--- |
| **NFR Manifest** | The definitive, machine-readable contract defining all Non-Functional Requirements. Always stored as a versioned **JSON** file in the repository. | The single source of truth for all automated NFR audits (G1 and G2). |
| **Technical Specification Blueprint** | The detailed, LLM-generated design document (typically Markdown) that outlines the code structure, data flow, and architecture before coding begins. | The artifact validated at the **G1 Gate**. |
| **Gherkin Sketch** | The initial, essential subset of Gherkin steps (e.g., 3-5 critical `Given/When/Then` scenarios) authored by the human to define the core functional intent. | The human's high-value input into the **Hybrid BDD Model**. |
| **Gherkin Feature File** | The final, complete, LLM-augmented file containing all BDD scenarios used for acceptance testing (G3). | The artifact representing the fully defined functional requirement. |
| **SLM Audit Findings JSON** | The structured output from the SLM Auditor (G1 or G2) listing specific NFR violations, line numbers, and justifications based on the NFR Manifest. | The actionable input used by the human reviewer during Micro-Gating. |

### III. Roles & Processes

| Term | Definition | Context/Rationale |
| :--- | :--- | :--- |
| **G1: Architectural Viability Gate** | The point where the Architect reviews the **Technical Specification Blueprint** for NFR compliance, validated by the **SLM NFR Contract Validator**. | Ensures systemic viability before implementation. |
| **G2: Code Integrity Gate** | The point where the Engineer reviews the generated **Code Diff** for Generative Debt (complexity, security, dependency violations), validated by the **SLM Code Auditor**. | Prevents high-debt code from entering the main branch. |
| **G3: Strategic Acceptance Gate** | The final sign-off point where the Product Owner/Analyst approves the functional behavior **and** NFR compliance (Dual-Audit). | The official acceptance criteria for the entire feature. |
| **Dual-Audit G3 Gate** | The procedure at G3 requiring two separate confirmations: 1) BDD scenarios pass, and 2) a final SLM check confirms NFRs (e.g., latency, PII safety) are met on the staging environment. | The refinement necessary to push the WRC above 0.89. |
| **HITL (Human-in-the-Loop)** | The acknowledgment that human expertise (the Architect, Engineer, Analyst) is mandatory for strategic oversight and audit of AI-generated artifacts. | A core design philosophy of the methodology. |
