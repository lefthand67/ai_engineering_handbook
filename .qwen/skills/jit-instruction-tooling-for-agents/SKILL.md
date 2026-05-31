---
name: jit-instruction-tooling-for-agents
description: Designing validation tools that provide Just-In-Time (JIT) instructions to AI agents to prevent "diagnostic loops" and reduce token waste.
source: auto-skill
extracted_at: '2026-05-31T12:00:00.000Z'
---

## Overview
When AI agents encounter raw error messages from validation scripts, they often enter a "diagnostic loop": repeatedly reading the same source files across multiple turns to deduce the cause of the failure. This wastes tokens, increases latency, and frequently leads to cycles that require human intervention.

## The JIT Instruction Pattern
Instead of providing a binary pass/fail or a raw traceback, the tool should act as an **Instructor**, providing actionable guidance directly within the error output.

### Implementation Steps
1. **Identify the Failure Mode**: Determine exactly which rule was violated (e.g., missing frontmatter field, broken link, or invalid commit prefix).
2. **Generate a Direct Instruction**: Provide a clear, actionable "How-to-Fix" message.
   - **Ineffective (Raw Error)**: `Error: Field 'token_size' missing in file.md`
   - **Effective (JIT Instruction)**: `file.md:token_size — Missing required field. Action: Add 'token_size: <value>' to the options block in frontmatter. [config_source: .vadocs/types/guide.conf.json]`
3. **Enforce Precise Targeting**: The instruction should guide the agent to map the error to a specific fix and a specific file pair (e.g., the `.md` and its paired `.ipynb`), explicitly banning "global cleanups" or "fix-all" scripts.
4. **Contextualize the Fix**: If the fix depends on a configuration file or an ADR, reference the configuration source or ADR ID explicitly to prevent the agent from guessing.

## Validation and Testing
- **No-Vendor-Lock-In Testing**: Test the JIT instructions on lower-tier or open-source models (e.g., Gemma-4-31b). If the agent can resolve the error using only the JIT instructions without additional "exploration" reads, the instructions are sufficiently governed.
- **Metric for Success**: A measurable reduction in the number of `read_file` calls per error resolution cycle.
- **Behavioral Goal**: The agent should move directly from `Error -> Fix -> Stage` without an intermediate `Error -> Read -> Analyze -> Read -> Fix` sequence.
