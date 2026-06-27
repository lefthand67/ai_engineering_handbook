---
id: 26010
title: Adoption of Molecule for Automated Ansible Role Validation
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Implementation of the **Molecule** testing framework with **Podman**
  for automated verification of Ansible roles..
tags:
- testing
date: 2026-01-24
options:
  type: adr
  birth: '2026-01-24'
  version: 1.0.0
  token_size: 843
  status: proposed
  superseded_by: null
---
# ADR-26010: Adoption of Molecule for Automated Ansible Role Validation

## Title

Implementation of the **Molecule** testing framework with **Podman** for automated verification of Ansible roles.

## Status

Proposed

## Date

2026-01-17

## Context

With the adoption of Ansible {term}`ADR-26009`, we require a mechanism to verify that infrastructure changes are correct and idempotent before they are applied to production servers.

* **Reliability:** {term}`ADR-26001` established that "every hook must have a corresponding test suite... to ensure automation reliability." This principle must extend to our infrastructure code.
* **Manual Bottlenecks:** Testing on live servers or manual VM snapshots is slow, non-disposable, and introduces "Human Debt."
* **Environment Parity:** We need a way to simulate our Fedora/Debian targets locally using our existing Podman-based stack.

## Decision

We will adopt **Molecule** as the primary testing harness for all Ansible roles.

1. **Driver:** We will use the `molecule-plugins[podman]` driver to leverage our local Podman installation for ephemeral test containers.
2. **Lifecycle Automation:** Every role will include a `molecule/` directory to orchestrate the `create`, `converge`, `idempotence`, and `verify` stages.
3. **Verification Engine:** We will use the **Ansible Verifier** (Ansible-based test playbooks) to perform functional assertions (e.g., verifying service ports are open and responding).
4. **Systemd Support:** Test containers will be configured to run `systemd` to accurately simulate the production environment and test systemd-managed Podman pods.

## Consequences

### Positive

* **High Integrity:** Automatically catches non-idempotent tasks and configuration errors during the "Check vs. Fix" cycle.
* **Developer Velocity:** Molecule provides an ephemeral, disposable environment, allowing developers to test locally in seconds without cloud costs or VM overhead.
* **CI/CD Readiness:** Molecule tests can be integrated into the pre-commit framework or remote CI runners to gate production deployments.

### Negative

* **Complexity:** Requires additional configuration files (`molecule.yml`, `prepare.yml`, `verify.yml`) for each role.
* **Privileged Execution:** Running `systemd` inside Podman containers typically requires `privileged: true` or specific capability mapping. **Mitigation:** Standardize local development on rootless Podman with specific `molecule.yml` security overrides.

## Alternatives

* **Manual VM Testing:** Rejected as it is non-idempotent, slow, and cannot be integrated into automated CI/CD pipelines.
* **Ansible-test:** Rejected as it is primarily focused on testing Ansible collections rather than individual infrastructure roles.
* **Testinfra (Python-based):** Considered but relegated to a secondary option. While powerful, using the native Ansible Verifier keeps the testing logic consistent with the configuration logic (YAML), adhering to SVA simplicity.

## References

* {term}`ADR-26001`: Use of Python and OOP for Git Hook Scripts
* {term}`ADR-26009`: Adoption of Ansible for Idempotent Configuration Management
* [Molecule Documentation](https://ansible.readthedocs.io/projects/molecule/)

## Participants

1. Vadim Rudakov
2. Senior DevOps Systems Architect (Gemini)
