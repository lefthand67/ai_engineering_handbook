# AI Systems Grounding in Computing Disciplines

-----

Owner: Vadim Rudakov, lefthand67@gmail.com
Version: 0.2.1
Birth: 2025-12-05
Last Modified: 2025-12-06

-----

> INFO: *The handbook is optimized for environments supporting Mermaid.js diagrams. For static export, rasterized versions are available in Appendix A.*

This document maps the AI System Lifecycle to the foundational disciplines defined by the **ACM/IEEE Joint Task Force on Computing Curricula** (available at [https://www.acm.org/education/curricula-recommendations](https://www.acm.org/education/curricula-recommendations)). This provides a structured, globally-adopted context for the roles and required expertise within the generic AI Engineering team. AI Engineering is viewed here as an **emergent, convergent domain**, synthesizing principles from multiple computing disciplines.

## The Foundational Computing Disciplines and Their Contribution to Production AI Systems

The table below maintains the official ACM/IEEE Computing Curricula structure but reclassifies ACM's "Data Science" for terminological accuracy in a production context.

| Discipline | Latest Version | Target Audience/Focus Areas | Key Differences/Overlaps | AI/ML Implementation Examples |
| :--- | :--- | :--- | :--- | :--- |
| **Computer Engineering** | CE2016 | Undergraduate programs in Computer Engineering. | Focuses on **hardware-software integration**; crucial for specialized accelerator design. | [**FPGA/ASIC optimization**](../1\_execution/optimization\_fpga\_asic\_hardware\_acceleration\_for\_ai.md) for inference, [**CUDA kernel development**](../1\_execution/optimization\_nvidia\_gpu\_cuda\_nsight\_and\_systems\_thinking.md), low-level memory management for HPC. |
| **Computer Science** | CS2023 | Undergraduate programs in Computer Science. | Broad foundational computing; emphasizes **theoretical aspects, algorithms, and complexity**. | **Algorithm design** for efficient sampling, **Time/Space complexity analysis** of inference, **Novel attention mechanism design**. |
| **Cybersecurity** | CSEC2017 | Post-secondary degree programs in Cybersecurity. | Focuses on **security competencies**; essential for robust, compliant MLOps deployment. | **Threat modeling** for MLOps pipelines, **Adversarial attack mitigation** (e.g., poisoning), secure API endpoint deployment. |
| **ML/Statistical Foundations**[^1] | CCDS2021 | Undergraduate programs with a data science focus. | Integrates computing with statistics; focuses on **analysis, modeling, and core ML principles**. | **Feature engineering**, **Exploratory Data Analysis (EDA)**, **Model selection/hyperparameter tuning**, designing evaluation metrics. |
| **Information Systems** | IS2020 | Undergraduate programs in Information Systems. | Emphasizes **business and system competencies**; organizational use of information. | **Data Governance** strategy, **Stakeholder management** for data access, **Explainability (XAI)** compliance reporting, **Business process modeling** around AI outputs. |
| **Information Technology** | IT2017 | Baccalaureate programs in Information Technology. | Focuses on practical **infrastructure and support**; vital for monitoring and platform maintenance. **(Requires MLOps/SRE augmentation)**. | **Cloud resource provisioning** (Terraform/CloudFormation), **Containerization** (Docker/Podman), **System monitoring** and alerting. |
| **Software Engineering** | SE2014 | Specific to the **software development lifecycle**; emphasizes engineering practices, design, and testing. **(Requires MLOps/SRE augmentation)**. | **Microservice design** for model serving, **Automated testing** (unit/load), **CI/CD pipeline construction** (GitOps), code quality standards. |

[^1]:
    *CCDS2021 provides a **competency model** for Data Science, not a full degree curriculum equivalent to CS or SE. In a production setting, this discipline is implemented as **Machine Learning Engineering (MLE)** for efficient deployment.*

## AI Systems Connection to the ACM Disciplines

The diagram shows AI Systems not as a separate branch, but as the **convergent product** of the foundational disciplines.

```mermaid
---
config:
  theme: redux
  layout: elk
---
flowchart TB
 subgraph Foundation["The Core Foundation (ACM Curricula Roots)"]
        CS("Computer Science: Theory & Algorithms")
  end
 subgraph Engineering["System & Code Focus"]
        CE["Computer Engineering: Hardware + Software"]
        SE["Software Engineering: Development Lifecycle"]
  end
 subgraph Specialized["Data, Risk & Analysis Focus"]
        DS["ML/Statistical Foundations (CCDS2021)"]
        Cyb["Cybersecurity: Protection & Threats"]
  end
 subgraph Business_Tech["Deployment & Operational Focus"]
        IS["Information Systems: Business Use of Data"]
        IT["Information Technology: Infrastructure & Support"]
  end
 subgraph Discipline_Groups["Disciplinary Focus Areas"]
        Engineering
        Specialized
        Business_Tech
  end
 subgraph AI_Systems["The Convergent Layer: Production AI Lifecycle (MLOps)"]
        AIH("1. Hardware & Optimization")
        AIT("2. Training & Modeling")
        AID("3. Deployment & MLOps")
  end
    CS ==> Engineering & Specialized & Business_Tech
    CE -.-> SE
    DS -.-> IS
    CE == "Optimization & Low-Level Systems" ==> AIH
    DS == Data Prep & Model Training ==> AIT
    SE == Code Quality & CI/CD ==> AID
    IT == Infrastructure & SRE ==> AID
    IS == Requirements & Governance ==> AID
    Cyb == Trust & Resilience ==> AID

    style CS fill:#00BFFF, stroke:#00BFFF, color:#FFF, stroke-width:3px
    style CE fill:#FFD700, stroke:#FFD700, color:#333
    style SE fill:#FFD700, stroke:#FFD700, color:#333
    style DS fill:#FF6347, stroke:#FF6347, color:#FFF
    style Cyb fill:#FF6347, stroke:#FF6347, color:#FFF
    style IS fill:#90EE90, stroke:#90EE90, color:#333
    style IT fill:#90EE90, stroke:#90EE90, color:#333
    style Engineering stroke:#FFD600
    style Specialized stroke:#D50000
    style Business_Tech stroke:#00C853
    style AIH fill:#8A2BE2, stroke:#8A2BE2, color:#FFF, stroke-width:4px
    style AIT fill:#8A2BE2, stroke:#8A2BE2, color:#FFF, stroke-width:4px
    style AID fill:#8A2BE2, stroke:#8A2BE2, color:#FFF, stroke-width:4px
    style Discipline_Groups stroke:#000000
    style Foundation stroke:#2962FF
    style AI_Systems stroke:#AA00FF
    linkStyle 0 stroke:#2962FF,fill:none
    linkStyle 1 stroke:#2962FF,fill:none
    linkStyle 2 stroke:#2962FF,fill:none
    linkStyle 5 stroke:#FFD600,fill:none
    linkStyle 6 stroke:#D50000,fill:none
    linkStyle 7 stroke:#FFD600,fill:none
    linkStyle 8 stroke:#00C853,fill:none
    linkStyle 9 stroke:#00C853,fill:none
    linkStyle 10 stroke:#D50000,fill:none
```

## Breakdown of AI Grounding (Production Context)

1.  **Hardware & Optimization (AIH)**

      * **Grounded in:** **Computer Engineering** (CE2016).
      * **Production Context:** Covers high-performance computing clusters and hardware-software co-design. This is where **systems thinking** and low-level optimization (memory, latency) are applied to specialized accelerators (GPUs, TPUs) for efficiency.

2.  **Training & Modeling (AIT)**

      * **Grounded in:** **ML/Statistical Foundations** (CCDS2021).
      * **Production Context:** The engineering application of these principles is **Machine Learning Engineering (MLE)**, focused on reproducible training, model versioning, bias mitigation, and data pipeline integrity.

3.  **Deployment & MLOps (AID)**

      * **Grounded in:** **Software Engineering** (SE2014), **Information Technology** (IT2017), and **Cybersecurity** (CSEC2017).
      * **Production Context:** This phase synthesizes multiple disciplines and **must be augmented by MLOps/SRE principles**, which go beyond the scope of older curricula. Adherence to standards like **ISO/IEC 23053 (AI Engineering Framework)** and **ISO/IEC 29148 (Requirements Engineering)** is mandatory.
          * **Software Engineering** handles model integration into scalable, robust microservices.
          * **Information Technology** handles the underlying cloud infrastructure, logging, and continuous performance monitoring (the "Ops" of MLOps).
          * **Cybersecurity** ensures compliance, integrity, and threat-response, crucial for a trusted service.

## Appendix A. Renderred Diagram

![](./images/ai_systems_grounding_in_computing_disciplines_diagram.png)
