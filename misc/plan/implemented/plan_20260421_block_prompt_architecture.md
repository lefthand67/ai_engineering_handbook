# Plan: Block-Based Prompt Architecture (SSoT)

**Date:** 2026-04-21
**Status:** Active (Refining Path Resolution)
**Related ADRs:** ADR-26047 (Heuer), ADR-26048 (WRC)
**Goal:** Migrate monolithic consultant prompts to a JIT-composed block architecture to ensure Single Source of Truth (SSoT) for shared methodology, user stacks, and tradecraft.

## 0. Session Progress (Handoff)

The following work has been completed in the current session:
- **Infrastructure**: Created `ai_system_layers/3_prompts/blocks/` hub.
- **SSoT Extraction**: Created core block files (`common_user_stack.json`, `common_principles.json`, `wrc_sva_framework.json`, `standard_output_protocol.json`, `heuer_tradecraft.json`).
- **Compiler Upgrade**: Implemented recursive `_includes` resolution in `tools/scripts/prepare_prompt.py`.
- **TDD**: Added 117 tests covering recursive, nested, circular, and adversarial scenarios (94% coverage).
- **Migration**: Converted all 4 consultant monoliths into thin manifests.
- **Documentation**: Updated `ai_system_layers/3_prompts/README.md` to describe the Block Architecture.

**Current Blocker / Next Step**: The `_includes` resolution currently relies on relative paths from the CWD. This is fragile. **The next agent should immediately start with Task 6: Path Resolution & Config SSoT.**

---

## 1. Full Context Analysis

### Current State
Prompts are stored as monolithic JSON files in `ai_system_layers/3_prompts/consultants/`. Core logic (WRC, SVA, User Stack, Principles) is duplicated across these files.

**File Breakdown:**
- `ai_systems_consultant.json`: Contains full WRC/SVA logic, full user stack, core principles.
- `devops_consultant.json`: Contains full WRC/SVA logic, full user stack, core principles.
- `ai_brainstorming_colleague.json`: Contains partial user stack, partial principles.
- `handbook_consultant.json`: Contains partial user stack, partial principles.

### Directory Tree (Current)
```
ai_system_layers/3_prompts/consultants/
├── ai_brainstorming_colleague.json
├── ai_systems_consultant.json
├── devops_consultant.json
└── handbook_consultant.json
```

### Target State
Prompts are split into **Manifests** (consultant-specific) and **Blocks** (shared). `prepare_prompt.py` resolves these at runtime.

**Directory Tree (Target):**
```
ai_system_layers/3_prompts/
├── blocks/
│   ├── common_user_stack.json
│   ├── common_principles.json
│   ├── wrc_sva_framework.json
│   ├── standard_output_protocol.json
│   └── heuer_tradecraft.json
└── consultants/
    ├── ai_brainstorming_colleague.json (Manifest)
    ├── ai_systems_consultant.json (Manifest)
    ├── devops_consultant.json (Manifest)
    └── handbook_consultant.json (Manifest)
```

---

## 2. Cross-Reference Map

| Original File | Target Block / Manifest | Change Type |
|---|---|---|
| `ai_systems_consultant.json` $\rightarrow$ `user_stack` | `blocks/common_user_stack.json` | Move to Block |
| `ai_systems_consultant.json` $\rightarrow$ `principles` | `blocks/common_principles.json` | Move to Block |
| `ai_systems_consultant.json` $\rightarrow$ `wrc_sva` | `blocks/wrc_sva_framework.json` | Move to Block |
| `ai_systems_consultant.json` $\rightarrow$ `output_protocol` | `blocks/standard_output_protocol.json` | Move to Block |
| `devops_consultant.json` $\rightarrow$ `user_stack` | `blocks/common_user_stack.json` | Move to Block |
| `devops_consultant.json` $\rightarrow$ `wrc_sva` | `blocks/wrc_sva_framework.json` | Move to Block |
| All Consultants $\rightarrow$ Heuer Tradecraft | `blocks/heuer_tradecraft.json` | New Injection |

---

## 3. Task Rationale & Operations

### Task List
- ✅ Task 1: Infrastructure Setup
- ✅ Task 2: Block Extraction (SSoT)
- ✅ Task 3: JIT Builder Upgrade (`prepare_prompt.py`)
- ✅ Task 4: TDD Verification
- ✅ Task 5: Manifest Migration
- ⏭️ Task 6: Path Resolution & Config SSoT (Immediate Next Step)

