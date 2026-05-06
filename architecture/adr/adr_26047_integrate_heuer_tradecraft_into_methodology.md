
---
title: Integrate Heuer Intelligence Tradecraft into AI System Methodology
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: 2026-04-19
description: Establishment of Richard Heuer's intelligence tradecraft (ACH, Disconfirmation,
  Linchpin Analysis) as a core methodology for the AI system to counter the autoregressive
  consistency trap.
tags:
- architecture
- prompts
options:
  type: adr
  birth: 2026-04-19
  version: 0.1.0
  token_size: 1592
  id: 26047
  status: proposed
  superseded_by: null
---
# ADR-26047: Integrate Heuer Intelligence Tradecraft into AI System Methodology

## Date
2026-04-19

## Status

proposed

## Context
Generative AI models based on the Transformer architecture operate via **Autoregressive Generation** and **Causal Masking**. In this paradigm, every generated token $t$ is sampled from a probability distribution conditioned on the preceding context $0 \dots t-1$. A **single generation pass** (or single-session reasoning) refers to this uninterrupted autoregressive sequence where the model generates a complete response without external intervention, meaning it cannot "backtrack" or modify previously generated tokens based on insights gained later in the same sequence. Once a token is produced, it is appended to the context, and in the subsequent step, the model's attention mechanism must account for this new token as a fixed part of the input.

This creates an **Autoregressive Feedback Loop**: the model's own outputs become its primary constraints. Because the model is optimized for linguistic and logical coherence, it tends to converge on a single high-probability narrative—a phenomenon termed **Probabilistic Convergence**. Once a model generates an initial plausible hypothesis, the internal self-attention scores favor subsequent tokens that "agree" with that hypothesis, effectively trapping the model in a consistent but potentially biased trajectory.

While the model can append corrective tokens (e.g., "Actually, let me reconsider..."), this does not constitute true backtracking. These tokens remain subject to the autoregressive momentum of the original, biased context. See [A-26016](/architecture/evidence/analyses/A-26016_causal_masking_attention_mechanics_for_prompt_engineering.md) for a technical breakdown of why appending tokens cannot overcome the fixed bias of the KV Cache.

Research in [A-26019](/architecture/evidence/analyses/A-26019_heuer_methodology_integration_for_consultant_prompts.md) and stress-tests in [A-26023](/architecture/evidence/analyses/A-26023_heuer_brainstorm_stress_test.md) indicate that this mechanism often leads to "Satisficing" (settling on the first plausible answer) and "Performative Refutation" (simulating a challenge while maintaining the original conclusion). Integrating Richard Heuer's intelligence tradecraft—specifically the Analysis of Competing Hypotheses (ACH)—provides a procedural countermeasure to this feedback loop by mandating the exploration of divergent paths before the system converges on a final result.

## Decision
We will integrate Heuer's tradecraft as a foundational **system-wide methodology** for high-criticality analytical tasks. This methodology is not a set of suggestions but a set of **architectural constraints** on the reasoning process to break the autoregressive consistency trap.

### 1. Ecosystem-Wide Application
Heuer tradecraft will be applied across all layers of the AI system where an analytical conclusion is required:
- **Consultant Prompts:** Implementation of procedural instructions to trigger structured reasoning.
- **Agent Orchestration:** Implementation of sequential pipelines to break context momentum.
- **Evaluation Metrics:** Integration of tradecraft rigor into the WRC (Weighted Response Confidence) calculation.

### 2. Procedural Standards (The Heuer Block)
The core tradecraft will be codified in a Single Source of Truth (SSoT) block (e.g., `ai_system_layers/3_prompts/consultants/blocks/heuer_tradecraft.json`) and enforced as follows:

- **Divergence Mandate:** For high-criticality tasks, the system must explicitly generate $N$ competing hypotheses *before* evaluating evidence. This forces the model to attend to multiple potential trajectories in the context before the "momentum" of a single conclusion takes hold.
- **Diagnosticity Priority:** The analytical process must prioritize identifying evidence that *disproves* hypotheses. This counters the model's tendency to select tokens that confirm the existing prefix.
- **Linchpin Identification:** Mandatory identification of the "linchpin" assumption—the specific conceptual or data-level dependency that, if invalidated, would fundamentally shift the token-level probability distribution of the conclusion.
- **ACH Trigger:** ACH is mandatory whenever the initial predicted confidence is low ($P < 0.85$) or a "Criticality" flag is set.

### 3. Breaking the Context Loop (The Cognitive Firewall)
To counter the effect of context-level momentum in single-session reasoning, the system will support a **Sequential Agent Pipeline** for critical analyses. By handing off analysis between fresh agent instances, we effectively "reset" the autoregressive context while preserving the analytical state:
1. **Divergent Agent:** Generates hypotheses.
2. **Evidence Mapper:** Maps data to hypotheses.
3. **Adversarial Agent:** Tasked specifically with the refutation of the leading hypothesis.
4. **Synthesis Agent:** Final arbiter based on the resilience of the remaining hypotheses.

## Consequences

### Positive
- **Mitigation of Satisficing:** Forces the model to move from "System 1" (greedy path selection) to "System 2" (structured evaluation).
- **Improved Calibration:** Confidence scores ($P$) become a reflection of the hypothesis's resilience to disconfirmation rather than a measure of sequence probability.
- **Structural Integrity:** Ensures the "Smallest Viable Architecture" (SVA) is derived from a process of elimination.

### Negative / Risks
- **Latency and Cost:** Multiple passes and structured paths increase total token generation and time-to-completion.
- **Complexity:** Requires more sophisticated orchestration logic to manage the "Cognitive Firewall" pipeline.
- **Constraint Evasion:** Large models may still attempt to "simulate" the rigor while maintaining their bias if the procedural instructions are not strictly enforced.

## Alternatives
- **Single-Turn "Chain of Thought":** Relying on CoT to solve bias. **Rejection Reason:** CoT is still subject to the same autoregressive momentum; if the first few "thoughts" are biased, the rest of the chain will likely follow.
- **Fine-Tuning for Rigor:** Training models to be "more analytical". **Rejection Reason:** Brittle and expensive compared to procedural prompting and orchestration.

## References
- `S-26023`: Distributional Shift and Token Sequences
- `S-26024`: Causal Masking and KV Cache Momentum
- [A-26019: Heuer Methodology Integration for Consultant Prompts](/architecture/evidence/analyses/A-26019_heuer_methodology_integration_for_consultant_prompts.md)
- [A-26023: Heuer Brainstorm: Stress-Testing Integration Conclusions](/architecture/evidence/analyses/A-26023_heuer_brainstorm_stress_test.md)

## Participants
1. Vadim Rudakov
