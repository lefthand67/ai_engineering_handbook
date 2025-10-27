# 📚 Actionable Handbook: Custom Domain Embeddings and Tokenization for Local LLMs

---

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 1.0.0  
Birth: 27.10.2025  
Modified: 27.10.2025  

---

This guide outlines the critical steps and architectural considerations for creating a robust, domain-specific embedding model and its associated custom vocabulary (tokenizer) for use with small, local Language Models (1B-14B) in a production setting.

> WARNING! No code examples were tested.

## 1. Architectural Mandate: Contextual Embeddings via Fine-Tuning

For small LLMs, **Retrieval-Augmented Generation (RAG)** is the primary method for injecting domain knowledge. This requires **high-quality, contextual embeddings**. Avoid training non-contextual models like Word2Vec from scratch; focus on fine-tuning an efficient pre-trained transformer model.

| Step | Goal | Tooling | ISO 29148 Compliance |
| --- | --- | --- | --- |
| **Data Preparation** | Curate a clean, versioned corpus. | Python, DVC | **Traceability:** Every embedding must map back to a specific, versioned document. |
| **Vocabulary Analysis** | Quantify the need for a custom tokenizer. | Hugging Face `transformers` | **Verifiability:** Ensure domain terms are represented as single, semantically rich tokens. |
| **Tokenization Pipeline** | Train a domain-specific tokenizer (if needed). | Hugging Face `tokenizers` (Rust/Python) | **Unambiguity:** Use a fixed vocabulary index for deployment across environments. |
| **Model Fine-Tuning** | Adjust an efficient, pre-trained model to the domain's semantic space. | `sentence-transformers`, PyTorch | **Precision:** Achieve high Contextual Recall and Precision scores. |

## 2. Phase I: Vocabulary Analysis and Custom Tokenizer (If Required)

The first bottleneck in domain adaptation is the **tokenizer's vocabulary**.

### 2.1 Quantify Out-Of-Vocabulary (OOV) Rate

Before training a new tokenizer, you must prove the existing one is insufficient.

1.  **Select a Proxy Tokenizer:** Choose the tokenizer from a popular, efficient model that is similar to your target (e.g., a BGE or MiniLM tokenizer).

2.  **Calculate the Token-to-Word Ratio:** This metric indicates token efficiency.

    $$
    \text{Ratio} = \frac{\text{Total Tokens in Corpus}}{\text{Total Words (Whitespace-separated) in Corpus}}
    $$

    * **Actionable Threshold:** If this ratio for your technical prose is $\mathbf{> 1.25}$, the existing tokenizer is excessively splitting your jargon. **A custom tokenizer is required.**

3.  **Code Snippet (Python):**

    ```python
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained('BAAI/bge-small-en-v1.5')
    text = "The system utilized the novel sub-word tokenization technique."

    # Using the special .tokenize() method for analysis
    tokens = tokenizer.tokenize(text)
    token_count = len(tokens)
    word_count = len(text.split())

    print(f"Tokens: {token_count}, Words: {word_count}")
    
    # Simple ratio check: a high ratio indicates word-splitting on jargon
    token_to_word_ratio = token_count / original_word_count

    print(f"Token-to-Word Ratio: {token_to_word_ratio:.2f}")
    # If the Ratio is high, proceed to train a custom tokenizer.
    ```

### 2.2 Train the Custom Tokenizer (BPE/WordPiece)

If the OOV rate is high, use the `tokenizers` library to train a **Byte Pair Encoding (BPE)** or **WordPiece** tokenizer directly on your corpus.

1.  **Architecture:** Choose a vocabulary size appropriate for your domain (e.g., 30k to 50k).

2.  **Tooling:** Use the **Hugging Face `tokenizers`** library for industrial-grade, fast training.

      * **Pitfall Warning:** Ensure the custom tokenizer is trained with the **special tokens** ($\texttt{<CLS>}$, $\texttt{<SEP>}$) that your final embedding model expects. Misaligning special tokens will break the model's ability to create sentence-level embeddings.

3.  **Deployment Artifact:** Save the trained tokenizer as a **JSON file**. This file becomes a critical, versioned component of your system.

## 3. Phase II: Embedding Model Fine-Tuning

The most critical step for semantic performance is fine-tuning an existing model's head and weights on your specific data distribution.

### 3.1 Data Formatting for Contextual Learning

Contextual embeddings require comparative data, not just raw text.

1.  **Training Goal:** Teach the model that semantically similar documents should have close vectors.
2.  **Required Format:** You must generate **query-document pairs** or **triplets (Anchor, Positive, Negative)** from your corpus.
3.  **Actionable Strategy (Synthetic Data):** Leverage a capable model (even a cloud one) *strictly* for data generation: feed it chunks of your corpus and prompt it to generate 2-3 plausible questions/queries that document would answer. This is the **most efficient way to create a labeled dataset** for RAG-centric fine-tuning.

### 3.2 Fine-Tuning Execution (PyTorch / Sentence-Transformers)

1.  **Base Model Selection:** Choose a small, efficient pre-trained model (e.g., `all-MiniLM-L6-v2`, `e5-small-v2`).

2.  **Loss Function:** Use a **ranking loss** that optimizes for retrieval:

      * **Triplet Loss:** Ensures $d(\text{Anchor}, \text{Positive}) < d(\text{Anchor}, \text{Negative})$.
      * **Multiple Negatives Ranking Loss (MNRL):** Highly effective for RAG tasks, treating all other examples in the batch as negatives.

3.  **Dimensionality Constraint:** Limit the output dimension to **384 or 512** for a 4B-14B local LLM system. This minimizes storage and maximizes retrieval speed for vector lookups.

4.  **Actionable Implementation (PyTorch):**

    ```python
    from sentence_transformers import SentenceTransformer, losses
    from torch.utils.data import DataLoader

    # 1. Load an efficient base model
    model = SentenceTransformer('all-MiniLM-L6-v2') 

    # 2. Prepare your labeled data (examples) into a DataLoader
    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=32)

    # 3. Define the critical ranking loss function
    train_loss = losses.MultipleNegativesRankingLoss(model=model)

    # 4. Train
    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=3,  # Keep epochs low to prevent catastrophic forgetting
        warmup_steps=100
    )
    # Save the final, fine-tuned model (weights and configuration)
    model.save('path/to/my_custom_embedding_model')
    ```

## 4. System Deployment and Verification

### 4.1 Deployment Artifacts

The final, versioned system component consists of two integrated parts:

1.  **The Fine-Tuned Model Weights** (e.g., PyTorch `.safetensors` or `.bin` files).
2.  **The Custom Tokenizer Configuration** (The saved JSON file).

### 4.2 Podman Containerization

Package both the model and its custom tokenizer into a single, isolated container for deployment stability.

  * **Instruction:** Ensure the **`Containerfile`** copies the custom tokenizer file *alongside* the model weights and that your Python server code explicitly loads both before starting the FastAPI endpoint.

### 4.3 ISO 29148 Verification Step

Your commitment to quality requires you to verify the semantic improvement.

1.  **Test Set Challenge:** Use the held-out **Test Set** of query-document pairs.
2.  **Run Comparison:** Generate embeddings for the test queries using:
    a.  The **original (un-tuned)** model.
    b.  The **fine-tuned** model.
3.  **Verification Metric:** Calculate the **Mean Reciprocal Rank (MRR)** or **Precision at $K$ (P@1, P@3)**. The fine-tuned model **must** show a measurable, significant improvement in correctly ranking the relevant document closer to the top. This measured performance gain is your verifiable evidence that the custom vocabulary and embedding training were successful.
