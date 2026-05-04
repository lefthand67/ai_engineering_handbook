---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.1
kernelspec:
  name: bash
  display_name: Bash
  language: bash
---

---
title: 'Format as Architecture: Signal-to-Noise in Prompt Delivery'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Analyzes how the serialization format (JSON, YAML, XML, Markdown) of
  a system prompt affects LLM behavior, token costs, and instruction adherence.
tags:
- prompts
- architecture
date: '2026-05-02'
options:
  type: guide
  version: 0.2.2
  birth: '2026-02-15'
  token_size: 5052
---

+++

This article examines how the serialization format of a system prompt affects LLM behavior. The choice between JSON, YAML, XML, and Markdown is not cosmetic -- it changes the signal-to-noise ratio in the transformer's attention budget and may bias the model toward different processing modes. We present a qualitative format comparison, training-distribution effects, security analysis, and a decision framework. For runnable token measurements and BPE tokenizer mechanics, see the companion article [Token Economics of Prompt Delivery](/ai_system_layers/3_prompts/token_economics_of_prompt_delivery.ipynb).

+++

## 1. The Problem: Format Is Not Neutral

+++

Every token in a transformer's input occupies a position in the sequence and participates in self-attention across all layers. During the **prefill phase** -- when the model processes the entire prompt in parallel -- each token's Query vector is compared against every other token's Key vector. The computational cost scales quadratically with sequence length (O(n²) for self-attention). Structural characters like `{`, `}`, `"`, `,` participate in this computation even though they carry no semantic content.

The effect is twofold: structural tokens **increase computational cost** (more FLOPs for the attention matrix multiplication) and **dilute the attention distribution** -- with more tokens in the softmax denominator, each content token receives a slightly smaller share of the attention probability mass. A structural token can receive near-zero attention weight if the model has learned it is semantically irrelevant, but the FLOPs to compute that near-zero weight are still incurred ([A-26016](/architecture/evidence/analyses/A-26016_causal_masking_attention_mechanics_for_prompt_engineering.md)).

The question is not "which format is prettiest" but "which format maximizes instructional signal per token."

+++

## 2. The Two-Audience Principle

+++

A system prompt pipeline typically involves two distinct consumers:

1. **The compiler/generator** -- reads the source template once, performs transformations (placeholder substitution, curriculum generation), and outputs the result. This consumer needs unambiguous structure, tooling support (`jq`, `json.load()`), and validation.

2. **The runtime model** -- reads the generated output every session. This consumer needs to internalize behavioral rules, reference structured data (curriculum phases, user profile), and follow protocols. Signal-to-noise ratio directly affects instruction compliance.

These consumers have different format requirements:

| Consumer | Needs | Optimal format |
|----------|-------|---------------|
| Compiler (one-time) | Validation, tooling, unambiguous structure | JSON |
| Runtime model (every session) | Low noise, instruction compliance, field access | YAML |
| Structured data records | Strictness, parseable fields | JSON |
| Scope boundaries with untrusted content | Explicit delimiters, injection resistance | XML |

This leads to a natural format boundary: **JSON for development artifacts, YAML for runtime instructions, XML for scope boundaries with untrusted content, JSON for structured data records.**

The [prepare_prompt.py](/tools/scripts/prepare_prompt.py) tool in this repository implements this boundary -- it converts JSON source prompts to YAML-like format before delivery to the LLM.

+++

## 3. Token Noise Analysis by Format

+++

To compare formats fairly, we count **format-specific structural tokens** -- delimiters that one format requires but others do not. The `:` key-value separator is shared by JSON and YAML, so it is not counted as overhead for either. All examples use the same 4-key snippet for direct comparison.

### 3.1 JSON

JSON requires explicit delimiters for every structural boundary:

```json
"patience_with_attempts": {
  "rule": "Give the student two attempts to answer before simplifying",
  "on_first_miss": "Guide toward understanding with a hint or different angle",
  "on_second_miss": "Simplify the explanation and try a different approach"
}
```

Format-specific tokens: `"` quotes (x14), `{`, `}`, `,` (x2) = ~18 tokens beyond what any key-value format requires.

