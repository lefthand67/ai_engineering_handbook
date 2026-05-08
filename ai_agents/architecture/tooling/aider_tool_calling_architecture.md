---
title: Aider Tool Calling Architecture Analysis
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: 2026-05-06
description: Source-level analysis of the tool calling mechanism in Aider, focusing
  on the dual approach of JSON schemas and Coder Protocols, and its hierarchical steering
  model.
tags:
- agents
- architecture
options:
  type: guide
  birth: 2026-05-06
  version: 1.2.0
  token_size: 1411
---
# Aider Tool Calling Architecture Analysis

This analysis examines the tool calling implementation in Aider, detailing how it defines tools, integrates them with various LLMs, and employs a hierarchical steering model to ensure precise code editing.

## 1. Tool Definitions: Schemas and Protocols

Aider uses a dual approach to tool definitions: native JSON schemas for modern LLMs and "Coder Protocols" for structural precision.

### 1.1 JSON Schema Definitions
For models that support native tool calling, Aider defines capabilities using JSON schema dictionaries.

**Path**: `ai_agents/research/ai_coding_agents/aider/aider/coders/editblock_func_coder.py`

**Snippet**:
```python
    functions = [
        dict(
            name="replace_lines",
            description="create or update one or more files",
            parameters=dict(
                type="object",
                required=["explanation", "edits"],
                properties=dict(
                    explanation=dict(
                        type="string",
                        description=(
                            "Step by step plan for the changes to be made to the code (future"
                            " tense, markdown format)"
                        ),
                    ),
                    edits=dict(
                        type="array",
                        items=dict(
                            type="object",
                            required=["path", "original_lines", "updated_lines"],
                            properties=dict(
                                path=dict(
                                    type="string",
                                    description="Path of file to edit",
                                ),
                                original_lines=dict(
                                    type="array",
                                    items=dict(
                                        type="string",
                                    ),
                                    description=(
                                        "A unique stretch of lines from the original file,"
                                        " including all whitespace, without skipping any lines"
                                    ),
                                ),
                                updated_lines=dict(
                                    type="array",
                                    items=dict(
                                        type="string",
                                    ),
                                    description="New content to replace the `original_lines` with",
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    ]
```

### 1.2 The "Coder Protocol" Pattern
Unlike agents that rely solely on API-level tools, Aider implements **Coder Protocols**. These are strictly formatted text blocks (e.g., `SEARCH/REPLACE`) that the LLM is steered to produce. This ensures consistency across models that may have varying tool-calling capabilities.

**Implementation**: Found in `aider/coders/` (e.g., `editblock_prompts.py`, `wholefile_prompts.py`).

## 2. LLM Integration and Invocation

### 2.1 Request Integration
Aider integrates tool definitions into the LLM request via LiteLLM, forcing the model to use specific functions when necessary.

**Path**: `ai_agents/research/ai_coding_agents/aider/aider/models.py`
```python
        if functions is not None:
            function = functions[0]
            kwargs["tools"] = [dict(type="function", function=function)]
            kwargs["tool_choice"] = {"type": "function", "function": {"name": function["name"]}}
```

### 2.2 Capture and Execution Loop
Tool calls are captured in the base coder and executed by specific implementations.

**Path (Capture)**: `ai_agents/research/ai_coding_agents/aider/aider/coders/base_coder.py`

**Snippet (Capture)**:
```python
            if completion.choices[0].message.tool_calls:
                self.partial_response_function_call = (
                    completion.choices[0].message.tool_calls[0].function
```

**Path (Execution)**: `ai_agents/research/ai_coding_agents/aider/aider/coders/editblock_func_coder.py`

**Snippet (Execution)**:
```python
    def _update_files(self):
        # ...
        args = self.parse_partial_args()
        if not args:
            return

        edits = args.get("edits", [])

        edited = set()
        for edit in edits:
            path = get_arg(edit, "path")
            original = get_arg(edit, "original_lines")
            updated = get_arg(edit, "updated_lines")
            # ...
```

The `EditBlockFunctionCoder` parses the `tool_calls` arguments into a dictionary and applies the `original_lines` $\rightarrow$ `updated_lines` replacement logic to the target files.

## 3. The Three-Tier Steering Model

Aider prevents hallucinations and ensures editing precision through a hierarchical steering architecture.

### Tier 1: Tool-Level Steering (Semantic)
Aider embeds high-intensity constraints directly into the prompts associated with each coder.

- **Mechanism**: `_prompts.py` files use imperative language ("MUST", "DO NOT") to define the boundaries of the tool.
- **Evidence**: `aider/coders/editblock_prompts.py`
  - *"Every SEARCH section must EXACTLY MATCH the existing file content, character for character..."*
- **Role**: Ensures the LLM produces structurally valid blocks that can be parsed without ambiguity.

### Tier 2: Operational Steering (Modality)
Aider manages operational modes through a class-based persona hierarchy.

- **Mechanism**: `CoderPrompts` $\rightarrow$ `ArchitectPrompts` $\rightarrow$ `EditblockPrompts`.
- **Modality Switching**: Aider can switch between an **Architect** (who provides high-level directions) and an **Editor** (who implements specific changes).
- **Evidence**: `architect_prompts.py`
  - *"Act as an expert architect engineer and provide direction to your editor engineer... DO NOT show the entire updated function/file/etc!"*
- **Role**: Defines the persona and goal of the agent for the current turn.

### Tier 3: Contextual Steering (Conventions)
Aider uses a structural "compass" to steer the LLM toward relevant files in large repositories.

- **Mechanism**: The **RepoMap**. Aider uses `grep-ast` to extract tags and a PageRank-like algorithm to rank the importance of symbols.
- **Evidence**: `repomap.py` and `repo.py`.
- **Injection**: The resulting condensed map of the codebase is injected into the prompt, guiding the LLM's decision on which files to request or edit.
- **Role**: Provides structural awareness and prevents the LLM from guessing file locations in complex projects.
