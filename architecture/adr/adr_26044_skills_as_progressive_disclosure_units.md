---
id: 26044
title: Skills as Progressive Disclosure Units
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Defines skills as versioned, testable units of expertise that are injected into the agent's context on demand.
tags:
- context_management
date: 2026-03-18
options:
  type: adr
  birth: '2026-03-18'
  version: 1.0.0
  token_size: 2686
  status: proposed
  superseded_by: null
---
<!-- Quality guidelines: /architecture/architecture_decision_workflow_guide.md -->

# ADR-26044: Skills as Progressive Disclosure Units

## Date

2026-03-18

## Status

proposed

## Context

{term}`ADR-26038`
established context engineering as the core design principle and stated, in one sentence, that
"skills are injected instructions, not separate agents" following the SKILL.md pattern validated
by cross-vendor convergence. That sentence is a principle, not a specification. The ecosystem
needs a formal definition of the skill unit to:

1. **Enable consistent implementation** — without a spec, each agent that wants to load skills
   would invent its own format, fragmenting the ecosystem.
2. **Budget context accurately** — progressive disclosure requires frontmatter fields
   (`token_size`, `tags`, `description`) that drive selection. These fields need a schema.
3. **Define the skill/subagent boundary** — {term}`ADR-26038`
   permits fork-and-join subagents but distinguishes them from skills. The boundary is not yet
   operationally defined.
4. **Clarify MCP's role** — the emerging standards stack places MCP as the runtime tool
   connectivity layer and SKILL.md as the capability packaging layer; their interaction needs
   explicit guidance.

### Cross-Vendor Convergence on SKILL.md

The most significant evidence from
[A-26009: Compass — The Realistic State of Agentic AI 2026](/architecture/evidence/analyses/A-26009_compass_realistic_state_of_agentic_ai_2026.md)
is that the SKILL.md format — YAML frontmatter plus Markdown instructions in a directory with
optional scripts and references — was released by Anthropic as an open standard in December 2025,
and OpenAI adopted the same format for Codex CLI and ChatGPT. This is the closest the industry
has come to a portable, reusable skill format.

The convergence is notable because it is independent: two competing vendors arrived at the same
structure from different architectural starting points (Claude Code's tool-use loop vs. OpenAI's
assistant API). When independent implementations converge, the shared structure is extracting
something real.

### Skill Marketplaces and Security Risk

Skill marketplaces are materializing at scale: SkillsMP hosts 31,000+ agent skills. But a Snyk
study (February 2026, n=3,984) found that **36% of community skills have security flaws** —
prompt injection, data exfiltration, or unsafe tool invocations embedded in skill instructions.
Community skills require an explicit vetting gate before ecosystem adoption.

### The Progressive Disclosure Principle

The [NVIDIA RULER benchmark](/architecture/evidence/analyses/A-26009_compass_realistic_state_of_agentic_ai_2026.md)
found that effective context is only 50-65% of the advertised context window. Loading all
available skills into the system prompt at startup is not viable — it consumes the available
context before any user task begins. Skills must be loaded on demand.

"Progressive disclosure" — loading only what the current task requires — is the mechanism that
makes the skill library scale beyond a handful of capabilities.

### Relationship to ADR-26034

{term}`ADR-26034`
(rejected) proposed the Agentic OS paradigm and introduced the SKILL.md + tools/ + tests/
folder structure. The OS framing was rejected; the folder structure was retained in {term}`ADR-26038` as
a "validated pattern." ADR-26044 formalizes exactly what was retained: the skill unit structure,
selection mechanism, and boundaries.

## Decision

We adopt the **progressive disclosure unit** as the formal definition of a skill in this
ecosystem.

### 1. Skill Structure

A skill is a directory with a required `SKILL.md` and two optional subdirectories:

```
skill_name/
  SKILL.md          # Required: frontmatter + Markdown instructions
  tools/            # Optional: executable scripts invoked by the skill
  tests/            # Optional: golden-file fixtures for skill verification
```

`SKILL.md` has two parts:

- **YAML frontmatter** (machine-readable): `name`, `description`, `tags`, `token_size`
  (computed at publish time), and optionally `mcp_servers` (list of MCP server identifiers
  the skill depends on at runtime).
- **Markdown body** (human and agent readable): procedural instructions that the agent follows
  when this skill is active. Instructions describe behavior, not implementation steps. No bash
  invocations, no tool command syntax — those belong in `tools/`.

`tools/` contains executable scripts (Python, Bash) that the skill's instructions reference.
`tests/` contains golden-file fixtures that verify the skill's behavior without API calls.

### 2. Progressive Disclosure Mechanism

Skills are not loaded at agent startup. They are loaded on demand:

1. The agent maintains a skill registry — a list of skill frontmatter objects (name, description,
   tags, token_size) loaded at startup. The registry's total token cost must be under 5% of
   the working context budget.
2. When a user task arrives, the agent matches task intent against registry metadata and selects
   the minimal set of skills needed.
3. Selected skills are injected into the working context window as additional instructions.
4. When a skill's task is complete, its instructions are removed from the active context to
   reclaim budget.

The frontmatter fields `description`, `tags`, and `token_size` exist specifically to support
this selection and budgeting loop. Without these fields, the agent must load and inspect the
full skill body to decide relevance — defeating the purpose of progressive disclosure.

### 3. Skills Are Injected Instructions, Not Subagents

