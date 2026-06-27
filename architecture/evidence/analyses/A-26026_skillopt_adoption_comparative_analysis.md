---
id: A-26026
title: SkillOpt vs. DSPy Comparative Analysis
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Comparative analysis between SkillOpt and DSPy for agent skill optimization.
tags:
- agents
- model
- architecture
date: 2026-06-08
options:
  type: analysis
  status: active
  produces: ADR-26057
  birth: 2026-06-08
  version: 1.0.0
  token_size: 828
---
# Architectural Analysis: SkillOpt vs. DSPy for Agent Skill Optimization

## Problem Statement
The current "Skill Engineering" process is predominantly heuristic-driven (manual iteration) or one-shot synthetic, creating a "Prompt Engineering Gap" where skill performance depends on engineer intuition rather than an objective function. We need to determine the optimal framework for transitioning to "Textual State Optimization" without introducing excessive runtime complexity or vendor lock-in.

## Approach Evaluation

### Textual State Optimization (SkillOpt)
SkillOpt treats the skill document as the "weights" of the agent. It performs surgical, bounded edits on Markdown files using a Rollout $\rightarrow$ Reflect $\rightarrow$ Update loop.

**WRC Calculation:**
- **E (Empirical):** 0.90 (Strong results across 6 benchmarks)
- **A (Adoption):** 0.60 (Emerging, integrated in gbrain)
- **P (Performance):** 1.00 (Zero-dependency, Git-native)
- **Final WRC: 0.865**

### Programmatic Abstraction (DSPy)
DSPy treats the prompt as a compiled artifact of a program, optimizing few-shot examples and signatures via a "Teleprompter."

**WRC Calculation:**
- **E (Empirical):** 0.90 (Industry gold standard)
- **A (Adoption):** 0.90 (Widespread enterprise use)
- **P (Performance):** 0.70 (High abstraction tax, runtime dependency)
- **Final WRC: 0.82**

### Comparative Trade-off Matrix
| Metric | DSPy (Programmatic) | SkillOpt (Textual) | Delta / Winner |
| :--- | :--- | :--- | :--- |
| **State Portability** | Medium (JSON/Strings) | High (Single `.md` file) | **SkillOpt** |
| **Inference Overhead** | Low (compiled) | Zero (native text) | **SkillOpt** |
| **Opt. Granularity** | Coarse (Example selection) | Fine (Surgical text edits) | **SkillOpt** |
| **Developer UX** | "Coding" (Pythonic) | "Editing" (Doc-centric) | **SkillOpt** (for this ecosystem) |

## Key Insights

### 1. The Abstraction Tax
The primary differentiator is the runtime requirement. DSPy requires the framework to be present to manage the "compiled" prompts. SkillOpt produces a plain Markdown file that requires **zero dependencies** at inference time, aligning perfectly with the **Smallest Viable Architecture (SVA)** principle.

### 2. SVA Audit Summary
- **SkillOpt:** Satisfies all C1-C6 constraints. P-Score: 1.0.
- **DSPy:** Violates C3 (Git-Native Traceability - opaque state) and C4 (Proportional Complexity). P-Score: 0.7.

### 3. Recommendation
For the specific goal of optimizing modular agent skills authored as Markdown, **SkillOpt** is the superior choice. It optimizes the native format of the ecosystem rather than forcing the ecosystem to adapt to a programmatic framework.

## References
- Yang et al., "SkillOpt: Executive Strategy for Self-Evolving Agent Skills", 2026.
- DSPy Documentation: "Programming not Prompting".
