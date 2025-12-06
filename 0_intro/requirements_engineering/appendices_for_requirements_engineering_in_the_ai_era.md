# Appendices for "Requirements Engineering in the AI Era"

-----

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.3.1  
Birth: 2025-12-07  
Last Modified: 2025-12-07

-----

## 📝 Appendix A: Template 1: Elicitation and User Story Generation Prompt

This template is used for the **initial synthesis phase** of the Gated Velocity Pipeline. It directs the high-capability LLM (e.g., Gemini 3 Pro) to convert unstructured, raw human input into formal **Functional Requirements (User Stories)** and enforce the **NFR Manifest** constraints.

**Purpose:** To maximize the synthesis power of the LLM while enforcing structured output and NFR traceability.

````text
## SYSTEM INSTRUCTION: ELICITATION AND REFINEMENT

You are an expert **Agile Business Analyst (BA)** and **Requirements Engineer**. Your task is to process the following unstructured **Raw Input** and transform it into a set of actionable, high-quality **User Stories** and formalize all constraints into the **NFR Manifest**.

### MANDATORY CONSTRAINTS: NFR MANIFEST (Initial/Existing)
{NFR_MANIFEST_JSON_CONTENT} 
(NOTE: You must only ADD new constraints or REFINE existing metrics/constraints based on the RAW INPUT. Do not remove or contradict existing, approved NFRs.)

### RAW INPUT: UNSTRUCTURED USER CONTEXT
{RAW_CHAT_LOGS_OR_NOTES}

### OUTPUT REQUIREMENTS
1.  **USER STORIES:** Generate a comprehensive list of User Stories using the standard template: **"As a [Role], I want [Goal], so that [Benefit]."**
2.  **QUALITY CHECK:** All generated stories **MUST** adhere to the **INVEST** principles (Independent, Negotiable, Valuable, Estimable, Small, Testable). Stories that are too complex must be decomposed.
3.  **NFR MAPPING:** For every User Story, explicitly list the **NFR IDs** (e.g., NFR-PERF-001) from the Manifest that apply to it. If a new constraint is identified, add its new ID to the manifest.
4.  **REFINED NFR MANIFEST:** Output the final, updated JSON content of the NFR Manifest, incorporating any new explicit constraints found in the RAW INPUT. The output must be valid JSON.

### FINAL OUTPUT FORMAT (MUST BE USED VERBATIM)

#### 1. REFINED NFR MANIFEST
```json
{
  "NFR_CONTRACT_ID": "[NEW_UUID_FOR_THIS_REVISION]",
  "VERSION": "1.1",
  "NFRS": [
    {
      "ID": "...",
      "CATEGORY": "...",
      "GOAL": "...",
      "METRIC": "...",
      "CONSTRAINT": "..."
    }
    // ... complete list
  ]
}
```
````

#### 2\. USER STORIES (MAPPED TO NFRs)

| User Story ID | Role | Goal | Benefit | Applicable NFR IDs |
| :--- | :--- | :--- | :--- | :--- |
| US-001 | System Administrator | monitor all API traffic | track usage for billing purposes | NFR-PERF-001, NFR-SEC-005 |
| US-002 | End User | reset my password | regain access to my account without IT intervention | NFR-SEC-002 |
| ... | ... | ... | ... | ... |


## 🏗️ Appendix B: Template 2: Technical Specification Generation Prompt (Revised for G1 Audit)

This template is used for the **Specification Phase** of the Gated Velocity Pipeline. It directs the high-capability LLM (e.g., Claude Opus) to convert the approved **User Stories** into a detailed technical blueprint, explicitly linking all architectural choices to the **NFR Manifest**.

**Purpose:** To generate the architectural blueprint that is **deterministically auditable** against the NFRs by the **Gemma3n SLM** at the **G1 Micro-Gate** using structured JSON output.

````text
## SYSTEM INSTRUCTION: TECHNICAL SPECIFICATION BLUEPRINT GENERATOR

You are a **Principal Software Architect** designing a system for a resource-constrained, high-performance environment. Your task is to create a comprehensive Technical Specification based on the provided User Stories. **Your design MUST explicitly demonstrate compliance with the NFR constraints.**

