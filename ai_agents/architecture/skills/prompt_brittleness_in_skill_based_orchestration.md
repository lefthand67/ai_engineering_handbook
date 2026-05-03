
---
title: Prompt Brittleness in Skill-Based Orchestration
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: '2026-05-02'
description: Why skill-based orchestration fails — three failure modes, layered countermeasures,
  and honest assessment of prompt engineering at scale
tags:
- prompts
- architecture
options:
  type: guide
  birth: '2026-04-10'
  version: 1.0.1
  token_size: 1439
---
# Prompt Brittleness in Skill-Based Orchestration

## Source and Reproducibility

**Repository:** [obra/superpowers](https://github.com/obra/superpowers)
**Version analyzed:** v5.0.7 (commit `b7a8f76`)
**Analysis date:** April 2026

The superpowers repo contains 14 SKILL.md files that program the LLM to behave as an orchestrator through carefully crafted prompts. This analysis examines why this approach is fundamentally brittle and what the system does about it.

:::{seealso}
For how different platforms discover and load skills, see {ref}`skill_discovery_across_platforms`.
:::

## The Brittleness Problem

There is no orchestration framework. The skills are carefully crafted prompts that program the LLM to behave as an orchestrator. Three real failure modes:

### 1. Context Window Limits

The skills are designed with token efficiency in mind, but this is a soft constraint. If the conversation grows large enough, older skill content can be truncated. The LLM then follows whatever remains of the skill instructions.

### 2. Instruction Drift

This is acknowledged explicitly. The entire `writing-skills/testing-skills-with-subagents.md` methodology exists because of it:

> "If you didn't watch an agent fail without the skill, you don't know if the skill prevents the right failures."

The countermeasure is **adversarial pressure testing**: run the agent through time pressure, sunk cost, exhaustion, and authority overrides — then check if it still complies. If it doesn't, close the loophole with explicit counters. This is the RED-GREEN-REFACTOR cycle applied to prompts.

### 3. Hallucination / Skipping

The LLM can skip skill invocation entirely. The `using-superpowers` skill says "if there's even a 1% chance a skill applies, invoke it" — but the LLM can still ignore this. No hard enforcement exists.

## What the System Does to Fight Brittleness

The codebase uses layered mechanisms to reduce (but not eliminate) failure rates:

| Layer | Mechanism | What It Does |
|-------|-----------|--------------|
| **HARD-GATE** | `<HARD-GATE>` XML tags in skills | Tells the LLM "do NOT proceed until X" |
| **Rationalization tables** | Explicit excuse → reality mappings | Pre-empts common rationalizations ("too simple to test", "tests after achieve same goals") |
| **Red Flags lists** | "STOP" triggers | Pattern-matches against thoughts that precede violations |
| **TodoWrite enforcement** | Skills create checklists as explicit todos | Makes compliance visible and trackable |
| **Two-stage review** | Spec review → Quality review | Catches skipped steps after the fact |
| **verification-before-completion** | "Evidence before claims, always" | Prevents false success declarations |

### How Rationalization Tables Work

Every rule in every skill exists because a real agent violated it in a real session. The testing methodology:

1. Run a pressure scenario WITHOUT the skill (RED phase)
2. Document the agent's exact rationalizations verbatim
3. Write the skill addressing those specific failures (GREEN phase)
4. Re-run with the skill, verify compliance
5. Find new rationalizations, add counters (REFACTOR phase)
6. Repeat until no new loopholes appear

Example rationalization table from `verification-before-completion`:

| Excuse | Reality |
|--------|---------|
| "Should work now" | RUN the verification |
| "I'm confident" | Confidence ≠ evidence |
| "Just this once" | No exceptions |
| "Linter passed" | Linter ≠ compiler |
| "Agent said success" | Verify independently |
| "I'm tired" | Exhaustion ≠ excuse |

### How Two-Stage Review Catches Violations

Even if the implementer skips a step, the review chain is designed to catch it:

```
Implementer → Spec Reviewer → Code Quality Reviewer
     ↑                              ↓
     └──── fix issues ←─────────────┘
              (re-review loop)
```

The spec reviewer is explicitly instructed: "Do not trust the implementer's report. Read the actual code." The code quality reviewer then checks for SOLID principles, test coverage, and maintainability. Both reviewers can send work back for fixes.

## The Honest Assessment

### What Works

1. **Skills are tested against real LLM behavior**, not theoretical correctness. The TDD methodology means every rule exists because a real agent violated it in a real session.
2. **Rationalization tables are empirically derived**, not guessed. They capture what agents actually say when rationalizing, then counter each one.
3. **Review gates catch violations after the fact.** Even if the implementer skips a step, the spec reviewer and code quality reviewer will (usually) catch it.
4. **Skills are token-efficient.** Only metadata loads at startup; full content loads on demand. This reduces context pressure.

### What Fails

1. **The LLM skips the skill check entirely.** No hard enforcement exists. The LLM can rationalize away the 1% rule despite the Red Flags table.
2. **Context overflow truncates skill content.** If the skill gets cut off mid-rule, the LLM follows whatever remains.
3. **Model changes break skills silently.** Skills are tuned against specific model versions. A model update can break compliance without any test catching it (unless the test is re-run).
4. **Multiple skills conflict.** When two skills give overlapping or contradictory instructions, the LLM picks arbitrarily.
5. **No programmatic assertions.** There's no `assert` that can fail hard. Everything is "trust the LLM to follow instructions it wrote itself."

### Bottom Line

**It's prompt engineering at scale.** The best available techniques (explicit counters, rationalization tables, commitment devices, hard gates, two-stage review) make it more robust than naive prompting — but it's still fundamentally probabilistic. The system reduces failure rates through empirical testing rather than eliminating them through guarantees.

The difference from a traditional orchestrator: a traditional system fails with an error you can catch and fix. This system fails silently — the LLM just doesn't do what you asked, and you only notice when the output is wrong.
