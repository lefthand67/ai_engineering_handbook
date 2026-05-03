---
title: Open WebUI Tool System Analysis
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: 2026-05-03
description: Source-level analysis of the tool definition, registration, and execution
  pipeline in Open WebUI.
tags:
- agents
- architecture
options:
  type: analysis
  birth: 2026-05-03
  version: 1.0.0
  token_size: 2117
  id: A-26026
  status: accepted
---
# Open WebUI Tool System Analysis

This analysis examines the implementation of the tool system in Open WebUI, focusing on how tools are defined, how their schemas are generated for LLMs, and the mechanism used to execute them.

## 1. Tool Activation and Scoping

### Claim
Tool activation in Open WebUI is dynamic and request-driven; tools are not statically bound to models but are injected into the session via the request payload based on model or folder context.

### Evidence
**File**: `backend/open_webui/utils/middleware.py`
**Logic**: Extraction of `tool_ids` from `form_data` and `metadata`.

```python
# Model-level tools from request body
tool_ids = form_data.pop('tool_ids', None)

# ... later in the same request flow ...

# Folder/Context-level tools from metadata
tool_ids = metadata.get('tool_ids', None)

# ... both are then passed to get_tools
tools_dict = await get_tools(
    request,
    tool_ids,
    user,
    { ... },
)
```

### Explanation
The frontend determines which tools should be available based on the current context (the selected model or the active folder/collection). These are passed as a list of IDs in the `tool_ids` field. The backend (`middleware.py`) acts as a pass-through, extracting these IDs and calling `get_tools()`, which resolves the IDs into executable callables. This allows a single tool to be shared across multiple models or restricted to a specific context without modifying the tool's code.

---

## 2. Tool Definition and Schema Generation

### Claim
Open WebUI uses Python type hints and reStructuredText (reST) docstrings to automatically generate OpenAI-compatible tool specifications for built-in and local tools.


### Evidence
**File**: `backend/open_webui/utils/tools.py`
**Functions**: `convert_function_to_pydantic_model` and `get_tool_specs`

```python
def convert_function_to_pydantic_model(func: Callable) -> type[BaseModel]:
    # ...
    type_hints = get_type_hints(func)
    signature = inspect.signature(func)
    parameters = signature.parameters

    docstring = func.__doc__
    function_description = parse_description(docstring)
    function_param_descriptions = parse_docstring(docstring)

    field_defs = {}
    for name, param in parameters.items():
        type_hint = type_hints.get(name, Any)
        default_value = param.default if param.default is not param.empty else ...
        param_description = function_param_descriptions.get(name, None)

        if param_description:
            field_defs[name] = (
                type_hint,
                Field(default_value, description=param_description),
            )
        else:
            field_defs[name] = type_hint, default_value

    model = create_model(func.__name__, **field_defs)
    model.__doc__ = function_description
    return model
```

### Explanation
The system leverages Python's introspection capabilities. The `convert_function_to_pydantic_model` function reads the function's type hints and parses the docstring (specifically looking for `:param name: description` patterns). It then uses Pydantic's `create_model` to dynamically generate a model representing the function's arguments. This model is subsequently passed to `convert_pydantic_model_to_openai_function_spec` (from `langchain_core`), which produces the JSON schema required by OpenAI-compatible APIs.

---

## 2. Context Injection via Parameter Wrapping

### Claim
Open WebUI injects internal state (such as the current user, request object, and chat metadata) into tool functions using a wrapping mechanism that hides these parameters from the LLM.

### Evidence
**File**: `backend/open_webui/utils/tools.py`
**Function**: `get_async_tool_function_and_apply_extra_params`

```python
async def get_async_tool_function_and_apply_extra_params(
    function: Callable, extra_params: dict
) -> Callable[..., Awaitable]:
    sig = inspect.signature(function)
    extra_params = {k: v for k, v in extra_params.items() if k in sig.parameters}
    partial_func = partial(function, **extra_params)

    # Remove the 'frozen' keyword arguments from the signature
    parameters = []
    for name, parameter in sig.parameters.items():
        if name in extra_params:
            continue
        parameters.append(parameter)

    new_sig = inspect.Signature(parameters=parameters, return_annotation=sig.return_annotation)
    # ...
    update_wrapper(new_function, function)
    new_function.__signature__ = new_sig
    return new_function
```

