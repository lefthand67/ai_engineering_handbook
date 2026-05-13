
---
title: 'Handbook Peer Review — Format as Architecture: Signal-to-Noise in Prompt Delivery'
description: 'System prompt: `handbook_peer_reviewer.json` v0.2.3 (Principal Software Engineer, peer review).'
date: 2026-03-25
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
tags:
- prompts
- architecture
options:
  token_size: 1891
  id: S-26015
  model: claude-opus-4-6
  extracted_into: null
  type: source
---

# S-26015: Handbook Peer Review — Format as Architecture

System prompt: `handbook_peer_reviewer.json` v0.2.3 (Principal Software Engineer, peer review).

Peer review of `ai_system/3_prompts/format_as_architecture_signal_noise_in_prompt_delivery.md` with cross-reference to teaching notebook `teaching/urfu/2026_spring/01_system_prompts/token_comparison.ipynb`.

+++

## Review Verdict

Strong draft, publishable with targeted corrections. Core thesis is solid, measurement methodology is good.

+++

## Technical Accuracy Issues

### Section 1 — "equal computational cost" is misleading

The claim "a transformer processes every token with equal computational cost" is technically true for FLOPs per token in a single forward pass, but conflates compute cost with attention allocation. Attention weights are not uniform — they are learned and vary dramatically per token. Should say: "every token occupies a position in the sequence and participates in self-attention across all layers, consuming fixed compute regardless of whether it carries instructional content."

### Section 2.1/2.3 — Colon-counting inconsistency

Colons are counted as noise in JSON (4 tokens) but also present in YAML (4 tokens). The comparison in 2.3 counts only `:` as YAML's structural tokens — but these are the same colons. The honest comparison should focus on what JSON adds beyond what YAML requires: quotes and braces.

### Section 2.2 — Markdown noise count too precise

`###` is typically tokenized as 1-2 tokens, not 1. The claimed "~10 noise tokens" is too precise for an estimate. Should say "roughly 10-13" or "~half of JSON's structural overhead."

### Section 2.7 — BPE space+word merging needs nuance

The claim `" hello"` is one token is correct for cl100k_base but the mechanism is vocabulary-specific, not a universal BPE property. Clarify: "In tokenizers trained on English text (cl100k_base, o200k_base), the space-prefix pattern is very common in the vocabulary because it appears billions of times in the training data."

### Section 3 — Training distribution claims too strong

The hypothesis that JSON activates "data parsing mode" and YAML activates "instruction following mode" is correctly hedged. But Section 6.1 attributes v0.40.0 → v0.41.0 improvement partly to format change, when the change also embedded templates in the meta-prompt (confounding variable). Must explicitly acknowledge.

### Section 6.2 — Qwen3-Max "agreement" is not evidence

LLMs are sycophantic by default. Either remove or reframe: "The model's independent suggestion of YAML for output format, before being shown our analysis, is consistent with the hypothesis."

+++

## Missing Content

### XML omitted

