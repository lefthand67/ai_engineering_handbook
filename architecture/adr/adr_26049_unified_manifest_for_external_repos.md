---
id: 26049
title: Unified Manifest for External Repository Management
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Transition from a registry-only system to a state-based synchronization
  system using a unified manifest as the Single Source of Truth (SSoT).
tags:
- devops
- architecture
date: 2026-04-21
options:
  type: adr
  birth: 2026-04-21
  version: 1.0.0
  token_size: 1026
  status: accepted
  superseded_by: null
---
# ADR-26049: Unified Manifest for External Repository Management

## Date
2026-04-21

## Status
accepted

## Context
Previously, external product repositories used for research were managed through a decoupled registry system. Users would `register` a directory and then `setup` (clone) repositories into it. 

This approach had several flaws:
1. **Lack of Synchronization:** There was no central record of *which* specific repositories should exist in which directories. The registry only tracked directories, not the content within them.
2. **Environment Drift:** Collaborators could have different sets of repositories cloned, leading to "works on my machine" issues when referencing external source code.
3. **Manual Cleanup:** Removing a repository from the "desired" set required manual deletion and manual registry updates.
4. **Consumer Desynchronization:** Files like `.gitignore` and `myst.yml` (used to exclude external repos from git/docs) were updated during registration but could easily drift if directories were moved or renamed manually.

## Decision
We are moving to a **State-Based Synchronization** model. The central authority for the external repository state is now a unified manifest file: `.vadocs/inventory/manage_external_repos.json`.

### The Unified Manifest (SSoT)
The manifest combines two previously separate concerns:
1. **Registry:** Which directories are designated for external repos (and their descriptions/consumers).
2. **Inventory:** Which specific git repositories (URL, name, description) belong in those directories.

### The Synchronization Mechanism
We implement a `sync` command in `tools/scripts/manage_external_repos.py` that follows a strict reconciliation loop:

1. **Discovery:** The tool maps the **Desired State** (manifest), the **Registered State** (manifest), and the **Actual State** (filesystem scan for `.git` folders).
2. **Delta Calculation:** It identifies discrepancies:
    - **Missing:** Repos in manifest but not on disk.
    - **Orphans:** Repos on disk but not in manifest.
    - **Ghosts:** Directories registered in the manifest but missing from the filesystem.
3. **Resolution:** The user is prompted to resolve orphans (Remove/Ignore) and ghosts (Unregister/Keep).
4. **Execution:** The tool performs the necessary `git clone`, directory registration, or deletion to align the actual state with the desired state.

### Key Feature Additions
- **`sync-consumers`**: A new command that automatically rebuilds `.gitignore` and `myst.yml` based on the manifest's directory list, ensuring exclusion rules are always up-to-date.
- **`--dry-run`**: Both `sync` and `sync-consumers` support a dry-run mode to preview changes without modifying the filesystem or configuration.
- **Unified Registry**: Removal of legacy `.vadocs/validation/external-repos.conf.json` in favor of the manifest.

## Consequences

### Positive
- **Guaranteed Consistency:** All contributors are guaranteed to have the exact same set of external repositories.
- **Idempotency:** Running `sync` repeatedly ensures the system returns to the desired state regardless of manual drift.
- **Verifiability:** The `--dry-run` flag allows agents and humans to verify the intended state before execution.
- **Automated Maintenance:** `sync-consumers` removes the risk of accidentally committing external source code.

### Negative / Risks
- **Manifest Overhead:** Adding a new repository now requires a commit to the JSON manifest rather than just running a CLI command. **Mitigation**: Future implementation of CLI wrappers for manifest editing.

## Alternatives
- **Separate Inventory File:** Maintaining a separate `inventory.json` while keeping the registry in a config file. **Rejection Reason**: Increases fragmentation and the risk of the registry and inventory drifting apart.
- **Dynamic Discovery only:** Relying purely on filesystem scans without a manifest. **Rejection Reason**: No way to define "Desired State"; cannot detect missing repositories that *should* be there.

## References
- [manage_external_repos.py](/tools/scripts/manage_external_repos.py)
- [Unified Manifest Config](/.vadocs/inventory/manage_external_repos.json)

## Participants
1. Vadim Rudakov
