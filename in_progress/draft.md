

### **Reference List: Provenance of Techniques**

This section is crucial. It moves our practices from being "things that seem to work" to "disciplined engineering applications of published concepts."

| Concept / Technique | Origin & Formalization | Core Paper / Resource | Key Authors | Why We Use It |
| :--- | :--- | :--- | :--- | :--- |
| **Schema-Guided Reasoning (SGR)** | A formalization of structured output techniques for LLM agents, emphasizing transparency and control. | [Schema-Guided Reasoning (SGR) for LLM Agents](https://abdullin.com/schema-guided-reasoning/) (Blog Post) | Rinat Abdullin | To enforce a deterministic, predictable, and loggable output structure from LLMs, making them suitable for production systems. |
| **Chain-of-Thought (CoT)** | A technique to improve reasoning by forcing the LLM to generate intermediate steps. | [Chain-of-Thought Prompting Elicits Reasoning in Large Language Models](https://arxiv.org/abs/2201.11903) | Wei et al. (Google Research) | To break down complex tasks (like requirements elicitation) into smaller, more reliable steps, improving final answer accuracy. |
| **ReAct (Reason + Act)** | A paradigm that synergizes reasoning (generating verbal chains of thought) and acting (taking actions like calling a tool). | [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629) | Yao et al. (Princeton/Google) | To provide a framework for our multi-step agentic workflows, where the LLM must reason about the user's input before "acting" (outputting structured data). |
| **Function Calling / Tool Use** | The native protocol for LLMs to request execution of defined functions. | [OpenAI Function Calling Documentation](https://platform.openai.com/docs/guides/function-calling) | OpenAI | This is the target protocol for mature models. Our structured YAML output is a form of "tool call" that we standardize. We aim to be compatible with this native, trained behavior. |
| **Gherkin Language** | A business-readable, structured language for defining test cases. | [Cucumber BDD Documentation](https://cucumber.io/docs/gherkin/) | - | An industry standard for defining unambiguous, testable acceptance criteria. Its `Given/When/Then` structure is perfectly suited for LLM generation. |
| **MoSCoW Method** | A prioritization technique used in business analysis and agile project management. | [DSDM AgilePF Framework](https://www.agilebusiness.org/page/ProjectFramework_09_MoSCoWPrioritisation) | - | An industry-standard, well-understood framework for prioritizing requirements, providing clear context to the LLM and stakeholders. |
| **Boundary Priming (XML-tags)** | A prompt engineering technique for robustly separating instructions from data. | [MITRE ATLAS (Adversarial Threat Landscape for AI Systems)](https://atlas.mitre.org/techniques/AML.T0015/) | MITRE | To prevent prompt injection and ensure user-provided data is treated as data, not executable instruction, thereby increasing system security and reliability. |

This reference list provides the foundational knowledge. The following sections detail how we apply these concepts.

---

### **1. Core Principle: Separation of Concerns**

We apply the classic software engineering principle to LLM interactions: separate the **instruction** (the prompt) from the **data** (the input) and the **output** (the deliverable). Use the right format for the right job to maximize clarity for the LLM, leveraging the referenced techniques.

*   **Prompt Formatting:** Use **Markdown** and **XML-like tags** for clarity and robustness (**Boundary Priming**).
*   **Process:** Use **Chain-of-Thought (CoT)** and **ReAct** to design multi-step workflows.
*   **Input/Output Data:** Use structured serialization formats like **YAML** or **JSON** (**Schema-Guided Reasoning**).

