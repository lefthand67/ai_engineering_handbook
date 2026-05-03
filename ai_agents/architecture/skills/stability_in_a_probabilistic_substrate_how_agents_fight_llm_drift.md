
---
title: 'Stability in a Probabilistic Substrate: How Agents Fight LLM Drift'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: '2026-04-08'
description: How AI coding agents fight LLM hallucination and instruction non-compliance.
  Hard guarantees (tool denial, circuit breakers) vs soft techniques (HARD-GATE tags,
  rationalization tables) — with source code evidence.
tags:
- architecture
- agents
- prompts
options:
  version: 1.0.0
  birth: '2026-04-08'
  type: guide
  token_size: 2349
---
# Stability in a Probabilistic Substrate: How Agents Fight LLM Drift

## The Fundamental Problem

Traditional software fails with an error you can catch and fix. **LLM-based systems fail silently** — the model just doesn't do what you asked, and you only notice when the output is wrong.

There is no `assert` that can fail hard on LLM behavior. No type system can guarantee that the LLM will follow instructions. The entire substrate is **probabilistic** — every API call carries a risk of hallucination, instruction skipping, or rationalization.

The question is not "how do we eliminate failures?" — it is "how do we reduce failure rates to acceptable levels?"

:::{seealso}
For the mechanics of how subagents are spawned and how compaction works at the API level, see [How Subagents Actually Work](/ai_agents/architecture/orchestration/how_subagents_actually_work_myth_of_process_spawning.md) and [The Compaction API Contract](/ai_agents/architecture/context_management/compaction_api_contract_why_system_prompts_dont_mix.md).
:::

## What's Actually Reliable vs. What Isn't

### Reliable — Enforced by Code, Not Prompts

These mechanisms are **deterministic** — they work regardless of LLM behavior:

| Mechanism | How It Works | Agent |
|-----------|-------------|-------|
| **Tool denial** | `Permission.fromConfig({ "*": "deny" })` — runtime blocks tool access, LLM cannot override | OpenCode compaction |
| **Circuit breaker** | After 3 consecutive failures → feature permanently disabled for session | Claude Code auto-compact |
| **Token thresholds** | Compaction triggers at exact token count: `effectiveContextWindow - 13_000` | Claude Code |
| **History boundaries** | `filterCompacted()` streams from DB and stops at compaction marker — deterministic code | OpenCode |
| **Overflow guards** | Won't compress if it would increase token count | Qwen Code |
| **PTL retry truncation** | Drops 20% of groups on prompt-too-long, retries up to 3 times | Claude Code |

**Tool denial** — the strongest guarantee available:

```typescript
// OpenCode compaction agent — ALL tools denied
compaction: {
  permission: Permission.merge(
    defaults,
    Permission.fromConfig({ "*": "deny" }),  // ← hard guarantee
    user
  ),
}
```

The compaction agent literally **cannot** call tools. This is enforced by the runtime permission system, not by asking the LLM nicely.

**Circuit breaker** — prevents infinite failure loops:

```typescript
// Claude Code — src/services/compact/autoCompact.ts
MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES = 3
```

After 3 consecutive auto-compact failures, the circuit breaker trips and auto-compact is **permanently disabled** for that session. No LLM compliance required — this is a state machine transition.

**PTL (Prompt-Too-Long) retry truncation** — emergency escape hatch:

When the compaction request itself hits the provider's context limit:
- If the token gap is parseable: drops groups until the gap is covered
- Otherwise: drops 20% of groups as a fallback
- Always keeps at least one group to summarize
- Prepends `[earlier conversation truncated for compaction retry]`
- Retries up to 3 times (`MAX_PTL_RETRIES = 3`)

### Unreliable — Depends on LLM Compliance

These techniques **reduce** failure rates but do not **eliminate** them:

| Technique | How It Works | Reliability |
|-----------|-------------|-------------|
| **HARD-GATE tags** | `<HARD-GATE>Do NOT proceed until X</HARD-GATE>` — explicit stop signals in XML | Soft — LLM can ignore |
| **Rationalization tables** | Pre-empt known failure modes: `"I'm confident"` → `Confidence ≠ evidence` | Reduces drift, doesn't eliminate |
| **Two-stage review** | Implementer → Spec Reviewer → Code Quality Reviewer | Catches violations, doesn't prevent |
| **Structured output** | Summary templates: `## Goal`, `## Instructions`, etc. | Improves compliance, not guaranteed |
| **Skill instructions** | `SKILL.md` files with behavior-shaping instructions | LLM can skip or modify |
| **Commitment devices** | TodoWrite checklists that must be completed | Visible but not enforced |

**HARD-GATE tags** from Superpowers:

```markdown
<HARD-GATE>
Do NOT proceed with implementation until you have:
1. A clear spec from the user
2. A test plan
3. A list of files you will modify
</HARD-GATE>
```