XML is dominant in many production prompt systems (Anthropic's system prompts use XML tags extensively). For a "format as architecture" article, omitting XML is a significant gap. XML has: explicit delimiters (injection-resistant), named scope boundaries, low noise relative to JSON (no quotes on values), strong attention anchors (tag names repeat at open/close).

### Mixed formats not discussed

Real production prompts rarely use pure formats. Claude's system prompts mix XML tags with Markdown inside them. Decision framework should address hybrid approaches.

### No cross-tokenizer validation

Article uses only tiktoken (cl100k_base / o200k_base) and claims "relative rankings between formats will be similar" for other tokenizers — but never proves it.

### No language effects

Article implicitly assumes English. Russian text tokenizes very differently — GPT-2 fragments Cyrillic into bytes while Qwen2.5 (151k vocab) handles Russian well. Format overhead percentage changes by language.

+++

## Pedagogical Issues

### Two-Audience Principle should come earlier

Section 4 is the conceptual anchor — the reason format choice matters. Currently appears after 3 sections of format analysis. Reader processes the comparison without knowing why they should care. Should be Section 2.

### Bold wrapping on ## headings is redundant

`## **1. The Problem**` — `##` already renders bold. Visual noise in source, renders as double-bold in some renderers.

### prepare_prompt.py referenced but never linked

Mentioned in Sections 4 and 9 but no path/link provided.

+++

## Frontmatter Issues

- `author` should be `authors` (plural, list of objects per ADR-26042/MyST spec)
- Missing: `description`, `tags`, `type` fields

+++

## Cross-Reference: token_comparison.ipynb

Teaching notebook at `teaching/urfu/2026_spring/01_system_prompts/token_comparison.ipynb` provides:

### What the notebook adds

1. **Multi-model tokenizer comparison** — GPT-2 (50k vocab), Qwen2.5 (151k), DeepSeek, GigaChat via HuggingFace `AutoTokenizer`. Can verify format ranking across tokenizers.
2. **Russian vs English token efficiency** — GPT-2 fragments Cyrillic into bytes, Qwen2.5 handles Russian as whole-word tokens. Format overhead percentage changes by language.
3. **Chars-per-token efficiency metric** — `len(text)/len(tokens)`, clean intuitive metric not used in the article.
4. **Visual comparison** — matplotlib bar charts, side-by-side.
5. **Vocabulary size as explanatory variable** — implicitly shows vocab size is the dominant factor in token count.

### Concrete borrowing recommendations

1. Add a cross-tokenizer validation cell to Section 5: run `devops_consultant.json` through GPT-2, Qwen2.5, DeepSeek in all 4 formats. If ranking holds — much stronger claim.
2. Add subsection on language effects (Russian content on local models).
3. Borrow `chars/token` metric for quantitative comparison table.
4. Don't borrow: ANSI color visualization (not portable to static article), `deepseek-native` path (installation-specific), GigaChat tokenizer (niche).

+++

## Series Split Proposal

Article tries to do three things: conceptual argument, token-level analysis, hands-on measurement. Proposed split into two articles:

### Part 1: Format as Architecture

- Goal: convince reader that format is an architectural decision, give decision framework
- Content: problem statement, format comparison (qualitative), training distribution hypothesis, two-audience principle (moved to Section 2), XML added, security, decision framework, Mentor Generator case study
- Code cells: zero or minimal
- Size: ~200 lines

### Part 2: Token Economics of Prompt Delivery

- Goal: teach BPE mechanics, prove claims with measurements, cross-tokenizer validation
- Content: BPE tokenizer mechanics, token noise counting, runnable measurements (tiktoken + HuggingFace), cross-tokenizer validation (from teaching notebook), language effects (Ru/En), chars/token metric, matplotlib charts
- Code cells: heavy
- Size: ~250-300 lines

Part 2 cross-references Part 1 for "so what"; Part 1 references Part 2 for "proof."

+++

## Priority Summary

| Priority | Item | Section |
|---|---|---|
| High | Fix colon-counting inconsistency | 2.1, 2.3 |
| High | Add XML to format comparison | 2.6, 8 |
| High | Fix frontmatter (authors, description, tags, type) | Frontmatter |
| High | Acknowledge confounding variables in v0.40→v0.41 | 6.1 |
| Medium | Move Two-Audience Principle earlier | Structure |
| Medium | Soften "equal computational cost" claim | 1 |
| Medium | Remove bold wrapping from ## headings | All |
| Medium | Add link/path to prepare_prompt.py | 4, 9 |
| Medium | Cross-tokenizer validation (from teaching notebook) | New section |
| Medium | Language effects (Ru/En) | New section |
| Low | Reframe or remove Qwen3-Max "agreement" | 6.2 |
| Low | Add chars/token metric to comparison table | 2.6 |
| Low | Pin token counts to specific commit | 5.7 |
