---
title: Context Management — Aider
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Deep dive into Aider's async background summarization of conversation
  history — how it manages done_messages, cur_messages, and the token budget system.
tags:
- architecture
- agents
date: '2026-04-05'
options:
  version: 1.0.0
  birth: '2026-04-05'
  type: guide
  token_size: 1536
---
# Context Management — Aider

**Agent version:** v0.86.3.dev (commit `bdb4d9ff`)
**Analysis date:** 2026-04-05

## Architecture Overview

Aider uses a **dual-buffer system** for conversation history, managed by the `Coder` class:

- **`done_messages`** — Completed turns (user + assistant exchanges already processed)
- **`cur_messages`** — Current turn-in-progress (latest user input and assistant response being generated)

Each turn follows this flow in `run_one()`:
1. `init_before_message()` resets per-message state
2. User input is appended to `cur_messages`
3. `send_message()` assembles full context, sends to API, appends assistant reply to `cur_messages`
4. `move_back_cur_messages()` merges `cur_messages` into `done_messages`, clears `cur_messages`

The dual-buffer handoff (`move_back_cur_messages`) is the key mechanism that separates completed turns from the active one:

```python
def move_back_cur_messages(self, message):
    # Add any final assistant response to cur_messages
    if message:
        self.cur_messages.append({
            "role": self.main_model.role.name,
            "content": message,
        })
    # Merge completed turns into done_messages
    self.done_messages += self.cur_messages
    self.cur_messages = []
    # Save to history/session file
    self.save_history()
```

This ensures that only completed turns are candidates for summarization — the current turn always stays raw.

## History Transmission

Aider sends the **full assembled context** on every call, not raw history. The `format_chat_chunks()` method constructs a `ChatChunks` dataclass with ordered segments:

```python
@dataclass
class ChatChunks:
    system: List       # System prompt
    examples: List     # Few-shot examples
    done: List         # Summarized done messages
    repo: List         # Repo map context
    readonly_files: List
    chat_files: List   # Open file contents
    cur: List          # Current turn messages
    reminder: List     # Optional system reminder
```

Final payload: `system + examples + readonly_files + repo + done + chat_files + cur + reminder`

**Key file:** `aider/coders/base_coder.py` — `format_chat_chunks()` (~line 1200)

## Token Counting

Pre-send check in `check_tokens()`:
```python
input_tokens = self.main_model.token_count(messages)
max_input_tokens = self.main_model.info.get("max_input_tokens") or 0
if max_input_tokens and input_tokens >= max_input_tokens:
    # Warn user, suggest /drop or /clear
```

Model context windows come from LiteLLM's `model_prices_and_context_window.json` (cached, 24h TTL).

## Compaction: Async Background Summarization

**Key file:** `aider/history.py` — `ChatSummary` class

### Threshold

`max_chat_history_tokens` = min(max_input_tokens / 16, 8192), floor 1024

For a 128K model: 8192 tokens (capped). For 8K model: 1024 tokens (floored).

### Algorithm

1. If total `done_messages` tokens fit within threshold, return unchanged
2. Split messages into **head** (older) and **tail** (recent) using half-max-token boundary (iterating in reverse)
3. Summarize head via a separate LLM call with prompt: `"I spoke to you previously about a number of things.\n"`
4. If combined summary + tail still exceeds limit, recurse (max depth 3)
5. If messages ≤ 4 or depth > 3, summarize everything into a single message

### Non-blocking Design

Summarization runs **asynchronously** on a background thread:
- `summarize_start()` — kicks off background thread
- `summarize_worker()` — performs the LLM calls
- `summarize_end()` — replaces `done_messages` with summarized result

This means the main conversation loop is **never blocked** by summarization. The summarized result is applied at the start of the next `format_chat_chunks()` call.

**Key file:** `aider/coders/base_coder.py` — `summarize_start()` / `summarize_end()` (~line 1001)

## Overflow Handling

### Pre-send Warning

`check_tokens()` warns the user if tokens approach the limit, suggesting `/drop` or `/clear`. User can choose to proceed anyway.

### Runtime Error Recovery

When LiteLLM raises `ContextWindowExceededError` in `send_message()`:
```python
if ex_info.name == "ContextWindowExceededError":
    exhausted = True
    break
```

Then `show_exhausted_error()` provides a detailed breakdown:
```
Model <name> has hit a token limit!
Input tokens: ~X of Y
Output tokens: ~X of Y
Total tokens: ~X of Y
```

### Output Limit (FinishReasonLength)

When the response hits the output token limit, Aider retries with **assistant prefill** (if the model supports it):
```python
except FinishReasonLength:
    if not self.main_model.info.get("supports_assistant_prefill"):
        exhausted = True
        break
    # Continue with partial response as prefix
    messages[-1]["content"] = self.multi_response_content
```

## Repo Map Token Budgeting

The repo map dynamically sizes its token budget based on available context:

```python
padding = 4096
if max_map_tokens and self.max_context_window:
    target = min(max_map_tokens, self.max_context_window - padding, ...)
```

When no files are in the chat, the repo map gets a bigger view.

## System Reminder Injection

In `format_chat_chunks()`, a reminder is conditionally appended either as a separate system message or stuffed into the last user message, depending on whether there is room:

```python
max_input_tokens = self.main_model.info.get("max_input_tokens") or 0
if not max_input_tokens or total_tokens < max_input_tokens:
    # Add the reminder
```

## Key Files

| File | Role |
|------|------|
| `aider/coders/base_coder.py` | `Coder` class — dual-buffer system, send loop, summarization |
| `aider/history.py` | `ChatSummary` — async background summarization |
| `aider/coders/chat_chunks.py` | `ChatChunks` dataclass — context assembly structure |
| `aider/models.py` | Model registry, context window resolution from LiteLLM |
| `aider/repomap.py` | Dynamic repo map token budgeting |
