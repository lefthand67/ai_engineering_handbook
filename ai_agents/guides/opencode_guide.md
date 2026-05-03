
---
title: OpenCode Agent Guide
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: 2026-04-26
description: Technical overview and usage guide for the OpenCode AI coding agent
tags:
- agents
- development
options:
  type: guide
  birth: 2026-04-26
  version: 1.0.0
  token_size: 816
---
# OpenCode Agent Guide

OpenCode is an open-source AI coding agent designed to provide a high-performance, provider-agnostic alternative to proprietary coding assistants. It emphasizes terminal-centric workflows, flexibility in model selection, and a robust client-server architecture.

## Core Philosophy

OpenCode is built on the principle that developers should have total control over their AI tooling, including the choice of model and the environment in which the agent executes.

### Key Technical Pillars

- **100% Open Source:** Full transparency of the agent's internal logic and tool-use patterns.
- **Provider Agnostic:** Decouples the agent's orchestration layer from the LLM provider.
- **Client-Server Architecture:** The agent can run as a server (on a powerful workstation or remote VM) while being driven by various clients (TUI, mobile app, etc.).
- **TUI-First UX:** Optimized for terminal users, featuring deep integration with terminal capabilities and a focus on efficiency.

## Model Configuration

One of OpenCode's primary advantages is its flexibility regarding the "brain" of the agent.

### Local Models & BYOK

OpenCode supports multiple integration paths for LLMs:

- **Local Models:** Can be connected to local inference servers (e.g., Ollama, vLLM), ensuring data privacy and eliminating per-token costs.
- **BYOK (Bring Your Own Key):** Supports direct API integration with major providers:
  - Claude (Anthropic)
  - GPT (OpenAI)
  - Gemini (Google)

:::{tip}
Using local models is recommended for highly sensitive codebases where data cannot leave the local network.
:::

## Agent Modes

OpenCode implements specialized modes to manage the balance between autonomy and safety.

- **`build` Agent:** The default mode. Has full access to the filesystem and shell to perform active development, refactoring, and testing.
- **`plan` Agent:** A read-only mode designed for codebase exploration and architectural analysis. It denies file edits by default and requires explicit permission for bash commands.
- **`general` Subagent:** Invoked via `@general`, this agent handles complex, multi-step research tasks and deep searches that would otherwise clutter the primary conversation context.

## OpenCode vs. Qwen Code

Both OpenCode and Qwen Code provide professional-grade AI coding capabilities, supporting a wide range of LLMs (including local models and BYOK) and offering high-efficiency terminal-based interfaces.

| Feature | OpenCode | Qwen Code |
| :--- | :--- | :--- |
| **Licensing** | Open Source | Proprietary |
| **Model Support** | Provider Agnostic (Local/BYOK) | Provider Agnostic (Local/BYOK) |
| **UX / Interface** | Terminal-centric (TUI/CLI) | Terminal-centric (TUI/CLI) |
| **Architecture** | Client-Server / Local | Client-Server / Local |

## Selection Criteria: Which one to use?

Since both agents share a similar feature set regarding model flexibility and user experience, the choice primarily depends on licensing and ecosystem preferences:

### Choose OpenCode if:
- You require an **open-source toolchain** that you can audit, fork, or contribute to.
- You prefer a tool developed within the open-source community.

### Choose Qwen Code if:
- You prefer the **official implementation** and optimizations provided by the Qwen team.
- You are looking for a tool with deep integration into the Alibaba/Qwen ecosystem.
