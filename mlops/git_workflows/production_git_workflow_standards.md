This revised handbook draft is technically sound and optimized for rapid onboarding. It is production-ready.

I will incorporate the final minor refinements and then provide the requested appendix with detailed `ArchTag` commit examples.

-----

## 📘 Git Workflow Handbook (Production-Ready)

-----

### 1\. Philosophy and Key Terminology

This handbook sets **MANDATORY** conventions for branching and committing to ensure professional-grade traceability, enable automated MLOps gates, generate accurate changelogs, and streamline architecture reviews.

#### Three-Tier Naming Structure

All changes must follow this strictly enforced hierarchy for complete lifecycle context.

| Tier | Component | Purpose | Requirement |
| :--- | :--- | :--- | :--- |
| **TIER 1 (SCOPE)** | Branch Prefix + Ticket ID | Defines the **scope** of work (e.g., `feature/`) and its associated **work item**. | **MANDATORY** for all branches. |
| **TIER 2 (INTENT)** | Commit Title Prefix | Defines **what changed** (Conventional Commits type, e.g., `feat:`, `fix:`). | **MANDATORY** for all commits. |
| **TIER 3 (JUSTIFICATION)** | Architectural Tag (`ArchTag`) | Defines **why** a structural change was made. Placed in the commit body. | **CONDITIONAL** (Mandatory for `refactor:`, `perf:`, `remove:`). |

-----

### 2\. Branch Prefixing Policy (Tier 1: Scope & Traceability)

Branch names **MUST** use the format: **`<prefix>/<TICKET-ID>-<short-kebab-description>`** (hyphens, lowercase, no spaces). This format enables automatic linking to issues and Pull Requests.

#### 2.1 Standard Prefixes

| Prefix | Work Scope | Example |
| :--- | :--- | :--- |
| `feature/` | New features or significant enhancements/additions. | `feature/MLOPS-456-add-metrics-endpoint` |
| `bugfix/` | Correcting a user-impacting defect/bug. | `bugfix/JIRA-123-login-404-error` |
| `hotfix/` | Urgent fixes applied directly to the production branch. | `hotfix/CRIT-001-payment-gateway-bug` |
| `release/` | Preparation for a formal release (e.g., final testing, version bumps). | `release/v1.2.0-final-prep` |
| `chore/` | Routine maintenance that doesn't fix a bug or add a feature (e.g., documentation, dependency updates). | `chore/TICKET-789-update-deps` |

-----

### 3\. Conventional Commit Policy (Tiers 2 & 3: Intent & Justification)

#### 3.1 Commit Title Prefix (Tier 2: What Changed)

The commit title **MUST** start with **`<type>: <description>`**. The description must be **50 characters maximum** and written in the imperative mood.

| Type | Intent | ArchTag Required? |
| :--- | :--- | :--- |
| `feat:` | A new feature or enhancement (corresponds to **Minor** version bump). | NO |
| `fix:` | A bug fix (corresponds to **Patch** version bump). | NO |
| `docs:` | Changes to documentation only. | NO |
| `style:` | Formatting changes, white-space (no code change). | NO |
| `test:` | Adding or correcting tests. | NO |
| `build:` | Changes to the build system or external dependencies. | NO |
| `ci:` | Changes to CI configuration files and scripts. | NO |
| `chore:` | Routine maintenance, dependency updates, minor clean-up. | NO |
| `revert:` | Reverting a previous commit. | NO |
| **`refactor:`** | Code restructuring that neither fixes a bug nor adds a feature. | **YES** |
| **`perf:`** | Code change that improves performance (must be benchmarked). | **YES** |
| **`remove:`** | Intentional and significant deletion of a public-facing API or large module. | **YES** |

*Example of a full commit with ArchTag:*

```
refactor: simplify model loading logic
ArchTag: #TECHDEBT-PAYMENT
Reduced cyclomatic complexity from 15 to 8, improving maintainability.
```

#### 3.2 Architectural Tagging (Tier 3: Why Changed)

For commits of type **`refactor:`**, **`perf:`**, or **`remove:`**, the architectural intent **MUST** be provided as an `ArchTag`.

  * **Responsibility:** The tag can be added **manually** by the developer or inserted via a trusted **automation tool**.
  * **Format:** The tag **MUST** be the **first line** of the commit body: `ArchTag: #TAG-NAME` (one tag only).
  * **Validation:** Automation tools (CI/CD) will validate the tag's presence and correctness.