A skill executes within the main agent's context window and LLM loop. It is not:

- A separate process
- A separate LLM call
- A message-passing endpoint

This is the boundary established by {term}`ADR-26038`:
skills are injected, subagents are forked. The decision rule is:

- **Inject a skill** when the task requires a capability the agent does not have loaded —
  a domain-specific procedure, an output template, a set of constraints.
- **Fork a subagent** when the task requires isolated context — a long parallel research
  task whose intermediate state would pollute the parent's context, or a task that must
  complete independently and return a structured result.

MCP tool servers are neither skills nor subagents — they are runtime tool endpoints that any
skill or the agent itself may invoke. A skill that depends on an MCP server declares it in its
frontmatter `mcp_servers` field; the agent runtime resolves the server connection before
injecting the skill.

### 4. Security Gate for External Skills

Community skills from marketplaces require explicit review before ecosystem adoption. The review
checks for prompt injection vectors, data exfiltration patterns, and unsafe tool invocations.
Reviewed skills are committed to the repository's `skills/` directory — they are not fetched
at runtime. This eliminates supply-chain risk from dynamic skill loading.

First-party skills authored within the ecosystem are exempt from the external review gate but
are still subject to the standard test suite (`tests/` fixtures must pass).

## Consequences

### Positive

- **Token-predictable capability loading**: `token_size` in frontmatter makes context budgeting
  for skills exact, not estimated. The agent can reject skills that exceed the remaining budget
  before injecting them.
- **Cross-runtime portability**: The SKILL.md structure is the same format used by Claude Code,
  Codex CLI, and ChatGPT — skills authored in this ecosystem are portable to any runtime
  supporting the standard.
- **Test-verifiable behavior**: The `tests/` directory enables skill verification without API
  calls. CI can verify that a skill's tools produce expected outputs before deployment.
- **Clear security boundary**: The "reviewed-and-committed" model eliminates runtime supply-chain
  risk. Skills are auditable artifacts in version control, not network-fetched executables.
- **Operationalizes ADR-26038 decision point**: The inject/fork decision rule gives implementers
  a concrete test to apply, replacing a one-sentence principle with a named criterion.

### Negative / Risks

- **Registry synchronization**: As skills are added or updated, the in-memory registry must
  stay consistent with the on-disk `skills/` directory. **Mitigation:** a startup integrity
  check validates registry metadata against actual SKILL.md frontmatter; mismatches are a
  startup error, not a silent inconsistency.
- **Progressive disclosure requires good metadata**: Skill selection quality depends entirely
  on `description` and `tags` quality. Poorly written metadata causes incorrect skill selection.
  **Mitigation:** `vadocs` validates that `description` is non-empty and `tags` is non-empty
  for all skill types; the quality of the content is a human responsibility.
- **Token_size drift**: `token_size` is computed at publish time; if a skill is edited without
  recomputing, the budget estimate is stale. **Mitigation:** the pre-commit hook recomputes
  `token_size` for any changed `SKILL.md` (analogous to how `check_adr.py` maintains the index).
- **MCP server availability**: A skill that declares `mcp_servers` cannot execute if the server
  is unavailable. **Mitigation:** skills should declare MCP dependencies only for genuinely
  external capabilities; local, standalone skills have no server dependency.

## Alternatives

- **All skills loaded at startup (static injection)**: Simple and predictable, no selection
  logic needed. **Rejected:** NVIDIA RULER data shows context window degrades at high occupancy.
  Loading 10 skills × 2,000 tokens each consumes 20K tokens before any user message — leaving
  insufficient budget for conversation history and retrieved context in a 32K window.

- **Skills as separate LLM calls (per-skill subagents)**: Each skill gets its own context
  window, eliminating interference. **Rejected:** {term}`ADR-26038`
  establishes that context isolation between agents causes incompatible decisions. Forked
  subagents are permitted for independent parallel tasks, not as a default execution model
  for every skill.

- **Skills as MCP tool servers**: Package each skill as an MCP server; the agent invokes the
  skill via a tool call. **Rejected:** this requires a running server process for every
  capability, adds network overhead for local skills, and does not solve the budgeting problem
  (the agent still needs to know which server to call). MCP is the right layer for external
  service connectivity; it is the wrong layer for procedural instruction injection.

- **Dynamic runtime skill fetching**: Skills fetched from a marketplace URL at task time.
  **Rejected:** introduces supply-chain risk without mitigation (Snyk: 36% flaw rate). All
  production skills must be reviewed and committed before they can execute.

## References

- {term}`ADR-26038` — establishes "skills as injected instructions, not subagents"; this ADR formalizes that principle
- {term}`ADR-26034` — rejected predecessor; SKILL.md + tools/ + tests/ folder structure retained from here
- [A-26009: Compass — The Realistic State of Agentic AI 2026](/architecture/evidence/analyses/A-26009_compass_realistic_state_of_agentic_ai_2026.md) — cross-vendor convergence evidence, progressive disclosure finding, Snyk security data
- {term}`ADR-26042` — skill frontmatter extends the common schema; `type: skill` resolves from the type registry
- {term}`ADR-26037` — inject/fork decision rule operationalizes SVA for skills
- {term}`ADR-26032` — skills are the procedural tier; this ADR does not change that boundary

## Participants

1. Vadim Rudakov
2. Claude Sonnet 4.6 (AI Engineering Advisor)
