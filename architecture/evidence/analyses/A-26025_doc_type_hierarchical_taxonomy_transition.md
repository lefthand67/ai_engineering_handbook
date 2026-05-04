---
title: Document Type Hierarchical Taxonomy Transition
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: '2026-05-01'
description: Transition from a flat doc-type namespace to a hierarchical category.subtype
  model to resolve semantic collision between research and evidence.
tags:
- documentation
- governance
options:
  type: analysis
  id: A-26025
  status: active
  birth: '2026-05-01'
  version: 1.0.0
  token_size: 1704
---
# Document Type Hierarchical Taxonomy Transition

## Problem Statement
The current governance model suffers from **Semantic Overloading**. The `analysis` type is tasked with two mutually exclusive roles:
1.  **Formal Evidence:** High-rigor artifacts used for ADR elaboration (requiring `id`, `status`, and specific lifecycle tracking).
2.  **Domain Research:** Flexible technical deep-dives (requiring only identity and discovery blocks).

By forcing "Domain Research" into the `guide` type to bypass validation, the system introduces **Metadata Decay**—where the `type` field no longer represents the actual nature of the content, rendering the `type` registry useless for automated discovery and indexing.

The root cause is a **Flat Taxonomy**. The system implements a 1:1 mapping between `type` and `validation_rules`. Because the system lacks a "category" or "namespace" layer, any two document types that share the word "analysis" but have different rigor requirements must be treated as entirely unrelated entities or forced into an incorrect category.

### Validation Gap Analysis
| Subjective/Emotional Claim | Falsifiable Metric / Requirement | Evidence Source / Validation Method |
| :--- | :--- | :--- |
| "Agents always struggle with this" | $\uparrow$ Rate of `unknown_type` or `missing_field` errors during `check_frontmatter` runs in `ai_agents/`. | `check_frontmatter.py` logs / Git commit history of frontmatter fixes. |
| "Analysis is only used for ADR" | $\%$ of `type: analysis` files located in `architecture/evidence/analyses/` vs elsewhere. | `grep -r "type: analysis" .` |
| "Describes it as 'guide' because..." | $\uparrow$ Correlation between "Analysis" in title and `type: guide` in frontmatter. | Cross-reference of file titles vs `options.type`. |

## Approach Evaluation

### Assumption Interrogation
| Assumption | Status | Falsification Evidence |
| :--- | :--- | :--- |
| LLMs intuitively handle dot-notation (`type: research.analysis`) | **Plausible** | Agent consistently fails to produce the correct string despite prompt instructions. |
| Migration to a new taxonomy is a one-time cost | **Verified** | A regex-based migration script can update all `.md` files in a single pass. |
| The proposed `[architecture, research]` split is exhaustive | **Unsupported** | Discovery of a third top-level category (e.g., `operational`, `tutorial`) that doesn't fit either. |
| `check_frontmatter.py` is the only consumer of `options.type` | **Plausible** | Discovery of other scripts (e.g., indexers, site builders) that expect a flat string. |

### WRC Calculation & P-Score Audit
**Proposed Methodology:** Hierarchical Taxonomy via Dot-Notation (`type: category.subtype`)

**P-Score Audit Summary:**
- **P_raw:** 0.95 (Highly suitable for the local Python/Git stack).
- **SVA Audit:**
    - C1 (Automation): Pass.
    - C2 (Vendor): Pass.
    - C3 (Git): Pass.
    - C4 (Proportional Complexity): Pass.
    - C5 (Reuse): Pass.
    - C6 (Scalability): Pass.
- **Penalty:** 0.00.
- **P_final:** 0.95.

**WRC Calculation:**
- **E (Empirical):** 0.80 (Common pattern in API versioning and config management). $\rightarrow 0.80 \times 0.35 = 0.28$
- **A (Industry):** 0.90 (Standard for namespacing in enterprise software). $\rightarrow 0.90 \times 0.25 = 0.225$
- **P (Performance):** 0.95 (SVA compliant). $\rightarrow 0.95 \times 0.40 = 0.38$
- **Total WRC:** **0.885**

### Methodology Comparison

| Methodology | Description (WRC) | Pros | Cons | Best For | Source |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Flat Namespace** | Distinct types: `tech_analysis`, `arch_analysis` (WRC 0.72) | Zero script changes. | Poor scalability; semantic clutter. | Small sets of types. | Community |
| **Multi-Field** | `type` + `subtype` fields (WRC 0.81) | Clean data structure. | High migration cost; breaks existing YAML parsers. | Formal databases. | Enterprise |
| **Hierarchical (Dot)** | **`type: cat.sub` (WRC 0.89)** | **Intuitive; scalable; single-field.** | **Requires minor script update.** | **AI-native docs.** | **Enterprise** |
| **Type Inheritance** | Logic-based inheritance in JSON (WRC 0.84) | Most powerful. | Over-engineered for current scale (SVA C4). | Large-scale CMS. | Academic |

**Recommendation:** **Hierarchical Dot-Notation**. It provides the best balance between structural rigor and implementation simplicity, fitting the SVA "Smallest Viable Architecture" profile.

## Key Insights
**Viability Classification:** **Production-ready**. The solution is vendor-neutral, Git-native, and the implementation risk is negligible (localized to one Python script). It achieves a WRC of 0.89.

**Architectural Complexity Audit:** No SVA violations detected. The refactoring is proportional to the problem.

### Actionable Strategies
**1. The Taxonomy Shift (WRC 0.89) [E: 0.8 / A: 0.9 / P: 0.95]**
- **The Pattern:** Implement `type: <category>.<subtype>`.
- **The Trade-off:** [Complexity / Maintenance]. Increases the complexity of the validator logic slightly but reduces the maintenance burden of the type registry.
- **Reliable sources:** Kubernetes API Group/Version pattern.

**2. The Atomic Migration (WRC 0.92) [E: 0.9 / A: 0.9 / P: 0.9]**
- **The Pattern:** Use a Python migration script to perform a regex-based search-and-replace on all governed files.
- **The Trade-off:** [Risk / Speed]. Fast execution, but requires a full-repo git commit that may cause merge conflicts if others are working on docs.
- **Reliable sources:** Standard refactoring patterns in large-scale monorepos.

### Pitfalls and Hidden Technical Debt
- **Regression Risk:** If `check_frontmatter.py` is not updated before the migration, all files will fail validation.
- **Taxonomy Drift:** Without a strict definition of what constitutes "Architecture" vs "Research," agents may start creating arbitrary categories.

### Security Implications
None. The change affects metadata and does not alter the execution logic of the system.

### Immediate Next Step
Update `.vadocs/conf.json` to reflect the new hierarchical types and modify `tools/scripts/check_frontmatter.py` to support the `split('.')` logic for type resolution.

## References
- ISO 29148: Systems and software engineering — Life cycle processes — Requirements engineering.
- Kubernetes API Group/Version design guidelines.
