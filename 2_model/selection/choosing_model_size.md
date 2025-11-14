# Choosing Model Size for Chats, Workflows, and Agents: Model Size, Reasoning, and Optimization

See also: 
- [LLM Usage Patterns: Chats, Workflows, and Agents in AI](./4_orchestration/patterns/llm_usage_patterns.md)

---

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.1.1  
Birth: 19.10.2025  
Modified: 15.11.2025

---

The size of the Large Language Model (LLM) affects its performance, resource requirements, and suitability for specific applications. Larger models offer deeper understanding, better reasoning, and more nuanced outputs—at the cost of increased inference compute, memory, and latency.

## 1. Chats: Small to Medium Models (1B to 7B–13B parameters)

- **Use Case**: Interactive conversations, simple question answering, FAQs, and light creative tasks where **latency is paramount**.
- **Recommended Sizes**:
    - Small models (1B, 3B parameters) work well on mobile and edge devices for fast, low-latency chat.
    - Medium models (7B to 13B) strike a good balance for general-purpose chatbots, offering conversational fluidity and context retention.
- **Why**: Chats prioritize **low latency**. Smaller, highly-optimized models are selected to maximize inference speed and minimize the expensive compute required to maintain a fast conversational flow. These models are often deployed using aggressive **quantization** (e.g., 4-bit) to reduce memory and speed up computation.

## 2. Workflows: Medium to Large Models (7B to 33B+ parameters)

- **Use Case**: Multi-step processes requiring summarization, classification, or generation of structured outputs within predefined pipelines.
- **Recommended Sizes**:
    - 7B models suffice for many text extraction and simple workflow steps.
    - Larger models (13B to 33B) are preferred for more nuanced or multi-domain workflows needing better comprehension or specialized tasks.
- **Why**: Workflows require stronger and more accurate inference over defined steps. Task modularity allows resource allocation focused at critical points, enabling the selective use of larger, specialized models where comprehension is essential.

### 3. Agents: Large to Extra Large Models (13B+ to 70B+ parameters)

- **Use Case**: Autonomous systems requiring planning, dynamic tool invocation, contextual adaptation, and complex multi-turn decision making.
- **Recommended Sizes**:
    - Large models starting at 13B+ parameters for richer reasoning and multi-tool handling.
    - Models 70B+ or even larger are necessary for highly specialized contexts, deeper contextual awareness, and high reliability.
- **Why**: Agents need high capacity for dynamic decision-making, flexible behavior, and, critically, processing the large **token consumption** resulting from iterative self-correction, reflection, and maintaining conversation/action history. This process benefits most from the superior, emergent reasoning capabilities of large models.

## 4. The Role of Schema-Guided Reasoning (SGR)

Schema-Guided Reasoning (SGR) does not contradict the described principles; rather, it represents an advanced **mitigation technique** that allows engineers to push the boundaries of smaller models in complex Agentic and Workflow systems. 

SGR and related techniques (like constrained decoding) act as **scaffolding** for LLMs, effectively enhancing the reasoning of smaller models in Agentic systems without resorting to the largest parameter counts.

SGR works by:

1.  **Enforcing Reasoning Structure:** The process translates a domain expert's mental checklist or required logical flow into a rigid, enforced JSON schema (or similar structured output format).
2.  **Constrained Decoding:** The LLM is forced to generate output that adheres strictly to this schema, step-by-step.
3.  **Microprompting:** The schema itself contains meaningful field names, descriptions, and cascades, which act as **microprompts** at the moment of generation, guiding the model's attention and thinking process toward the next logical step.

### SGR's Impact on Model Size Conclusions

| SGR Goal | Impact on Model Size | Outcome |
| :--- | :--- | :--- |
| **Tool Selection** | Reduces ambiguity in decision-making. | **7B–13B models** can reliably select the correct tool and parameters from a set of 10+ options, a task that often requires a 33B+ model without SGR constraints. |
| **Iterative Planning**| Constrains the planning space. | Instead of generating a long, potentially flawed chain-of-thought, the model generates only the **next immediate action** as dictated by the schema. This reduces the cognitive load and token count needed per planning step. |
| **Accuracy** | Improves output reliability and consistency. | SGR can boost the accuracy and auditability of smaller models, making them acceptable for production environments where consistency is paramount (e.g., compliance or finance). |

### Refined Agent Recommendation (Hybrid Approach)

For engineers, this means that the core recommendation holds, but with a powerful footnote:

> **Recommendation Refined:** While Agents requiring true, unconstrained, general-purpose reasoning still need large models (33B+), most production Agents focus on a defined set of tools and logic. By leveraging **Schema-Guided Reasoning** and **Hybrid Architectures**, engineers can successfully deploy **Medium Models (13B)** as the core decision-maker in highly reliable agentic systems, drastically reducing latency and operational costs compared to using 70B+ models.

## 5. Practical Resource Considerations

This table provides a comprehensive overview, matching the conceptual complexity of the three usage patterns (Chat, Workflow, Agent) to tangible engineering considerations like hardware and application scope.

| Model Size | Parameters (B) | Typical Hardware Requirements (4-bit Inference) | Suitable For | Example Use Cases |
| :--- | :--- | :--- | :--- | :--- |
| **Small** | 1B–3B | ~8 GB RAM, low compute, edge/mobile platforms | Lightweight chat, quick responses, local processing | **On-device** search enhancements (Ctrl+F), basic prompt filtering/routing, real-time code completion in IDEs, local function calling for simple tasks. |
| **Medium** | 7B–13B | 16–32 GB RAM (VRAM), consumer GPUs | General chat, most workflows, **SGR-enhanced Agents** | **Customer service** chatbots (RAG-powered), document summarization, complex software development tasks (local-only), personal data analysis, internal knowledge base assistants. |
| **Large** | 33B+ | 64+ GB RAM (VRAM), powerful GPUs or cloud infrastructure | Complex workflows, **Unconstrained Agents** | Multi-step **agentic workflows** (e.g., automated market research or lead generation), deep data analytics across disparate systems (SQL, NoSQL, docs), advanced creative writing and reasoning engines. |
| **Extra Large** | 70B+ | 72+ GB RAM (VRAM), high-end GPUs, distributed systems | Advanced agents, high autonomy/generality | High-fidelity translation, **domain-expert consulting agents** (e.g., legal or financial compliance), fundamental research modeling, building highly autonomous enterprise systems. |

## Final Model Size Advice

- Start with the smallest model that meets your performance needs to conserve compute and cost.
- Monitor accuracy and response quality; scale model sizes up if deeper comprehension or decision-making is required.
- For highly autonomous agents, allocate infrastructure for very large models or ensemble approaches.

**Architectural Best Practice:**

Consider a **Hybrid Architecture** where a smaller, highly efficient model (e.g., 3B or 7B) acts as a **router** or **controller**. This smaller model's task is limited to rapid classification (e.g., intent classification or tool selection), which then directs traffic to the appropriate large model or workflow. This pattern significantly optimizes resource allocation, maintaining low latency for routing while allocating high compute only for complex tasks.

This nuanced understanding prepares engineers to match AI model size to application method, balancing capability, latency, and cost efficiently.

## Summary

Understanding chats, workflows, and agents helps you

- Choose the right AI architecture
- Build scalable and maintainable AI systems
- Leverage LLMs effectively combined with Python control
