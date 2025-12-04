# AI Systems Grounding in Computing Disciplines

-----

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.1.0   
Birth: 2025-12-05  
Last Modified: 2025-12-05

-----

> INFO: *The handbook is optimized for environments supporting Mermaid.js diagrams. For static export, rasterized versions are available in Appendix A.*

This document maps the AI System Lifecycle to the foundational disciplines defined by the **ACM/IEEE Joint Task Force on Computing Curricula** (available at https://www.acm.org/education/curricula-recommendations). This provides a structured, world-adopted context for the roles and required expertise within our AI Engineering team.

The table below and the subsequent diagram are based on the **official ACM/IEEE Computing Curricula**. However, our diagram introduces the **AI Lifecycle** as a new primary branch stemming from these foundational disciplines, illustrating how each phase is grounded in a specific computing area.

| Discipline | Latest Version | Brief Description | Target Audience/Focus Areas | Key Differences/Overlaps |
| :--- | :--- | :--- | :--- | :--- |
| **Computer Engineering** | CE2016 (2016) | Curriculum guidelines for undergraduate degree programs. | Undergraduate programs in Computer Engineering. | Focuses on **hardware-software integration**; crucial for specialized accelerator design (e.g., TPUs, ASICs). |
| **Computer Science** | CS2023 (2023) | Curriculum guidelines for undergraduate programs. | Undergraduate programs in Computer Science. | Broad foundational computing; emphasizes **theoretical aspects, algorithms, and complexity**. |
| **Cybersecurity** | CSEC2017 (2017) | Curriculum guidelines for post-secondary degree programs, with foundational supplements. | Post-secondary degree programs in Cybersecurity. | Focuses on **security competencies**; essential for robust, compliant MLOps deployment. |
| **Data Science** | CCDS2021 (2021) | Computing competencies for undergraduate data science curricula. | Undergraduate programs with a data science focus. | Integrates computing with statistics; emphasizes **analysis, modeling, and machine learning principles**. |
| **Information Systems** | IS2020 (2020) | A competency model for undergraduate programs. | Undergraduate programs in Information Systems. | Emphasizes **business and system competencies**; organizational use of information. |
| **Information Technology** | IT2017 (2017) | Curriculum guidelines for baccalaureate degree programs. | Baccalaureate programs in Information Technology. | Focuses on practical **infrastructure and support**; vital for monitoring and platform maintenance. |
| **Software Engineering** | SE2014 (2014) | Curriculum guidelines for undergraduate degree programs. | Undergraduate programs in Software Engineering. | Specific to the **software development lifecycle**; emphasizes engineering practices, design, and testing. |

```mermaid
---
config:
  theme: redux
  layout: elk
---
flowchart TB
 subgraph Foundation["The Foundation
          (ACM Curricula Roots)"]
        CS("Computer Science: Theory & Algorithms")
  end
 subgraph Engineering["Engineering Focus"]
        CE["Computer Engineering: Hardware + Software"]
        SE["Software Engineering: Development Lifecycle"]
  end
 subgraph Specialized["Specialized Focus"]
        Cyb["Cybersecurity: Protection & Threats"]
        DS["Data Science / ML Engineering: Analysis & Modeling"]
  end
 subgraph Business_Tech["Business/Tech Focus"]
        IS["Information Systems: Business Use of Data"]
        IT["Information Technology: Infrastructure & Support"]
  end
 subgraph AI_Systems["AI Systems & Lifecycle (Production Reality)"]
        AIH["1. Hardware & Infrastructure (Deep Systems)"]
        AIT["2. Training & Modeling (MLOps Prep)"]
        AID["3. Deployment & MLOps (Cloud/DevOps)"]
  end
    CS ==> Engineering & Specialized & Business_Tech & AI_Systems
    CE == Hardware for AI ==> AIH
    IT == Infrastructure & Monitoring ==> AI_Systems
    IS == Main Consumer ==> AI_Systems
    DS == Data & Model Training ==> AIT
    SE == Software Deployment of AI ==> AI_Systems
    Cyb == Security & Compliance ==> AI_Systems
    CE -. Overlap .- SE
    DS -. Overlap .- IS
    IS -. Overlap .- IT

    style CS fill:#00BFFF, stroke:#00BFFF, color:#FFF, stroke-width:3px
    style CE fill:#FFD700, stroke:#FFD700, color:#333
    style SE fill:#FFD700, stroke:#FFD700, color:#333
    style Cyb fill:#FF6347, stroke:#FF6347, color:#FFF
    style DS fill:#FF6347, stroke:#FF6347, color:#FFF
    style IS fill:#90EE90, stroke:#90EE90, color:#333
    style IT fill:#90EE90, stroke:#90EE90, color:#333
    style AIH fill:#8A2BE2, stroke:#8A2BE2, color:#FFF
    style AIT fill:#8A2BE2, stroke:#8A2BE2, color:#FFF
    style AID fill:#8A2BE2, stroke:#8A2BE2, color:#FFF
    linkStyle 0 stroke:#2962FF,fill:none
    linkStyle 1 stroke:#2962FF,fill:none
    linkStyle 2 stroke:#2962FF
    linkStyle 3 stroke:#2962FF,fill:none
    linkStyle 4 stroke:#FFD600,fill:none
    linkStyle 5 stroke:#00C853,fill:none
    linkStyle 6 stroke:#00C853,fill:none
    linkStyle 7 stroke:#D50000,fill:none
    linkStyle 8 stroke:#FFD600,fill:none
    linkStyle 9 stroke:#D50000,fill:none
    linkStyle 10 stroke:#FFD600,fill:none
    linkStyle 11 stroke:#FF6347,fill:none
    linkStyle 12 stroke:#00C853,fill:none
```

**Breakdown of AI Grounding (Production Context)**

1.  **Hardware & Infrastructure (AIH)**

      * **Grounded in:** **Computer Engineering** (CE2016).
      * **Production Context:** This covers the high-performance computing clusters, hardware-software co-design, and deep optimization required for specialized chips (GPUs/TPUs). **A deep understanding requires principles rooted in Electrical Engineering** for those working on custom accelerator design or low-level memory management.

2.  **Training & Modeling (AIT)**

      * **Grounded in:** **Data Science / Machine Learning Engineering** (CCDS2021).
      * **Production Context:** While Data Science covers the *principles* (data preparation, model selection), the engineering team applies this as **Machine Learning Engineering (MLE)**, focusing on efficient model training, versioning, and readiness for MLOps pipelines.

3.  **Deployment & MLOps (AID)**

      * **Grounded in:** **Software Engineering** (SE2014), **Information Technology** (IT2017), and **Cybersecurity** (CSEC2017).
      * **Production Context:** This phase synthesizes multiple disciplines and **MUST adhere to modern Cloud Engineering and DevOps/SRE standards**, moving beyond the scope of the older SE/IT curricula.
          * **Software Engineering** handles the model integration into scalable, robust, production-grade applications.
          * **Information Technology** handles the underlying cloud infrastructure, logging, and performance monitoring (the "Ops" of MLOps).
          * **Cybersecurity** ensures the system meets compliance, integrity, and threat-response requirements crucial for a trusted production service.

## Appendix A. Renderred Diagram

![](./images/ai_systems_grounding_in_computing_disciplines_diagram.png)
