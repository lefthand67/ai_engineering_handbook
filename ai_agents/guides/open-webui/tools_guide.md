---
title: 'Open WebUI Tools: Practical Implementation Guide'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: 2026-05-03
description: Practical implementation guide for creating local Python tools and connecting
  external OpenAPI servers in Open WebUI.
tags:
- agents
- development
options:
  type: guide
  version: 1.0.0
  birth: 2026-05-03
  token_size: 1413
---
# Open WebUI Tools: Practical Implementation Guide

This guide provides a hands-on approach to creating and deploying tools in Open WebUI. It complements the [Open WebUI Tool System Analysis](/ai_agents/architecture/tooling/open_webui_tool_system.md).

## 1. Creating Local Python Tools

Local tools are Python scripts that Open WebUI loads dynamically. The system uses your **type hints** and **docstrings** to tell the LLM how to use the tool.

### The "Hello World" Template
Create a Python file (e.g., `my_tool.py`). The simplest tool is just a function.

```python
from pydantic import BaseModel, Field
from typing import Optional

class Tools:
    def say_hello(self, name: str) -> str:
        """
        Greets the user by name.

        :param name: The name of the person to greet.
        :return: A friendly greeting string.
        """
        return f"Hello, {name}! I am an Open WebUI tool."
```

### Critical Requirements for Local Tools

#### A. The Docstring Format (reST)
Open WebUI **requires** reStructuredText (reST) format for parameter descriptions. If you omit the `:param` tag, the LLM will not receive a description for that argument.

**Correct:**
```python
"""
Search for a user by ID.

:param user_id: The unique UUID of the user.
:return: User profile data.
"""
```

**Incorrect:**
```python
"""
Search for a user by ID.
Args:
    user_id: The unique UUID of the user.
"""
```

#### B. Type Hinting
Always use explicit type hints (e.g., `str`, `int`, `float`, `bool`, `list[str]`). These are converted directly into the JSON schema provided to the LLM.

---

## 2. Advanced Tool Configuration (Valves)

Valves allow you to add configuration settings to your tools that can be modified via the Web UI without changing the code.

### Global Valves (Admin Settings)
Use a `Valves` class for settings that apply to everyone.

```python
from pydantic import BaseModel, Field

class Tools:
    class Valves(BaseModel):
        api_key: str = Field(default="", description="API Key for the external service")
        timeout: int = Field(default=30, description="Request timeout in seconds")

    def get_data(self, query: str) -> str:
        """
        Fetch data from an API.
        :param query: The search query.
        """
        # Access global valves via self.valves
        key = self.valves.api_key
        return f"Fetching {query} using key {key[:4]}..."
```

### User Valves (Per-User Settings)
Use a `UserValves` class for settings that each user can configure individually.

```python
class Tools:
    class UserValves(BaseModel):
        preferred_language: str = Field(default="English", description="Language for tool responses")

    def translate(self, text: str) -> str:
        """
        Translates text to the user's preferred language.
        :param text: Text to translate.
        """
        # Access user-specific valves via self.user_valves (injected by the system)
        lang = getattr(self, 'user_valves', None).preferred_language if hasattr(self, 'user_valves') else "English"
        return f"Translating '{text}' to {lang}..."
```

---

## 3. Creating External Tool Servers (OpenAPI)

If you have an existing API, you don't need to write Python code for Open WebUI. You just need an **OpenAPI Specification (JSON/YAML)**.

### Requirements for the API
1.  **OpenAPI 3.0+**: Your server must expose a `/openapi.json` or `/swagger.json` endpoint.
2.  **`operationId`**: Every endpoint must have a unique `operationId`. Open WebUI uses this ID as the tool's name.
3.  **Descriptions**: Provide clear `summary` and `description` fields in your OpenAPI spec so the LLM knows when to call the endpoint.

### Connection Setup
1.  Go to **Workspace** $\rightarrow$ **Tools** $\rightarrow$ **Add Tool Server**.
2.  Enter the **URL** of your server.
3.  Select the **Auth Type** (e.g., Bearer Token).
4.  Open WebUI will fetch the spec and automatically register all `operationId`s as available tools.

---

## 4. Managing Tool Scope (Visibility)

Tools in Open WebUI are not "globally" active. You must explicitly define which contexts have access to which tools.

### A. Model-Level Scope
You can bind tools to a specific model. This is the most common way to ensure a specialized model has the right capabilities.
1.  Go to **Workspace** $\rightarrow$ **Models**.
2.  Edit your target model.
3.  In the **Tools** section, select the tools you want to attach.
4.  **Effect**: Only chats started with this model will have these tools available.

### B. Folder/Context-Level Scope
You can bind tools to a specific folder or collection.
1.  Navigate to your **Workspace** $\rightarrow$ **Collections/Folders**.
2.  Assign tools to the folder context.
3.  **Effect**: Any model used within that folder's context will automatically gain access to these tools, regardless of the model's own default tool set.

---

## 5. Using Tools in the Interface

Once a tool is created or connected:

1.  **Configure Settings**:
    *   Go to **Workspace** $\rightarrow$ **Tools**.
    *   Click the gear icon $\text{⚙️}$ next to your tool to edit the **Valves**.
2.  **Invoke**:
    *   Start a chat with the assigned model (or within the assigned folder).
    *   Ask a question that triggers the tool (e.g., "Search for user 123").
    *   The model will generate a tool call, the backend will execute it, and the result will be fed back into the conversation.