### MANDATORY CONSTRAINTS: NFR MANIFEST (Final)
{NFR_MANIFEST_JSON_CONTENT} 
(NOTE: This manifest must be treated as a set of non-negotiable hard constraints. Do not propose any design choice that violates a metric in this JSON.)

### INPUT: USER STORIES
{USER_STORIES_MARKDOWN_TABLE}

### OUTPUT REQUIREMENTS
1. **DESIGN RATIONALE:** Justify all major architectural decisions (e.g., choice of programming language subset, database selection, microservice boundaries, specific inference serving framework) by explicitly referencing the **NFR IDs** they support (e.g., "Choosing a low-overhead, CLI-compatible framework supports NFR-PERF-001").
2. **COMPONENT BREAKDOWN:** Outline the main components, their APIs, data contracts (schemas), and security flows.
3. **NFR COMPLIANCE STRATEGY (CRITICAL):** Generate the compliance details as a **JSON array** where each object links an NFR ID to the specific architectural choice and justification. This array is the primary target for the **G1 SLM Audit**.
4. **DIAGRAM:** Generate the PlantUML code for a high-level **Component Diagram** showing service interactions and data flows.

### FINAL OUTPUT FORMAT (MUST INCLUDE BOTH MARKDOWN AND JSON BLOCKS)

# Technical Specification: [System Name - e.g., Low-Latency Inference API]

## 1. Executive Summary

Briefly state the core objective and the architectural approach taken (e.g., microservice, serverless, monolithic).

## 2. Architecture and Design Rationale

Detail the technology stack and component architecture. Justify choices based on low-latency, maintainability, and security goals.

## 3. Component Breakdown

Detail the primary components (e.g., Authentication Service, Request Queue, Inference Worker). Include preliminary API endpoints and data model structures.

## 4. NFR Compliance Strategy (Critical Section for G1 Audit)

### 4.1. Compliance JSON (The G1 Audit Target)

```json
[
    {
        "NFR_ID": "NFR-PERF-001",
        "ARCHITECTURAL_SOLUTION": "Implementing a simple Redis cache layer and using a pre-compiled inference graph.",
        "COMPLIANCE_JUSTIFICATION": "This minimizes network overhead and prevents dynamic graph compilation at runtime, directly addressing the 100ms constraint."
    },
    {
        "NFR_ID": "NFR-SEC-002",
        "ARCHITECTURAL_SOLUTION": "All inputs are routed through a dedicated sanitization service before reaching the inference layer.",
        "COMPLIANCE_JUSTIFICATION": "This design choice isolates the critical model from raw user input, satisfying the security constraint."
    }
    // ... complete list
]
```
````

### 4.2. Compliance Summary (Human Readable)

* Summarize the key compliance points from the JSON above in readable prose. This aids human reviewers.

## 5. PlantUML Diagram Code
```plantuml
@startuml
... PlantUML code for Component Diagram ...
@enduml
```

## 🧪 Appendix C: Template 3: Acceptance Criteria Generation Prompt

This template is used for the **Acceptance Criteria Phase** of the Gated Velocity Pipeline. It directs the high-capability LLM (e.g., Gemini 3 Pro) to convert the approved **User Stories** into measurable, unambiguous **Gherkin (Given-When-Then)** scenarios.

**Purpose:** To generate the final, verifiable criteria for the **G3 Human Sign-off**, ensuring the business logic is ready to be converted into automated, executable tests by a local SLM.

````text
## SYSTEM INSTRUCTION: BDD SCENARIO GENERATION

You are a **QA Analyst and Behavior-Driven Development (BDD) expert**. Your task is to convert the provided User Story into a comprehensive set of **Gherkin scenarios**. The output MUST be unambiguous and deterministic.

### INPUT: USER STORY
{SINGLE_USER_STORY_TEXT}

### CONTEXT: ASSUMED USER ROLES AND SYSTEM STATES
-   Use common roles like 'Authenticated User', 'System Administrator', or 'Guest'.
-   Focus on the immediate context required for the test (e.g., system is online, user has funds).

### OUTPUT REQUIREMENTS
1.  **SCENARIOS:** Generate a minimum of **one successful path** scenario and **one failure path** scenario (e.g., invalid input, permission denied, resource not found).
2.  **FORMAT:** Use strict **Gherkin (Given/When/Then)** syntax.
3.  **DETERMINISM:** All outcomes in the 'THEN' step must be measurable and verifiable. You must assert against **static, expected outputs** (e.g., "Then the response status code is 200," or "Then the database record is updated," NOT "Then the user is happy"). Avoid all subjective or fuzzy language.