This is a **soft** signal. The LLM can (and does) ignore it. There is no runtime enforcement — it is just XML-formatted text in the prompt.

**Rationalization tables** from Superpowers' `verification-before-completion`:

| Excuse | Reality |
|--------|---------|
| "Should work now" | RUN the verification |
| "I'm confident" | Confidence ≠ evidence |
| "Just this once" | No exceptions |
| "Linter passed" | Linter ≠ compiler |
| "Agent said success" | Verify independently |
| "I'm tired" | Exhaustion ≠ excuse |

These counter pre-empt known rationalizations, but they only work if the LLM **reads and follows** the table. Under context pressure, the table can be truncated.

**Two-stage review** from Superpowers' subagent-driven development:

```
Implementer → Spec Reviewer → Code Quality Reviewer
     ↑                              ↓
     └──── fix issues ←─────────────┘
              (re-review loop)
```

The spec reviewer is explicitly instructed: **"Do not trust the implementer's report. Read the actual code."** This catches violations after the fact but does not prevent them.

## The Adversarial Testing Methodology

Superpowers uses a **RED → GREEN → REFACTOR** cycle applied to prompts:

1. **RED phase**: Run a pressure scenario WITHOUT the skill. Document the agent's exact rationalizations verbatim.
2. **GREEN phase**: Write the skill addressing those specific failures.
3. **REFACTOR phase**: Re-run with the skill, verify compliance. Find new rationalizations, add counters.
4. **Repeat** until no new loopholes appear.

The testing methodology from `writing-skills/testing-skills-with-subagents.md`:

> "If you didn't watch an agent fail without the skill, you don't know if the skill prevents the right failures."

Pressure scenarios include:
- **Time pressure** — rush the agent, see if it skips steps
- **Sunk cost** — agent has invested effort, see if it skips verification to declare success
- **Exhaustion** — long session, see if fatigue causes rationalization
- **Authority overrides** — tell the agent "the previous work is correct," see if it still verifies

## The Failure Modes That Remain

Even with all these techniques, failures still occur:

| Failure Mode | Why It Happens | Mitigation |
|-------------|----------------|------------|
| **Skill skipping** | LLM rationalizes away the 1% rule despite Red Flags table | Two-stage review catches after the fact |
| **Context overflow truncation** | Skill content gets cut off mid-rule | Token-efficient design (<150 words for frequent skills) |
| **Model version changes** | New model breaks compliance without any test catching it | Re-run adversarial tests after model updates |
| **Skill conflicts** | Two skills give overlapping/contradictory instructions | LLM picks arbitrarily — no resolution mechanism |
| **Compaction quality** | Summary omits critical context | Structured summary template with required sections |
| **Silent hallucination** | LLM generates plausible but incorrect summary | No programmatic assertion available — inherent limitation |

## The Honest Assessment

From the Superpowers source analysis:

> **"It's prompt engineering at scale.** The best available techniques (explicit counters, rationalization tables, commitment devices, hard gates, two-stage review) make it more robust than naive prompting — but it's still fundamentally probabilistic. The system reduces failure rates through empirical testing rather than eliminating them through guarantees."

> **"The difference from a traditional orchestrator: a traditional system fails with an error you can catch and fix. This system fails silently — the LLM just doesn't do what you asked, and you only notice when the output is wrong."**

## Defense in Depth: The Layered Approach

The most robust agents use multiple layers that catch different failure modes:

```
Layer 0: HARD CONSTRAINTS (code-enforced)
  ├── Tool permissions (runtime blocks access)
  ├── Circuit breakers (hard failure limits)
  ├── Token thresholds (exact trigger points)
  └── History boundaries (deterministic markers)

Layer 1: PROMPT ENGINEERING (soft, but tested)
  ├── HARD-GATE XML tags
  ├── Rationalization tables
  ├── Structured output templates
  └── Skill instructions with token efficiency

Layer 2: REVIEW GATES (catches after the fact)
  ├── Spec reviewer (verifies against requirements)
  ├── Code quality reviewer (checks SOLID, tests)
  └── verification-before-completion (evidence before claims)

Layer 3: EMERGENCY ESCAPE HATCHES
  ├── PTL retry truncation (drops history on overflow)
  ├── Circuit breaker (disables after repeated failures)
  └── Manual override (/compress, force compact)
```

No single layer is sufficient. The combination makes failures **less likely** and **more detectable** — but never impossible.

## Key Takeaway

**You cannot programmatically enforce LLM behavior.** The best you can do is:

1. **Enforce constraints at the runtime level** where possible (tool permissions, token limits, circuit breakers)
2. **Test prompts adversarially** to discover failure modes before deployment
3. **Build review gates** that catch violations after the fact
4. **Accept the probabilistic nature** of the substrate and design accordingly

The agents analyzed in this repository represent the state of the art in managing this problem. They make failures less likely through empirical testing rather than eliminating them through guarantees. This is a fundamental limitation of building on LLM APIs, not a temporary engineering gap.
