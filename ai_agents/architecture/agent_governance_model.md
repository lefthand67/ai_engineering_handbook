
---
title: Agent Governance Model (L0-L5)
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: 2026-04-27
description: A conceptual framework for separating agent infrastructure from policy
  enforcement (L0-L5).
tags:
- architecture
- agents
- security
options:
  version: 1.0.0
  birth: 2026-04-27
  type: guide
  token_size: 706
---
# Agent Governance Model (L0-L5)

To analyze and implement security in AI agents, we distinguish between the **Infrastructure Layers** (the plumbing) and the **Governance Layers** (the rules). This separation ensures that we can change security policies without modifying the underlying execution engine.

## The Layered Architecture

### Infrastructure Layers (L0 $\rightarrow$ L2)
These layers provide the raw capability to execute tools but do not make policy decisions about whether a tool *should* run. They are the "given" environment.

- **L0: The OS / Kernel**: The absolute final arbiter. If the OS user lacks permission to a file or resource, no agent setting can override it. The OS represents the "Hard Truth" of the system.
- **L1: The Runtime / API**: The execution environment (e.g., Node.js, Python) and system modules (e.g., `fs`, `os`) that translate high-level code into system calls the OS understands.
- **L2: The Agent Core**: The engine that manages the lifecycle of a tool call (Request $\rightarrow$ Schedule $\rightarrow$ Execute $\rightarrow$ Respond). It is the machinery that drives the agent's actions.

### Governance Layers (L3 $\rightarrow$ L5)
These are the **Policy Filters** placed on top of the engine. This is where "Permission Enforcement" actually happens. The goal is to intercept a request from the LLM before it ever reaches L2.

- **L3 (Tool Policy)**: The tool's own internal risk assessment. This is often dynamic and based on the tool's arguments (e.g., "Is this file path inside the workspace?").
- **L4 (User Policy)**: Explicit overrides defined by the user (e.g., via `settings.json`). This allows the user to grant or restrict access regardless of the tool's default opinion.
- **L5 (Mode Policy)**: The current operational state of the agent (e.g., `YOLO` vs `PLAN`). This acts as a final reconciliation layer that determines how `ask` results from L3/L4 are handled.

## Summary Table

| Layer | Name | Role | Type | Decision |
| :--- | :--- | :--- | :--- | :--- |
| **L0** | OS/Kernel | Final Arbiter | Infrastructure | Physical Permission |
| **L1** | Runtime | Translator | Infrastructure | API Execution |
| **L2** | Agent Core | Engine | Infrastructure | Lifecycle Mgmt |
| **L3** | Tool Policy | Risk Assessment | Governance | Tool Default $\rightarrow$ `ask/allow/deny` |
| **L4** | User Policy | Override | Governance | User Rule $\rightarrow$ `ask/allow/deny` |
| **L5** | Mode Policy | Reconciliation | Governance | Final Outcome $\rightarrow$ `Execute/Prompt` |