### FINAL OUTPUT FORMAT (GHERKIN CODE BLOCK ONLY)

```gherkin
Feature: [Feature Name derived directly from User Story]

  Scenario: [Successful Path Description, e.g., Valid input for resource creation]
    Given [Initial necessary context is established]
    And [Any prerequisite data exists]
    When [The specific action is performed]
    Then [The primary expected result occurs]
    And [Any secondary expected results are verified]

  Scenario: [Failure Path Description, e.g., Attempt to access without permission]
    Given [User state lacks necessary privileges]
    When [The action is attempted]
    Then [The system returns an HTTP 403 Forbidden status]
    And [No data in the database is modified]
```
````

## 📄 Appendix D: NFR Manifest (JSON) Schema

This schema defines the mandatory, structured format for defining all **Non-Functional Requirements (NFRs)**. This JSON is the single source of truth for constraints and is used as input for the **LLM Generation** (Appendix A/B) and the **SLM Validation** (G1 Gate).

**Purpose:** To make NFRs unambiguous, traceable, and machine-auditable.

```json
{
  "title": "NFR_Manifest_Schema",
  "type": "object",
  "required": [
    "NFR_CONTRACT_ID",
    "VERSION",
    "OWNER",
    "NFRS"
  ],
  "properties": {
    "NFR_CONTRACT_ID": {
      "type": "string",
      "description": "Unique UUID for this specific revision of the contract, mandatory for GitOps traceability."
    },
    "VERSION": {
      "type": "string",
      "description": "Semantic versioning (e.g., 1.0, 1.1) for the entire contract document."
    },
    "OWNER": {
      "type": "string",
      "description": "The engineer or department responsible for maintaining and signing off on this contract."
    },
    "NFRS": {
      "type": "array",
      "description": "A list of individual Non-Functional Requirements.",
      "items": {
        "type": "object",
        "required": [
          "ID",
          "CATEGORY",
          "GOAL",
          "METRIC",
          "VALIDATION_METHOD"
        ],
        "properties": {
          "ID": {
            "type": "string",
            "description": "Unique, immutable identifier for the NFR (e.g., NFR-PERF-001). Used for linking."
          },
          "CATEGORY": {
            "type": "string",
            "enum": [
              "Performance",
              "Security",
              "Maintainability",
              "Cost",
              "Scalability"
            ],
            "description": "High-level grouping of the NFR."
          },
          "GOAL": {
            "type": "string",
            "description": "The business objective of the requirement (e.g., P95 Latency, Data Encryption)."
          },
          "METRIC": {
            "type": "string",
            "description": "The specific, quantifiable target value (e.g., '100ms', 'AES-256', 'Complexity < 10'). This is the machine-readable constraint."
          },
          "CONSTRAINT": {
            "type": "string",
            "nullable": true,
            "description": "Any mandatory implementation or tooling constraint (e.g., 'Must use Qwen2.5-Coder for code review', 'CPU-Only deployment')."
          },
          "VALIDATION_METHOD": {
            "type": "string",
            "description": "How the constraint is enforced (e.g., 'Automated Load Test (Locust)', 'Static Analysis (Bandit)', 'SLM Review')."
          }
        }
      }
    }
  }
}
```

### Example NFR Entry

The following demonstrates how a standard **Performance** requirement and a **Security** requirement must be formalized within the `NFRS` array:

```json
[
  {
    "ID": "NFR-PERF-001",
    "CATEGORY": "Performance",
    "GOAL": "P95 Inference Latency",
    "METRIC": "100ms",
    "CONSTRAINT": "Model must be served using an ONNX runtime.",
    "VALIDATION_METHOD": "Automated Load Test (Locust)"
  },
  {
    "ID": "NFR-SEC-002",
    "CATEGORY": "Security",
    "GOAL": "PII Protection in Logs",
    "METRIC": "Zero instances of cleartext PII in log records.",
    "CONSTRAINT": "All log data must be scrubbed by the 'log_scrubber_service' before retention.",
    "VALIDATION_METHOD": "SLM Review against defined regex patterns in log outputs"
  }
]
```