---

### Task 1: Infrastructure Setup (Completed)
**Rationale:** Create the storage location for reusable prompt fragments.
**Action:** `mkdir -p ai_system_layers/3_prompts/blocks/`

### Task 2: Block Extraction (SSoT) (Completed)
**Rationale:** Isolate shared logic into atomic files to eliminate duplication.
**Blocks created:**
- `common_user_stack.json`: The authoritative technical environment description.
- `common_principles.json`: "Emotionless", "Anti-bias", "Peer Review" rules.
- `wrc_sva_framework.json`: The full WRC formula, SVA C1-C6 constraints, and audit protocols.
- `standard_output_protocol.json`: The response structure, ISO 29148 tagging, and formatting rules.
- `heuer_tradecraft.json`: The procedural instructions for ACH and bias mitigation (from ADR-26047).

### Task 3: JIT Builder Upgrade (`prepare_prompt.py`) (Completed)
**Rationale:** `prepare_prompt.py` upgraded to a recursive composer.
**Logic Implemented:**
1. Load JSON.
2. If `_includes` key exists, iterate through paths.
3. Recursively load and merge included JSON blocks.
4. Final merge: Consultant Manifest overrides $\rightarrow$ Block contents.
5. Remove `_includes` key from final output.

### Task 4: TDD Verification (Completed)
**Rationale:** Builder handles edge cases safely.
**Tests Added:**
- Zero Includes, Single Include, Multiple Includes, Nested Includes, Missing File, Circular Dependency, Adversarial Deep Nesting (50+ levels), Type Mismatches.

### Task 5: Manifest Migration (Completed)
**Rationale:** Convert existing monoliths into clean manifests.
**Actions:**
1. Removed duplicated `user_stack`, `wrc_sva`, `principles`, and `output_protocol` sections from consultants.
2. Added `"_includes": [...]` at the top of each manifest.
3. Retained unique `persona`, `role`, and consultant-specific `goals`.

### Task 6: Path Resolution & Config SSoT (Refinement)
**Rationale:** Currently, `_includes` are resolved relative to CWD, which is fragile. We need an absolute reference point for the blocks hub.
**Operation:**
1. **Config SSoT**: Add `[tool.prompt_blocks]` section to `pyproject.toml` defining `blocks_dir = "ai_system_layers/3_prompts/blocks"`.
2. **Root Detection**: Update `prepare_prompt.py` to detect the project root (via `.git` or `pyproject.toml`).
3. **Path Resolution**:
    - Load `blocks_dir` from config.
    - In `_resolve_includes`, if an include path is relative, resolve it against the configured `blocks_dir` relative to the project root.
4. **Verification**: Add tests that run `prepare_prompt.py` from subdirectories to ensure blocks are still resolved correctly.

---

## 4. Implementation Details

### New File: `blocks/common_user_stack.json`
```json
{
  "user_stack": {
    "OS": "Fedora/Debian",
    "languages": "Python, SQL, Bash, C",
    "ml": "numpy, pandas, matplotlib, scikit-learn, PyTorch/Tensorflow",
    "devops": "GNU/Linux, git, pre-commit, github actions, podman",
    "db": "PostgreSQL, psycopg",
    "ai": "ollama, litellm, HuggingFace",
    "documentation": ["JupyterLab>=4", "MyST", "LaTex", "Markdown", "jupytext"]
  }
}
```

### New File: `blocks/common_principles.json`
```json
{
  "core_principles": {
    "user_friendliness": "Use user-friendly language; technical and concepts overload makes the text much harder to comprehend by human reviewers which is a kind of technical debt.",
    "emotionless": "Be honest and objective without trying to be liked. No emotions, no empathy, only reasoning.",
    "anti_emotional_bias": "NEVER use evaluative language that implies subjective praise (e.g., 'powerful', 'brilliant'). ONLY use technical, falsifiable descriptors (e.g., 'empirically validated', 'fails on null inputs'). Treat all user claims as hypotheses to be stress-tested.",
    "peer_review": "Internally peer review your answer before final output for objectivity."
  }
}
```

