# Project Freeze State - ADR Governance Merge

**Verified: 2026-06-28** — Logic migrated and old script deleted (commit `889028c`). CLI integration, ADR-26058 doc, and term-reference flags remain pending.

## Objective
Merge `tools/scripts/check_adr_index.py` into `tools/scripts/check_adr.py` to create a single authoritative tool for ADR structural and relational validation.

## Completed Work
- **Logic Migration**: Core functions `validate_index_sync`, `fix_index`, `find_broken_term_references`, `validate_term_references`, `fix_term_references` are present in `tools/scripts/check_adr.py`.
- **Cleanup**: `tools/scripts/check_adr_index.py` and `tools/tests/test_check_adr_index.py` deleted (commit `889028c`). `check_adr_index_recovered.py` also removed.
- **Test Adjustments**: `test_check_adr.py` imports updated; `TestIndexSyncEdgeCases` and `TestPartitionedIndex` cover index sync logic. All 130 tests pass (`uv run pytest tools/tests/test_check_adr.py`).

## Pending Tasks
1. **CLI Integration**: The `main()` function in `tools/scripts/check_adr.py` (lines 559–679) currently defines only `--verbose`, `--fix` (structural only), and `--migrate`. The following flags are **not wired**:
   - `--fix` must be expanded to call `fix_index()` for index regeneration (currently only calls `fix_invalid_status`, `fix_title_mismatch`, `fix_duplicate_sections`).
   - `--check-terms` — call `validate_term_references()`, report errors, exit 1 if blocking.
   - `--fix-terms` — call `fix_term_references()`, report fixed files.
2. **Test Coverage for Term Refs**: No tests reference `--check-terms` or `--fix-terms` CLI paths (since the flags don't exist). Once implemented, add tests mirroring the old `test_check_adr_index.py` cases.
3. **Documentation**: Create `architecture/adr/adr_26058_consolidation_of_adr_governance_tooling.md` to formalize this architectural change. File does not exist yet.

## Artifacts
- `tools/scripts/check_adr.py` (679 lines): Contains merged logic but CLI is incomplete.
- `tools/tests/test_check_adr.py` (2500+ lines): 130 tests pass; missing term-reference CLI tests.

---

# Project Freeze: 2026-06-13 (SkillOpt Adoption)

**Verified: 2026-06-28** — Frontmatter fix and tests already committed. SkillOpt artifacts remain untracked; `adr_index.md` modified but unstaged.

## Status: In-Progress

### Goal
Finalize the adoption of SkillOpt for empirical agent skill optimization and fix a critical bug in the frontmatter validator that caused false positives with Mermaid diagrams.

### Completed Work
- Fixed `tools/scripts/check_frontmatter.py` to correctly identify the project metadata block and ignore subsequent Mermaid fences in the document body.
- Added TDD tests in `tools/tests/test_check_frontmatter.py` (`TestMermaidFalsePositives`) to prevent regressions.
- Corrected frontmatter in `architecture/evidence/sources/S-26025_skillopt_adoption_analysis.md` (removed illegal fields, updated token size, moved model to options).
- Verified that SkillOpt adoption artifacts (`S-26025`, `A-26026`, `ADR-26057`) and `architecture/adr_index.md` pass validation with the fixed parser.
- `tools/scripts/check_frontmatter.py` and `tools/tests/test_check_frontmatter.py` are **already committed** (no modifications in working tree).

### Pending Tasks
- [ ] Stage and commit the following **untracked** files (`git status` shows `??`):
    - `architecture/evidence/sources/S-26025_skillopt_adoption_analysis.md`
    - `architecture/evidence/analyses/A-26026_skillopt_adoption_comparative_analysis.md`
    - `architecture/adr/adr_26057_adoption_of_skillopt_for_empirical_agent_skill_optimization.md`
- [ ] Stage and commit the **modified** file (`git status` shows `M`):
    - `architecture/adr_index.md` (updated with ADR-26057 entry)
- [x] ~~`tools/scripts/check_frontmatter.py`~~ — already committed
- [x] ~~`tools/tests/test_check_frontmatter.py`~~ — already committed

---

# Critical Next Step: Agent Workflow & Governance Transition

**Verified: 2026-06-28** — ADR-26055 exists. `CONSTITUTION.md` not created. Symlinks unchanged (`QWEN.md`, `CLAUDE.md` → `AGENTS.md`). Not started.

## Objective
Implement the transition to the **Modular Knowledge Pull Architecture** as defined in [ADR-26055](/architecture/adr/adr_26055_modular_knowledge_pull_architecture.md).

## The "Symlink vs. Token Bloat" Problem
There is a critical conflict between current maintenance efficiency and the goal of reducing system prompt bloat:
- **Current State**: `QWEN.md`, `CLAUDE.md`, etc., are symlinked to `AGENTS.md`. This allows "edit once, update all" maintenance across different agent platforms.
- **ADR-26055 Requirement**: Move detailed procedural workflows out of the primary entry point to prevent "Token Bombs" and "Needle-in-a-Haystack" failures.
- **The Conflict**: Simply breaking the symlinks to reduce tokens would force the maintainer to edit 3+ files for every rule change, violating the Single Source of Truth (SSoT) principle.

## Required Resolution Path
The implementation must find a "Logical Single Point" that preserves maintenance efficiency without inflating the prompt. 
**Proposed Approach**:
1. **Split Master**: Create a `CONSTITUTION.md` (Global Invariants SSoT) and keep `AGENTS.md` (Operational Manual SSoT).
2. **Dual Symlinking**: All agent entry points symlink to `CONSTITUTION.md`.
3. **Pull-Based Discovery**: The Constitution directs agents to "pull" detailed workflows from `AGENTS.md` and specialized Skills only when needed.

---

# Future Brainstorming: AI-Native Evolution via Knowledge Pull

**Verified: 2026-06-28** — Correctly deferred. Sections 1 and 2 still incomplete; this section must not be started until they are resolved.

**Status: Unsolved Problem**
**Constraint**: This must be brainstormed and designed **ONLY after** all current unfinished work (ADR Governance Merge and SkillOpt Adoption) is fully completed and committed.

## Goal
Transition the project from a "human-authored, AI-assisted" repository to a "really AI-native" project where the project's own evolution is governed by the same "Pull" mechanisms used for task execution.

## The Roadmap as a "Strategic SOP"
The need for a centralized roadmap should not be solved by creating another monolithic file to be "pushed" into prompts. Instead, the roadmap must be the first major artifact of the **Modular Knowledge Pull Architecture**:

1. **Roadmap as Routing Layer**: The roadmap should not just list features, but act as a high-level map that routes agents to the specific Modular SOPs (Skills) required to achieve each milestone.
2. **Pull-Based Progress Tracking**: Instead of agents reading a static roadmap, they should be able to "pull" the current strategic phase, identify the gap between the current state and the roadmap's target, and then pull the necessary operational skills to close that gap.
3. **Machine-Queryable Trajectory**: By structuring the roadmap as a pullable artifact (with frontmatter and modular sections), we enable agents to autonomously prioritize tasks based on the project's long-term trajectory without overloading the context window.

This transforms the roadmap from a passive document into an active, architectural component that drives the project's autonomous evolution.


