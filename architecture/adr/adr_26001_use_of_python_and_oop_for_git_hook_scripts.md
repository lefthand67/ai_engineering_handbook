
---
title: Use of Python and OOP for Git Hook Scripts
date: 2026-01-24
tags:
- git
options:
  token_size: 782
  id: 26001
  status: accepted
  superseded_by: null
  type: adr
  version: 1.0.0
  birth: '2026-01-24'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Standardizing Git Hook Implementation with Python and Object-Oriented
  Programming (OOP).
---
# ADR-26001: Use of Python and OOP for Git Hook Scripts

## Title

Standardizing Git Hook Implementation with Python and Object-Oriented Programming (OOP)

## Status

Accepted

## Date

2026-01-06

## Context

The project requires a robust mechanism for enforcing local development standards (e.g., commit message formats, linting, and branch naming conventions). Traditionally, Shell scripts are used for Git hooks, but they present several challenges as project complexity grows:

* **Lack of Testing:** Shell scripts are difficult to unit test, often leading to "broken" hooks that block developer workflows.
* **Maintenance Debt:** Complex logic (regex, JSON handling) in Bash is hard to read and prone to platform-specific bugs (e.g., macOS vs. Linux sed).
* **Code Duplication:** Shared logic across different hooks (pre-commit, pre-push) is difficult to manage without a structured language.

## Decision

We will implement all Git hooks using **Python** following an **Object-Oriented (OOP)** architecture.

### Key Implementation Requirements:

All Git hooks will be written in Python. These scripts must follow Object-Oriented Programming (OOP) principles to encapsulate hook logic. Furthermore, **every** hook must have a corresponding test suite written in pytest to ensure automation reliability and prevent regressions.

## Consequences

### Positive

* **Reliability:** By using `pytest`, we can simulate Git states (e.g., detached HEAD, merge conflicts) to ensure hooks behave correctly before they are deployed to the team.
* **Developer Experience:** Python provides clearer error messages and stack traces than Shell, making it easier for developers to debug why a hook failed.
* **Extensibility:** The OOP approach allows us to create "Mixins" for specific tasks, such as a `JiraIntegrationMixin` for hooks that need to validate ticket IDs against an external API.

### Negative/Risks

* **Execution Latency:** Python's startup time is roughly 100ms–200ms. **Mitigation:** Logic will be kept lean, and heavy imports will be deferred until needed within specific methods.
* **Interpreter Dependency:** Requires Python to be present on the host machine. **Mitigation:** We are standardizing on Python 3.13+ as part of our core development environment.

## Alternatives

* **Shell/Bash:** Rejected due to poor testability and difficulty handling complex data structures.
* **Functional Python:** Rejected because the shared state (Git environment variables) and shared utility methods are more naturally represented as class attributes and methods.
* **Other languages:** Rejected because Python's standard library is suited for CLI-based system tasks and is already a core requirement of our backend stack.

## References

* [Pytest Documentation](https://docs.pytest.org/)
* [Pre-commit Framework](https://pre-commit.com/)
* [Clean Code: A Handbook of Agile Software Craftsmanship (Object-Oriented Section)](https://www.oreilly.com/library/view/clean-code-a/9780136083238/)

## Participants

1. Vadim Rudakov
2. Senior AI Architect (Gemini 3 Flash)
