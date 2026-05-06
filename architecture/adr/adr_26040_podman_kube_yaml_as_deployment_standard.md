
---
title: Podman Kube YAML as Deployment Standard
date: 2026-03-09
tags:
- devops
options:
  token_size: 1730
  id: 26040
  status: accepted
  superseded_by: null
  type: adr
  version: 1.0.0
  birth: '2026-03-09'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: '<!-- Quality guidelines: /architecture/architecture_decision_workflow_guide.md
  -->.'
---
<!-- Quality guidelines: /architecture/architecture_decision_workflow_guide.md -->

# ADR-26040: Podman Kube YAML as Deployment Standard

## Date
2026-03-09

## Status

Accepted

## Context

[ADR-26039: pgvector as Ecosystem Database Standard](/architecture/adr/adr_26039_pgvector_as_ecosystem_database_standard.md) is deployment-agnostic — it decides *what* database to use but not *how* to run it. The ecosystem needs a standard way to define, deploy, and manage containerized services (Postgres with pgvector, future agent services, supporting infrastructure).

The ecosystem already runs production services (Forgejo, Traefik, Nextcloud) using Podman with Kubernetes YAML manifests and systemd integration. [ADR-26009: Adoption of Ansible for Idempotent Configuration Management](/architecture/adr/adr_26009_adoption_of_ansible_for_idempotent_confi.md) decides the orchestration layer (Ansible replacing bash scripts), but the underlying deployment artifact — the Kube YAML manifest — needs to be standardized as the single format for describing containerized workloads.

Three requirements drive this decision:

1. **Portability**: manifests should work on any Linux machine with Podman installed, without additional tooling
2. **Lifecycle management**: containers must survive reboots and be manageable via standard system tools
3. **Rootless by default**: containers run under a non-root user, consistent with the ecosystem's security posture

## Decision

We adopt **Kubernetes YAML manifests executed via Podman** as the single format for all containerized deployments in the ecosystem.

1. **Kube YAML as the deployment artifact.** Each containerized service is defined as a standard Kubernetes Pod manifest (apiVersion `v1`, kind `Pod`). Template variables are rendered by the orchestration layer (ADR-26009) before deployment. The manifest is the version-controlled, reviewable artifact — the orchestrator is a separate concern.

2. **`podman-kube@.service` for lifecycle management.** Podman's built-in systemd template unit maps a Kube YAML file path to a systemd service. This provides boot persistence, restart-on-failure, and `journalctl` logging via `systemctl --user` — rootless by default. This replaces the legacy `podman generate systemd` approach (deprecated in Podman 5+).

3. **Named volumes for persistent data.** Stateful services (databases, configuration) use Podman named volumes referenced via `PersistentVolumeClaim` in the manifest. Volume creation and pre-population are the orchestrator's responsibility, not the manifest's.

## Consequences

### Positive

- **Single deployment format**: one Kube YAML manifest per service — the same file works with `podman play kube` directly, with the `podman-kube@.service` systemd unit, or with Ansible's `containers.podman` collection
- **Native systemd integration**: `podman-kube@.service` provides restart-on-failure, boot persistence, and standard `journalctl` logging without generating custom service files
- **Rootless by default**: `systemctl --user` runs pods under the service user, not root. Combined with Podman's daemonless architecture, this eliminates the attack surface of a privileged container daemon
- **Kubernetes vocabulary without Kubernetes complexity**: the manifests use standard Kubernetes API objects (Pod, PersistentVolumeClaim) — if the ecosystem ever outgrows single-node deployment, the same manifests work in a real Kubernetes cluster with minimal changes
- **Orchestrator-independent**: the Kube YAML is the artifact; whether bash scripts, Ansible, or a future tool renders and deploys it is a separate concern (ADR-26009)

### Negative / Risks

- **Pod-level granularity only**: Podman's Kube YAML support covers `Pod`, `Deployment`, `PersistentVolumeClaim`, and `ConfigMap` — not the full Kubernetes API (no Services, Ingress, NetworkPolicy). **Mitigation**: the ecosystem is single-node; higher-level networking concerns are handled outside the manifest
- **Secret management is out-of-band**: Kube YAML env vars with placeholder values require the orchestration layer to inject secrets before deployment. **Mitigation**: secret injection is the orchestrator's responsibility (ADR-26009). Secrets are never committed to version control
- **`podman-kube@.service` requires Podman 4.4+**: older distributions may not include this template unit. **Mitigation**: the ecosystem targets current Fedora/Debian stable releases where Podman 4.4+ is standard
- **Template rendering is not standardized by this ADR**: whether `envsubst`, Jinja2, or Ansible handles variable substitution is left to the orchestration layer. **Mitigation**: this is intentional — the Kube YAML is the portable artifact, rendering is the orchestrator's job

## Alternatives

- **Docker Compose.** Industry-standard multi-container orchestration. **Rejection Reason**: requires the Docker daemon (a privileged root process). Podman Compose exists as a compatibility wrapper but is a second-class citizen — it translates Compose files into Podman commands rather than using Podman's native Kube YAML support. The ecosystem has standardized on Podman (rootless, daemonless) and gains nothing from the Compose format.

- **Podman Compose.** Drop-in replacement for Docker Compose using Podman. **Rejection Reason**: adds a Python dependency (`podman-compose`) that duplicates functionality already native to Podman (`podman play kube`). The Compose format doesn't integrate with systemd natively — it still requires generating service files or running a foreground process.

- **`podman generate systemd` (legacy).** Generates systemd unit files from running containers. **Rejection Reason**: deprecated in Podman 5+ in favor of `podman-kube@.service` and Quadlet. Generates static files that must be regenerated when container configuration changes. The `podman-kube@.service` template unit is the recommended replacement.

- **Quadlet (`.container`, `.pod` files).** Podman's newer systemd integration using INI-style unit files. **Rejection Reason**: Quadlet defines containers in a Podman-specific format, not portable Kubernetes YAML. While it integrates well with systemd, it sacrifices the ability to use the same manifests in a Kubernetes cluster. Kube YAML provides a superset of Quadlet's capabilities with broader portability.

- **Plain `podman run` commands.** Direct CLI invocation without manifests. **Rejection Reason**: no declarative artifact to version-control, review, or share. Restart-on-boot requires manual systemd unit creation. Not reproducible across machines.

## References

- [ADR-26039: pgvector as Ecosystem Database Standard](/architecture/adr/adr_26039_pgvector_as_ecosystem_database_standard.md) — the first service requiring containerized deployment
- [ADR-26009: Adoption of Ansible for Idempotent Configuration Management](/architecture/adr/adr_26009_adoption_of_ansible_for_idempotent_confi.md) — orchestration layer that renders and deploys Kube YAML manifests
- [Podman Kube YAML documentation](https://docs.podman.io/en/latest/markdown/podman-kube-play.1.html) — `podman play kube` reference
- [Running Kubernetes workloads with Podman and systemd](https://www.redhat.com/sysadmin/kubernetes-workloads-podman-systemd) — RedHat guide for `podman-kube@.service` pattern

## Participants

1. Vadim Rudakov
2. Claude Opus 4.6