In a typical 300-line JSON system prompt, an estimated 20-30% of tokens are structural characters. These characters encode information (nesting, type boundaries) that is redundant when indentation already conveys hierarchy. For measured numbers on a production prompt, see [Token Economics of Prompt Delivery](/ai_system_layers/3_prompts/token_economics_of_prompt_delivery.ipynb).

+++

### 3.2 YAML

YAML conveys structure through indentation and minimal punctuation:

```yaml
patience_with_attempts:
  rule: Give the student two attempts to answer before simplifying
  on_first_miss: Guide toward understanding with a hint or different angle
  on_second_miss: Simplify the explanation and try a different approach
```

Format-specific tokens: zero. The `:` separators (x4) are shared with JSON. YAML adds no quotes, no braces, no commas.

Indentation uses whitespace tokens, which typically receive lower attention weights in practice. These whitespace tokens also serve as **attention anchors** -- boundary signals that help the transformer's attention heads segment the prompt into semantically meaningful blocks. This is an empirical observation about models trained on structured text (code, YAML, Markdown), not an architectural guarantee of all transformers ([A-26016](/architecture/evidence/analyses/A-26016_causal_masking_attention_mechanics_for_prompt_engineering.md)). YAML achieves the lowest structural noise of any format that preserves machine-readable key-value structure. When using PyYAML in a pipeline, set `width=float('inf')` to disable line-wrapping -- the default `width=80` adds ~4% token overhead from continuation-line tokens with no semantic benefit.

+++

### 3.3 XML

XML uses explicit named tags:

```xml
<patience_with_attempts>
  <rule>Give the student two attempts to answer before simplifying</rule>
  <on_first_miss>Guide toward understanding with a hint or different angle</on_first_miss>
  <on_second_miss>Simplify the explanation and try a different approach</on_second_miss>
</patience_with_attempts>
```

Format-specific tokens: `<`, `>`, `</`, `>` for every key, plus the key name is repeated in the closing tag. For this 4-key snippet, that is roughly 20-25 tokens of structural overhead (hand-counted estimate; XML and Markdown are not measured in the [Appendix](/ai_system_layers/3_prompts/appendix_yaml_serializer_variance.ipynb)) -- comparable to JSON, but distributed differently.

However, XML provides two properties that other formats lack:

- **Named scope boundaries.** Each `</tag>` explicitly closes its scope, making hierarchy unambiguous even without indentation. This matters for injection resistance (see Section 6).
- **Strong attention anchors.** Tag names repeat at open and close, giving the transformer explicit signposts to segment sections. For large prompts, these anchors can improve positional awareness.

XML tags are widely used in production prompt systems -- Anthropic's own system prompts use them extensively for scope isolation ([A-26018: XML Tags as Scope Boundaries](/architecture/evidence/analyses/A-26018_xml_tags_scope_isolation_prompt_architecture.md)).

+++

### 3.4 Markdown

Markdown replaces JSON delimiters with formatting symbols:

```markdown
### Patience with Attempts
- **Rule**: Give the student two attempts to answer before simplifying
- **On first miss**: Guide toward understanding with a hint or different angle
- **On second miss**: Simplify the explanation and try a different approach
```

Format-specific tokens: `###` (1-2 tokens), `-` (x3), `**` open/close (x6) = roughly 10-13 tokens (hand-counted estimate; not measured empirically).

