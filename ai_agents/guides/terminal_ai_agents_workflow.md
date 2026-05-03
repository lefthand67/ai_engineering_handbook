---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.1
kernelspec:
  name: python3
  display_name: Python 3 (ipykernel)
  language: python
---

---
title: Terminal AI Agents Workflow
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: '2026-05-02'
description: A guide to the hybrid development workflow combining editor plugins and
  CLI agents for maximum efficiency.
tags:
- agents
- workflow
- development
options:
  type: guide
  birth: '2026-01-01'
  version: 1.0.0
  token_size: 1076
---
# Terminal AI Agents Workflow

+++

The best way to work with AI tools in your development workflow is by adopting a hybrid strategy: use **editor plugins** for rapid, in-buffer tasks (like completion and single-file edits) and **CLI agents** for agentic, multi-file refactoring that leverages the power and stability of the terminal.

This guide covers the general philosophy and workflow patterns. For setup instructions and tool-specific guides, see the cross-references below.

+++

## **1. Our Tool Stack**

+++

| Category | Tools | Core Function | Best For |
| :--- | :--- | :--- | :--- |
| **Vim Plugin** | `vim-ollama` | **In-buffer completion, chat, single-file edits.** | Lowest latency, inline code completion, quick refactoring. |
| **CLI Agent** | Aider, Qwen Code, Claude Code | **Multi-file refactoring & committing.** Reads Git context and makes atomic changes. | Complex refactors, generating new files, fixing tests across the codebase. |

+++

## **2. General Workflow Patterns**

+++

### Pattern 1: In-Editor Quick Edit (Vim Plugin)

+++

1.  **Select Code:** Use **`V`** or **`v`** to select the code block to refactor.
2.  **Ask Plugin:** Trigger the plugin's edit/chat command.
3.  **Prompt:** Type your instruction (e.g., "Rewrite using list comprehension").
4.  **Diff Review:** The plugin shows proposed changes. Accept or reject line-by-line.

This pattern is the lowest-latency way to do single-file edits. It works in Vim with `vim-ollama` or any editor with an AI plugin.

+++

### Pattern 2: Multi-File Feature Implementation (CLI Agent)

+++

1.  **Open Terminal:** Use a terminal session (standalone or split in your editor).
2.  **Start Agent:** Launch your CLI agent (e.g., `aider --model ollama_chat/qwen2.5-coder:14B`).
3.  **Add Files:** Tell the agent what to work on (e.g., `/add main.py utils.py tests/test_utils.py`).
4.  **Prompt:** Give a high-level instruction spanning multiple files.
5.  **Reload & Review:** The agent modifies files on disk. Your editor detects changes and prompts you to reload buffers. Review the diff.

This pattern applies to Aider, Qwen Code, Claude Code, and similar CLI-based agents.

+++

### Pattern 3: Hybrid Mode (Cloud + Local)

+++

For large-context planning tasks, use a capable cloud LLM (Gemini, Grok) via API as the architect model, while a local SLM handles execution:

- **Architect mode:** Cloud LLM for high-level planning and design
- **Editor model:** Local SLM for coding, testing, and fixing

:::{seealso}
> - [Connect to Cloud LLMs via API](/ai_agents/guides/connect_to_capable_llms_api_keys.ipynb) — API key setup and model orchestration
> - [Aider Commands Handout](/ai_agents/guides/aider/aider_commands_handout.ipynb) — CLI agent reference
:::

+++

## **3. Tool-Specific Guides**

+++

- [vim-ollama Plugin Setup](/ai_agents/guides/vim_ollama/vim_ollama_plugin_setup.ipynb) — Vim installation, key mappings, troubleshooting
- [Aider Commands Handout](/ai_agents/guides/aider/aider_commands_handout.ipynb) — CLI agent setup, commands, proxy configuration
- [Claude Code Memory](/ai_agents/guides/claude/claude_code_memory_vs_claude_md.md) — Claude Code project memory and `.claude/` conventions
- [Kilo Code CLI Setup](/ai_agents/guides/kilocode/kilocode_cli_setup.ipynb) — Kilo Code installation and configuration
- [Connect to Cloud LLMs via API](/ai_agents/guides/connect_to_capable_llms_api_keys.ipynb) — API keys, free-tier limits, data privacy
