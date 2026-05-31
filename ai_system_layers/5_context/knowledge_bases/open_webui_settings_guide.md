---
title: Open WebUI Knowledge Base Configuration Guide
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Step-by-step configuration for Open WebUI RAG settings to optimize for
  VRAM and retrieval accuracy.
tags:
- devops
- context_management
date: 2026-04-30
options:
  type: guide
  version: "1.0.0"
  birth: 2026-04-30
  token_size: 901
---
# Open WebUI Knowledge Base Configuration Guide

Once you have selected your embedding model (see [Understanding Embeddings](/ai_system_layers/2_model/selection/embeddings_explained.md) for the "Why"), use these settings to ensure your documents are indexed and retrieved accurately.

This guide covers the settings found in **Settings $\rightarrow$ Documents**.

## 1. Indexing Settings
Controls how files are processed during upload or "Re-index."

| Setting | Recommended | Description |
| :--- | :--- | :--- |
| **Embedding Batch Size** | `32` | Chunks sent to the model at once. Balance speed vs. VRAM. |
| **Concurrent Requests** | `1` | Parallel requests to Ollama. Keep low on single-GPU systems to avoid OOM. |

## 2. Retrieval (RAG) Settings
Determines how the system finds information to answer your prompt.

### The Core Balance
- **Top K (`5 - 10`):** Number of document chunks retrieved.
    - *Too low:* AI misses the answer.
    - *Too high:* AI gets overwhelmed and uses more VRAM.
- **Hybrid Search (`Enabled`):** Combines **Vector Search** (concepts) with **BM25 Search** (keywords). Highly recommended for technical docs.
- **BM25 Weight (`0.4`):** Balance between meaning (`0`) and keywords (`1`). `0.4` is the sweet spot for engineering data.

### Refined Search
- **Enrich Hybrid Search Text (`Disabled`):** Adds surrounding context to chunks. Use only if search accuracy is poor.
- **Full Context Mode (`Disabled`):** **Danger!** Sends the entire document. Will likely crash 16GB VRAM systems.

## 3. Reranking (Optional)
A "second pass" filter to sort the **Top K** results.

| Setting | Recommended | Note |
| :--- | :--- | :--- |
| **Reranking Model** | `None` | Use only if you have spare VRAM. Otherwise, it slows down retrieval. |
| **Top K Reranker** | `3 - 5` | Final number of chunks passed to the LLM if reranking is on. |
| **Relevance Threshold** | `0.1 - 0.5` | Filters out low-match documents. See "The Threshold Trap" below. |

---

### ⚠️ The Threshold Trap
The **Relevance Threshold** is the most common cause of "silent failures" (system works, but returns no sources).

**The Model Size Problem:**
Smaller embedding models often produce lower raw similarity scores than giant 8B+ models, even if they found the correct document.

- If you set a high threshold (e.g., **`0.75`**), a small model might find the perfect answer but only score it at `0.65`.
- The system will **discard the correct answer**, and the AI will claim it can't find any information.

**Recommendation:** If your chat isn't finding sources, **lower this value to `0.1` or `0`**. If results appear, gradually increase it.

---

### ⚠️ Critical Maintenance: The Dimension Mismatch
Because embedding dimensions are **locked** upon collection creation (see [Understanding Dimensions](/ai_system_layers/2_model/selection/embeddings_explained.md)), switching models will cause a `Dimension Mismatch` error.

**The Fix:**
1. Go to **Workspace $\rightarrow$ Knowledge**.
2. **Delete** the existing knowledge base.
3. **Create** a new knowledge base and re-upload your files.
4. This forces the database to create a new collection with the correct dimensions.
