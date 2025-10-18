# LLM usage patterns: Chats, Workflows, and Agents in AI

---

Владелец: Вадим Рудаков, lefthand67@gmail.com  
Версия: 0.1.0

---

Large Language Models (LLMs) like GPT have transformed how we build AI applications. But to design effective AI systems, engineers must understand the **theoretical and practical differences** between three fundamental usage patterns:

- **Chats**
- **Workflows**
- **Agents**

This tutorial unpacks these concepts clearly and practically, empowering you to choose the right architecture for your next AI project.

## I. Chat, Workflow, Agent

### 1. What is a Chat?

#### Theoretical View
A **chat** primarily involves conversational interaction: the AI model responds directly to user inputs with natural language outputs. It focuses on understanding intent and generating coherent, context-aware text.

- Chat is **reactive**: awaits user input and replies.
- Interaction is typically **single or multi-turn dialogue**.
- Behavior driven by **prompt engineering**.

#### Practical Implementation
- Usually implemented as a single LLM call wrapped with some conversational context management.
- Can be embedded in chatbots, customer support, or assistant interfaces.
- Python code mainly manages prompt histories and token limits.

**Example:** A customer support chatbot answering product questions.

### 2. What is a Workflow?

#### Theoretical View
Workflows use LLMs as components within a **predefined, structured pipeline** of AI and non-AI tasks.

- Consists of **sequential or conditional steps**.
- Each step solves a **specific subtask**, like classification, summarization, or data extraction.
- The process is **deterministic and scripted** by human engineers.

> **Note:** While workflows may include conditional branching and error handling that appear dynamic, their decision logic is entirely scripted by human engineers. This means workflows are deterministic and lack genuine autonomy — they do not adapt or revise plans based on situational understanding beyond predefined rules.

#### Practical Implementation
- Implemented as **Python scripts or orchestrated pipelines**.
- Uses frameworks like LangChain Pipelines, or custom code chaining multiple LLM calls.
- Handles inputs/outputs between steps, error checking, and optional fallback.

**Example:** A resume screening system that extracts skills, scores relevance, then generates a summary report.

### 3. What is an Agent?

#### Theoretical View
Agents are **autonomous AI systems** that perceive environment inputs, plan actions, dynamically select and execute tasks, and adapt based on context.

The term "agent" encompasses a variety of AI architectures. In modern frameworks, agents typically consist of a planner-executor model, where reasoning about next actions is distinct from actual tool invocation and execution. This separation helps realize truly autonomous, adaptive systems beyond simple scripted automation.

- Combines **LLM reasoning with tool/to API invocation**.
- Has **decision-making capabilities**: choosing next steps based on intermediate results.
- Supports **iterative self-correction and feedback loops**.

In sophisticated agent architectures, the reasoning and control layers are often separated. The planner component, typically an LLM, generates the high-level decision-making plan based on goals and context. Meanwhile, the executor system performs specific actions — invoking APIs, managing tools, and maintaining state — following the planner's instructions. This modularity enhances flexibility and robustness.

#### Practical Implementation
- Implemented as complex software architectures integrating LLMs with external APIs, databases, and tools.
- Uses control flow logic alongside model calls.
- Examples: LangChain Agents, OpenAI function-calling agents, multi-agent systems.

**Example:** A virtual assistant that plans a trip by querying weather, booking flights, and updating itinerary dynamically.

### Key Differences Summary

| Aspect            | Chat                   | Workflow                                  | Agent                                    |
|-------------------|------------------------|-------------------------------------------|------------------------------------------|
| **Purpose**        | Human-like conversation | Structured multi-step tasks                | Autonomous task planning & execution     |
| **Architecture**   | Single LLM interaction  | Fixed pipeline of modular steps            | Dynamic control flow with tools & APIs   |
| **Autonomy**       | Low; reactive           | Medium; scripted process                    | High; adaptive and self-directed          |
| **Complexity**     | Simple                  | Moderate                                   | High                                     |
| **Examples**       | FAQ bot                 | Document summarization pipeline            | AI assistant booking trips                |

### Practical Tips for AI Engineers

- **Start with chats** if your need is straightforward conversational AI.
- **Use workflows** for automating well-defined multi-step AI tasks where you can specify the sequence.
- **Build agents** when your system needs to autonomously plan, choose tools, and adapt based on complex contexts.
- Python and prompt engineering are the foundation for all three, but agent design requires handling **tool integration, decision logic, and state management**.
- Frameworks like **LangChain** help accelerate workflows and agents by providing reusable components.
- Advanced agents designed for production environments require strong evaluation and observability mechanisms. These include feedback loops for continuous learning, guardrails like sandboxed tool execution, and optionally human-in-the-loop checkpoints to ensure safety, correctness, and compliance in autonomous decision-making.

### Example Code Skeletons

#### Chat (Python + Prompt)
```python
user_input = "What are the benefits of solar energy?"
prompt = f"Answer in a friendly tone: {user_input}"
response = llm.call(prompt)
print(response)
```

