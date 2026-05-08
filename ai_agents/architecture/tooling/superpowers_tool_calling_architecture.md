---
title: Superpowers Tool Calling Architecture Analysis
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: 2026-05-06
description: Source-level analysis of the "skill" system in Superpowers, examining
  prompt-based tool invocation and the instruction hierarchy.
tags:
- agents
- architecture
options:
  type: guide
  birth: 2026-05-06
  version: 1.1.0
  token_size: 1080
---
# Superpowers Tool Calling Architecture Analysis

This analysis examines the "skill" system in Superpowers. Unlike traditional agents, Superpowers is a plugin that provides "prompt-tools"—behavioral contexts that the LLM invokes to change its operational mode.

## 1. Skill (Tool) Definitions

**Claim**: Skills are defined as directories containing a `SKILL.md` file with YAML frontmatter for discovery (name and description) and a Markdown body for behavior-shaping instructions.

**Path**: `ai_agents/research/ai_skills_plugins/superpowers/skills/brainstorming/SKILL.md`

**Snippet**:
```yaml
---
name: brainstorming
description: You MUST use this before any creative work - creating features, building
  components, adding functionality, or modifying behavior. Explores user intent, requirements
  and design before implementation.
options: {}
---
```

**Explanation**: The YAML frontmatter provides the metadata necessary for the host agent to index and discover the skill, while the Markdown content provides the actual operational logic.

## 2. LLM Integration and Bootstrap Injection

**Claim**: Superpowers integrates with the LLM by transforming the first user message of a session to inject bootstrap instructions and modifying the runtime configuration to include the skills directory for automatic discovery.

**Path**: `ai_agents/research/ai_skills_plugins/superpowers/.opencode/plugins/superpowers.js`

**Snippet**:
```javascript
    config: async (config) => {
      config.skills = config.skills || {};
      config.skills.paths = config.skills.paths || [];
      if (!config.skills.paths.includes(superpowersSkillsDir)) {
        config.skills.paths.push(superpowersSkillsDir);
      }
    },

    'experimental.chat.messages.transform': async (_input, output) => {
      const bootstrap = getBootstrapContent();
      if (!bootstrap || !output.messages.length) return;
      const firstUser = output.messages.find(m => m.info.role === 'user');
      if (!firstUser || !firstUser.parts.length) return;
      if (firstUser.parts.some(p => p.type === 'text' && p.text.includes('EXTREMELY_IMPORTANT'))) return;
      const ref = firstUser.parts[0];
      firstUser.parts.unshift({ ...ref, type: 'text', text: bootstrap });
    }
```

**Explanation**: The `config` hook ensures the `superpowers` skills directory is registered in the host agent's search path, and `experimental.chat.messages.transform` injects the `using-superpowers` bootstrap content into the first user message to ensure the agent is immediately aware of the skill system without bloating the system prompt.

## 3. Tool Invocation Mechanism

**Claim**: The agent is instructed to invoke skills using the host agent's native tool (e.g., `Skill` tool in Claude Code or `skill` tool in OpenCode) to load the full `SKILL.md` content into the context.

**Path**: `ai_agents/research/ai_skills_plugins/superpowers/skills/using-superpowers/SKILL.md`

**Snippet**:
```markdown
## How to Access Skills

**In Claude Code:** Use the `Skill` tool. When you invoke a skill, its content is loaded and presented to you—follow it directly. Never use the Read tool on skill files.

**In Copilot CLI:** Use the `skill` tool. Skills are auto-discovered from installed plugins. The `skill` tool works the same as Claude Code's `Skill` tool.

**In Gemini CLI:** Skills activate via the `activate_skill` tool. Gemini loads skill metadata at session start and activates the full content on demand.
```

**Explanation**: Superpowers leverages the host agent's existing infrastructure for "progressive disclosure," where only metadata is pre-loaded, and the full procedural logic is injected only upon explicit tool invocation.

## 4. Steering and Constraints

**Claim**: Skills employ `<HARD-GATE>` blocks or "Red Flag" tables to prevent common LLM failure modes, such as rationalization or premature implementation.

**Path**: `ai_agents/research/ai_skills_plugins/superpowers/skills/brainstorming/SKILL.md`

**Snippet**:
```markdown
<HARD-GATE>
Do NOT invoke any implementation skill, write any code, scaffold any project, or take any implementation action until you have presented a design and the user has approved it. This applies to EVERY project regardless of perceived simplicity.
</HARD-GATE>
```

**Explanation**: These constraints act as "behavioral circuit breakers" that the LLM must check against, ensuring that high-discipline workflows (like mandatory design approval) are not bypassed in favor of "perceived simplicity."