Markdown has less structural noise than JSON, but its formatting symbols (`*`, `#`, `` ` ``) are not zero-cost. Each `**bold**` marker is 2 tokens (`**` open + `**` close) that carry no semantic content -- only a formatting signal. For a 300-line file, Markdown formatting overhead is roughly 10-15% of tokens.

More critically, **Markdown destroys machine-readable structure**. Keys become headings, values become prose, and nesting becomes ambiguous. A downstream system cannot reliably extract `patience_with_attempts.on_first_miss` from Markdown the way it can from JSON, YAML, or XML. Markdown headers define "soft" boundaries -- the end of a section is implied by the start of the next header, not by an explicit delimiter ([A-26018: XML Tags as Scope Boundaries](/architecture/evidence/analyses/A-26018_xml_tags_scope_isolation_prompt_architecture.md)).

+++

### 3.5 Minified JSON

Minified JSON (`jq -c`) removes all whitespace between structural elements, collapsing the entire prompt onto a single line:

```json
{"patience_with_attempts":{"rule":"Give the student two attempts to answer before simplifying","on_first_miss":"Guide toward understanding with a hint or different angle","on_second_miss":"Simplify the explanation and try a different approach"}}
```

Format-specific tokens remain the same as pretty JSON (~18), but every indentation space and newline is eliminated. This gives minified JSON the lowest absolute token count of any format.

The trade-off: without newlines or indentation, there are no **attention anchors**. The transformer receives a dense, continuous stream with no structural signposts to segment sections during the prefill phase. For short prompts this is negligible; for 2,000+ token prompts the absence of boundary signals forces the model to rely on content-level cues alone to maintain positional awareness across the "wall of text" ([A-26016](/architecture/evidence/analyses/A-26016_causal_masking_attention_mechanics_for_prompt_engineering.md)).

+++

### 3.6 YAML Literal Block Scalar

The YAML `|` (literal block scalar) style preserves newlines exactly as written:

```yaml
patience_with_attempts:
  rule: |
    Give the student two attempts to answer before simplifying
  on_first_miss: |
    Guide toward understanding with a hint or different angle
  on_second_miss: |
    Simplify the explanation and try a different approach
```

Counterintuitively, this is one of the **most expensive** formats. Every line inside a `|` block must be indented relative to the key, adding leading whitespace tokens to every single line. Whether YAML Literal ends up more or less expensive than Pretty JSON depends on the serializer: PyYAML's `|` (clip) keeps it slightly below Pretty JSON, while yq's `|-` (strip) applied to all scalars pushes it above. See the [Appendix: YAML Serializer Variance](/ai_system_layers/3_prompts/appendix_yaml_serializer_variance.ipynb) for per-file measurements.

Use `|` only when whitespace must be preserved exactly (e.g., embedded code snippets or Bash scripts inside a prompt).

+++

### 3.7 Comparison Table

| Format | Format-specific overhead | Key-value addressable | Attention anchors | Injection resistance |
|--------|------------------------|-----------------------|-------------------|---------------------|
| Standard YAML | None (`:` shared) | Yes | Strong (indentation) | Low (whitespace) |
| Minified JSON | ~18 tokens (but zero whitespace) | Yes | None | High (delimiters) |
| Raw JSON (pretty) | ~18 tokens | Yes | Moderate (braces) | High (delimiters) |
| Markdown | ~10-13 tokens | No | Moderate (soft headers) | Low |
| XML | ~20-25 tokens (repeated tag names) | Yes | Strong (named tags) | High (delimiters) |
| YAML Literal (`\|`) | None + indentation tax * | Yes | Strong (indentation) | Low (whitespace) |

\* YAML token costs are serializer-dependent: PyYAML's `width` parameter and yq's scalar coercion rules shift the cost by 100+ tokens on a typical prompt. Standard YAML with `width=∞` is the cheapest human-readable option; YAML Literal ranking vs Pretty JSON flips between tools. See the [Appendix: YAML Serializer Variance](/ai_system_layers/3_prompts/appendix_yaml_serializer_variance.ipynb) for isolation experiments.

For measured token counts across formats and tokenizers, see [Token Economics of Prompt Delivery](/ai_system_layers/3_prompts/token_economics_of_prompt_delivery.ipynb).

+++

## 4. Training Distribution Effects

+++

Beyond raw token counts, the format may influence how the model processes the content. This is an empirical observation, not a proven mechanism.

**JSON in training data** appears primarily as serialized data: API responses, database exports, configuration dumps, package manifests. Models trained on this distribution may associate JSON structure with "data to parse and extract from" rather than "instructions to follow."

**YAML in training data** appears in configuration and instruction contexts: Kubernetes manifests, Ansible playbooks, CI/CD pipelines, GitHub Actions workflows. These are contexts where the YAML content IS the instruction set -- the system reads it and executes it.

**XML in training data** appears in both document markup (HTML/XHTML, RSS, SOAP) and structured instruction contexts (Ant build files, Maven POMs, Android manifests). XML's dual role in training data gives it a more neutral processing prior than JSON or YAML. Modern LLMs trained on chat templates also use XML-like delimiters to distinguish between system, user, and assistant roles -- making XML tags particularly effective as scope markers ([A-26018: XML Tags as Scope Boundaries](/architecture/evidence/analyses/A-26018_xml_tags_scope_isolation_prompt_architecture.md)).

**Markdown in training data** appears as documentation, READMEs, blog posts, and technical guides. The association is with "content to present to humans" rather than "structured configuration to execute." Using Markdown headers (`##`) in prompts may nudge the model toward a descriptive or informative mode rather than an operational one ([A-26018: XML Tags as Scope Boundaries](/architecture/evidence/analyses/A-26018_xml_tags_scope_isolation_prompt_architecture.md)).

The hypothesis: when a model reads a system prompt in JSON format, the training-distribution prior nudges it toward treating the content as data. When it reads the same content in YAML, the prior nudges it toward treating the content as operational instructions.

The case study in {ref}`faa-case-study` is consistent with this hypothesis but is confounded by a simultaneous structural change — the format effect cannot be isolated from a single observation. We do not have controlled multi-model benchmarks to confirm or refute it.

> **Open question:** If format response is learned from training corpus, the same format may prime different cognitive modes in different models — YAML may mean "execute" to a model trained heavily on DevOps corpora and "describe" to a model trained on scientific literature. This makes format a hidden variable in cross-model instruction-following benchmarks: comparisons may be measuring format familiarity, not underlying capability. No controlled experiment (same content × multiple formats × multiple models × behavioral outcome) exists yet. Tracked in `techdebt.md` (TD-007).

+++

(faa-case-study)=
## 5. Case Study: Structured File Generation

+++

A production system uses an LLM (Qwen3-Max) as a "compiler" -- it reads a JSON meta-prompt containing templates and generates a structured YAML file with 15 top-level sections, placeholder substitution, and immutable metadata fields.

**Initial design:** the LLM received templates as separate files and was instructed to copy and fill them. The output format was JSON. Result: catastrophic drift -- 10 of 15 sections dropped, immutable fields rewritten, structural parity violated. The LLM treated the templates as context to understand, not source code to copy.

**Revised design:** templates were embedded directly in the meta-prompt, and the output format was changed to YAML. Same model, same content. Result: ~95% compiler fidelity (defined as: all top-level sections present with correct structure, literal values preserved verbatim, placeholders substituted correctly) -- all 15 sections present, literal values preserved verbatim, correct placeholder substitution. The remaining ~5% issues (one key renamed, two nested fields dropped, one key truncated) are compliance issues, not format problems.

**Important caveat:** this improvement is confounded by two simultaneous changes -- the format switch (JSON → YAML output) AND the structural change (embedding templates in the meta-prompt). We cannot isolate the format effect from this single comparison. The result is consistent with the training-distribution hypothesis (Section 4) but does not prove it.

+++

## 6. Security Considerations

+++

Indentation-based formats introduce a specific class of prompt injection vulnerability that delimiter-based formats (JSON, XML) are less susceptible to.

### 6.1 The "Out-Indenting" Attack

In YAML or any indentation-scoped format, hierarchy is determined by whitespace depth. If user-generated content is dynamically inserted into an indented block, a malicious input can "out-indent" -- using fewer leading spaces to escape the intended scope and inject instructions at a higher level of the prompt hierarchy.

For example, if user input is inserted at 4-space indentation depth, an attacker can submit content with 0-space indentation to place instructions at the root level, potentially overriding system instructions.

### 6.2 Mitigation

- **Terminal anchors.** End critical instruction blocks with explicit markers (e.g., a new top-level key) so that scope cannot be extended by injected content.
- **Programmatic indentation enforcement.** When inserting dynamic content, strip all leading whitespace and re-indent programmatically to the intended depth. Never trust user-supplied indentation.
- **Validate after assembly.** Parse the assembled prompt as YAML/JSON and validate against a strict schema (Pydantic model or JSON Schema) before sending it to the LLM. Parsing alone is insufficient -- a structurally valid document can still contain injected keys at unexpected nesting levels. Schema validation catches scope violations that a parser accepts silently.

### 6.3 Format Comparison for Injection Resistance

JSON and XML have explicit delimiters (`}`, `</tag>`) that are harder to forge in free-text input. YAML and Markdown rely on whitespace, which is invisible and easy to manipulate. If your prompt pipeline inserts untrusted content, prefer delimiter-based formats for the injection boundary or sanitize aggressively.

### 6.4 The Hybrid Pattern: YAML Instructions + XML Scope Tags

In practice, many production systems use **mixed formats** at the injection boundary: XML tags to isolate untrusted user content within an otherwise YAML prompt. This combines YAML's low noise for instructions with XML's scope safety for dynamic content ([A-26018: XML Tags as Scope Boundaries](/architecture/evidence/analyses/A-26018_xml_tags_scope_isolation_prompt_architecture.md)).

A practical implementation embeds XML tags directly in the JSON source as part of the prompt architecture, so the conversion pipeline preserves them without additional scripting:

```json
{
  "instructions": {
    "role": "DevOps Consultant",
    "constraints": ["No proprietary tools", "Prefer shell scripts"]
  },
  "runtime_data": {
    "user_query": ["<query>", "[USER_QUERY]", "</query>"]
  }
}
```

After JSON-to-YAML conversion, the `<query>` tags survive as terminal anchors in the YAML output, preventing out-indenting attacks without requiring a custom injection script. The JSON list structure avoids escaped newlines while keeping the SSoT clean ([A-26018: XML Tags as Scope Boundaries](/architecture/evidence/analyses/A-26018_xml_tags_scope_isolation_prompt_architecture.md)).

+++

## 7. Decision Framework

+++

When choosing a format for any prompt or LLM-consumed file:

1. **Who reads this file?** If a compiler/tooling reads it once, use JSON. If the LLM reads it every session as instructions, use YAML. If scope isolation is critical, use XML tags.

2. **Does the consumer need to follow instructions or parse data?** Instructions benefit from low noise (YAML). Data parsing benefits from strictness (JSON).

3. **Does the consumer need key-value access?** If yes, Markdown is unsuitable. Choose between JSON (strict), YAML (clean), or XML (verbose but explicit).

4. **How large is the file?** For small files (<50 lines), format barely matters. For large files (300+ lines), the noise difference between formats is significant.

5. **What is the delivery mechanism?** Web chat (paste/attach) favors YAML for readability. API calls favor JSON for tooling. Configuration management favors YAML for editability.

6. **Token budget or reasoning quality?** If you are hitting a context window ceiling, minified JSON (`jq -c`) gives the lowest token count. If you have headroom, standard YAML with `width=∞` provides better attention anchors and instruction adherence at a modest token premium (~7% over minified JSON). YAML literal (`|`) should be reserved for whitespace-sensitive content only — its cost relative to Pretty JSON is serializer-dependent (see [Appendix](/ai_system_layers/3_prompts/appendix_yaml_serializer_variance.ipynb)).

7. **Does the pipeline insert untrusted content?** If yes, prefer delimiter-based formats (JSON, XML) at the injection boundary, or sanitize indentation programmatically (see Section 6). Consider the hybrid pattern: XML scope tags around user content within a YAML prompt.

+++

## 8. Summary

+++

Format is not a cosmetic choice. It is an architectural decision that affects:

- **Signal-to-noise ratio** in the transformer's positional and computational budget
- **Processing mode** influenced by training data distribution
- **Token cost** with measured differences of up to 18–21% between formats on the same content (18% PyYAML, 21% yq — see [Appendix: YAML Serializer Variance](/ai_system_layers/3_prompts/appendix_yaml_serializer_variance.ipynb))
- **Structural integrity** of key-value data downstream
- **Security posture** when inserting dynamic content into prompts

YAML occupies the optimal position for LLM-consumed instruction files: lowest structural noise among formats that preserve machine-readable structure, with attention anchors that promote instruction adherence. JSON is optimal for development artifacts, structured data records, and tooling integration. XML excels at scope isolation and injection-boundary safety, and is the format of choice when mixing trusted instructions with untrusted content. Markdown is appropriate for human documentation but unsuitable for structured prompt delivery.

The [prepare_prompt.py](/tools/scripts/prepare_prompt.py) script in this repository implements this principle by converting JSON source prompts to clean YAML before LLM delivery. For token-level measurements and BPE mechanics that support these conclusions, see [Token Economics of Prompt Delivery](/ai_system_layers/3_prompts/token_economics_of_prompt_delivery.ipynb).
