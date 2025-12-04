# Production Git Workflow Standards

-----

Owner: Vadim Rudakov, lefthand67@gmail.com
Version: 0.4.0
Birth: 2025-11-29
Last Modified: 2025-12-04

-----

This handbook sets **MANDATORY** conventions for branching and committing. Adherence ensures professional-grade traceability, enables automated MLOps gates, generates accurate changelogs, and streamlines architectural reviews.

## 1. Three-Tier Naming Structure

All changes must follow this strictly enforced hierarchy for complete lifecycle context.

| Tier | Component | Purpose | Requirement |
| :--- | :--- | :--- | :--- |
| **TIER 1 (SCOPE)** | Branch Prefix + Ticket ID | Defines the **scope** of work (e.g., `feature/`) and its associated **work item**. | **MANDATORY** for all branches. |
| **TIER 2 (INTENT)** | Commit Title Prefix | Defines **what changed** (Conventional Commits type, e.g., `feat:`, `fix:`). | **MANDATORY** for all commits. |
| **TIER 3 (JUSTIFICATION)** | Architectural Tag (ArchTag) | Defines **why** a structural change was made. Placed in the commit body. | **CONDITIONAL** (Mandatory for `refactor:`, `perf:`, `BREAKING CHANGE` Footer). |

## 2. Tier 1: Scope & Traceability - Branch Prefixing Policy

Branch names **MUST** use the format:

`<prefix>: <TICKET-ID>-<short-kebab-description>`

*Names must be lowercase with hyphens. This format enables automatic linking to issues and Pull Requests.*

| Prefix | Work Scope | Example |
| :--- | :--- | :--- |
| `feature/` | New features or significant enhancements/additions. | `feature/MLOPS-456-add-metrics-endpoint` |
| `bugfix/` | Correcting a user-impacting defect/bug. | `bugfix/JIRA-123-login-404-error` |
| `hotfix/` | Urgent fixes applied directly to the production branch. | `hotfix/CRIT-001-payment-gateway-bug` |
| `release/` | Preparation for a formal release (e.g., final testing, version bumps). | `release/v1.2.0-final-prep` |
| `chore/` | Routine maintenance that doesn't fix a bug or add a feature (e.g., documentation, dependency updates). | `chore/TICKET-789-update-deps` |

## 3. Tiers 2 & 3: Intent & Justification - Conventional Commit Policy

### 3.1 Tier 2: **What** Changed - Commit Title Prefix

The commit title **MUST** start with `<type>: <description>`. The description must be **50 characters maximum** and written in the **imperative mood**.

| Group | Type | Intent | ArchTag Required? | SemVer Impact |
| :--- | :--- | :--- | :--- | :--- |
| **Core** | `feat:` | A new feature or enhancement. | NO | **Minor** |
| | `fix:` | A bug fix. | NO | **Patch** |
| **Breaking** | *(any type)* + `BREAKING CHANGE` footer | Introduces an incompatible API/behavior change. | **YES** | **Major** |
| **Architectural** | `refactor:` | Code restructuring that neither fixes a bug nor adds a feature; can change public API. | **YES** | Patch/Minor/Major |
| | `perf:` | Code change that measurably improves performance; can change public API. | **YES** | Patch/Minor/Major |
| **Routine** | `docs:` | Changes to documentation only. | NO | None |
| | `test:` | Adding or correcting tests. | NO | None |
| | `chore:` | Routine maintenance, dependency updates, minor clean-up. | NO | None |
| **Internal/Temporary** | `WIP:` | **Incomplete work. Must be squashed/rebased before merging.** | NO | None |

> NOTE: Commit types inform SemVer, but do not dictate it. Final SemVer must be validated against API/behavior contracts.

#### **BREAKING CHANGE** Footer

The official way to signal changes that **break compatibility** is:

```
<type>(<optional scope>): <description>

BREAKING CHANGE: <description of breaking impact>
```

| Intent | Correct Conventional Commit Form |
|----------------------|----------------------------------|
| **Removing a feature** (user-facing) | `feat: remove legacy auth API`<br>`BREAKING CHANGE: The /v1/login endpoint is deleted. Use /v2/auth.` |
| **Removing internal code** (no external impact) | `refactor: delete unused cache module`<br>*(No `BREAKING CHANGE` needed)* |
| **Removing a config option or API** (breaking) | `fix: drop support for deprecated TLS 1.0`<br>`BREAKING CHANGE: TLS 1.0 connections are now rejected.` |

> 💡 **Key principle**: A **breaking change** is defined by **observable behavior change for consumers** — not by the act of change itself.

> Read more: **Conventional Commits – Breaking Changes**  
>    *Conventional Commits Specification, Section "Commit Message with Description and Breaking Change Footer"* [Conventional Commits WG], 2019  
>     https://www.conventionalcommits.org/en/v1.0.0/#commit-message-with-description-and-breaking-change-footer

