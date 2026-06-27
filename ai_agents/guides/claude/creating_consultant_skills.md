---
title: Creating Consultant Skills for Claude Code
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Recipe for wrapping JSON consultant prompts as Claude Code skills with
  symlink-to-source pattern and namespace conventions.
tags:
- agents
- prompts
date: '2026-04-11'
options:
  type: guide
  birth: '2026-03-25'
  version: 1.0.1
  token_size: 1151
---
# Creating Consultant Skills for Claude Code

## Problem

The ecosystem maintains structured consultant prompts as JSON files in
`ai_system/3_prompts/consultants/`. These prompts define complete personas —
role, tone, protocols, output format — and are designed to be injected into
LLM conversations verbatim. Invoking them manually (copy-paste or `cat`)
is friction that discourages use.

Claude Code skills turn these prompts into slash commands (`/sv-devops-consultant`)
that inject the full JSON at invocation time, with zero duplication.

## Architecture

```
ai_system/3_prompts/consultants/       ← SSoT: JSON prompt files
    ai_brainstorming_colleague.json
    devops_consultant.json
    ...

.claude/skills/                        ← skill wrappers
    sv-devops-consultant/
        SKILL.md                       ← frontmatter + loader template
        prompt.json -> ../../../ai_system/3_prompts/consultants/devops_consultant.json
```

Each skill directory contains:

- **`prompt.json`** — a relative symlink (`ln -srf`) to the original JSON in `consultants/`
- **`SKILL.md`** — a short wrapper that loads the symlinked JSON via shell injection

The JSON files remain the single source of truth. Editing a consultant prompt
automatically updates the corresponding skill.

## Skill wrapper template

Every `SKILL.md` follows the same pattern:

```yaml

name: sv-<skill-name>
description: <one-line description — Claude uses this to decide when to load the skill>
argument-hint:
- <hint for autocomplete>
options:
  type: guide
---

You are now operating as the consultant defined in the following JSON prompt.
Adopt the role, tone, principles, and protocols exactly as specified.

!`cat ${CLAUDE_SKILL_DIR}/prompt.json`

The user's input is:

$ARGUMENTS
```

Key mechanisms:

- `` !`cat ${CLAUDE_SKILL_DIR}/prompt.json` `` — runs **before** Claude sees
  the skill content; the shell output replaces the placeholder inline
- `$ARGUMENTS` — everything the user types after the slash command
- `${CLAUDE_SKILL_DIR}` — absolute path to the skill's directory at runtime

## Creating a new skill

1. **Create the skill directory:**

   ```bash
   mkdir .claude/skills/sv-<name>
   ```

2. **Symlink the source JSON:**

   ```bash
   cd <repo-root>
   ln -srf ai_system/3_prompts/consultants/<source>.json .claude/skills/sv-<name>/prompt.json
   ```

   `ln -srf`: `-s` symbolic, `-r` compute relative path automatically, `-f` overwrite if exists.

3. **Create `SKILL.md`** using the template above. Set `name:` to match the
   directory name exactly.

4. **Restart Claude Code** — skills are discovered at session start.

## Namespace convention

All ecosystem skills use the `sv-` prefix (short for soviar). This:

- Avoids collisions with built-in Claude Code skills (e.g., `brainstorm`)
- Makes all custom skills discoverable by typing `/sv-` in the prompt
- Creates a clear boundary between upstream and ecosystem commands

## Skill resolution rules

Claude Code discovers project skills from `.claude/skills/` in the **current
project directory** and its subdirectories. Important constraints:

- Skills in a **parent** directory are **not** inherited by child repos —
  resolution walks down, not up
- To share skills across sibling repos, either place them in `~/.claude/skills/`
  (personal scope, always available) or symlink the skill directories into each
  repo's `.claude/`
- When skills share a name across scopes, priority is:
  enterprise > personal (`~/.claude/`) > project (`.claude/`)

## Current skill inventory

| Slash command | Source JSON | Domain |
|---|---|---|
| `/sv-ai-brainstorm-colleague` | `ai_brainstorming_colleague.json` | Ideation, OSS exploration |
| `/sv-ai-systems-consultant-hybrid` | `ai_systems_consultant_hybrid.json` | AI architecture, WRC/SVA |
| `/sv-devops-consultant` | `devops_consultant.json` | CI/CD, IaC, automation |
| `/sv-handbook-reviewer` | `handbook_consultant.json` | Documentation peer review |
| `/sv-local-ai-systems-consultant` | `local_ai_systems_consultant.json` | Local/edge LLM systems |
| `/sv-python-test-architect` | `python_test_architect.json` | pytest suite generation |
