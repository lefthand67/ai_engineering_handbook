
---
title: Agents Break the Layer Model — Repo Restructuring Decision
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: AI coding agents are the assembled product, not a component — they consume
  all layers 1-5. This analysis documents the category error, explores alternatives
  via Heuer-style hypothesis testing, and justifies moving ai_system/ to ai_system_layers/
  and 6_agents/ to ai_agents/ at repo root.
tags:
- architecture
- agents
date: '2026-04-05'
options:
  type: analysis
  birth: '2026-04-05'
  version: 1.0.0
  token_size: 1269
  id: A-26022
  status: active
  sources:
  - S-26021
  produces: []
---
# Agents Break the Layer Model — Repo Restructuring Decision

**Analysis date:** 2026-04-05
**Source:** `S-26021_agents_repo_restructuring_discussion.md`

## Problem Statement

The six-layer `ai_system/` directory was designed as a component catalog: execution → model → prompts → orchestration → context. `6_agents/` was added as the sixth layer — the layer that "uses all the rest."

After completing a source-level analysis of 6 coding agents (context management guide, `ai_system/6_agents/context_management/`), a fundamental category error emerged:

> **Agents are not a component. They are the assembled product.**

The six layers describe engine parts (execution hardware, model weights, prompt files, orchestration code, context stores). An agent is none of these individually — it is the car that uses all of them. Having `6_agents/` inside `ai_system/` is like having "car" listed as one more engine part in a parts catalog.

This analogy crystallized during the discussion when the user asked whether `6_agents/` should move one directory up or to `tools/`. The answer was neither — the relationship isn't spatial, it's categorical. Agents are the system; the layers are its parts.

## Approach Evaluation

Three hypotheses were generated and tested:

### H1: Keep `6_agents/` inside `ai_system/`, reframe as "capstone layer"

**Evidence for:** Layer 6 is where all pieces come together. Every layer directory contains analysis ABOUT that layer. The pattern is consistent — agent analysis just happens to span multiple dimensions.

**Evidence against:** Preserves the broken numbering convention. Makes agents a "part" of the system rather than the thing that the system produces. Future agent research (agent identity, multi-agent coordination, emergent behavior) won't map to any of the five layers — the scope will expand beyond the framework.

**Assessment:** Rejected. The consistency is superficial, not structural.

### H2: Move to `ai_agents/` at root, rename `ai_system/` to `ai_architecture/`

**Evidence for:** Clean separation between blueprint and product. "Architecture" matches existing repo vocabulary (ADRs already use "architecture" to mean structural design decisions).

**Evidence against:** "Architecture" is a claim that agents themselves don't have. Agents have their own architecture. Multi-agent systems have their own architecture. Any future product category will have its own architecture. The name becomes ambiguous the moment a second product appears.

**Assessment:** Rejected. The name would fail under future expansion.

### H3: Move to `ai_agents/` at root, rename `ai_system/` to `ai_system_layers/`

**Evidence for:** `ai_system_layers/` says exactly what it is — a numbered stack of technical components. `ai_agents/` at root is a separate research domain about external products. Neither pretends to be the other. No ambiguity under future expansion — any new product gets its own root-level directory.

**Evidence against:** Longer name (16 characters). Breaks the convention of short directory names. Loses the "this is about AI systems" framing.

**Assessment:** Accepted. The specificity outweighs the verbosity. Precision > brevity for a structural rename.

## Key Insights

### The Naming Problem Revealed the Category Error

The naming debate surfaced the real issue: `ai_system/` was always a misnomer. It was never about "an AI system" — it was about the components OF an AI system. The rename to `ai_system_layers/` makes this explicit retroactively.

The user's observation — "the agent IS the ai system, and our current ai_system dir is like an engine parts catalog" — was the pivot point that resolved the ambiguity.

### Final Confirmation

**User:** "no, the agents have their own architecture, the multi-agent system have their, who know what new products I will add tomorrow to my catalog?"

This confirmed H3 over H2. Any future product would make `ai_architecture/` ambiguous. `ai_system_layers/` is the only name that says "these specific numbered levels, nothing more."

## Appendix

**Decision:**

| Change | Before | After |
|--------|--------|-------|
| Component catalog | `ai_system/` | `ai_system_layers/` |
| Agent research | `ai_system/6_agents/` | `ai_agents/` (repo root) |
| Layer numbering | 1–6 | 1–5 (no phantom layer 6) |

**Implications:**
1. **Breaking change.** Every path reference to `ai_system/` becomes stale. Requires major version bump.
2. **Migration notice** needed in `AGENTS.md` for 2-3 release cycles.
3. **Cross-references** across all ADRs, scripts, configs, and docs need updating.
4. **The `agents` tag** is added to `.vadocs/conf.json` to classify agent-level analysis that doesn't map to any single layer.

## References

- Implementation plan: `misc/plan/plan_20260405_restructure_ai_system_and_agents.md`