#### Workflow (Chained Steps)
```python
def extract_topics(text):
    return llm.call(f"Extract main topics from: {text}")

def summarize(topics):
    return llm.call(f"Write a summary based on: {topics}")

business_question = "Explain renewable energy trends."
topics = extract_topics(business_question)
summary = summarize(topics)
print(summary)
```

#### Agent (Decision + Tool Invocation)
```python
class Agent:
    def __init__(self, tools):
        self.tools = tools

    def act(self, user_input):
        plan = llm.call(f"Plan best action for: {user_input}")
        for step in plan:
            if step == "weather_check":
                result = self.tools['weather_api'](user_input)
            elif step == "send_email":
                result = self.tools['email'](user_input)
            # adapt based on results
        return result

agent = Agent(tools={'weather_api': get_weather, 'email': send_email})
agent.act("Schedule outdoor event next week")
```

***

## II. Choosing Model Size for Chats, Workflows, and Agents

The size of the Large Language Model (LLM) affects its performance, resource requirements, and suitability for specific applications. Model sizes are generally measured in billions of parameters (B), where larger models tend to offer deeper understanding, better reasoning, and more nuanced outputs — at the cost of more inference compute, memory, and storage.

### 1. Chats: Small to Medium Models (1B to 7B–13B parameters)

- **Use Case**: Interactive conversations, simple question answering, FAQs, and light creative tasks.
- **Recommended Sizes**: 
  - Small models (1B, 3B parameters) work well on mobile and edge devices for fast, low-latency chat.
  - Medium models (7B to 13B) strike a good balance for general-purpose chatbots offering conversational fluidity and context retention.
- **Why**: Chats rarely require complex reasoning or heavy multitasking, so smaller, efficient models are preferable to provide responsiveness without expensive infrastructure.
- **Examples include**: 7B-parameter models running locally or cloud-hosted chatbot APIs.

### 2. Workflows: Medium to Large Models (7B to 33B+ parameters)

- **Use Case**: Multi-step processes requiring summarization, classification, or generation of structured outputs within predefined pipelines.
- **Recommended Sizes**:
  - 7B models suffice for many text extraction and simple workflow steps.
  - Larger models (13B to 33B) are preferred for more nuanced or multi-domain workflows needing better comprehension or specialized tasks.
- **Why**: Workflows often require more accurate and deeper understanding but task modularity allows resource allocation focused at critical points, enabling larger models selectively.
- **Examples**: Multi-step document processing, automated report generation, or data transformation pipelines.

### 3. Agents: Large to Extra Large Models (13B+ to 70B+ parameters)

- **Use Case**: Autonomous systems requiring planning, dynamic tool invocation, contextual adaptation, and multi-turn complex decision making.
- **Recommended Sizes**:
  - Large models starting at 13B+ parameters for richer reasoning and multi-modal inputs.
  - Models 70B+ or even larger are necessary for advanced contexts, deeper contextual awareness, and high reliability.
- **Why**: Agents need high capacity for decision-making, learning from iterative feedback, and flexible behavior across many domains, benefiting from the greater size and complexity.
- **Examples**: Virtual AI assistants orchestrating APIs, autonomous research assistants, or multi-agent systems interacting with diverse external tools.

### Practical Resource Considerations

| Model Size | Parameters (B) | Typical Hardware Requirements                 | Suitable For                       |
|------------|----------------|------------------------------------------------|----------------------------------|
| Small      | 1B–3B          | ~8 GB RAM, low compute, edge/mobile platforms  | Lightweight chat, quick responses|
| Medium     | 7B–13B         | 16–32 GB RAM, consumer GPUs                     | General chat, most workflows     |
| Large      | 33B+           | 64+ GB RAM, powerful GPUs or cloud infrastructure | Complex workflows, mid-level agents |
| Extra Large| 70B+           | 72+ GB RAM, high-end GPUs, distributed systems  | Advanced agents, high autonomy   |

### Summary Table: Model Size per AI Method

| AI Method  | Recommended Model Size | Key Reason                       | Example Use Case                          |
|------------|-----------------------|---------------------------------|------------------------------------------|
| Chat       | 1B – 13B              | Fast, efficient interaction     | Mobile chatbot, customer support        |
| Workflow   | 7B – 33B+             | Strong inference over defined steps | Document processing pipelines           |
| Agent      | 13B – 70B+            | Complex reasoning, multi-tool handling | Virtual assistants with dynamic planning|

### Final Model Size Advice

- Start with the smallest model that meets your performance needs to conserve compute and cost.
- Monitor accuracy and response quality; scale model sizes up if deeper comprehension or decision-making is required.
- For highly autonomous agents, allocate infrastructure for very large models or ensemble approaches.
- Use hybrid architectures to combine small models in workflows with large models for strategic decision points.

> **Note:** Smaller or medium-sized models can serve as effective controller or router components within hybrid systems. For example, a small model may determine which larger specialized LLM to invoke or select a particular workflow branch, optimizing compute resources while maintaining responsiveness.

This nuanced understanding prepares engineers to match AI model size to application method, balancing capability, latency, and cost efficiently.

---

## Summary
Understanding chats, workflows, and agents helps you

- Choose the right AI architecture
- Build scalable and maintainable AI systems
- Leverage LLMs effectively combined with Python control
