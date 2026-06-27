---
id: 26022
title: Standardization of Public Documentation Hosting on GitHub Pages
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: 2026-02-06.
tags:
- devops
- documentation
date: 2026-02-06
options:
  type: adr
  birth: '2026-02-06'
  version: 1.0.0
  token_size: 1033
  status: accepted
  superseded_by: null
---
# ADR-26022: Standardization of Public Documentation Hosting on GitHub Pages

## Date

2026-02-06

## Status

Accepted

## Context

As the ecosystem expands into multiple standalone repositories, we require a unified, scalable, and low-maintenance strategy for publishing technical documentation. Historically, some projects utilized a [self-hosted stack involving Podman, Traefik, and Nginx](/tools/docs/website/02_self_hosted_deployment.ipynb). While robust, this "private server" approach introduces several risks for **open-source** projects:

* **Maintenance Tax:** Managing server security, SSL certificates, and container runtimes adds "unjustified orchestration layers" to the development lifecycle.
* **Single Point of Failure:** Documentation availability is tied to the uptime of a personal server rather than a globally distributed CDN.
* **Infrastructure Coupling:** Contributors cannot easily replicate the deployment environment, i.e. reproduce the entire Production Pipeline, not just the local preview. This creates a barrier to entry for documentation improvements.
* **Security Overhead:** Managing SSH keys and server secrets in GitHub Actions for `rsync` deployments increases the attack surface.

## Decision

We will standardize **GitHub Pages (GH Pages)** as the canonical hosting platform for all public-facing documentation across the ecosystem.

### Implementation Requirements:

1. **Serverless Deployment:** All public repositories MUST utilize the official `actions/deploy-pages` GitHub Action to publish build artifacts. The use of manual `rsync` or SSH-based deployment to private infrastructure is deprecated for public repos.
2. **CI-Driven Builds:** Documentation MUST be built within a GitHub Actions runner. For MyST-based projects, this involves running `myst build --html` before uploading the resulting `_build/html` directory as an artifact.
3. **Integrity Guardrails:** Every deployment workflow MUST include a validation phase, see {term}`ADR-26012`
4. **Zero-Artifact Commits:** Rendered HTML files and `_build/` directories MUST NOT be tracked in Git. Deployment must occur dynamically from source logic.

## Consequences

### Positive

* **High Availability:** Documentation is hosted on GitHub's global infrastructure with 99.9% uptime and native SSL/TLS management.
* **Reduced Complexity:** Removes the need for Traefik, Podman, and Nginx configuration for standard static sites.
* **Enhanced Security:** Eliminates the need to store sensitive SSH private keys in GitHub Secrets.
* **Global Performance:** Leveraging GitHub’s CDN ensures low-latency access for international users.
* **SVA Compliance:** Adheres to the Smallest Viable Architecture by utilizing commodity hosting for a commodity task.

### Negative / Risks

* **Vendor Lock-in:** Documentation hosting is tied to GitHub. **Mitigation:** MyST Markdown is a standard format; the build process remains portable to any static host (Netlify, Vercel) if needed.
* **Static Limitation:** GH Pages does not support server-side logic (e.g., dynamic forms or databases). **Mitigation:** The current documentation engine is strictly static-site-gen based.
* **Build Minutes:** Complex builds consume GitHub Actions minutes. **Mitigation:** Use caching for `uv` environments and Node modules to keep build times under 2 minutes.

## Alternatives

* **Self-Hosted Podman/Traefik:** Rejected for public repos due to maintenance overhead and lack of geo-redundancy.
* **ReadTheDocs (RTD):** Considered, but rejected as the primary standard because GH Pages offers tighter integration with our existing GitHub-centric validation workflows and MyST-MD tooling.
* **Monorepo Documentation:** Rejected in favor of the {term}`ADR-26020` - Hub-and-Spoke model.

## References

- {term}`ADR-26012`: Extraction of Documentation Validation Engine
- {term}`ADR-26015`: Mandatory Sync-Guard & Diff Suppression
- {term}`ADR-26020`: Hub-and-Spoke Ecosystem Documentation Architecture
- [GitHub Pages Deployment Guide](/tools/docs/website/01_github_pages_deployment.ipynb)
- [Self-Hosted Website Deployment](/tools/docs/website/02_self_hosted_deployment.ipynb) (deprecated for public repos)

## Participants

1. Vadim Rudakov
2. Senior DevOps Systems Architect (Gemini)
