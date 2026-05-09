
---
title: YAML Serializer Variance — Token Economics of Format Choice
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: The token cost of a YAML-formatted prompt is a function of (format, serializer,
  tokenizer) — three variables, not one. PyYAML's default line-wrapping and yq's boolean
  coercion flip the YAML Literal vs Pretty JSON ranking.
tags:
- prompts
- architecture
date: 2026-03-27
options:
  type: analysis
  birth: 2026-03-27
  version: 1.1.0
  token_size: 689
  id: A-26017
  status: active
  sources:
  - S-26018
  produces: []
---
# A-26017: YAML Serializer Variance — Token Economics of Format Choice

+++

## Problem Statement

+++

The [Format as Architecture](/ai_system_layers/3_prompts/format_as_architecture_signal_noise_in_prompt_delivery.ipynb) handbook and its companion [Token Economics of Prompt Delivery](/ai_system_layers/3_prompts/token_economics_of_prompt_delivery.ipynb) treat format as the sole variable in prompt token cost. Session measurements (`S-26018`) exposed that this is incomplete: two tools producing valid, semantically equivalent YAML from the same JSON source yield token counts differing by 100+ tokens, and the relative ranking of YAML Literal vs Pretty JSON **flips** depending on which tool is used. The token cost of a prompt format is a function of three variables:

$$\text{token\_cost} = f(\text{format},\ \text{serializer},\ \text{tokenizer})$$

The three serializer behaviours driving the divergence — PyYAML `width=80` line-wrapping, yq boolean coercion in literal style, and single vs double quote style — are isolated, measured, and verified for semantic fidelity in the [Appendix: YAML Serializer Variance](/ai_system_layers/3_prompts/appendix_yaml_serializer_variance.ipynb). All measurements use 5 production prompt files and report median deltas; the appendix cells are runnable against any version of the prompt corpus. The appendix also contains the stack recommendation and the assessment of which handbook claims require serializer qualification.

+++

## References

+++

- `S-26018` — Session empirical measurements: PyYAML vs yq token comparison on `devops_consultant.json` v0.3.0, diff output, cross-tokenizer results
- [Appendix: YAML Serializer Variance](/ai_system_layers/3_prompts/appendix_yaml_serializer_variance.ipynb) — Full analysis: isolation experiments (B1–B4), fidelity tests (C1–C3), ranking stability (D1–D3), stack recommendation (F1–F2)
- [Token Economics of Prompt Delivery](/ai_system_layers/3_prompts/token_economics_of_prompt_delivery.ipynb) — Handbook; Section 2.5 and Summary require serializer qualification per this analysis
- [Format as Architecture](/ai_system_layers/3_prompts/format_as_architecture_signal_noise_in_prompt_delivery.ipynb) — Handbook; comparison table §3.7 requires serializer footnote
