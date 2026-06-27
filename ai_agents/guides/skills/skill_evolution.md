---
title: 'Skill Evolution Pipeline: From Intuition to Empirical Optimization'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Operational framework for evolving agent skills using a textual optimization
  loop with SkillOpt, treating skill documents as trainable state optimized against
  empirical evidence.
tags:
- agents
- prompts
- workflow
date: '2026-06-28'
options:
  type: guide
  birth: '2026-06-28'
  version: 1.0.0
  token_size: 1111
---
(skill_evolution_pipeline)=
# Skill Evolution Pipeline: From Intuition to Empirical Optimization

This document defines the operational framework for evolving agent skills using a textual optimization loop. Instead of manual prompt engineering, we treat the skill document as a "trainable state" that is optimized against empirical evidence.

## 1. The Evolution Lifecycle

The transition from a human-authored seed prompt to a production-grade optimized skill follows a five-stage cycle.

```{list-number}
**Seed Phase (Intuition)**
The skill is authored by a human expert based on desired behavior and project conventions. This is the `SKILL.md` (Seed).

**Observation Phase (Failure Capture)**
The skill is deployed in a staging environment. Failures are logged, and "blind spots" (cases where the agent deviates from the golden path) are identified.

**Synthesis Phase (Golden Set)**
A curated dataset is created consisting of:
- `train/`: Examples used by the optimizer to generate candidates.
- `val/`: The "Validation Gate" used to accept or reject edits.
- `test/`: The final benchmark for performance verification.

**Optimization Phase (Empirical Loop)**
Using the `SkillOpt` framework, a strong "Optimizer" model iterates on the seed prompt, applying textual edits that strictly improve the validation score.

**Deployment Phase (Integration)**
The resulting `best_skill.md` is reviewed, versioned, and promoted to the active skills directory.
```

## 2. Technical Implementation with SkillOpt

### 2.1 Data Split Architecture

The effectiveness of the evolution depends on the quality of the `items.json` files.

:::{tip}
**The "Contrastive" Approach**
When building your Golden Set, include "Negative Examples"—tasks where the agent typically fails—and provide the "Golden Answer" that demonstrates the exact reasoning or constraint the agent missed.
:::

**Dataset Schema:**
- **Question:** The trigger/request.
- **Context:** The environmental state or codebase snippets.
- **Answers:** The minimal set of constraints or outputs that define a "PASS."

### 2.2 Optimizer Configuration

The optimization is governed by a YAML configuration. Key levers include:

- **Textual Learning Rate:** Controls the magnitude of edits. Higher rates allow for structural changes; lower rates refine existing wording.
- **Validation Gate (`hard` vs `soft`):** 
    - `hard`: Exact match. Use for deterministic tasks (e.g., file paths, API keys).
    - `soft`: Partial credit. Use for creative or architectural tasks.

## 3. Integration with the AI Stack

This pipeline transforms how we manage the five-layer architecture:

- **Layer 3 (Prompts):** Skills move from being "Static Text" to "Versioned Artifacts." Every `best_skill.md` should be linked to the dataset version used to optimize it.
- **Layer 4 (Orchestration):** The orchestrator no longer relies on a single monolithic prompt but dynamically loads evolved skills that have been empirically proven to work.

## 4. Governance and Maintenance

### 4.1 When to Re-Optimize?
A skill should enter the evolution pipeline again if:
1. **Model Drift:** The target model is updated (e.g., Qwen 2.5 $\rightarrow$ 3.0).
2. **Regression:** New failures are detected in production.
3. **Scope Expansion:** New requirements are added to the skill's responsibility.

### 4.2 Verification Protocol
Before a `best_skill.md` is merged, it must pass the **Regression Test**:
- It must maintain or improve the score on the `test/` split.
- It must not introduce "Over-fitting" (performing perfectly on `val/` but failing on `test/`).

:::{warning}
**The Over-fitting Trap**
Avoid using too many epochs on a small validation set. If the Optimizer finds a "hack" (a specific phrase that triggers a pass on those 10 examples but fails generally), the skill is compromised. Always verify on a clean, unseen test set.
:::

## 5. Quick-Start Command Reference

All optimization commands must be executed from the `SkillOpt` tool directory:
`ai_agents/research/ai_skills_plugins/SkillOpt`

```bash
# Navigate to the tool directory
cd ai_agents/research/ai_skills_plugins/SkillOpt
```

**Run Optimization:**
```bash
python scripts/train.py --config configs/skill_name/default.yaml --split_dir data/skill_name_split
```

**Verify Performance:**
```bash
python scripts/eval_only.py --config configs/skill_name/default.yaml --skill ckpt/skill_name/best_skill.md
```
