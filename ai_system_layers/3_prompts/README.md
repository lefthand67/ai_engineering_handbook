---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.1
---

---
title: 'Layer 3: Prompts-as-Infrastructure'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: "2026-05-02"
description: Overview of the Prompts-as-Infrastructure layer, describing the block-based
  architecture for scalable prompt engineering.
tags:
- prompts
- architecture
options:
  type: guide
  birth: "2026-01-01"
  version: "1.0.0"
  token_size: 661
---
# Layer 3: Prompts-as-Infrastructure

+++

This directory implements a **Block-Based Prompt Architecture** designed for Single Source of Truth (SSoT) and scalable maintenance of complex consultant personas.

## **1. Architecture Overview**

Instead of monolithic prompt files, the system uses a **JIT-composed block architecture**. This ensures that shared methodology, technical stacks, and tradecraft are defined once and reused across all consultants.

### **The SSoT Hub (`/blocks`)**
Shared prompt fragments are stored in `ai_system_layers/3_prompts/blocks/`. These blocks contain authoritative definitions for:
- **Common User Stack**: The project's technical environment.
- **Core Principles**: Behavioral rules and quality standards.
- **Consulting Context**: Production-ready definitions and industry standards (ISO 29148/SWEBOK).
- **Frameworks**: Specialized methodologies (e.g., WRC/SVA, Heuer Tradecraft).
- **Output Protocols**: Standard response structures and formatting.

### **Consultant Manifests (`/consultants`)**
Consultant files are now **Manifests**—thin skins that describe how to assemble a persona from the hub blocks. A manifest declares its dependencies via an `_includes` list and provides specific overrides to specialize the persona.

### **JIT Compilation**
The [`prepare_prompt.py`](/tools/scripts/prepare_prompt.py) script acts as the compiler. At runtime, it:
1. Recursively resolves all `_includes`.
2. Merges the blocks into a single structure.
3. Applies overrides from the manifest (Manifest values > Block values).
4. Converts the resulting JSON to a clean, YAML-like format for LLM delivery.

+++

## **2. Directory Structure**

```{code-cell}
tree . --gitignore -I "*.md"
```

## **3. Creating a New Consultant**

To create a new consultant, define a JSON manifest in `/consultants` following this pattern:

```json
{
  "metadata": {
    "title": "Specialized Consultant",
    "version": "1.0.0"
  },
  "_includes": [
    "blocks/common_principles.json",
    "blocks/common_user_stack.json",
    "blocks/standard_output_protocol.json"
  ],
  "consultant_persona": {
    "role": "Expert in X",
    "tone": "Analytical"
  },
  "USER_INPUT": "..."
}
```