### New File: `blocks/wrc_sva_framework.json`
```json
{
  "wrc_framework": {
    "definition": "Weighted Response Confidence (WRC) is a quantitative metric (0.00 to 1.00) based on three component scores (E, A, P).",
    "formula": "WRC = (E * 0.35) + (A * 0.25) + (P * 0.40).",
    "components": {
      "E": "Empirical Evidence Score (Quantifies support from research/benchmarks).",
      "A": "Industry Adoption Score (Quantifies use in production MLOps/DevOps environments).",
      "P": "Predicted Performance Score (P_final) -- suitability for the local stack AFTER SVA Penalty Audit."
    },
    "sva_violations": {
      "C1": "Automation-First Operation: workflow step not executable non-interactively via CLI or API (Penalty: -0.10)",
      "C2": "Vendor Portability: single-vendor dependency that prevents migration within one sprint (Penalty: -0.10)",
      "C3": "Git-Native Traceability: artifacts not stored in version-controlled, text-diffable formats (Penalty: -0.10)",
      "C4": "Proportional Complexity: component cost exceeds the cost of the problem it addresses (Penalty: -0.10)",
      "C5": "Reuse Before Invention: duplicates logic already present in an existing, tested component (Penalty: -0.10)",
      "C6": "Bounded Scalability: undocumented or unfixable degradation at 10x input growth (Penalty: -0.10)"
    },
    "p_min_production": "Any solution with Final P < 0.70 after penalties is automatically classified as PoC-only. Production-ready solutions must achieve WRC >= 0.89."
  },
  "wrc_protocols": {
    "p_score_audit": [
      "1. Score P_raw (0.00-1.00) based on local stack suitability.",
      "2. Audit the proposal against C1-C6 SVA violations.",
      "3. Calculate Penalty: Penalty = (Number of violations) * 0.10.",
      "4. Calculate Final P: P_final = P_raw - Penalty."
    ],
    "wrc_calculation_cot": [
      "1. Weighted E Score Calculation: E_score = [E_value] * 0.35",
      "2. Weighted A Score Calculation: A_score = [A_value] * 0.25",
      "3. Weighted P Score Calculation: P_score = [P_final] * 0.40",
      "4. Total WRC Calculation: WRC = [E_score] + [A_score] + [P_score]"
    ]
  }
}
```

### New File: `blocks/heuer_tradecraft.json`
```json
{
  "heuer_tradecraft": {
    "objective": "Mitigate cognitive bias and 'Satisficing' in LLM analysis by forcing divergent analytical paths.",
    "protocols": {
      "disconfirmation": "Prioritize evidence that DISPROVES the primary hypothesis over evidence that confirms it.",
      "ach_mandatory": "Analysis of Competing Hypotheses: Explicitly list 3+ plausible alternative explanations for any observed pattern.",
      "linchpin_analysis": "Identify the 'Linchpin Assumption'—the single point of failure that, if proven false, collapses the entire recommendation."
    },
    "bias_check": [
      "Is this narrative too 'smooth'? (Sign of Satisficing)",
      "Am I ignoring outliers because they don't fit the WRC high-score narrative?",
      "Would a critical peer find this evidence insufficient?"
    ]
  }
}
```

---

## 5. Verification Commands

| Command | Expected Output |
|---|---|
| `mkdir -p ai_system_layers/3_prompts/consultants/blocks/` | Directory created successfully |
| `uv run tools/scripts/prepare_prompt.py ai_system_layers/3_prompts/consultants/ai_systems_consultant.json` | Final prompt contains merged content from all included blocks |
| `uv run pytest tools/tests/test_prepare_prompt.py` | All tests (Zero, Single, Multiple, Nested, Missing, Circular) PASS |
| `uv run tools/scripts/check_json_files.py` | All `.json` files are syntactically valid |

## 6. Self-Review Checklist
- [ ] Recursive inclusion supported? ✅
- [ ] Circular dependency protection implemented? ✅
- [ ] Missing file leads to exit 1? ✅
- [ ] SSoT achieved for WRC/SVA/UserStack? ✅
- [ ] Heuer Tradecraft integrated via block? ✅
- [ ] Manifests are significantly smaller and focused on persona? ✅
- [ ] TDD tests cover all boundary cases? ✅
- [ ] Block path resolution is config-driven and CWD-independent? ✗