### Explanation
To avoid requiring the LLM to provide internal identifiers (like `user_id` or `chat_id`), Open WebUI uses `functools.partial` to pre-bind these "extra parameters" to the tool function. Crucially, it then creates a new `inspect.Signature` that excludes these pre-bound parameters. This ensures that when the system generates the tool spec or validates the LLM's call, only the actual user-facing parameters are considered.

---

## 3. Multi-Provider Tool Orchestration

### Claim
The tool system supports three distinct providers: built-in Python functions, user-defined local modules, and external tool servers (OpenAPI and MCP).

### Evidence
**File**: `backend/open_webui/utils/tools.py`
**Function**: `get_tools`

```python
# Simplified logic from get_tools
for tool_id in tool_ids:
    tool = await Tools.get_tool_by_id(tool_id)
    if tool:
        # Local Tool Logic
        module = request.app.state.TOOLS.get(tool_id, None)
        # ...
    else:
        if tool_id.startswith('server:'):
            # External Server Logic (OpenAPI / MCP)
            if type == 'openapi':
                # ... fetch spec from tool_server_data
```

### Explanation
The `get_tools` function acts as a dispatcher. It first checks the database for a local tool. If not found, it checks if the `tool_id` follows the `server:<type>:<id>` pattern.
- **Built-in Tools**: Loaded via `get_builtin_tools` based on model capabilities.
- **Local Tools**: Dynamically loaded as Python modules with support for `Valves` (global settings) and `UserValves` (per-user settings).
- **External Servers**: The system fetches an OpenAPI specification from a configured URL and maps `operationId`s to tool names.

---

## 4. External Tool Execution Pipeline

### Claim
External tools are executed by mapping the LLM's provided arguments to the target API's path, query, and request body parameters as defined in the OpenAPI specification.

### Evidence
**File**: `backend/open_webui/utils/tools.py`
**Function**: `execute_tool_server`

```python
async def execute_tool_server(
    url: str,
    headers: Dict[str, str],
    cookies: Dict[str, str],
    name: str,
    params: Dict[str, Any],
    server_data: Dict[str, Any],
) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    # ...
    for route_path, methods in paths.items():
        for http_method, operation in methods.items():
            if isinstance(operation, dict) and operation.get('operationId') == name:
                matching_route = (route_path, methods)
                break
    # ...
    for param in operation.get('parameters', []):
        param_name = param.get('name')
        param_in = param.get('in')
        if param_name in params:
            if param_in == 'path':
                path_params[param_name] = params[param_name]
            if param_in == 'query':
                query_params[param_name] = params[param_name]
```

### Explanation
When an external tool is called, `execute_tool_server` performs a lookup in the cached OpenAPI spec using the tool's name as the `operationId`. It then iterates through the operation's parameters, sorting the LLM's arguments into `path_params`, `query_params`, or `body_params` based on the `in` field of the OpenAPI parameter definition. Finally, it constructs and sends an `aiohttp` request to the external server.

---

## 5. Access Control Integration

### Claim
Tool execution is guarded by an access control layer that verifies permissions for both local tools and external tool server connections.

### Evidence
**File**: `backend/open_webui/utils/tools.py`
**Calls**: `AccessGrants.has_access` and `has_connection_access`

```python
# Local tool check
if (
    not (user.role == 'admin' and BYPASS_ADMIN_ACCESS_CONTROL)
    and tool.user_id != user.id
    and not await AccessGrants.has_access(
        user_id=user.id,
        resource_type='tool',
        resource_id=tool.id,
        permission='read',
        user_group_ids=user_group_ids,
    )
):
    log.warning(f'Access denied to tool {tool_id} for user {user.id}')
    continue

# External server check
if not await has_connection_access(user, tool_server_connection, user_group_ids):
    log.warning(f'Access denied to tool server {server_id} for user {user.id}')
    continue
```

### Explanation
Before a tool is added to the `tools_dict` returned to the model, the system performs a permission check. For local tools, it checks if the user is the owner, an admin, or has been granted explicit access via the `AccessGrants` system. For external servers, it uses `has_connection_access` to verify if the user's group membership allows connection to that specific server.
