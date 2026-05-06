---
title: Aider Tool Calling Architecture Analysis
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: 2026-05-06
description: Source-level analysis of the tool calling mechanism in Aider, focusing
  on class-based declarations, litellm integration, and streaming tool capture.
tags:
- agents
- architecture
options:
  type: guide
  birth: 2026-05-06
  version: 1.1.0
  id: A-26056
  status: accepted
  token_size: 1197
---
# Aider Tool Calling Architecture Analysis

This analysis examines the tool calling implementation in Aider, detailing how it defines tools, integrates them with various LLMs via LiteLLM, and manages the execution of edits.

## 1. Tool Definitions

**Claim**: Aider defines its editing capabilities using JSON schema dictionaries that specify the required parameters and types for the LLM.

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

**Explanation**: The `EditBlockFunctionCoder` class contains a `functions` list where the `replace_lines` tool is defined. This schema forces the LLM to provide an explanation and a list of edits, each consisting of a file path, the exact original lines to be replaced, and the new content.

## 2. LLM Integration

**Claim**: Aider integrates these tool definitions into the LLM request by setting the `tools` and `tool_choice` parameters in the `litellm.completion` call.

**Path**: `ai_agents/research/ai_coding_agents/aider/aider/models.py`

**Snippet**:
```python
        if functions is not None:
            function = functions[0]
            kwargs["tools"] = [dict(type="function", function=function)]
            kwargs["tool_choice"] = {"type": "function", "function": {"name": function["name"]}}
```

**Explanation**: In the `send_completion` method, if tool functions are provided, they are wrapped in the OpenAI-compatible `tools` format. The `tool_choice` is explicitly set to force the model to use the specified function.

## 3. Tool Invocation

**Claim**: Tool calls are captured from the LLM response in the base coder and then parsed and executed in specific coder implementations.

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

**Explanation**: The `base_coder.py` captures the `tool_calls` from the LLM response and stores them in `partial_response_function_call`. The `EditBlockFunctionCoder` then uses `parse_partial_args()` to convert the tool's arguments into a Python dictionary, which is then iterated over to apply the file edits.

## 4. Tool Constraints and Steering

**Claim**: Aider enforces strict constraints on the LLM's output through detailed descriptions in the tool schema.

**Path**: `ai_agents/research/ai_coding_agents/aider/aider/coders/editblock_func_coder.py`

**Snippet**:
```python
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
```

**Explanation**: To prevent the LLM from hallucinating or skipping content during a replace operation, the `original_lines` parameter description explicitly instructs the model to include "all whitespace, without skipping any lines". This ensures the replacement logic can find a unique and exact match in the target file.
