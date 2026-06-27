---
title: 'The Superpowers Methodology: Agent-Centric Engineering & Skill Design'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Agent-centric engineering methodology treating process as code, covering
  TDD for skills, golden examples, rubric-based validation, and the three-layer skill
  architecture.
tags:
- agents
- development
- workflow
date: '2026-06-28'
options:
  type: guide
  birth: '2026-06-28'
  version: 1.0.0
  token_size: 4300
---
# The Superpowers Methodology: Agent-Centric Engineering & Skill Design

## Overview: Process-as-Code
The `superpowers` project is not merely a collection of instructions; it is a software development methodology where **process is treated as code**. The core philosophy is that agent behavior should not be left to chance or "good prompting," but should be engineered through a repeatable, verifiable, and iterative pipeline.

The goal is to transform the AI agent from a "guessing machine" into a disciplined engineer that follows a mandatory, linear workflow.

---

## 1. The General Engineering Pipeline
For any new task (feature or bug), the project enforces a strict, linear pipeline. Jumping straight to code is considered a process failure.

### The Workflow Stages:
1.  **Socratic Brainstorming $\rightarrow$ Spec**: 
    *   The agent does not implement; it interrogates. 
    *   It refines rough ideas through targeted questioning, explores alternatives, and presents the design in digestible chunks for human validation.
    *   **Outcome**: A validated design document.
2.  **Environmental Isolation (Git Worktrees)**:
    *   Work is performed in isolated git worktrees.
    *   This ensures a clean baseline and prevents the "pollution" of the main development branch during experimental phases.
3.  **Bite-Sized Planning**:
    *   The approved spec is broken down into a high-granularity implementation plan.
    *   **Constraint**: Tasks must be "bite-sized" (typically 2–5 minutes each).
    *   **Requirement**: Every task must list exact file paths and specific verification steps.
4.  **Subagent-Driven Development**:
    *   Fresh subagents are often dispatched to handle individual tasks.
    *   **Two-Stage Review**: Each task undergoes a review for **spec compliance** (did it meet the design?) followed by a review for **code quality**.
5.  **Strict TDD (RED-GREEN-REFACTOR)**:
    *   Implementation is governed by a rigid TDD cycle.
    *   **The Hard Rule**: Writing implementation code before a failing test is a violation. In strict mode, code written before the test is deleted.
6.  **Branch Finalization**:
    *   Final verification of tests, clean-up of the worktree, and a decision on the merge/PR strategy.

---

## 2. The Meta-Workflow: TDD for Skills
Because the "product" of this repository is the skills themselves, the developers apply TDD to **documentation**. They treat a skill as a "behavior-shaping program."

### The RED-GREEN-REFACTOR Cycle for Documentation:
*   **RED (Baseline Failure)**: 
    *   Run a "pressure scenario" (a complex task) with a subagent **without** the skill.
    *   Document exactly how the agent fails. 
    *   **Crucial Step**: Capture the "Rationalizations"—the specific excuses the agent makes to justify taking a shortcut or ignoring a rule.
*   **GREEN (Minimal Skill)**:
    *   Write a minimal `SKILL.md` that specifically addresses the observed failures and counters the documented rationalizations.
*   **REFACTOR (Loophole Closing)**:
    *   Run the scenario again. If the agent finds a new "loophole" or a new way to rationalize a mistake, the skill is updated to explicitly forbid that new behavior.
    *   The cycle repeats until the agent's behavior is bulletproof.

### The "Iron Law"
**No skill exists without a failing test first.**
Adding a section "just because it seems like a good idea" is forbidden. Every line of a skill must be a response to a documented failure.

---

## 3. PR Rigor & Quality Governance
The project maintains an intentionally high PR rejection rate (historically ~94%) to prevent "AI slop" and maintain a zero-dependency core.

### Acceptance Criteria:
*   **Evidence of Real Pain**: PRs must solve a problem that was actually experienced, not a theoretical "improvement" flagged by another AI.
*   **Human-in-the-Loop**: There must be clear evidence that a human reviewed the complete diff. Purely AI-generated PRs are closed immediately.
*   **Domain Purity**: Only general-purpose skills enter the core. Domain-specific tools (e.g., project-specific helpers) must be standalone plugins.
*   **Zero-Dependency**: No new third-party dependencies are accepted unless they enable a new harness (IDE/CLI).

