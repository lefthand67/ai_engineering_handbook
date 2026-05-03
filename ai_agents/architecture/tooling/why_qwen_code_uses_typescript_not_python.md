
---
title: Why Qwen Code Uses TypeScript, Not Python
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: 2026-04-04
description: Technical rationale for Qwen Code's TypeScript implementation over Python
tags:
- development
- architecture
options:
  type: guide
  birth: 2026-04-04
  version: 1.0.0
  token_size: 1059
---
# Why Qwen Code Uses TypeScript, Not Python

## Implementation Language Decision

**Qwen Code is pure TypeScript** — it uses **Node.js built-in modules** for all file operations:

- `node:fs` / `node:fs/promises` — for `readFile()`, `existsSync()`, `stat()`
- `node:path` — for path resolution
- `node:os` — for temp directory detection

No shell-outs, no `exec`, no `spawn`, no OS tools like `cat`/`head`/`tail`.

---

## Why TypeScript, Not Python?

**1. Inherited from Gemini CLI**

The project explicitly states it's *"based on Google Gemini CLI with adaptations to better support Qwen-Coder models."* Google Gemini CLI was already written in TypeScript. Rewriting it in Python would have been a massive undertaking with little upside.

**2. Node.js is the standard runtime for CLIs in the JS ecosystem**

If you're building a CLI tool in the JavaScript/TypeScript world, Node.js (or Bun/Deno) is the runtime. It ships with built-in modules for filesystem access, process management, streams, etc. — no need for a separate language.

**3. TypeScript gives you compile-time safety for a complex codebase**

This isn't a simple script — it's a full agentic framework with:
- Tool abstractions (`BaseDeclarativeTool`, `BaseToolInvocation`)
- Permission systems
- Session management
- OAuth, MCP, LSP integrations
- React-based terminal UI (via Ink)

TypeScript's type system catches bugs early, which matters when the codebase spans many packages and hundreds of files.

**4. The terminal UI uses Ink (React for CLI)**

Ink lets you build interactive terminal UIs with React components. That's a React/JS ecosystem thing. Python has alternatives (like `textual` or `rich`), but they wouldn't integrate with the existing codebase.

**5. Node.js performance is fine for this use case**

The bottleneck in an agentic CLI isn't the language — it's:
- Network latency (API calls to the LLM)
- Shell execution waiting for external processes
- File I/O

Node.js's event loop actually handles this well. Python would be similar in practice.

**Why not Python?**

Python *is* popular for CLI tools and AI/ML work, but:
- No existing codebase to build on (Gemini CLI is TS)
- Different package ecosystem (pip vs npm)
- Slower cold starts for the CLI launch
- Weaker type system (type hints are optional, not enforced)

In short: **it's TypeScript because the project it forks from was TypeScript, and there was no compelling reason to rewrite it.**

---

## Building Your Own Agent: Python vs TypeScript

You can absolutely write your own agent in Python. In fact, Python is one of the most popular languages for building AI agents.

**Python's strengths for agents:**

- **Rich ecosystem**: LangChain, LangGraph, LlamaIndex, CrewAI, AutoGen, Haystack
- **AI/ML native**: Most LLM SDKs (OpenAI, Anthropic, etc.) are Python-first
- **Data pipelines**: Easier integration with pandas, numpy, scikit-learn, etc.
- **Faster prototyping**: Less boilerplate, quicker to iterate

**When to pick Python vs TypeScript:**

| | Python | TypeScript |
|--|--------|------------|
| **Data/ML-heavy agent** | ✅ Better | — |
| **CLI terminal tool** | Good (Rich, Textual) | ✅ Better (Ink, oclif) |
| **Web-based agent** | Good (FastAPI) | ✅ Better (Next.js, Express) |
| **Team's primary language** | Python team | JS/TS team |

**For your own agent, consider:**

- **What's your team comfortable with?** Use what you already know.
- **Where will it run?** CLI, web service, embedded? Both languages work everywhere, but ecosystems differ.
- **Do you need tight IDE/tooling integration?** TypeScript dominates the editor ecosystem (VS Code extensions, LSP servers are mostly TS).
- **Performance needs?** Both are fine for agent work. The bottleneck is almost always the LLM API call, not the language.

If you're starting from scratch with no existing codebase, Python is a great choice. The reason Qwen Code uses TypeScript is purely inheritance from Gemini CLI, not because TS is objectively better for agents.
