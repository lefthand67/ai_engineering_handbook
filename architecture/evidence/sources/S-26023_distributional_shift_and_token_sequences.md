
---
title: Distributional Shift and Token Sequences
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: 2026-03-26
description: Technical clarification on the distinction between token vocabulary membership
  and sequence distribution, focusing on how whitespace removal causes distributional
  shift
tags:
- model
options:
  type: source
  token_size: 2019
  id: S-26023
  model: Qwen3.5-Plus
  extracted_into: null
---
### User

> Attached: A-26016_causal_masking_attention_mechanics_for_prompt_engineering.md (text/markdown)

distributional shift - how can the input token distribution shift away from what it was trained on if the query is tokenized with the model's tokenizer? the tokens we get are familiar to the model, we do not use non-familiar tokens that may shift the distribution. am I wrong?

### Assistant

# Introduction

The question raises a critical nuance in large language model (LLM) inference: the distinction between **token vocabulary membership** and **token sequence distribution**. You are correct that using a model's native tokenizer ensures that every generated token ID exists within the model's vocabulary (i.e., no `<UNK>` or unknown tokens are produced). However, the claim that removing inter-word spaces causes a **distributional shift** remains technically accurate. This shift does not stem from the introduction of unknown tokens, but rather from the alteration of **which** known tokens are selected and the **statistical probability** of their sequences relative to the pretraining data.

This analysis clarifies why valid token IDs can still constitute an out-of-distribution input when formatting changes, such as space removal, alter the underlying tokenization pattern. The explanation draws upon the technical mechanics outlined in *"Hands-On Large Language Models"* by **Jay Alammar** and **Maarten Grootendorst**, as well as the architectural analysis provided by **Vadim Rudakov**.

# Historical Context

### Early Tokenization: Word-Level Constraints
In the early history of Language AI, representation methods like **bag-of-words** treated text as unordered collections of words (Alammar & Grootendorst, 2024). Later, **word2vec** introduced dense vector embeddings but relied on strict word-level tokenization (Mikolov et al., 2013). A significant limitation of this era was the inability to handle out-of-vocabulary (OOV) words; if a word was not in the training vocabulary, it could not be represented. This established the early understanding that token familiarity was binary: a word was either known or unknown.

### Subword Evolution: BPE and Space Prefixing
The transition to Transformer architectures necessitated more robust tokenization schemes to handle open vocabularies. **Byte Pair Encoding (BPE)** became the standard for many generative models, including the GPT family (Radford et al., 2019). A crucial innovation in modern BPE tokenizers (such as those used in GPT-2, Llama, and Phi-3) is the explicit handling of whitespace.

According to *"Hands-On Large Language Models"*, modern tokenizers often store space-prefixed words and bare words as **different vocabulary entries** with different learned embeddings (Alammar & Grootendorst, 2024). For example, the token `Ġcat` (indicating a space precedes "cat") is distinct from `cat` (no preceding space). During pretraining, the model learns specific semantic and positional associations for `Ġcat` because it appears frequently in natural text. The bare token `cat` appears far less frequently, typically only in contexts like URLs, code, or concatenated strings.

### Modern Limitations: Distributional Sensitivity
While modern tokenizers solve the OOV problem, they introduce sensitivity to **token sequence distribution**. As noted in the analysis by **Vadim Rudakov**, removing inter-word spaces forces the tokenizer to produce the "bare" version of tokens instead of the "space-prefixed" version (Rudakov, 2026). Although both token IDs exist in the vocabulary, the **sequence** of bare tokens is statistically rare compared to the space-prefixed sequences seen during pretraining. This creates a distributional shift where the input representation diverges from the data distribution the model's attention mechanisms and embeddings were optimized for.

# Modern Relevance: Mechanics of the Shift

### Token Identity vs. Token Context
The core misunderstanding lies in equating "valid token ID" with "familiar input." When spaces are removed:
1.  **Token Selection Changes:** The tokenizer selects `cat` instead of `Ġcat`. These have different embedding vectors.
2.  **Sequence Probability Changes:** The model learned that `Ġthe` usually follows `Ġcat`. It rarely learned the transition from `cat` to `the` without an intervening space token.
3.  **Attention Patterns Disrupt:** The attention heads, which learned to rely on space tokens as boundary signals (or "attention anchors"), lose these cues. While the model can still decode the content, the **learned attention patterns, positional associations, and semantic representations** were built on the space-prefixed token distribution (Rudakov, 2026).