---

## 4. Knowledge Management: Decisions vs. Examples

The repository distinguishes between **governance** (what we decided) and **training** (how we do it).

### ADRs vs. Golden Examples
*   **ADRs (Architectural Decision Records)**: These store the *Conclusion*. They answer: *"Why did we choose this path?"* They are for humans and maintainers.
*   **Golden Examples (Specs/Plans)**: These store the *Process*. They are archived in `docs/plans` and `docs/specs` as "Few-Shot" examples for agents.

### The "Few-Shot" Training Logic
Instead of giving an agent a rulebook on "how to write a spec," the project points the agent to a **Golden Example**. 
*   **Macro-Plans**: Permanent records of major architectural shifts. They serve as templates for future complex tasks.
*   **Micro-Plans**: Ephemeral task lists that live and die with the Git Worktree. They are not archived because their value is in the *execution*, not the *record*.

By providing "Golden Examples," the developers use the LLM's pattern-matching capability to enforce a level of detail and rigor that prose instructions alone cannot achieve.

### The Danger of Golden Examples: Pollution and Drift
Using "Golden Examples" is a double-edged sword. If applied naively, it leads to two major failures: **Context Pollution** and **Data Drift**.

**1. Context Pollution (Token Noise)**
Loading every example into the prompt is a catastrophe for the context window. It dilutes the agent's focus and consumes excessive tokens. 
*   **Mitigation (Selective/Lazy Loading)**: The goal is to avoid loading examples into the system prompt. Instead, the skill acts as a pointer. The agent is instructed: *"If you are unsure of the required depth for the Spec, read `docs/examples/perfect-spec.md`."* The agent reads the file, extracts the pattern into its short-term memory, and then proceeds. The example is a tool used for a moment, not a permanent weight in the prompt.

**2. Data Drift (Pattern Hallucination)**
This is the "silent killer" of agent-centric systems. As a project evolves (e.g., moving from a monolith to microservices), a "Golden Example" from six months ago will teach the agent to write outdated specs. In specialized domains like **Security**, this drift is critical: a pattern that was "Golden" two years ago may be a vulnerability today.

*   **Mitigation (Lifecycle Management)**: Golden Examples must be treated exactly like production code. They are not static archives; they are versioned assets. When the methodology changes, the example must be refactored or deleted immediately.
*   **TDD Signal**: The "TDD for Skills" cycle is the primary detection mechanism. If a developer notices an agent is producing "correct" but "outdated" patterns, it is a signal that the Golden Example has drifted and must be updated.
*   **The Freshness Constraint**: To prevent the agent from choosing between conflicting patterns, high-discipline teams often keep only the *most recent successful example* of a specific type, deleting older versions.