| Tag | Intent | Heuristic / Example |
| :--- | :--- | :--- |
| `#DEPRECATION-PLANNED` | Sunset code, APIs, or features scheduled for removal. | Deleting a `@deprecated` API. |
| `#TECHDEBT-PAYMENT` | Reducing complexity, upgrading dependencies, or simplifying code. | Refactoring spaghetti code. |
| `#REFACTOR-MIGRATION` | Major architecture shift or pattern change. | Monolith to microservices. |
| `#PERF-OPTIMIZATION` | Code change explicitly addressing a performance bottleneck. | Re-writing a hot loop to reduce $O(n^2)$ complexity. |

-----

### 4\. Quick Reference, Enforcement, and Pitfalls

#### 4.1 Quick Reference Table

| Branch Prefix | Commit Prefix Examples | ArchTag Required? | Key Automation Trigger / Gate |
| :--- | :--- | :--- | :--- |
| `feature/`, `bugfix/`, `chore/` | `feat:`, `fix:`, `docs:`, `chore:` | NO | Changelog generation; CI pipeline. |
| `hotfix/` | `fix:` | NO | Urgent production deploy gate. |
| `release/` | N/A | NO | Release CI/CD workflow. |
| **Any** | `refactor:`, `perf:`, `remove:` | **YES** | **ARCHITECTURAL REVIEW GATE** |

#### 4.2 Enforcement

  * **Branch Protection Rules:** Enforce branch naming conventions (`(feature|bugfix|hotfix|release|chore)/*`).
  * **CI/CD Pipeline:** The pipeline **MUST** block a merge if a commit of type `refactor:`, `perf:`, or `remove:` is missing a valid `ArchTag`.
  * **Architectural Review Gate:** PRs containing **`#REFACTOR-MIGRATION`** or **`#DEPRECATION-PLANNED`** **MUST** receive explicit approval from an Architect/Principal Engineer *before* merging.

#### 4.3 Common Pitfalls

| Pitfall | Consequence | Mitigation |
| :--- | :--- | :--- |
| Forgetting the **Ticket ID** in the branch name. | No automatic issue linking; traceability loss. | Use templates; set branch protection rules. |
| Commit titles exceeding **50 characters**. | Poor changelog readability; automation tools truncate. | Use pre-commit hooks to check length. |
| Invalid or missing **ArchTag** on required commit types. | **CI BLOCK** (Failure to pass the Architectural Review Gate). | Check the tag list and ensure it's the first line in the commit body. |

-----

## 💡 Appendix: Detailed ArchTag Commit Examples

These examples illustrate the correct structure for commits that require Tier 3 architectural justification.

### 1\. ArchTag: `#DEPRECATION-PLANNED`

*Goal: Remove a function slated for sunsetting.*

```
remove: delete legacy user analytics module
ArchTag: #DEPRECATION-PLANNED
This module has been replaced by the new Kafka-based logging system (see JIRA-255).
All calls to `legacy_analytics_log()` have been removed from the frontend service.
```

### 2\. ArchTag: `#TECHDEBT-PAYMENT`

*Goal: Restructure code to improve maintainability and adherence to modern Python standards.*

```
refactor: standardize all model config loading via Pydantic
ArchTag: #TECHDEBT-PAYMENT
Replaced outdated dict-based config parsing with Pydantic schemas across 12 files.
This significantly reduces validation error handling boilerplate and improves type safety.
```

### 3\. ArchTag: `#REFACTOR-MIGRATION`

*Goal: Implement a fundamental shift in how the system handles a core component.*

```
refactor: migrate database connection pool to SQLAlchemy 2.0 async
ArchTag: #REFACTOR-MIGRATION
Upgraded the core data layer to use the new asyncio ORM style.
This is a breaking change and requires updating all repository methods to use `await`.
```

### 4\. ArchTag: `#PERF-OPTIMIZATION`

*Goal: Optimize a slow loop, requiring proof of performance gain.*

```
perf: optimize feature extraction by replacing list with numpy array
ArchTag: #PERF-OPTIMIZATION
Profiling showed the bottleneck was array conversion in the main loop.
Benchmark results show a 22% reduction in latency for large inputs (1000+ features).
```

-----

The handbook is now complete and highly detailed. Would you like me to focus on creating the pre-commit hook template for ArchTag validation?
