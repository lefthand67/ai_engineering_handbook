
---
title: Config-Driven Ignore Architecture Analysis
authors:
- name: Qwen Code
  email: rudakow.wadim@gmail.com
date: 2026-04-27
description: Architectural analysis and validation of the migration from hardcoded
  exclusions in paths.py to a unified, structured ignore manifest in .vadocs/.
tags:
- architecture
- governance
- documentation
options:
  type: analysis
  birth: 2026-04-27
  version: 1.3.0
  token_size: 2488
  id: A-26024
  status: active
---
# Config-Driven Ignore Architecture Analysis

## Problem Statement
The toolkit's path discovery and filtering logic is currently centralized in `tools/scripts/paths.py`. While functional, this file contains a "transitional kernel" that mixes utility functions with hardcoded data lists (e.g., `_STATIC_EXCLUDE_DIRS`).

**Architectural Conflict [ISO 29148: Verifiability]:**
The project mandate (as per the `misc/plan/plan_20260308_ecosystem_roadmap_vadocs_to_mentor.md` and ADR-26012) requires the toolkit to be "org-agnostic" and "config-driven." Hardcoding infrastructure noise (like `.git`, `.venv`, `node_modules`) directly in Python code violates the Single Source of Truth (SSoT) principle and forces code changes for simple configuration updates, creating unnecessary friction in the CI/CD pipeline.

**Root Cause Analysis:**
The technical debt originated from **Prototyping Convenience Bias**. During the early stages of the toolkit, hardcoding `_STATIC_EXCLUDE_DIRS` provided the lowest latency for implementation. However, as the project moved toward "org-agnostic" requirements, this convenience became a blocker for portability and traceability, transforming a temporary shortcut into a structural bottleneck.

## Approach Evaluation

### Validation Gap Analysis
The following table maps the current state against the required industrial-grade standards.

| Subjective Claim | Falsifiable Metric | Gap / Required Evidence |
| :--- | :--- | :--- |
| "Hardcoded Kernel" | Ratio of config-to-code changes for ignore updates. | Currently 1:1 (Every config change requires a code commit). |
| "Org-Agnostic" | Time to adapt toolkit to a new project with different noise patterns. | High; requires manual editing of `paths.py`. |
| "Scalability" | Cognitive load to audit all active exclusions across the toolkit. | High; excludes are scattered between `paths.py` and registry manifests. |
| "Professionalism" | Compliance with SWEBOK Software Configuration Management. | Fail; configuration is embedded in executable logic. |

### Assumption Interrogation
| Assumption | Status | Falsification Evidence |
| :--- | :--- | :--- |
| JSON is the optimal format for humans | **Plausible** | User preference survey favoring YAML for manual edits. |
| `global` ignores are universal across all tools | **Unsupported** | A tool (e.g., a git-history analyzer) that *requires* access to `.git`. |
| A single `ignores.json` will not bloat | **Plausible** | The `tools` map exceeding 100+ entries, leading to "Hub" symptoms. |
| Tools will implement the two-tier logic | **Unverified** | Actual implementation of the loading logic in `paths.py`. |

### Architectural Alternatives Considered
To arrive at the proposed design, several iterations were analyzed to balance **Centralization**, **Isolation**, and **Cognitive Load**.

- **Trial 1: The Monolith Hub**: Move all exclusion lists directly into the main `.vadocs/conf.json`.
  - **Pros**: Single file for all configuration.
  - **Cons**: The Hub becomes a "junk drawer." Adding tool-specific excludes for 15+ scripts would bloat the core governance config.
  - **Verdict**: Rejected due to poor scalability.
- **Trial 2: Fragmented Spokes (Complete Isolation)**: Create a separate JSON file for every list (e.g., `api_keys.json`) in a `validation/` directory.
  - **Pros**: Maximum isolation; no file is too large.
  - **Cons**: "File sprawl." Developers must search through multiple files to manage a single concept.
  - **Verdict**: Rejected due to high cognitive load and fragmentation.
- **Trial 3: Tiered Operational Governance**: Create a `.vadocs/operational/` directory to separate "Execution" from "Domain".
  - **Pros**: Better semantic separation than the `validation/` folder.
  - **Cons**: Still suffered from fragmentation; structure remained overly complex for the current project scale.
  - **Verdict**: Evolved into the proposed Unified Manifest.
- **Trial 4: The Registry Pattern**: Use `.vadocs/conf.json` as a registry of pointers (e.g., `"excludes": "operational/ignores.json"`).
  - **Pros**: Decouples the Hub from the actual data.
  - **Cons**: Added a layer of indirection that is unnecessary for the current scale.
  - **Verdict**: Integrated into final logic but simplified.

### Proposed Target Architecture: The Unified Manifest
The proposed design adopts a centralized manifest approach, prioritizing **Cohesion** and **Developer Intuition**.

**Structure: `.vadocs/ignores.json`**
- **`global`**: A list of paths that are "environmental noise" (e.g., `.git`, `.venv`). These are ignored by *every* tool in the ecosystem.
- **`tools`**: A map of tool-specific exceptions. This allows "business rules" (e.g., skipping a specific file in the API key scanner) to coexist with global rules without polluting them.

