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
title: General Purpose (Abstract Synthesis) vs Agentic (Instruction Adherence) Models
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Explores the bifurcation of LLM utility between General Purpose models
  (optimized for abstract synthesis) and Agentic models (optimized for strict instruction
  adherence).
tags:
- model
- architecture
date: '2026-05-02'
options:
  type: guide
  version: 0.1.3
  birth: '2026-01-16'
  token_size: 1170
---
# General Purpose (Abstract Synthesis) vs Agentic (Instruction Adherence) Models
## **1. The Core Divergence: Synthesis vs. Adherence**

+++

In the Q1 2026 landscape, the "One Model to Rule Them All" paradigm is deprecated. For the **Hybrid Bridge Pattern** defined in the [Multi-Phase AI Pipeline](/ai_system_layers/4_orchestration/workflows/multi_phase_ai_pipeline.ipynb), the selection of a Cloud Architect depends on the bifurcation of model utility:

> The problem is not just "which model is best," but the **Bifurcation of LLM Utility**. We are no longer in the era of the "one model to rule them all."

* **Agentic Models (Instruction-Locked):** Optimized for **Logic Rigidity**. These models treat system prompts as strict code and minimize "conversational drift" even at high context depths (128k+). They are the required tool for the **Architect Phase** to ensure the generated `artifacts/plan.md` is deterministic.
* **General Purpose Models (Abstract Synthesis):** Optimized for **Cognitive Breadth**. These models excel at "Step 0" (human-led problem discovery), where the objective is to challenge assumptions and identify architectural anti-patterns through latent knowledge retrieval.

:::{important} **Architectural Justification**
Using a "General Purpose" model for an "Agentic" task (like generating execution plans) introduces non-deterministic noise and "Pro Polish" debt, leading to failures in local 14B editors.
:::

:::{seealso}
> 1. {term}`ADR-26027`: Model Taxonomy: Reasoning-Class vs Agentic-Class Selection Heuristic
:::

+++

## **2. Model Zoo Classification (Jan 2026)**

+++

:::{warning}
As stated in {term}`ADR-26027`, this list is the Single Source of Truth for choosing the model for the Requirements Engineering step - General Purpose models are only allowed.
:::

| Tier | Models | Primary Capability | Architectural "Why" |
| --- | --- | --- | --- |
| **Agentic (Instruction-Locked)** | **Claude 4.0 Sonnet**, **Gemini 3 Flash**, **DeepSeek-V3** | **Logic Rigidity.** These models minimize "chatty" drift and follow system prompts as strict code. | Best for the **Architect role** in the [pipeline](/ai_system_layers/4_orchestration/workflows/multi_phase_ai_pipeline.ipynb). They produce a clean execution plan that a local model can apply without confusion. |
| **General Purpose (Synthesis)** | **GPT-5**, **Claude 4.5 Opus**, **Gemini 3 Pro** | **Abstract Depth.** These models excel at "Step 0" where the problem is not yet technical. | Best for **Human-led exploration.** They can challenge your stack choice by recalling niche historical failures of specific libraries. |
| **Thinking (Verification)** | **OpenAI o2**, **Gemini 3 (DeepThink)**, **DeepSeek-R1** | **System 2 Reasoning.** These models use "Chain of Thought" to self-verify logic. | Best for **Pre-flight verification.** Use them to check if your `plan.md` has security race conditions before hitting the editor. |

+++

## **3. The Execution Gap & Technical Debt**

+++

* **The "General Purpose" Hallucination:** GPT-level models often produce "creative" code that local SLMs (Small Language Models) like `qwen2.5-coder:14b` cannot interpret, resulting in an **Execution Gap**.
* **Persona Drift:** General-purpose models may ignore rigid "Senior Architect" constraints to be "helpful," violating the **Smallest Viable Architecture (SVA)** principle.
* **Model Version Drift:** All pipeline configurations must pin specific versions (e.g., `gemini-3-flash-preview`) to ensure logic stability.

+++

## **4. Selection Decision Matrix**

+++

| Task Type | Recommended Tier | Justification |
| --- | --- | --- |
| **Unstructured Brainstorming** | General Purpose | Highest "Reasoning Ceiling" for abstract problems. |
| **Plan Serialization (`plan.md`)** | Agentic | High-fidelity adherence to {term}`ADR-26027` selection heuristic. |
| **Security/Logic Audit** | Thinking | Self-verifying logic gates for high-stakes code. |
