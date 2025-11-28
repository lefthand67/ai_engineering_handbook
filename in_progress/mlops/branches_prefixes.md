# Policy: Branch Prefixes

-----

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.1.0  
Birth: 29.11.2025  
Modified: 29.11.2025 

-----

## Introduction

This document outlines the **mandatory policy for naming branches** within the repository. Establishing a consistent and standardized branching convention is crucial for improving **codebase clarity**, simplifying **code review processes**, and ensuring **efficient collaboration** across the development team.

This policy uses a **prefix system** to clearly indicate the purpose and scope of the changes contained within each branch, making it easy to identify the nature of the work (e.g., feature, fix, documentation, maintenance) at a glance. Adherence to this standard is required for all new branches.

## Syntax

```
<prefix>/<short_readable_topic_name>
```

## Core Logic of Branch Prefixes (Example)

| Prefix | Meaning | Examples |
|---|---|---|
| `feat/` | New features or enhancements | `feat/user-login`, `feat/api-integration` |
| `fix/` | Bug fixes | `fix/login-bug`, `fix/memory-leak` |
| `hotfix/` | Urgent fixes that need to be quickly deployed to production | `hotfix/payment-error`, `hotfix/crash-on-startup` |
| `chore/` | Technical tasks that do not affect functionality (dependency updates, etc.) | `chore/update-dependencies`, `chore/config-scripts` |
| `docs/` | Changes to documentation | `docs/api-docs-update`, `docs/setup-guide` |
| `test/` | Adding or updating tests | `test/add-unit-tests`, `test/fix-flaky-tests` |
| `refactor/` | Code refactoring without changing functionality | `refactor/clean-up-auth`, `refactor/improve-performance` |
| `wip/` | Work-in-progress branches, experimental and temporary, prototypes | `wip/new-design-experiments`, `wip/test-api-calls` |
| `release/` | Branches for release preparation | `release/1.0.0`, `release/1.2.3` |

**Naming Tip:**

  * Use a **readable topic name** after the prefix.
  * Separate words using `_` or `-`.

## Examples

```
wip/ai_ci_cd_notes
feat/context_engineering
fix/ci-cd-typo
```
