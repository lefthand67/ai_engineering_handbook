---
jupytext:
  formats: md:myst,ipynb
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
title: Model Sizing, Quantization, and VRAM Budgeting for Local Deployment
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Technical guide for sizing local language models, budgeting VRAM for
  weights and KV caches, and choosing appropriate quantization levels for production
  deployment.
tags:
- model
- hardware
date: '2026-05-02'
options:
  type: guide
  version: 1.0.2
  birth: '2025-10-19'
  token_size: 1936
---

+++

Deploying language models locally — whether as the **Editor** in the [Multi-Phase AI Pipeline](/ai_system_layers/4_orchestration/workflows/multi_phase_ai_pipeline.ipynb) or as a standalone inference endpoint — requires engineering three interrelated budgets: **model weights**, **KV cache memory**, and **quantization loss**. This article provides the sizing rationale that complements the [model classification](/ai_system_layers/2_model/selection/general_purpose_vs_agentic_models.ipynb) (Agentic / General Purpose / Thinking tiers) with concrete VRAM arithmetic.

:::{seealso}
> 1. {term}`ADR-26027`: Model Taxonomy: Reasoning-Class vs Agentic-Class Selection Heuristic
> 2. {term}`ADR-26021`: Content Lifecycle Policy for RAG-Consumed Repositories
> 3. [Hybrid Execution and KV Cache Offloading](/ai_system_layers/1_execution/hybrid_execution_and_kv_cache_offloading.ipynb) — deep dive on Host/Device memory architecture
:::

+++

## 1. Model Size Tiers and Pipeline Role Map

+++

The [Multi-Phase AI Pipeline](/ai_system_layers/4_orchestration/workflows/multi_phase_ai_pipeline.ipynb) assigns models to specific pipeline phases based on their capability tier. Size alone does not determine role — **instruction adherence** and **reasoning depth** matter more (see [General Purpose vs Agentic Models](/ai_system_layers/2_model/selection/general_purpose_vs_agentic_models.ipynb)).

| Tier | Parameter Range | Pipeline Role | Representative Models | Hardware Target |
| --- | --- | --- | --- | --- |
| **Micro** | 125M – 3B | Researcher (RAG retrieval), classifier, router | `ministral`, `phi-3-mini` | CPU / mobile / edge |
| **Editor** | 7B – 14B | **Editor** (Phase 3: Execution) | `qwen2.5-coder:14b-instruct-q4_K_M` | Consumer GPU (8–16 GB VRAM) |
| **Architect** | 70B+ / Cloud API | **Architect** (Phase 2: Planning) | **Claude 4.0 Sonnet**, **Gemini 3 Flash**, **DeepSeek-V3** | Cloud API |
| **Thinking** | Cloud API | Pre-flight verification | **OpenAI o2**, **Gemini 3 (DeepThink)**, **DeepSeek-R1** | Cloud API |

> **Key insight:** The local GPU budget is reserved for the **Editor** tier. Architect and Thinking models run via cloud API, so their parameter count is irrelevant to your VRAM planning. Plan your hardware around the Editor model.

+++

## 2. The "Short-Term Memory" Tax (KV Cache)

+++

When you load a model, you are not just paying for the **weights** (the "brain"). Every token of conversation history allocates **KV cache** (the "short-term memory") on the GPU.

* **The Problem:** A model that fits in VRAM at initialization can **OOM** (Out of Memory) mid-conversation as the KV cache grows with each turn.
* **The Rule of Thumb:** For a 14B model at Q4 quantization, budget **~2 GB of VRAM per 8,192 tokens** of active context.

This is why the hybrid bridge pattern enforces a **Hard Reset** at the Architect→Editor transition:

> The Editor instance is launched without the Architect's message history. It receives only `artifacts/plan.md` as input, keeping KV cache usage below 4 GB and leaving maximum headroom for model weights.

A **Context Gate** (e.g., capping chat history tokens) limits the Editor's KV cache growth to prevent the OOM crash that long interactive sessions would otherwise produce.

:::{seealso}
> [Hybrid Execution and KV Cache Offloading](/ai_system_layers/1_execution/hybrid_execution_and_kv_cache_offloading.ipynb) — for detailed Host/Device memory split, KV cache offloading strategies, and Mermaid diagrams of the memory lifecycle.
:::

+++

## 3. Quantization: Trading Precision for Deployment

+++

Quantization reduces model weights from 16-bit floats to lower-bit integers, shrinking VRAM requirements at the cost of minor accuracy loss.

| Format | Size Reduction | Accuracy Impact | When to Use |
| --- | --- | --- | --- |
| **FP16** (baseline) | — | — | Benchmarking, maximum quality |
| **Q8_0** | ~50% | Negligible | When VRAM is available but you want a safety margin |
| **Q4_K_M** | ~75% | ~1% logic degradation | **Default for local Editor deployment.** Best balance of size and quality. |
| **Q4_0** | ~75% | ~2–3% degradation | Budget hardware; test thoroughly before production use |

**Practical example:** `qwen2.5-coder:14b` at FP16 requires ~28 GB VRAM. At Q4_K_M, it fits in ~8 GB, leaving headroom for KV cache on a 12 GB consumer GPU.

:::{important}
The recommended Editor configuration uses Q4_K_M explicitly (e.g., `qwen2.5-coder:14b-instruct-q4_K_M`). This is not arbitrary — it's the quantization level validated for code editing tasks with acceptable logic retention.
:::

+++

## 4. Production Patterns

+++

### Pattern A: The Verifier Cascade

+++

Instead of routing everything to a large cloud model, use a two-stage local pipeline:

1. **The Drafter (7B):** Produces a fast, rough answer.
2. **The Verifier (14B):** Checks the draft against your rules/schema.

This maps naturally to the [pipeline's](/ai_system_layers/4_orchestration/workflows/multi_phase_ai_pipeline.ipynb) Architect→Editor flow: the Architect drafts the plan (cloud), and the Editor executes against the codebase (local). The Verifier Cascade extends this to fully local pipelines where cloud access is unavailable.

+++

### Pattern B: Hybrid Routing

+++

Use a micro model (≤3B) as a **gatekeeper** to classify incoming requests:

* **Simple requests** (greetings, FAQ lookups) → local Editor model.
* **Complex requests** (multi-file refactors, architectural decisions) → cloud Architect API.

In the [pipeline](/ai_system_layers/4_orchestration/workflows/multi_phase_ai_pipeline.ipynb) context, this is the **Researcher** role (Phase 1): a lightweight local model performs RAG retrieval to determine what context the Architect needs, avoiding expensive cloud API calls for work that can be handled locally.

+++

## 5. VRAM Budget Checklist

+++

For a target local deployment (e.g., 12 GB consumer GPU):

1. **Select the Editor model:** `qwen2.5-coder:14b` or equivalent in the 7B–14B range.
2. **Quantize to Q4_K_M:** Reduces ~28 GB → ~8 GB for a 14B model.
3. **Reserve KV cache headroom:** 2–4 GB depending on `max-chat-history-tokens` setting.
4. **Verify total:** Model weights + KV cache + OS overhead (~500 MB) must fit within VRAM.
5. **Enforce structured output:** If the Editor produces structured output, enforce schema compliance with Pydantic or Outlines to prevent broken responses.
6. **Stress test:** Run the longest expected input through the pipeline to verify no OOM under peak KV cache load.

| Component | Budget (12 GB GPU) |
| --- | --- |
| Model weights (14B Q4_K_M) | ~8 GB |
| KV cache (2048 tokens gate) | ~1 GB |
| OS / framework overhead | ~0.5 GB |
| **Available headroom** | **~2.5 GB** |
