---
title: Understanding Embeddings and Retrieval
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Conceptual guide to embedding vectors, dimensions, and model selection
  for RAG systems.
tags:
- model
- context_management
date: 2026-04-30
options:
  type: guide
  version: "1.0.0"
  birth: 2026-04-30
  token_size: 950
---
# Understanding Embeddings and Retrieval

If you are new to AI and RAG (Retrieval Augmented Generation), the concept of "embeddings" can feel abstract. This guide explains what they are and how to choose the right models for your system.

## 1. The "Librarian" Analogy
Imagine a library with millions of pages of text. If you ask a librarian, *"Find me something about the impact of inflation on housing,"* the librarian doesn't just search for the exact word "inflation." Instead, they understand the **concept** of inflation and the **concept** of housing.

**Embeddings** are how AI does this. An embedding model takes a piece of text and converts it into a long list of numbers (a **vector**).

- Texts with similar meanings are placed "close" to each other in a mathematical space.
- The AI doesn't search for words; it searches for **mathematical proximity**.

## 2. What are "Dimensions"?
You will often see numbers like **384**, **768**, or **4096**. These are the **dimensions** of the embedding.

Think of dimensions as the "resolution" of the meaning:
- **Low Dimension (e.g., 384):** Captures the general shape of the meaning. Very fast, tiny memory footprint.
- **High Dimension (e.g., 4096):** Captures tiny nuances, complex technical relationships, and subtle logic. Slower and uses significantly more VRAM.

> [!IMPORTANT]
> Once a "Knowledge Base" is created, its dimension is **locked**. Switching models with different dimensions requires deleting and recreating the collection. See the [Open WebUI Settings Guide](/ai_system_layers/5_context/knowledge_bases/open_webui_settings_guide.md) for the fix.

## 3. Choosing Your Model: The "Richness" Trade-off

Not all small models are created equal. When choosing an embedding model, consider the balance between **VRAM cost** and **semantic richness**.

### Encoder Models (The Specialists)
*Example: `nomic-embed-text-v2-moe`, `all-MiniLM-L6-v2`*
These are purpose-built for creating vectors.
- **Pros:** Blazing fast, tiny VRAM footprint ($\approx 0.5$ GB).
- **Cons:** Generally slightly lower reasoning than a giant LLM.
- **Top Recommendation:** `nomic-embed-text-v2-moe`. It uses a "Mixture of Experts" (MoE) architecture to provide the richness of a large model with the speed of a small one.

### LLM-Based Embeddings (The Generalists)
*Example: `qwen3-embedding:8b`*
Full LLMs repurposed for embeddings.
- **Pros:** Maximum nuance. Best for rare technical concepts.
- **Cons:** Massive VRAM usage (8 GB+).

### The "Shrunken Giant" Trap
Be careful with "distilled" small models (e.g., `qwen3-embedding:0.6b`). While they are small, they can feel "thin"—meaning they find the right documents but lack the semantic richness of a specialist model or a full 8B model. If results feel simplistic, switch to a specialized Encoder like Nomic.

## 4. Summary Recommendation

| Setup | Recommended Model | Why? |
| :--- | :--- | :--- |
| **Limited VRAM ($\le 16$GB)** | `nomic-embed-text-v2-moe` | Best balance of "richness" and speed. |
| **Ultra-High Precision** | `qwen3-embedding:8b` | Maximum nuance for rare tech. |
| **Extreme Speed / Minimal RAM** | `all-MiniLM-L6-v2` | The fastest "baseline" option. |

For practical implementation of these models in your system, see the [Open WebUI Settings Guide](/ai_system_layers/5_context/knowledge_bases/open_webui_settings_guide.md).
