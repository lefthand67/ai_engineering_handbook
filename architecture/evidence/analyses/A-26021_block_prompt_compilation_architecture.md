
---
title: Block Prompt Compilation Architecture
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Consultant prompts share 85-90% structure. Block compilation architecture
  extracts decision kernel as shared JSON, persona blocks as thin skins, assembled
  JIT by prepare_prompt.py and converted to YAML for runtime delivery. Heuer methodology
  becomes a composable decision block, not consultant-specific.
tags:
- prompts
- architecture
date: 2026-04-03
options:
  type: analysis
  birth: 2026-04-03
  version: 1.0.0
  token_size: 1605
  id: A-26021
  status: active
  sources:
  - S-26020
  produces: []
---
# A-26021: Block Prompt Compilation Architecture

+++

## Problem Statement

+++

Three consultant prompts (`ai_systems_consultant_hybrid.json`, `devops_consultant.json`, `local_ai_systems_consultant.json`) share 85-90% of their content: WRC formula, SVA violations C1-C6, response structure (15 steps), methodology comparison tables, assumption interrogation, protocols. Each new archetype duplicates this boilerplate. The Heuer methodology integration (planned for Phase 3 of the Heuer plan) would add the same tradecraft instructions to multiple prompts, further increasing duplication.

The question: how to structure prompts so shared logic lives in one place, archetype-specific content is thin and isolated, and the final prompt delivered to the LLM is a compiled artifact — not a hand-edited monolith.

+++

## Key Insights

+++

### 1. Decision Kernel Extraction

The overlap between hybrid and devops prompts maps to two distinct layers:

**Decision kernel (shared, ~85-90%):** WRC formula + components, SVA C1-C6 violations, P-score audit protocol, WRC calculation protocol, methodology rerouting protocol, response structure (15 steps), methodology comparison table columns, assumption interrogation table, validation gap analysis, anti-emotional bias principle, peer review principle, ISO 29148 framing, production_focus criteria.

**Persona skin (archetype-specific, ~10-15%):** Role/title text, user_stack details, MENU_OUTPUT introduction text, minor protocol wording differences ("source code" vs "prompt blocks"), domain-specific analytical_framework (devops only), bias_mitigation principle (hybrid only).

This is a textbook base + extension pattern. The kernel is the decision-making skill; the persona is injectable context.

### 2. Block Compilation Architecture

The final goal is JIT compilation from shareable JSON blocks:

```
blocks/decision_kernel.json        ← WRC, SVA, response structure, protocols (shared)
blocks/heuer_tradecraft.json       ← ACH, disconfirmation, linchpin (shared, for decision prompts)
blocks/hybrid_persona.json         ← role, stack, intro (archetype-specific)
blocks/devops_persona.json         ← role, stack, intro (archetype-specific)
blocks/devops_analytical_framework.json  ← domain heuristics (devops only)
```

Each consultant prompt becomes a thin manifest declaring its blocks:

```json
{
  "name": "ai_systems_consultant_hybrid",
  "blocks": ["decision_kernel", "heuer_tradecraft", "hybrid_persona"]
}
```

The compiler (`prepare_prompt.py`) resolves `_includes`, assembles into a single JSON, converts to YAML (standard, `width=float('inf')`), and outputs the ready prompt.

### 3. Heuer as Composable Decision Block

Heuer methodology is not "for consultant prompts" — it's a decision-making skill that any prompt manifest can include. The block contains `tradecraft_standards`, `ach_mandatory`, disconfirmation principle, and linchpin analysis instructions. Token budget: ~200-300 tokens. Trigger: decision-type questions (methodology/strategy), not all queries.

This makes Heuer composable with future skills beyond the current consultant prompts. The block is the unit of reuse; the prompt is a compiled artifact.

### 4. Static _includes Over Dynamic Resolution

Manifest-declared blocks (static) should precede compiler-evaluated conditions (dynamic). The manifest owner decides which blocks apply. Adding trigger-condition logic to the compiler adds complexity without evidence it's needed. If the prompt needs Heuer, the manifest says so.

### 5. Format Boundary Preserved

The architecture follows the Two-Audience Principle from the format-as-architecture articles:

- **JSON blocks** = development artifacts (compiler audience). Machine-readable, diffable, validated.
- **YAML output** = runtime delivery (LLM audience). Low noise, attention anchors, instruction-optimized.

`prepare_prompt.py` is the format boundary. Critical requirements:
- Must use `width=float('inf')` — PyYAML default (`width=80`) wastes ~80 tokens/prompt from line-wrapping
- Must NOT use yq for literal blocks — the `|-` terminator coerces booleans/numbers to indented lines, adding 2-3 tokens each
- Must preserve XML tags at injection boundaries for scope safety

### 6. Token Economics Justify the Architecture

Kernel extraction saves ~500-800 tokens total across 3 prompts (eliminating duplication). The Heuer block costs ~200-300 tokens but pays for itself in kernel savings. YAML delivery (width=∞) saves ~100-180 tokens per consultant vs Pretty JSON. Across 3 consultants, format optimization alone saves 300-540 tokens/session — dwarfing the Heuer block cost.

### 7. ADR Format Efficiency Problem (Cross-Cutting)

ADRs are authored as human-readable Markdown — optimal for docs site consumption but inefficient when loaded into agent context windows. The same format-as-architecture tension applies: when an agent reads 10 ADRs for context, markdown formatting inflates the token budget far beyond the decision content (decision, alternatives, rationale, consequences). This is a standalone analytical problem requiring its own investigation. Recorded in roadmap at Phase 1.13.

+++

## Rejected Ideas

+++

### Monolithic Prompts (Current State)

Keep each consultant as a self-contained JSON file. Rejected: 85-90% duplication means every fix to WRC/SVA/response structure must be applied 3x. New archetypes multiply the problem.

### Dynamic Block Resolution

Compiler evaluates trigger conditions (WRC < 0.90, question type) and adds blocks automatically. Rejected for phase 1: adds decision logic to the compiler, making it harder to audit. The manifest is the SSoT for what blocks apply. Conditional inclusion can be added later if evidence shows it's needed.

+++

## References

+++

1. `S-26020` — Session transcript: block prompt architecture and Heuer brainstorm (2026-04-03)
2. `ai_systems_consultant_hybrid.json` — Production hybrid consultant prompt
3. `devops_consultant.json` — Production devops consultant prompt
4. [Format as Architecture: Signal-to-Noise in Prompt Delivery](/ai_system_layers/3_prompts/format_as_architecture_signal_noise_in_prompt_delivery.ipynb)
5. [Token Economics of Prompt Delivery](/ai_system_layers/3_prompts/token_economics_of_prompt_delivery.ipynb)
6. [Appendix: YAML Serializer Variance](/ai_system_layers/3_prompts/appendix_yaml_serializer_variance.ipynb)
7. `tools/scripts/prepare_prompt.py` — Prompt compiler (needs refinement for block compilation)