### Computational vs. Attentional Cost
This shift impacts inference in two ways, as distinguished by **Vadim Rudakov**:
*   **Computational Cost:** Every token requires Query-Key dot products regardless of its semantic weight. Unusual token sequences do not reduce this cost.
*   **Attentional Weight:** The softmax normalization ensures attention weights sum to 1. If the model encounters a rare sequence (no spaces), the attention distribution may become less confident or diffuse, as the input deviates from the high-probability manifolds learned during pretraining.

### Empirical Evidence
In *"Hands-On Large Language Models"*, **Jay Alammar** and **Maarten Grootendorst** demonstrate that tokenizers like GPT-2 and Phi-3 explicitly encode whitespace information into token IDs (Alammar & Grootendorst, 2024). For instance, removing spaces changes the tokenization of "Hello World" from `['Hello', 'ĠWorld']` to `['Hello', 'World']` (where the second token lacks the space prefix indicator). This confirms that the input representation is fundamentally altered, even if no unknown tokens are introduced.

# Key Takeaways

*   **Vocabulary Membership $\neq$ Distributional Alignment:** Using the correct tokenizer ensures all token IDs are valid, but it does not guarantee the **sequence** of tokens matches the pretraining distribution.
*   **Space Prefixing is Semantic:** In modern BPE tokenizers, whitespace is not invisible; it is encoded into the token ID itself (e.g., `Ġ` symbol). Removing spaces changes the token IDs selected.
*   **Embedding Mismatch:** Space-prefixed tokens and bare tokens have different embedding vectors. Swapping one for the other changes the numerical input to the Transformer layers.
*   **Attention Anchors:** Structural tokens (like spaces) serve as boundary signals for attention heads. Their removal forces the model to rely on less familiar content-level cues, degrading reliability.
*   **Distributional Shift:** The degradation in output quality from removing spaces is due to a **distributional shift problem**, not a lack of "reasoning capacity" or unknown tokens.

# Literature List

1.  Alammar, J., & Grootendorst, M. (2024). *"Hands-On Large Language Models: Language Understanding and Generation"*. O'Reilly Media.  
    *Relevance:* Provides foundational explanations of tokenization schemes, specifically detailing how BPE tokenizers handle whitespace and space-prefixed tokens as distinct vocabulary entries.*

2.  Bahdanau, D., Cho, K., & Bengio, Y. (2014). *"Neural Machine Translation by Jointly Learning to Align and Translate"*. arXiv preprint arXiv:1409.0473.  
    *Relevance:* Introduces early attention mechanisms in RNNs, establishing the historical context for how models learn to weigh input elements, which evolved into the self-attention mechanisms sensitive to token distribution.*

3.  Mikolov, T., et al. (2013). *"Efficient Estimation of Word Representations in Vector Space"*. arXiv preprint arXiv:1301.3781.  
    *Relevance:* Describes the word2vec algorithm, highlighting the early limitations of word-level tokenization that necessitated the shift to subword methods sensitive to formatting.*

4.  Radford, A., et al. (2019). *"Language Models are Unsupervised Multitask Learners"*. OpenAI Blog.  
    *Relevance:* Describes the GPT-2 architecture and tokenizer, which popularized the byte-pair encoding scheme where whitespace is explicitly encoded into token IDs.*

5.  Rudakov, V. (2026). *"Causal Masking and Attention Mechanics — Implications for Prompt Format"*. Internal Analysis Document A-26016.  
    *Relevance:* Directly addresses the prompt engineering claims regarding whitespace, distinguishing between computational cost and attentional weight, and defining the removal of spaces as a distributional shift.*

6.  Vaswani, A., et al. (2017). *"Attention Is All You Need"*. Advances in Neural Information Processing Systems 30.  
    *Relevance:* Introduces the Transformer architecture, establishing the self-attention mechanism that relies on token embeddings and positional information, which are disrupted by tokenization shifts.*
