# 🚀 Production Git Workflow: Examples

-----

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.1.0  
Birth: 2025-12-01  
Last Modified: 2025-12-01

-----

## Detailed ArchTag Commit Examples

These examples illustrate the correct structure for commits that require Tier 3 architectural justification, using the $\text{ArchTag:TAG-NAME}$ format.

### 1. ArchTag: $\text{DEPRECATION-PLANNED}$

*Goal: Remove a function slated for sunsetting.*

```
remove: delete legacy user analytics module

ArchTag:DEPRECATION-PLANNED
This module has been replaced by the new Kafka-based logging system (see JIRA-255).
All calls to `legacy_analytics_log()` have been removed from the frontend service.
```

### 2\. ArchTag: $\text{TECHDEBT-PAYMENT}$

*Goal: Restructure code to improve maintainability and adherence to modern Python standards.*

```
refactor: standardize all model config loading via Pydantic

ArchTag:TECHDEBT-PAYMENT
Replaced outdated dict-based config parsing with Pydantic schemas across 12 files.
This significantly reduces validation error handling boilerplate and improves type safety.
```

### 3\. ArchTag: $\text{REFACTOR-MIGRATION}$

*Goal: Implement a fundamental shift in how the system handles a core component.*

```
refactor: migrate database connection pool to SQLAlchemy 2.0 async

ArchTag:REFACTOR-MIGRATION
Upgraded the core data layer to use the new asyncio ORM style.
This is a breaking change and requires updating all repository methods to use `await`.
```

### 4\. ArchTag: $\text{PERF-OPTIMIZATION}$

*Goal: Optimize a slow loop, requiring proof of performance gain.*

```
perf: optimize feature extraction by replacing list with numpy array

ArchTag:PERF-OPTIMIZATION
Profiling showed the bottleneck was array conversion in the main loop.
Benchmark results show a 22% reduction in latency for large inputs (1000+ features).
```
