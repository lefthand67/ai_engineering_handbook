
---
title: Skill Discovery Across AI Coding Platforms
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: '2026-05-02'
description: How AI coding platforms discover, index, and load skills — mechanisms,
  directory layouts, and setup instructions
tags:
- context_management
- architecture
options:
  type: guide
  birth: '2026-04-10'
  version: 1.0.1
  token_size: 1625
---
# Skill Discovery Across AI Coding Platforms

## Source and Reproducibility

**Repository:** [obra/superpowers](https://github.com/obra/superpowers)
**Version analyzed:** v5.0.7 (commit `b7a8f76`)
**Source directory:** `skills/` — 14 SKILL.md files plus supporting prompt templates
**Analysis date:** April 2026

To reproduce this analysis, clone the repo at this version and examine the skill files directly:

```bash
git clone https://github.com/obra/superpowers.git
cd superpowers
git checkout v5.0.7
ls skills/*/SKILL.md
```

Key files referenced in this analysis:

| File | Purpose |
|------|---------|
| `skills/using-superpowers/SKILL.md` | Bootstrap skill — skill invocation rules |
| `skills/subagent-driven-development/SKILL.md` | Three-role subagent orchestration |
| `skills/subagent-driven-development/implementer-prompt.md` | Implementer dispatch template |
| `skills/subagent-driven-development/spec-reviewer-prompt.md` | Spec compliance review template |
| `skills/subagent-driven-development/code-quality-reviewer-prompt.md` | Code quality review template |
| `skills/verification-before-completion/SKILL.md` | Verification enforcement |
| `skills/writing-skills/SKILL.md` | Skill creation methodology |
| `skills/writing-skills/testing-skills-with-subagents.md` | Adversarial testing methodology |
| `skills/writing-skills/anthropic-best-practices.md` | Anthropic's official skill authoring guide |
| `skills/dispatching-parallel-agents/SKILL.md` | Parallel dispatch pattern |
| `.opencode/plugins/superpowers.js` | OpenCode plugin — skill path registration |
| `.claude-plugin/plugin.json` | Claude Code plugin metadata |
| `.cursor-plugin/plugin.json` | Cursor plugin — skills/agents/commands/hooks paths |
| `hooks/session-start` | Session bootstrap hook — JSON output injection |
| `gemini-extension.json` | Gemini CLI plugin metadata |
| `.codex/INSTALL.md` | Codex installation via symlink |
| `.github/PULL_REQUEST_TEMPLATE.md` | PR template — contributor requirements |
| `AGENTS.md` / `CLAUDE.md` | Contributor guidelines for AI agents |

## How Skills Are Indexed

Each platform handles discovery differently. There is no unified indexing layer across platforms:

| Platform | Mechanism |
|----------|-----------|
| **Claude Code** | Native skill system. Scans `skills/*/SKILL.md`, parses YAML frontmatter, indexes `name` + `description`. Skills are loaded on-demand when the LLM invokes the `Skill` tool. |
| **OpenCode** | Plugin pushes `skills/` path into `config.skills.paths`. OpenCode scans that directory, parses frontmatter, and lazy-discovers skills. |
| **Codex** | Symlink: `~/.agents/skills/superpowers → skills/`. Codex's native skill discovery handles the rest. |
| **Cursor** | `plugin.json` points to `"skills": "./skills/"`. Cursor's plugin system discovers them. |
| **Gemini CLI** | `gemini-extension.json` with `contextFileName: "GEMINI.md"`. Skills load via `activate_skill` tool. |
| **Qwen Code** | Scans `~/.qwen/skills/*/SKILL.md` and `<project>/.qwen/skills/*/SKILL.md` — immediate subdirectories only, no nested `skills/` layout. Each skill directory must contain `SKILL.md` with `name` + `description` frontmatter. Symlinks supported (tested: valid dirs, broken links, file targets). Precedence: project > user > extension > bundled. |

Superpowers just puts `SKILL.md` files in a directory with YAML frontmatter and trusts each platform to find them.

### The Discovery Chain

```
User input: "help me plan this feature"
         ↓
Platform skills engine searches indexed descriptions
         ↓
Finds: brainstorming SKILL.md description mentions "building features"
         ↓
Loads full SKILL.md content into context (or presents as option)
         ↓
LLM invokes skill via Skill tool
```

The `name` becomes the skill identifier (used as `superpowers:brainstorming`). The `description` is what the LLM reads to decide whether to invoke the skill.

### Token-Efficient Loading

From Anthropic's best practices guide:

> "Not every token in your Skill has an immediate cost. At startup, only the metadata (name and description) from all Skills is pre-loaded. Claude reads SKILL.md only when the Skill becomes relevant, and reads additional files only as needed."

This is a platform-specific guarantee (Claude Code), not universal across all platforms. Once a skill *is* loaded, it competes with conversation history, code context, and other skills. Skills are aggressively trimmed for token efficiency: <150 words for frequently-loaded, <500 for others.

## Setting Up Superpowers Skills for Qwen Code

The superpowers repo uses a nested `skills/` subdirectory layout (`superpowers/skills/<skill-name>/SKILL.md`) that Qwen Code cannot discover directly — it expects skills at the immediate level of the base directory.

**Recommended layout:**

```
/ai_agents/research/ai_coding_agents/superpowers/          ← git repo (update with git pull)
  skills/
    brainstorming/SKILL.md
    using-superpowers/SKILL.md
    ...

~/.qwen/skills/                                  ← symlinks to each skill
  brainstorming -> /ai_agents/research/ai_coding_agents/superpowers/skills/brainstorming
  using-superpowers -> /ai_agents/research/ai_coding_agents/superpowers/skills/using-superpowers
  ...
```

**Setup commands:**

```bash
# Clone the superpowers repo into research/
git clone https://github.com/obra/superpowers.git /ai_agents/research/ai_coding_agents/superpowers

# Create symlinks for each skill (run from ~/.qwen/skills/)
cd ~/.qwen/skills/
for skill in brainstorming dispatching-parallel-agents executing-plans \
  finishing-a-development-branch receiving-code-review requesting-code-review \
  subagent-driven-development systematic-debugging test-driven-development \
  using-git-worktrees using-superpowers verification-before-completion \
  writing-plans writing-skills; do
  ln -sfn -r \
    /home/commi/Yandex.Disk/it_working/projects/soviar-systems/ai_engineering_book//ai_agents/research/ai_coding_agents/superpowers/skills/$skill \
    /home/commi/.qwen/skills/$skill
done
```

Update skills anytime with `cd /ai_agents/research/ai_coding_agents/superpowers && git pull` — the symlinks follow automatically.

:::{seealso}
For analysis of why skill-based orchestration is fundamentally brittle and how superpowers fights failure modes, see {ref}`prompt_brittleness_in_skills`.
:::