```json
{
  "global": [".git", ".venv", "node_modules"],
  "tools": {
    "tool_name": {
      "files": ["path/to/exception.md"],
      "strings": ["ignore-this-string"]
    }
  }
}
```

### Quantitative Validation (WRC)

**Current State Audit (Hardcoded)**
- **P_raw**: 0.40
- **SVA Penalties**:
  - C1 (Automation): Fail. Config changes require code commits. (-0.10)
  - C2 (Portability): Fail. Org-specific noise is baked into source. (-0.10)
  - C6 (Scalability): Fail. Noise grows linearly in code. (-0.10)
- **P_final**: 0.10
- **Total WRC**: **0.135** (PoC-only / Technical Debt)

**Proposed State Audit (Unified Manifest)**
- **P_raw**: 0.95
- **SVA Penalties**: None detected.
- **P_final**: 0.95

**WRC Calculation:**
| Component | Value | Weight | Weighted Score | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **E (Empirical)** | 0.90 | 0.35 | 0.315 | Standard pattern used by modern CLI tools. |
| **A (Adoption)** | 0.90 | 0.25 | 0.225 | Ubiquitous adoption of `.ignore` manifests. |
| **P (Performance)**| 0.95 | 0.40 | 0.380 | Zero overhead; high readability. |
| **Total WRC** | **0.92** | | | **Production-Ready** |

### Methodology Comparison

| Methodology | Description with WRC | Pros | Cons | Best For | Source |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Unified Manifest** | **(WRC 0.92)** [E: 0.9 / A: 0.9 / P: 0.95] Centralized JSON with tiers. | High cohesion, easy to audit. | No local-folder overrides. | Mid-sized project kernels. | Community |
| **Standard `.gitignore`**| (WRC 0.85) [E: 0.95 / A: 0.95 / P: 0.75] Parsing `.gitignore`. | Zero config duplication. | Limited to git-patterns. | Simple file discovery. | Enterprise |
| **Hierarchical Config** | (WRC 0.82) [E: 0.8 / A: 0.7 / P: 0.85] Folder-level ignore files. | Maximum granularity. | High fragmentation. | Massive monorepos. | Enterprise |
| **Env-Var Flags** | (WRC 0.60) [E: 0.5 / A: 0.6 / P: 0.70] CLI flags. | No file dependencies. | Non-persistent. | Ephemeral PoCs. | Community |

**Viability Classification:** **Production-Ready**. Satisfies all SVA criteria, maintains Git-native traceability, and aligns with industry-standard patterns.

## Key Insights

### Actionable Strategies
1. **The Layered Filter Pattern (WRC 0.94) [E: 0.9 / A: 0.9 / P: 0.95]**: Implement a filtering pipeline in `paths.py` applying masks in sequence: `System Global` $\rightarrow$ `Project Global` $\rightarrow$ `Tool Specific` $\rightarrow$ `Local Override`.
   - **The Trade-off**: [Complexity / Precision]. Increases logic complexity but eliminates false positives.
   - **Reliable sources**: *The Art of Unix Programming* [Eric S. Raymond], 2003.
2. **Schema-Enforced Governance (WRC 0.88) [E: 0.8 / A: 0.8 / P: 0.90]**: Define a JSON Schema for `.vadocs/ignores.json` and integrate it into the `pre-commit` pipeline.
   - **The Trade-off**: [Maintenance / Integrity]. Adds a schema file but prevents broken configs from crashing the pipeline.
   - **Reliable sources**: *JSON Schema Specification* [IETF], 2017.

### Pitfalls & Security
- **The Global Blindspot:** Tools requiring `.git` access will be blind by default.
  - **Mitigation:** Update `is_excluded` to allow an explicit `bypass_global_ignores` flag.
- **Path Normalization:** Static JSON strings fail across OSes (`/` vs `\`).
  - **Mitigation:** Normalize all paths using `pathlib` before comparison.
- **Secret Leakage:** Using `ignores.json` to hide sensitive files leaks their existence if the manifest is committed.
- **Path Traversal:** Ensure `tools` exceptions do not allow escaping the project root via `../` patterns.

## Appendix
**Conclusion & Next Steps:**
The migration from `paths.py` to `.vadocs/ignores.json` transforms the toolkit from a collection of scripts with hardcoded assumptions into a professional, config-driven system.

1. Implement `.vadocs/ignores.json` manifest.
2. Refactor `tools/scripts/paths.py` to load this manifest.
3. Update the `is_excluded` logic to support normalized paths and the `bypass_global_ignores` flag.

## References
- ISO 29148:2018 - Systems and software engineering — Life cycle processes — Requirements engineering.
- SWEBOK Guide v4 - Software Engineering Body of Knowledge.
- Git Configuration Specification [Git-scm.com].
- The Twelve-Factor App [Adam Wiggins], 2011.
- JSON Schema Specification [IETF], 2017.
