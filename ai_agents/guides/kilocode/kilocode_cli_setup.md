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
title: 'Kilo Code CLI: Installation and Setup'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: "2026-05-02"
description: Installation and configuration guide for Kilo Code CLI, including proxy
  setup and authentication.
tags:
- agents
- development
options:
  type: guide
  birth: "2026-03-01"
  version: "1.0.0"
  token_size: 1775
---
# Kilo Code CLI: Installation and Setup

+++

Kilo Code CLI is a terminal-based AI coding agent from [kilo.ai](https://kilo.ai). It connects to the **Kilo platform gateway**, which proxies 500+ cloud models (including free-tier ones). It supports interactive TUI sessions, one-off task runs, and MCP server integration.

:::{warning}
**This tool contradicts the hybrid LLM+SLM philosophy of this book.**

This book is built around the principle that local SLMs are first-class citizens: model selection is driven by capability (reasoning-class vs. agentic-class), not by vendor availability. Kilo Code CLI inverts this — it routes all traffic through the Kilo platform gateway (`api.kilo.ai`), requires account registration even for "free" models, and has no support for local Ollama models or direct API keys. Every inference call passes through a proprietary intermediary you do not control.

For terminal-based agentic coding aligned with this book's philosophy, use [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (cloud, direct API) or [aider](https://aider.chat) with `--model ollama/...` (local SLMs, no gateway).

This guide is kept as a reference and cautionary example.
:::

+++

:::{important}
**Kilo Code CLI ≠ Kilo Code VS Code Extension.**

The CLI (`@kilocode/cli` npm package) routes all model traffic through the Kilo platform gateway. It does **not** support local Ollama models or direct BYOK API keys to third-party providers (Anthropic, Google, DashScope, etc.). The VS Code extension (a Roo Code/Cline fork) supports those features — the CLI does not.
:::

+++

## **1. Install Kilo Code CLI**

+++

### Prerequisites

+++

Make sure Node.js 18+ is installed:

```bash
node --version
npm --version
```

+++

### Install via npm (user-local, no sudo)

+++

Installing to `~/.local` avoids permission issues on Fedora/Linux systems where `/usr/local/lib` is root-owned:

```bash
npm install -g @kilocode/cli --prefix ~/.local
```

+++

:::{note}
**Behind a corporate/Squid proxy?**
npm does not automatically pick up `HTTPS_PROXY` from the environment. Pass it explicitly:
```bash
npm install -g @kilocode/cli --prefix ~/.local \
  --proxy http://<username>:<password>@<proxy-host>:<port>
```
Or set it permanently so you never need the flag again:
```bash
npm config set proxy http://<username>:<password>@<proxy-host>:<port>
npm config set https-proxy http://<username>:<password>@<proxy-host>:<port>
```
Replace `<username>`, `<password>`, `<proxy-host>`, `<port>` with your actual proxy credentials.
:::

+++

### Add `~/.local/bin` to PATH

+++

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc
```

Verify:

```bash
kilo --version
```

+++

## **2. Authenticate with Kilo Platform**

+++

Kilo CLI requires a Kilo account to use any model — including free-tier ones. Log in via browser OAuth:

```bash
kilo auth login
```

This opens a browser-based OAuth flow. Credentials are stored in `~/.local/share/kilo/auth.json`.

```bash
kilo auth list    # show stored credentials
kilo auth logout  # log out
```

+++

## **3. Launch Kilo Code**

+++

### Interactive TUI (default)

+++

Navigate to your project directory and run:

```bash
cd /path/to/my/project
kilo
```

This opens the full terminal UI where you can chat with the agent, approve file edits, and run shell commands interactively.

+++

### One-off task (non-interactive)

+++

```bash
kilo run "add input validation to the signup form"
```

+++

### Key CLI flags

+++

| Flag | Description |
| :--- | :--- |
| `-m kilo/<model>` | Set the model (must be a valid Kilo model ID) |
| `-c` | Continue the last session |
| `-s <session-id>` | Resume a specific session |
| `--prompt "<text>"` | Pass an initial prompt non-interactively |

+++

## **4. Available Models**

+++

Kilo routes traffic through its gateway, which aggregates models from OpenRouter, Anthropic, Google, and others. Some models are free, others require Kilo credits.

List all available models:

```bash
kilo models            # list all model IDs
kilo models --verbose  # include cost and context window metadata
```

### Free-tier models (as of March 2026)

+++

| Model ID | Notes |
| :--- | :--- |
| `kilo/kilo-auto/free` | Auto-selected free model |
| `kilo/openrouter/free` | OpenRouter free tier proxy |
| `kilo/arcee-ai/trinity-large-preview:free` | 400B MoE, 128k context, good for agentic tasks |
| `kilo/minimax/minimax-m2.5:free` | Balanced capability |
| `kilo/x-ai/grok-code-fast-1:optimized:free` | Fast, code-focused |
| `kilo/stepfun/step-3.5-flash:free` | Lightweight, fast |

Launch with a specific model:

```bash
kilo -m kilo/arcee-ai/trinity-large-preview:free
```

+++

:::{note}
Free-tier model availability can change. Run `kilo models` to see the current list — model IDs ending in `:free` have zero cost.
:::

+++

## **5. Useful Commands Reference**

+++

```bash
kilo                        # launch interactive TUI
kilo run "<task>"           # run a one-off task
kilo models                 # list all available models
kilo models --verbose       # list with cost and context metadata
kilo session list           # list past sessions
kilo export <session-id>    # export session as JSON
kilo auth login             # log in to Kilo platform
kilo auth list              # show stored credentials
kilo auth logout            # log out
kilo mcp                    # manage MCP (Model Context Protocol) servers
kilo upgrade                # upgrade to the latest version
kilo stats                  # show token usage and cost statistics
kilo uninstall              # uninstall kilo and remove config files
```

+++

## **6. Uninstall**

+++

Kilo's built-in uninstall command removes the binary, config, and local data:

```bash
kilo uninstall
```

Then remove the npm package:

```bash
npm uninstall -g @kilocode/cli --prefix ~/.local
```

Remove leftover data directories:

```bash
rm -rf ~/.local/share/kilo
```

Verify nothing remains:

```bash
which kilo    # should return nothing
```

+++

:::{seealso}
- [Kilo Code GitHub](https://github.com/Kilo-Org/kilocode)
- [Kilo Code Documentation](https://kilo.ai/docs)
- [Kilo Code Getting Started](https://kilo.ai/docs/getting-started)
:::
