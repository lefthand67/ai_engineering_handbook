---
id: 26048
title: Formalize Weighted Response Confidence (WRC) as Ecosystem Evaluation Metric
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Establishment of the WRC scoring system as the authoritative metric for
  assessing the production-readiness of AI consultant outputs, integrating SVA penalties.
tags:
- architecture
- prompts
date: 2026-04-19
options:
  type: adr
  birth: 2026-04-19
  version: 0.1.0
  token_size: 1046
  status: proposed
  superseded_by: null
---
# ADR-26048: Formalize Weighted Response Confidence (WRC) as Ecosystem Evaluation Metric

## Date
2026-04-19

## Status

proposed

## Context
The AI system utilizes specialized consultant prompts (Hybrid, Local, DevOps) to provide high-stakes architectural advice. To avoid over-reliance on LLM-generated confidence scores (which are often poorly calibrated and prone to overconfidence), a structured, multi-component metric is needed to quantify the reliability of a response.

Currently, the Weighted Response Confidence (WRC) is embedded directly within the system prompts. While functional, this lacks governance; there is no authoritative record of the formula's rationale, the weighting of its components, or the semantic meaning of its thresholds. This constitutes technical debt (TD-006).

## Decision
We formalize the Weighted Response Confidence (WRC) as the ecosystem-wide standard for evaluating the quality and readiness of consultant outputs.

### 1. The WRC Formula
The WRC is a weighted average of three independent confidence dimensions:
$$\text{WRC} = 0.35 \cdot E + 0.25 \cdot A + 0.40 \cdot P$$

Where:
- **$E$ (Evidence):** Score based on the quantity and quality of external evidence/references cited.
- **$A$ (Alignment):** Score based on the adherence to project constraints and established architectural patterns.
- **$P$ (Probability/Confidence):** The model's internal estimation of the correctness of the conclusion, adjusted by the SVA framework.

### 2. Integration with SVA (Smallest Viable Architecture)
The $P$ component is not a raw value. It is subject to penalties derived from the SVA framework. Each violation of the six SVA constraints (C1-C6) applies a linear penalty to the probability score:
$$\text{P}_{\text{final}} = \text{P}_{\text{raw}} - (\text{violations} \cdot 0.10)$$

This ensures that an architecture that violates basic stability or efficiency constraints cannot be marked as high-confidence, regardless of the model's internal certainty.

### 3. Readiness Thresholds
The final WRC score determines the operational status of the recommendation:

- **$\text{WRC} \ge 0.89$**: **Production-Ready**. The recommendation is considered stable and can be implemented with minimal further review.
- **$0.70 \le \text{WRC} < 0.89$**: **Review Required**. The recommendation is plausible but requires human peer review or further stress-testing.
- **$\text{WRC} < 0.70$ or $\text{P}_{\text{final}} < 0.70$**: **PoC-Only**. The recommendation is a conceptual prototype. It is not suitable for production and must be treated as an experimental hypothesis.

## Consequences

### Positive
- **Objective Governance:** Moves the "authority" of the metric from a prompt string to a governed architectural decision.
- **Calibrated Confidence:** By penalizing SVA violations, the metric resists the LLM's natural tendency toward overconfidence.
- **Standardized Evaluation:** Provides a consistent language for human reviewers to assess AI-generated architecture.

### Negative / Risks
- **Formula Rigidity:** The weights (0.35, 0.25, 0.40) are heuristic. If future evidence suggests that $P$ should be weighted lower, the ADR must be updated.
- **Model Calibration:** The effectiveness of WRC still depends on the model's ability to honestly estimate $E, A,$ and $P_{\text{raw}}$.

## Alternatives
- **Binary Pass/Fail:** Using a simple checklist. **Rejection Reason:** Too coarse; fails to capture the nuance of "near-production" vs "experimental" results.
- **Raw Probability ($P$ only):** Relying solely on the model's confidence. **Rejection Reason:** High risk of hallucinated certainty; ignores evidence and alignment.

## References
- [ADR-26037: SVA Framework](/architecture/adr/adr_26037_smallest_viable_architecture_constraint_framework.md)

## Participants
1. Vadim Rudakov
