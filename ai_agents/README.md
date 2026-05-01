# ai_agents — Agent Framework Research & Tooling Guides

This directory consolidates all agent-related content: source-level analysis of external AI coding agents, architecture research, and practical tooling guides.

:::{note}
**Why this is at the repo root:** `ai_system_layers/` is the engine parts catalog (execution → context). Agents are not a layer — they're the assembled product. **ai_system/ is the engine parts catalog. ai_agents/ is the car.** Future agent-level research (multi-agent systems, agent identity, etc.) won't fit the six-layer framework. This directory lives at the root to resolve that category error permanently.
:::

## Structure

```
ai_agents/
├── README.md                  ← this file
├── research/                  ← external cloned repos (nested git)
│   ├── ai_coding_agents/      ← 9 agent source repos for study
│   ├── ai_infrastructure/     ← mempalace, open-webui
│   └── ai_skills_plugins/     ← agent plugins and extensions
├── architecture/              ← source-level analysis of agent internals
│   ├── context_management/    ← context window strategies
│   ├── session_history_management/ ← memory and crash recovery
│   ├── skills/                ← skill/prompt systems
│   └── tooling/               ← tool architectures
└── guides/                    ← practical setup and usage guides
    ├── vim_and_aider/         ← Vim + Ollama + Aider hybrid setup
    ├── aider/                 ← Aider commands handout, API key setup
    ├── kilocode/              ← Kilo Code CLI installation
    └── comparing_cli_agents/  ← draft comparison (WIP)
```

### Source Code (`research/ai_coding_agents/`)

Each subdirectory is an independent git repository, excluded from the parent repo's `.gitignore` and from script checks (`check_broken_links`, `check_link_format`, etc.) via `tools/scripts/paths.py`.

**Registered agents** (clone/update via `manage_external_repos.py`):

