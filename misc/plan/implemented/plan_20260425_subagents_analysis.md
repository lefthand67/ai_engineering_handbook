# Subagents Implementation Analysis Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Conduct a comprehensive architectural and source-code analysis of how "subagents" (child agents, worker agents) are implemented across various agent frameworks in the research directory.

**Architecture:**
The research will follow a structured discovery and deep-dive approach for each repository:
1. **Pattern Discovery**: Use `grep_search` to identify keywords related to agent orchestration (`subagent`, `child_agent`, `worker`, `dispatch`, `orchestrate`, `session_history`).
2. **Trace Analysis**: Identify the entry point of subagent calls and trace the execution flow through the source code.
3. **Governance & Logging**: Locate the code responsible for recording subagent interactions (logs, JSONL files, database entries).
4. **Context Mapping**: Analyze how state, system prompts, and history are isolated or shared between parent and subagents.
5. **Documentation**: Extract code snippets as evidence for every claim.

**Tech Stack:** `grep_search`, `read_file`, `run_shell_command` (for directory exploration).

---

## Research Matrix (Target Repositories)

| Category | Repositories |
| :--- | :--- |
| **Coding Agents** | aider, claude-code-main, gemini-cli, kilocode, openclaude, openclaw, opencode, qwen-code |
| **Infrastructure** | mempalace, open-webui |
| **Skills/Plugins** | claude-code (plugins), skills, superpowers |

---

## Task 1: Discovery & Mapping (All Repos)

**Goal:** Identify which repos actually implement subagents and where the core logic resides.

- [ ] **Step 1: Search for orchestration keywords in `ai_coding_agents/`**
  Run: `grep_search --pattern "subagent|child_agent|worker|dispatch" --path "ai_agents/research/ai_coding_agents/"`
- [ ] **Step 2: Search for orchestration keywords in `ai_infrastructure/`**
  Run: `grep_search --pattern "subagent|child_agent|worker|dispatch" --path "ai_agents/research/ai_infrastructure/"`
- [ ] **Step 3: Search for orchestration keywords in `ai_skills_plugins/`**
  Run: `grep_search --pattern "subagent|child_agent|worker|dispatch" --path "ai_agents/research/ai_skills_plugins/"`
- [ ] **Step 4: Create a "Subagent Map"**
  Document for each repo: `Repo Name` -> `Core Files` -> `Implementation Status (Yes/No/Unknown)`.

---

## Task 2: Analysis of Coding Agents (Part 1: High Profile)

**Target Repos:** `aider`, `claude-code-main`, `qwen-code`

**For each repo:**
- [ ] **Step 1: Analyze Calling Mechanism**
  - Identify the function that instantiates the subagent.
  - Extract code snippet showing the call and parameters.
- [ ] **Step 2: Analyze Context Isolation**
  - Check if the subagent gets a full copy of history or a filtered subset.
  - Extract code snippet of context preparation.
- [ ] **Step 3: Analyze Governance & Logging**
  - Find where the subagent's output is logged.
  - Identify the log format (e.g., `.jsonl`).
  - Extract code snippet of the logging call.
- [ ] **Step 4: Define Architectural Pattern**
  - Classify as: Supervisor, Chain, Peer-to-Peer, etc.

---

## Task 3: Analysis of Coding Agents (Part 2: Others)

**Target Repos:** `gemini-cli`, `kilocode`, `openclaude`, `openclaw`, `opencode`

**For each repo:**
- [ ] **Step 1: Analyze Calling Mechanism** (same as Task 2)
- [ ] **Step 2: Analyze Context Isolation** (same as Task 2)
- [ ] **Step 3: Analyze Governance & Logging** (same as Task 2)
- [ ] **Step 4: Define Architectural Pattern** (same as Task 2)

---

## Task 4: Analysis of AI Infrastructure

**Target Repos:** `mempalace`, `open-webui`

- [ ] **Step 1: Analyze Calling Mechanism**
- [ ] **Step 2: Analyze Context Isolation**
- [ ] **Step 3: Analyze Governance & Logging**
- [ ] **Step 4: Define Architectural Pattern**

---

## Task 5: Analysis of Skills & Plugins

**Target Repos:** `claude-code` (plugins), `skills`, `superpowers`

- [ ] **Step 1: Analyze Calling Mechanism** (specifically how plugins can trigger sub-calls)
- [ ] **Step 2: Analyze Context Isolation**
- [ ] **Step 3: Analyze Governance & Logging**
- [ ] **Step 4: Define Architectural Pattern**

---

## Task 6: Comparative Analysis & Final Report

**Goal:** Synthesize all findings into a final comparative document.

- [ ] **Step 1: Construct Comparison Matrix**
  Columns: Repo Name, Calling Method, Context Strategy, Log Format, Pattern, Complexity.
- [ ] **Step 2: Analyze Common Patterns**
  Identify the most common architectural choices and their pros/cons based on the source code.
- [ ] **Step 3: Final Write-up**
  Produce the final "Subagents Realization Report" with summarized architectural diagrams (in text/markdown) and key code references.

---
