---
id: 26057
title: Adoption of SkillOpt for Empirical Agent Skill Optimization
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Transition from heuristic-based skill crafting to an empirical, textual
  state optimization loop using SkillOpt.
tags:
- agents
- model
- testing
- architecture
date: 2026-06-08
options:
  status: proposed
  type: adr
  birth: 2026-06-08
  version: 1.0.0
  token_size: 872
---
# ADR-26057: Adoption of SkillOpt for Empirical Agent Skill Optimization

## Context
The current process for developing agent skills (behavioral specifications in Markdown) relies on manual heuristic iteration or one-shot synthetic generation. This lack of a formal objective function leads to inconsistent performance, regression during updates, and an inability to empirically prove the superiority of a specific skill version. 

The lack of a systematic optimization loop creates a "Prompt Engineering Gap" where skill quality is limited by the engineer's intuition rather than an optimized state derived from verifiable data.

Detailed architectural analysis and comparative evaluation against programmatic alternatives (e.g., DSPy) are documented in [A-26026](/architecture/evidence/analyses/A-26026_skillopt_adoption_comparative_analysis.md).

## Decision
We adopt **SkillOpt** as the primary methodology for the optimization and fine-tuning of the ecosystem's modular agent skills.

The adoption is based on the following mandates:
1. **Textual State Optimization:** Skills must be treated as trainable documents where the "weights" are the textual instructions and examples.
2. **Empirical Gating:** No skill update shall be merged into the trunk unless it demonstrates a statistically significant improvement (or non-regression) on a held-out validation set.
3. **SVA Compliance:** The optimization process must remain external to the runtime, ensuring that the deployed artifact remains a zero-dependency Markdown file.

## Status
Proposed


## Consequences

### Positive
- **Verifiable Quality:** Shifts skill development from "intuition-based" to "evidence-based," aligned with ISO 29148 standards.
- **Zero Runtime Overhead:** Unlike programmatic frameworks, the output is plain text, maintaining zero inference-time latency and no runtime dependencies.
- **Git-Native Traceability:** All optimized skills are stored as `.md` files, enabling precise diffing and versioning of behavioral changes.
- **Model Agnostic Deployment:** Optimized skills are portable across different model scales and providers.

### Negative
- **Evaluation Overhead:** Requires the creation and maintenance of high-fidelity evaluation datasets for every optimized skill.
- **Training Cost:** The optimization loop is token-intensive during the "compile-time" phase.
- **Convergence Time:** Empirical optimization is slower than manual editing for trivial changes.

### Risk Mitigations
- **Evaluation Leakage:** Mandatory strict separation of training and validation splits to prevent overfitting to the benchmark.
- **Optimizer Bias Audit:** Periodically audit optimized skills to ensure the optimizer model has not introduced stylistic artifacts that degrade performance on the target model.
- **Safety Guardrails:** All `best_skill.md` artifacts must undergo a security review to ensure that optimization has not introduced prompt-injection vulnerabilities.

## Date
2026-06-08

## Alternatives
1. **Manual Engineering:** Maintain current heuristic approach. Rejected due to lack of reproducibility and susceptibility to regressions.
2. **DSPy:** Programmatic prompt optimization. Rejected due to the "Abstraction Tax" (runtime dependency) and divergence from the ecosystem's native Markdown-first architecture.
3. **Weight Fine-Tuning (LoRA):** Modifying model weights. Rejected due to high GPU requirements, risk of catastrophic forgetting, and violation of the SVA principle regarding deployment complexity.

## References
- [A-26026: SkillOpt vs. DSPy Comparative Analysis](/architecture/evidence/analyses/A-26026_skillopt_adoption_comparative_analysis.md).
- Yang et al., "SkillOpt: Executive Strategy for Self-Evolving Agent Skills", 2026.

## Participants
- Senior AI Systems Architect