| Agent | External Source | Type | Relation |
|-------|----------------|------|----------|
| aider | [aider.chat](https://aider.chat/) | Python CLI | - |
| claude-code-main | (leaked source) | TypeScript CLI | - |
| kilocode | [Kilo-Org/kilo](https://github.com/Kilo-Org/kilo) | TypeScript CLI (Bun) | Fork of `opencode` |
| openclaw | [openclaw/openclaw](https://github.com/openclaw/openclaw) | TypeScript CLI | - |
| openclaude | [GitLawB/OpenClaude](https://github.com/GitLawB/OpenClaude) | TypeScript CLI (Node.js) | - |
| opencode | [anomalyco/opencode](https://github.com/anomalyco/opencode) | TypeScript CLI (Bun) | Upstream for `kilocode` |
| qwen-code | [QwenLM/qwen-code](https://github.com/QwenLM/qwen-code) | TypeScript CLI (Node.js) | Fork of `gemini-cli` |
| superpowers | [obra/superpowers](https://github.com/obra/superpowers) | Plugin for coding agents | - |

Run `uv run tools/scripts/manage_external_repos.py list` for the current registry with branch/remote/status.

### Analysis Notebooks

Findings from studying these agents are saved as MyST notebooks (`.md` + `.ipynb` pairs) in topic directories:

| Topic | Location | What's Studied |
|-------|----------|----------------|
| Context management | `context_management/` | Source-level analysis: full history pattern, compaction strategies, token budgets across 6 agents |
| Session history | `session_history_management/` | How agents manage context, memory, crash recovery |
| Skills | `skills/` | Skill discovery, indexing, triggering patterns |
| Tooling | `tooling/` | Tool architectures, shell execution, sandboxing |

## Workflow

### Managing Source Code Repositories

External repositories are managed via a **unified manifest** (`.vadocs/inventory/manage_external_repos.json`), which serves as the Single Source of Truth (SSoT) for both the registered directories and the specific repositories they should contain.

Use [tools/scripts/manage_external_repos.py](/tools/scripts/manage_external_repos.py) to reconcile the local state with this manifest. Run with `--help` for current usage patterns:

```bash
uv run tools/scripts/manage_external_repos.py --help
```

**Common operations:**
- `sync` — Reconcile filesystem and registry with the manifest (clones missing, prunes orphans).
- `sync --update` — Complete alignment: reconcile structure AND pull latest changes.
- `sync-consumers` — Align `.gitignore` and `myst.yml` with the current manifest.
- `update` — Quick refresh (git pull) of existing repositories.
- `list` — Show all repos and their current status.
- `setup` / `register` — Add new repos/directories (updates the manifest).

:::{tip}
Run `sync --update` before starting any analysis session — agent architectures evolve fast, and a stale checkout or missing repository can lead to wrong conclusions.
:::

### Research Process

To prevent data loss during context switches and maximize context window efficiency, follow the **Analyze $\rightarrow$ Save $\rightarrow$ Move** loop:

1.  **Analyze**: Study the code in-place using `git log`, `grep_search`, and source navigation.
2.  **Save**: Write detailed findings to a dedicated analysis file or MyST notebook **immediately** after finishing a repository's analysis, before moving to the next.
3.  **Move**: Summarize the session to clear context, then proceed to the next target.
4.  **Sync**: Ensure notebooks are synchronized using `uv run jupytext --sync`.

#### Technical Analysis Standard
To ensure technical accuracy and avoid speculative descriptions, all architectural analyses must follow a strict **Claim $\rightarrow$ Evidence (Code/Path) $\rightarrow$ Explanation** format. Descriptive "guide" styles are prohibited.

- **Requirement**: Every architectural claim must be paired with a specific file path and a supporting code snippet from the source.
- **Focus**: Avoid "how to" phrasing; focus exclusively on "how it is implemented."

## Key Learnings Across Agents

### Session History / Context Management

- **All agents** send the full conversation history on every API call — no chunking, no delta updates. Context grows unboundedly until compaction kicks in. See [context_management/overview.md](/ai_agents/architecture/context_management/context_management_in_ai_coding_agents.md) for the full analysis.
- **Qwen Code** uses append-only JSONL event logs (`{sessionId}.jsonl`) with tree-structured `uuid`/`parentUuid` links — crash-safe by design, supports `/compress` without mutating history.
- **Claude Code** has the most sophisticated system: 5-tier compaction from microcompact (server-side cache editing) through session memory (background agent maintaining a markdown summary file) to full compaction with PTL retry.
- **Aider** relies on git history as the session record — every change is a commit, making the codebase itself the memory. Async background summarization doesn't block the main loop.
- **Superpowers** avoids session history sharing entirely — subagents get fresh context per task to prevent context pollution.
- **KiloCode** uses an Agent Manager (VS Code extension) for multi-session orchestration — each session gets its own git worktree, with the extension coordinating `kilo serve` processes via HTTP + SSE.
- **OpenClaw** is a personal assistant — not a coding agent. Uses a Gateway as control plane with persistent session state across channels (WhatsApp, Telegram, etc.).

### Tool Systems

- **Qwen Code:** All tools extend `BaseDeclarativeTool` in TypeScript (`packages/core/src/tools/`).
- **Aider:** Python-based tool definitions with strong git integration.
- **OpenClaude:** Inherits Claude Code's tool set (bash, file ops, grep, glob, agents, MCP) with provider-agnostic routing.
- **KiloCode / OpenCode:** Fork lineage — OpenCode is the upstream, KiloCode adds the Agent Manager. Both enforce parallel tool execution (`ALWAYS USE PARALLEL TOOLS WHEN APPLICABLE`).

### Skill / Prompt Systems

- **Superpowers:** 16 Markdown skills (`SKILL.md` + frontmatter) that auto-trigger based on agent context. Skills are *code, not prose* — behavior-shaping instructions tuned through adversarial pressure testing. Priority system: user instructions > superpowers skills > default system prompt.
- **Qwen Code:** Markdown + YAML skill definitions discovered and invoked during conversation.
- **Aider:** Instruction files (`.aider.model.metadata.json`, `.aider.input.history`) and per-model configuration.

### Multi-Agent Orchestration

- **Superpowers** is a plugin, not an agent — but its `subagent-driven-development` skill implements a 3-role review pipeline: a controller (the host agent) dispatches fresh subagents sequentially (Implementer → Spec Reviewer → Code Quality Agent), each with curated context to avoid pollution.
- **Qwen Code** has a SubAgents system with configuration stored as Markdown + YAML frontmatter.
- **KiloCode** implements multi-session orchestration via its Agent Manager in VS Code — each session gets a git worktree and its own `kilo serve` process.
