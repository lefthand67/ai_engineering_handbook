
---
title: Adoption of Ansible for Idempotent Configuration Management
date: 2026-01-24
tags:
- devops
options:
  token_size: 945
  id: 26009
  status: proposed
  superseded_by: null
  type: adr
  version: 1.0.0
  birth: '2026-01-24'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Transitioning from procedural Bash-based server configuration to declarative,
  idempotent state management using **Ansible**..
---
# ADR-26009: Adoption of Ansible for Idempotent Configuration Management

## Title

Transitioning from procedural Bash-based server configuration to declarative, idempotent state management using **Ansible**.

## Status

Proposed

## Date

2026-01-17

## Context

There is a server configuration system that consists of a complex tree of 69 bash scripts and 31 directories. While functional, thr "Scripts-as-Infrastructure" approach presents several architectural risks:

* **Lack of Idempotency:** Bash scripts require manual, error-prone logic (e.g., `grep` and `if` blocks) to ensure they can be re-run without causing side effects or duplicating configuration lines.
* **Maintenance Debt:** Managing diverse services like Forgejo, Nextcloud, and Traefik through raw shell scripts leads to high cognitive load and violates the "Check vs. Fix" principle of SVA (Smallest Viable Architecture).
* **State Drift:** There is no native mechanism to report or revert manual changes (drift) on the server that deviate from the version-controlled scripts.
* **Alignment:** {term}`ADR-26001` and {term}`ADR-26002` established a preference for Python-standardized toolchains and version-controlled, automated logic.

## Decision

We will adopt **Ansible** as the primary engine for server configuration and SaaS deployment.

1. **Declarative Roles:** The existing bash script system structure (e.g., `forgejo_config`, `nextcloud_config`) will be refactored into **Ansible Roles** following the standard `roles/<role_name>/` structure.
2. **Native Podman Integration:** We will utilize the `containers.podman` collection to manage Podman pods and containers, replacing manual `podman play kube` shell calls.
3. **Jinja2 Templating:** The existing `render_templates.py` scripts will be deprecated in favor of Ansible’s native Jinja2 templating engine to maintain consistent environment parity.
4. **Agentless Execution:** All configurations will be pushed from the local Fedora/Debian development environment over SSH, maintaining the "No vendor lock-in" and "runnable locally" requirements of our SVA audit.

## Consequences

### Positive

* **Idempotency:** Ansible naturally ensures the system reaches the desired state without repetitive execution errors.
* **Reduction of Code:** Replacing procedural bash logic with declarative YAML modules significantly reduces the total lines of code to maintain.
* **Scalability:** Enables simultaneous deployment to multiple server targets using inventory management.
* **Auditability:** Ansible's "diff" and "check" modes allow for pre-execution verification of changes.

### Negative

* **Python Dependency:** Adds a requirement for Ansible and its dependencies in the local development environment. **Mitigation:** This is already consistent with the Python 3.13+ standard established in {term}`ADR-26001`.
* **Execution Overhead:** Ansible is generally slower than raw Bash due to SSH overhead and Python module execution. **Mitigation:** The gain in system integrity and reliability outweighs the millisecond-latency of deployment.

## Alternatives

* **Maintain Current Bash System:** Rejected due to increasing complexity and the lack of a "Check vs. Fix" mechanism.
* **Terraform:** Rejected as it is better suited for cloud infrastructure provisioning (API-driven) rather than OS-level configuration and service management.
* **Chef/Puppet:** Rejected as they typically require agent installation on the server, violating the "Smallest Viable Architecture" (SVA) principle of simplicity.

## References

* {term}`ADR-26001`: Use of Python and OOP for Git Hook Scripts
* {term}`ADR-26002`: Adoption of the Pre-commit Framework

## Participants

1. Vadim Rudakov
2. Senior DevOps Systems Architect (Gemini)