**The Trade-off: Guessing vs. Drift**
The developers of this repo have made a conscious trade-off. They believe the risk of **"AI-style guessing"** (relying on the LLM's generic, often mediocre training data) is far higher and more frequent than the risk of **"pattern drift."**

They would rather the agent be "consistently wrong" (which is easy to fix by updating one example) than "randomly mediocre" (which requires fighting the LLM's base nature in every single prompt).

**Advanced Guardrails: Negative Examples and Audits**
To further prevent drift and refine boundaries, one can implement:
*   **Anti-Patterns**: Create "Negative Examples" (e.g., `docs/examples/bad-br-fr.md`). By showing the agent a "mediocre" example and explicitly stating *"Do NOT do this,"* you create a behavioral boundary that supplements the Golden Example.
*   **Audit Triggers**: Integrate examples into the Post-mortem process. Every time a Post-mortem is written, ask: *"Did the agent follow an outdated Golden Example here?"* If the answer is yes, the example is treated as the bug, not the agent.

### Beyond Lazy Loading: Solving Content Contamination
Even with "Lazy Loading," if the agent reads a 2,000-token Golden Example every time it starts a task, you are still paying a "context tax" and, more importantly, you risk **Content Contamination**.

When an agent reads a specific example (e.g., a perfect spec for "User Authentication"), it often starts mimicking the *content* (mentioning tokens, passwords, or sessions) even when it's supposed to be writing a spec for "Database Indexing."

To be truly "smart" about this and avoid pollution, you move from **Few-Shot Mimicry** to **Rubric-Based Validation**.

#### Three Levels of Sophistication:

**Level 1: The Reviewer-Writer Split (The "Superpowers" Way)**
Instead of giving the Golden Example to the Writer (the agent doing the work), you give it only to the Reviewer (the subagent checking the work).
*   **The Writer**: Operates based on the `SKILL.md` instructions (the "Law"). It doesn't see the Golden Example.
*   **The Reviewer**: Has the Golden Example in its context. It doesn't rewrite the code; it provides a critique.
*   **The Result**: The Reviewer says: *"Your spec is too shallow. Compare your 'Edge Cases' section to the standard in `perfect-spec.md`. You are missing the level of detail regarding race conditions that we require."*
*   **Why this works**: The "Pollution" is isolated to the Reviewer agent. The Writer's context remains clean, and it only receives a high-level correction rather than a pattern to blindly mimic.

**Level 2: Distillation (The "Rubric" Approach)**
You treat the Golden Example as a source of truth to create a Rubric (a checklist of properties), then you throw the example away.
Instead of: *"Read this perfect spec and do the same,"* you write: *"A 'Golden Spec' must possess these 5 properties: (1) Lists at least 3 non-obvious edge cases, (2) References exactly which existing files will be modified, (3) Includes a 'Failure Mode' section... etc."*
*   **Why this works**: You've converted a Few-Shot Example (high token cost, high drift risk) into a Zero-Shot Rubric (low token cost, zero contamination).

**Level 3: The "Meta-Review" (The Ultimate Filter)**
You use a separate "Distiller Agent" to analyze the Golden Example and generate the Rubric automatically.
1.  **Distiller Agent**: Reads `perfect-spec.md` $\rightarrow$ Generates a `rubric.md` (the "DNA" of the example).
2.  **Writer Agent**: Uses `rubric.md` to write.
3.  **Reviewer Agent**: Uses `rubric.md` to validate.
*   **Why this works**: This is the cleanest possible architecture: The "Golden Example" is the seed, but the "Rubric" is the executable code. The actual example file never enters the production loop of a task.

#### Summary of the Evolution

| Stage | Method | Context Cost | Risk | Result |
| :--- | :--- | :--- | :--- | :--- |
| **Naive** | Dump examples in prompt | Very High | Massive Pollution | Generic "AI-style" slop |
| **Lazy** | Agent reads example on demand | Medium | Content Mimicry | Better, but "noisy" |
| **Split** | Reviewer holds the example | Low (Isolated) | Minimal | High rigor, clean writer |
| **Rubric** | Example $\rightarrow$ Rubric | Very Low | None | Surgical precision |

If you are building your own skills repo, don't just provide examples—provide rubrics derived from examples. That is how you achieve surgical precision without context pollution.

### Standards vs. Examples: The "Abstraction Gap"
A common question is whether a comprehensive standards document (e.g., a `testing_standards.md` that defines "Non-Brittle Assertions" and "Adversary Testing") is sufficient. While such documents are necessary as the "Law" of the project, they are often insufficient for LLMs due to the **Abstraction Gap**.

**The "What" vs. the "How"**
A standards document tells an agent **what** to do (e.g., *"Avoid brittle assertions"*), but it does not show them **how** to apply that rule to a specific, complex scenario. An LLM can read a rule and still produce a brittle assertion because it lacks a concrete "sense" of what "brittle" looks like in the context of a particular project. A Golden Example closes this gap by providing a concrete "This $\rightarrow$ That" transformation.

**The Ritual of Process**
Standard documents often enforce processes like TDD (Red $\rightarrow$ Green $\rightarrow$ Refactor). However, agents are notorious for "faking" these rituals—writing the test and the code simultaneously and claiming it was TDD. 
Golden Examples (especially those including session transcripts) demonstrate the **temporal sequence**: 
1.  Write a test.
2.  Observe a specific error message.
3.  Write the minimal code to fix it.
By showing the ritual, you teach the agent the *behavior* of TDD, not just the *definition* of it.

**The Constitution vs. Case Law**
To understand the relationship:
*   **Standards/Reference Skills are the Constitution**: They provide the foundational rules and boundaries.
*   **Golden Examples/Rubrics are the Case Law**: They show how the Constitution is applied in the real world to resolve specific, nuanced problems.

#### When is a Standard "Enough"?

| Scenario | Standard Document is Enough | Golden Example/Rubric is Required |
| :--- | :--- | :--- |
| **Agent Capability** | Highly experienced agent with a strong internal model of the domain. | Agent struggling with the "depth" or "style" of the required output. |
| **Task Complexity** | Straightforward tasks with clear, binary success criteria. | Complex tasks where "quality" is subjective or requires high nuance. |
| **Consistency** | When slight variance in implementation style is acceptable. | When absolute consistency across multiple different agents is required. |

---

## 5. Comparison: Human-Centric Governance vs. Agent-Centric Bootstrapping

When comparing a professional human-led engineering approach with the `superpowers` methodology, a fundamental difference in intent emerges: **Governance vs. Training**.

### Human-Centric Governance
This approach (exemplified by the use of **ADRs** and **Post-mortems**) is designed for human accountability and institutional memory.
*   **Focus**: The *Conclusion* and the *Lesson*.
*   **Primary Asset**: The ADR (Architectural Decision Record). It answers "Why did we do this?" and "What were the trade-offs?".
*   **Audit Trail**: Raw brainstorming records are kept in git memory for detailed forensic investigation if a decision is ever questioned.
*   **Goal**: To ensure a maintainable system where humans can understand the intent behind the code years later.

### Agent-Centric Bootstrapping
The `superpowers` approach is designed to solve the "LLM Variance" problem. It treats the codebase as a training set for the agent.
*   **Focus**: The *Process* and the *Pattern*.
*   **Primary Asset**: The "Golden Example." It answers "What does a perfect execution look like?".
*   **Audit Trail**: Specs and Plans are archived as few-shot templates. They aren't just records; they are active prompts.
*   **Goal**: To eliminate agent "guessing" by providing concrete targets that the LLM can pattern-match against.

### Summary Table

| Feature | Human-Centric Governance | Agent-Centric Bootstrapping |
| :--- | :--- | :--- |
| **Key Document** | ADR / Post-mortem | Golden Example (Spec/Plan) |
| **Mental Model** | "The Law" (Conclusion) | "The Tutorial" (Pattern) |
| **Primary Audience** | Humans / Maintainers | AI Agents / New Contributors |
| **Value Proposition** | Institutional Memory & Audit | Few-Shot Training & Consistency |
| **Success Metric** | a reasoned, documented decision | a behaviorally compliant agent |

---

## 6. Synthesis: The Anatomy of a "Complete Skill"

To build a truly professional, "bulletproof" skill, you are essentially creating a complete legal and operational framework for a specific behavior. If you look at it as a package, a "Complete Skill" consists of these three layers:

### 1. The Constitution (The `SKILL.md` / Reference)
*   **What it is**: The rules, the boundaries, the "musts" and "must-nots."
*   **Purpose**: To establish the legal framework. It defines what "Correct" looks like in theory.
*   **Example**: *"All validation scripts must have a corresponding test file. Avoid brittle assertions."*

### 2. The Case Law (The Golden Examples / Rubrics)
*   **What it is**: The evidence of the Constitution in action.
*   **Purpose**: To close the "Abstraction Gap." It shows the agent exactly how to apply the rules to a real-world, complex scenario.
*   **Example**: A session transcript showing the agent writing a failing test for a malformed YAML file, seeing the crash, and then implementing the fix.

### 3. The Infrastructure (The Tools / Supporting Files)
*   **What it is**: The machinery that makes the behavior easier to execute.
*   **Purpose**: To reduce cognitive load and prevent manual errors. If a task can be automated or templated, the agent shouldn't have to "think" about it.
*   **Example**: A `render-graphs.js` script to visualize flowcharts, or a `template.py` for a new validation script.

---

### The Final "Power Move": The Feedback Loop
The most important part of this entire system—the part that makes it "Superpowers" and not just "Documentation"—is that these three layers are linked by TDD.

1.  **Agent fails** $\rightarrow$ You realize the **Constitution** is missing a rule.
2.  **Agent is confused** $\rightarrow$ You realize the **Case Law (Example)** is missing or outdated.
3.  **Agent makes a mechanical error** $\rightarrow$ You realize the **Infrastructure (Tool)** needs to be built.

When you build specialized skills (e.g., for Security or BR/FR generation), providing all three—the Law, the Example, and the Tool—means you aren't just giving the agent a "tip," you are giving it a complete operational system that is almost impossible to deviate from.

