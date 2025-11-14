# LLM Usage Patterns: Chats, Workflows, and Agents in AI

Part I of "LLM Usage Patterns" Series. Chat, Workflow, Agent: Core Distinctions

[Part II: LLM Usage Patterns: Model Size, Reasoning, and Optimization](/home/commi/Yandex.Disk/it_working/projects/ai/ai_engineering_book/4_orchestration/patterns/llm_usage_patterns_p2.md)

---

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.1.0  
Birth: 19.10.2025  
Modified: 14.11.2025

---

Large Language Models (LLMs) like GPT have transformed how we build AI applications. But to design effective, production-ready AI systems, engineers must understand the **theoretical and practical differences** between three fundamental usage patterns:

* **Chats**
* **Workflows**
* **Agents**

## 1. What is a Chat?

### Theoretical View

A **chat** primarily involves conversational interaction: the AI model responds directly to user inputs with natural language outputs. It focuses on understanding intent and generating coherent, context-aware text.

* Chat is **reactive**: it awaits user input and replies.
* Interaction is typically a **single or multi-turn dialogue**.
* Behavior is driven by **prompt engineering** and context history management.

### Practical Implementation

* Usually implemented as a single LLM call wrapped with minimal conversational context management (history, token limits).
* **Operational Footprint:** **Low Latency** and **Low Cost** per query.

**Example:** A customer support chatbot answering product FAQs.

## 2. What is a Workflow?

### Theoretical View

Workflows use LLMs as components within a **predefined, structured pipeline** of AI and non-AI tasks.

* Consists of **sequential or conditional steps**.
* Each step solves a **specific subtask**, like classification, summarization, or data extraction.
* The process is **deterministic and scripted** by human engineers.

> **Note on Determinism:** While workflows may include conditional branching and error handling that appear dynamic, their decision logic is entirely scripted by human engineers. This means workflows are **deterministic** and lack genuine autonomy — they do not adapt or revise their sequence of steps based on situational understanding beyond predefined, hard-coded rules.

### Practical Implementation

* Implemented as **Python scripts or orchestrated pipelines** (e.g., using frameworks like LangChain Pipelines).
* Requires management of inputs/outputs between steps, error checking, and optional fallback mechanisms.
* **Operational Footprint:** **Moderate Latency** and **Moderate Cost** due to multiple sequential LLM calls.

**Example:** A resume screening system that extracts skills, scores relevance, then generates a summary report.

## 3. What is an Agent?

### Theoretical View

Agents are **autonomous AI systems** that perceive environment inputs, plan actions, dynamically select and execute tasks, and adapt based on context and feedback.

The agent's power comes from integrating **LLM reasoning with external tool/API invocation**. It has dynamic **decision-making capabilities**, choosing the *next* step based on the *result* (observation) of the *previous* step, enabling **iterative self-correction and feedback loops**.

In sophisticated agent architectures, the **planner-executor model** is crucial: the LLM (planner) generates the next high-level decision, and the executor system performs the specific action (tool/API call) and reports the observation back to the LLM for the next planning cycle. This enables true self-direction beyond scripted automation.

### Practical Implementation

* Implemented as complex, iterative software architectures integrating LLMs with external APIs, databases, and tools.
* Requires robust **control flow logic**, state management, and tool parsing.
* **Operational Footprint:** **High Latency** and **High Cost** due to the iterative nature of the decision loop, high token usage for history/reflection, and multiple sequential API calls.

**Example:** A virtual assistant that plans a trip by querying weather, dynamically booking flights based on availability, and updating the itinerary as new information arrives.

## 4. Key Differences Summary

| Aspect | Chat | Workflow | Agent |
| :--- | :--- | :--- | :--- |
| **Purpose** | Human-like conversation | Structured multi-step tasks | **Autonomous task planning & execution** |
| **Architecture** | Single LLM interaction | Fixed pipeline of modular steps | **Dynamic, iterative control loop** with tools & APIs |
| **Autonomy** | Low; reactive | Medium; scripted process (deterministic) | **High; adaptive and self-directed** (non-deterministic sequence) |
| **Complexity** | Simple | Moderate | **High** |
| **Operational Cost** | Low | Moderate | **High** (Token/Latency) |

## 5. Practical Tips for AI Engineers 🛠️

* **Start with chats** if your need is straightforward conversational AI.
* **Use workflows** for automating well-defined multi-step AI tasks where the execution sequence is known and can be specified in advance.
* **Build agents** when your system needs to autonomously plan, choose tools, and adapt its execution path based on intermediate results and complex context.
* **Operational Constraint:** Remember that complexity scales with operational cost and latency. **Agents** are the most flexible but typically incur the highest latency and token consumption due to iterative self-reflection and decision-making calls.
* **Production Agents:** Advanced agents designed for production require strong evaluation, guardrails (like sandboxed tool execution), and robust observability mechanisms, including human-in-the-loop checkpoints, to ensure safety, correctness, and compliance in autonomous decision-making. 

## 6. Example Code Skeletons

### Chat (Python + Prompt)

```python
user_input = "What are the benefits of solar energy?"
prompt = f"Answer in a friendly tone: {user_input}"
response = llm.call(prompt)
print(response)
```

### Workflow (Chained Steps)

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

### Agent (Iterative Decision + Tool Invocation)

This architecture demonstrates the iterative nature where the LLM is called repeatedly to make the next decision based on the current state and observed results.

```python
class Agent:
    def __init__(self, tools):
        self.tools = tools

    def act(self, user_input, max_steps=5):
        current_state = {'task': user_input, 'history': []}

        for step_count in range(max_steps):
            # 1. LLM plans the NEXT action based on the *current state*
            decision = llm.call(f"Based on history {current_state['history']}, what is the best next action for task: {user_input}?")
            
            tool_name, args = parse_decision(decision) # Hypothetical function to parse tool choice

            if tool_name == "FINISH":
                print("Task complete.")
                return current_state.get('result', "Success.")

            if tool_name in self.tools:
                # 2. Execute the action (Tool invocation)
                result = self.tools[tool_name](args)
                
                # 3. Update state with the observation/result for the next loop
                current_state['history'].append({'action': tool_name, 'observation': result})
            else:
                return f"Error: Invalid tool {tool_name} used."
        
        return "Max steps reached without finishing the task."

# Hypothetical usage
agent = Agent(tools={'weather_api': get_weather, 'email': send_email})
agent.act("Schedule outdoor event next week")
```