### 3.2 Tier 3: **Why** Changed - Architectural Tagging

For commits of type `refactor:`, `perf:`, or `BREAKING CHANGE` Footer, the architectural intent **MUST** be provided as an ArchTag (Architectural Tag).

  * **Format:** The tag **MUST** be the **first line** of the commit body: `ArchTag:TAG-NAME` (one tag only).
  * **Syntax Rules:** The tag **MUST NOT** include the `#` symbol or any spaces.
  * **Validation:** CI/CD automation tools will validate the tag's presence and correctness.

| Tag Name | Intent | Heuristic / Automation Gate |
| :--- | :--- | :--- |
| `DEPRECATION-PLANNED` | Sunset code, APIs, or features scheduled for removal. | PR requires Architect Approval (Hard Gate). |
| `TECHDEBT-PAYMENT` | Reducing complexity, upgrading dependencies, or simplifying code. | Signals maintenance work. |
| `REFACTOR-MIGRATION` | Major architecture shift or pattern change (e.g., monolith to microservice). | PR requires Architect Approval (Hard Gate). |
| `PERF-OPTIMIZATION` | Code change explicitly addressing a performance bottleneck. | Benchmarks must be provided in the commit body. |

### Example of a full commit with `ArchTag`

```
refactor: simplify model loading logic

ArchTag:TECHDEBT-PAYMENT
Reduced cyclomatic complexity from 15 to 8, improving maintainability.
```

## 4. The Guiding Principle: Atomic Commits

The goal of every feature branch's final history is **logical atomicity**. An **Atomic Commit** is a self-contained, complete, and logically isolated unit of work.

### Rules of Atomicity

  * **Rule 1: One Goal Per Commit.** A commit must achieve one objective only (e.g., *refactor logic*, *add unit tests*, *fix a bug*).
  * **Rule 2: Commits Must Be Stable.** Every commit in the final, merged history **MUST** be buildable and pass all tests. This is mandatory for advanced diagnostic tools like $\text{git bisect}$. **Broken commits are technical debt.**
  * **Rule 3: Cohesive Narrative.** The sequence of commits in a Pull Request (PR) must tell a clear story of how the feature was developed, making it easy for reviewers to follow the logic.

### The "Commit by Logic" Workflow

To create atomic commits, **DO NOT** use `git add .` indiscriminately.

| Step | Action | Tool | Goal |
| :--- | :--- | :--- | :--- |
| **Stage Selectively** | Use the patch utility to stage only changes relevant to a single logical task. | `git add -p` | **Group changes by function and purpose,** not by file or timing. |
| **Review and Commit** | Review the staged changes (`git diff --staged`). If they represent one complete, stable, logical step, commit them with a semantic type. | `git commit -m "feat: implement X interface"` | Ensure the commit is **atomic**. |
| **Iterate and Clean** | Perform the rebase and squashing procedure (Section 4). | `git rebase -i` | Produce a clean, coherent history ready for review and final merge. |

This disciplined approach ensures that your contributions are professionally structured, easily maintainable, and maximally effective for the long-term health of our engineering systems.

> Read more:
>   - "Pro Git", Chapter 7: Git Tools - Rewriting History' [Scott Chacon and Ben Straub] https://git-scm.com/book/en/v2/Git-Tools-Rewriting-History

## 5. Merge Strategy: Atomic Change Submission

All changes merged into mainline branches (`main`, `develop`, etc.) **MUST** be integrated as a **single, atomic commit**. This is not a Git convenience—it is a **fundamental engineering discipline** used in scaled production environments (Google, Meta, Microsoft) to ensure **reviewability, revertability, and traceability**.

### A. The BigTech Standard: One Change, One Commit

In professional code review systems:
- A Pull Request (PR) or Change List (CL) represents **one logical modification** to the system.
- Intermediate development steps (e.g., test scaffolding, incremental refactors) are **development artifacts**, not production history.
  - Preserving them in `main` adds **noise without operational value** and **dilutes accountability**.
  
> **Key Principle**:  
> *“If it can’t be reviewed, reverted, or reasoned about as a single unit, it’s not production-ready.”*

> Read more: 
>   - "Small CLs" https://google.github.io/eng-practices/review/developer/small-cls.html
>   - "Writing good CL descriptions" https://google.github.io/eng-practices/review/developer/cl-descriptions.html
>   - "Submitting patches: the essential guide to getting your code into the kernel" https://docs.kernel.org/process/submitting-patches.html

### B. Implementation: Enforced "Squash and Merge"

- **All PRs must be merged using "Squash and Merge"**.
- The **final commit message** must be:
  - A valid **Conventional Commit** (`feat:`, `fix:`, etc.),
  - **≤50 characters** in title,
  - Include a **body** containing:
    - Architectural rationale (with `ArchTag` if required),
    - `BREAKING CHANGE:` footer if applicable,
    - Link to ticket or design document.

> **Why not "Rebase and Merge"?**  
> While linear, it preserves intermediate commits that **were never reviewed as independent units**. In BigTech, **only the integrated state is production-grade**—everything else is draft .

> Read more:
>   - "Merge strategies and squash merge" https://learn.microsoft.com/en-us/azure/devops/repos/git/merging-with-squash

### C. Debugging Without `git bisect` Granularity

Fine-grained bisect is **not the primary debugging tool** in production systems. Instead, rely on:
- **Structured logging** (with trace IDs),
- **Metrics and alerting** (e.g., latency, error rates),
- **Atomic revert** (if a change breaks, revert the **entire unit**—not part of it).

If a change is **too large to debug or revert safely**, it **violates atomicity** and should have been split **before submission**.

### Enforcement

| Guardrail | Implementation |
|----------|----------------|
| **CI/CD Block** | PRs with >1 commit **fail pre-merge check** (unless exempted for large migrations). |
| **Reviewer Gate** | Reviewers **reject PRs** that are not logically atomic (e.g., mix refactor + feature). |
| **Merge Policy** | Repository settings **enforce "Squash and Merge"** as the only allowed method. |

> **Exception**: PRs tagged with `ArchTag:REFACTOR-MIGRATION` may use **"Rebase and Merge"** **only if** approved by an Architect and **each commit is independently CI-verified**.

## 6. Quick Reference, Enforcement, and Pitfalls

### 6.1 Quick Reference Table

| Branch Prefix | Commit Prefix Examples | ArchTag Required? | Key Automation Trigger / Gate |
| :--- | :--- | :--- | :--- |
| `feature/`, `bugfix/`, ` chore/  `| `feat:`, `fix:`, `docs:`, `chore:` | NO | Changelog generation; CI pipeline. |
| **Any** | `refactor:`, `perf:`, `BREAKING CHANGE` Footer | **YES** | **Architectural Review Gate** (CI/CD block). |
| **Any** | `WIP:` | NO | **CI BLOCK** (Failure to pass the Pre-Merge History Check). |

### 6.2 Enforcement

  * **CI/CD Pipeline:** The pipeline **MUST** block a merge if:
    1.  A commit of type `refactor:`, `perf:`, or `BREAKING CHANGE` Footer  is missing a valid `ArchTag`.
    2.  Any commit in the PR history contains the prefix `WIP:`.
  * **Architectural Review Gate:** PRs containing `ArchTag:REFACTOR-MIGRATION` or `ArchTag:DEPRECATION-PLANNED` **MUST** receive explicit approval from an Architect/Principal Engineer *before* merging.

### 6.3 Common Pitfalls

| Pitfall | Consequence | Mitigation |
| :--- | :--- | :--- |
| Forgetting the **Ticket ID** in the branch name. | No automatic issue linking; traceability loss. | Use templates; set branch protection rules. |
| Commit titles exceeding **50 characters**. | Poor changelog readability; automation tools truncate. | Use pre-commit hooks to check length. |
| Invalid or missing **ArchTag** on required commit types. | **CI BLOCK** (Failure to pass the Architectural Review Gate). | Check the tag list and ensure it's the first line in the commit body. |

-----

## Appendix A: Detailed ArchTag Commit Examples

These examples illustrate the correct structure for commits that require Tier 3 architectural justification, using the `ArchTag:TAG-NAME` format.

### 1. ArchTag: `DEPRECATION-PLANNED`

*Goal: Remove a function slated for sunsetting.*

```
feat: remove legacy user analytics module

ArchTag:DEPRECATION-PLANNED
This module has been replaced by the new Kafka-based logging system (see JIRA-255).
All calls to `legacy_analytics_log()` have been removed from the frontend service.

BREAKING CHANGE: The `legacy_analytics_log()` function and its HTTP endpoint /api/v1/log are no longer available.
```

### 2. ArchTag: `TECHDEBT-PAYMENT`

*Goal: Restructure code to improve maintainability and adherence to modern Python standards.*

```
refactor: standardize all model config loading via Pydantic

ArchTag:TECHDEBT-PAYMENT
Replaced outdated dict-based config parsing with Pydantic schemas across 12 files.
This significantly reduces validation error handling boilerplate and improves type safety.
```

### 3. ArchTag: `REFACTOR-MIGRATION`

*Goal: Implement a fundamental shift in how the system handles a core component.*

```
refactor: migrate database connection pool to SQLAlchemy 2.0 async

ArchTag:REFACTOR-MIGRATION
Upgraded the core data layer to use the new asyncio ORM style.
This is a breaking change and requires updating all repository methods to use `await`.
```

### 4. ArchTag: `PERF-OPTIMIZATION`

*Goal: Optimize a slow loop, requiring proof of performance gain.*

```
perf: optimize feature extraction by replacing list with numpy array

ArchTag:PERF-OPTIMIZATION
Profiling showed the bottleneck was array conversion in the main loop.
Benchmark results show a 22% reduction in latency for large inputs (1000+ features).
```
