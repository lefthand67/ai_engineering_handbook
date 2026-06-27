---
title: 'The Compaction API Contract: Why System Prompts Don''t Mix'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: How LLM APIs actually work — stateless, full message array per call,
  response = only new assistant text. Step-by-step compaction flow with code evidence
  from Qwen Code, OpenCode, and Claude Code.
tags:
- architecture
- agents
- context_management
date: '2026-04-08'
options:
  version: 1.0.0
  birth: '2026-04-08'
  type: guide
  token_size: 2586
---
# The Compaction API Contract: Why System Prompts Don't Mix

## The Core Insight

When developers think about "compaction" or "subagent spawning," they often imagine the system prompt being "mixed in" with the conversation history — like a web chat where the entire mixture of system and user messages accumulates over time. **This is not how LLM APIs work.**

The LLM API contract is **stateless request/response**:

| What you send | What you get back |
|---|---|
| Full message array: `[system, user, assistant, user, assistant, ...]` | **Only the new assistant message** — a single text/stream |

The API does **not** echo back the conversation history. The response contains **only the new assistant message** — the summary, the review, the code. The client (the agent) is responsible for:

1. Building the full message array on every call
2. Storing the response
3. Appending it to the history for the next call

This means that when a "compaction agent" or "forked agent" makes an API call with a different system prompt, **the old system prompt is not present** — it was never part of the response, and it is not carried over from the previous call. Each API call is a fresh request with exactly one system prompt.

:::{seealso}
For the broader picture of how subagents work (beyond just compaction), see [How Subagents Actually Work](/ai_agents/architecture/orchestration/how_subagents_actually_work_myth_of_process_spawning.md).
:::

## Normal Turn vs. Compaction Turn

### Normal Turn (Main Conversation)

```typescript
// packages/opencode/src/session/prompt.ts — OpenCode main loop
let msgs = yield* MessageV2.filterCompactedEffect(sessionID)
const modelMsgs = yield* Effect.promise(() => MessageV2.toModelMessages(msgs, model))

const result = yield* handle.process({
  messages: [
    systemMessage,       // ← normal agent system prompt
    ...modelMsgs,        // ← conversation history (user/assistant turns)
    newUserMessage,      // ← latest user input
  ],
})
```

The API call:
```
[system: "You are a coding agent with tools: read, write, edit, ..."]
[user: "Help me fix the bug in auth.ts"]
[assistant: "Let me read auth.ts..."]
[tool_result: "content of auth.ts"]
[assistant: "I see the issue..."]
[user: "Great, now fix it"]
```

The response: **only the assistant's new message** — e.g., `"I've fixed the bug. Here's what I changed..."`

### Compaction Turn (Separate API Request)

When context overflows, the runtime makes a **brand new API call**:

```
[system: PROMPT_COMPACTION ← entirely different system prompt!]
[user: "Help me fix the bug in auth.ts"]
[assistant: "Let me read auth.ts..."]
[tool_result: "content of auth.ts"]
[assistant: "I see the issue..."]
[user: "Great, now fix it"]
[assistant: "Done, I wrote the fix..."]
...
[user: "Summarize this conversation..."]  ← appended instruction
```

Same conversation history, **different system prompt**. The response: **only the summary**:

```
## Goal
Fix auth.ts bug — missing null check on line 42

## Instructions
- Check utils.ts next

## Discoveries
- The auth module uses JWT with 1h expiry

## Accomplished
- Fixed null check in auth.ts

## Relevant files / directories
- src/auth.ts (modified)
- src/utils.ts (needs review)
```

The old system prompt is **not** in this response. The LLM never sees both system prompts in the same request.

## Code Evidence: Three Agents, Same Pattern

### Qwen Code: The Clearest Example

Qwen Code's compression flow shows the full lifecycle most explicitly:

**Step 1: Build the compaction API call**

```typescript
const summaryResponse = await config.getContentGenerator().generateContent({
  model,
  contents: [
    ...historyToCompress,          // ← old conversation turns (user/assistant)
    {
      role: 'user',
      parts: [{
        text: 'First, reason in your scratchpad. Then, generate the <state_snapshot>.',
      }],
    },
  ],
  config: {
    systemInstruction: getCompressionPrompt(),  // ← DIFFERENT system prompt
  },
})
```

**Step 2: The API returns only the summary** — not the input history.

**Step 3: Replace the old history with the summary**

```typescript
extraHistory = [
  { role: 'user', parts: [{ text: summary }] },  // ← ONLY the summary text
  { role: 'model', parts: [{ text: 'Got it. thanks for the additional context!' }] },
  ...historyToKeep,  // The last 30% of conversation
]
```

**Step 4: The next main API call** sees:

```
[system: "You are Qwen Code, a coding assistant..."]  ← ORIGINAL system prompt restored
[user: "The user asked me to fix a bug in auth.ts. I identified..."]  ← summary as user message
[model: "Got it. thanks for the additional context!"]
[user: "Great, now also check utils.ts"]  ← new user message
```

The old 70% of conversation is **gone**. Only the summary remains, injected as a **user message** (not a system prompt).

**Step 5: Checkpoint in JSONL**

On success, a `system` record with subtype `chat_compression` is appended to the JSONL session file with a `compressedHistory` field — a snapshot of the new `Content[]` the model should see going forward. Original UI history records are **not mutated** — the checkpoint allows session resumption to reconstruct the compressed model-facing history.

### OpenCode: Compaction Agent + Boundary Detection

OpenCode defines the compaction agent with all tools denied:

```typescript
// packages/opencode/src/session/compaction.ts
compaction: {
  name: "compaction",
  mode: "primary",
  native: true,
  hidden: true,
  prompt: PROMPT_COMPACTION,
  permission: Permission.merge(
    defaults,
    Permission.fromConfig({ "*": "deny" }),  // ← hard guarantee: LLM cannot call tools
    user
  ),
  options: {},
}
```

After compaction succeeds, the summary is saved as a `compaction`-type part in the SQLite database. The next time the main agent reads history, `filterCompacted()` streams from the database in **reverse chronological order** and **stops** at the compaction boundary:

```typescript
// packages/opencode/src/session/message-v2.ts
export function filterCompacted(msgs: Iterable<MessageV2.WithParts>) {
  const result = [] as MessageV2.WithParts[]
  const completed = new Set<string>()
  for (const msg of msgs) {
    result.push(msg)
    if (
      msg.info.role === "user" &&
      completed.has(msg.info.id) &&
      msg.parts.some((part) => part.type === "compaction")  // ← stops here
    )
      break  // does NOT include history before this point
    if (msg.info.role === "assistant" && msg.info.summary && msg.info.finish && !msg.info.error)
      completed.add(msg.info.parentID)
  }
  result.reverse()
  return result
}
```

The compaction summary acts as a **hard boundary** — everything before it is never sent again. This is deterministic code, not LLM behavior.

### Claude Code: Forked Agent with Structured Summary

Claude Code's Tier 4 (Full Compaction) follows the same pattern:

1. Sends ALL messages to a "forked agent" with the compact prompt
2. The LLM produces a structured 9-section summary: Primary Request, Key Concepts, Files/Code, Errors/Fixes, Problem Solving, All User Messages, Pending Tasks, Current Work, Next Steps
3. The `<analysis>` scratchpad is stripped; only `<summary>` is kept
4. After compaction, post-compact attachments are re-injected:
   - File read state (up to 5 files, 50K token budget, 5K per file)
   - Skill invocations (25K token budget, 5K per skill)
   - Plan attachment, tool/MCP instruction deltas, hook outputs

The term "forked agent" in Claude Code's source code (`src/services/compact/compact.ts`) refers to this separate API call pattern — **not** an OS `fork()`.

## The Token Math

Every compaction implementation follows the same formula:

```
newTokenCount = originalTokenCount
              - (compressionInputTokenCount - overhead)
              + compressionOutputTokenCount
```

Where:
- `compressionInputTokenCount` = tokens in the history being compressed
- `overhead` = system prompt + instruction tokens (~1000 for Qwen Code)
- `compressionOutputTokenCount` = tokens in the summary response

Qwen Code's implementation:

```typescript
newTokenCount = Math.max(
  0,
  originalTokenCount - (compressionInputTokenCount - 1000) + compressionOutputTokenCount,
)
```

Guards prevent making things worse:
- Won't compress if compressible portion < 5% of total (futile)
- Won't proceed if the summary is empty
- Won't proceed if compression would **increase** token count
- Won't re-attempt after a failed compression unless forced manually

## What "Stateless" Really Means

The LLM API has **no session state**. It doesn't remember:

- Previous system prompts
- Previous API calls
- Any context not included in the current request

This is why agents must send the **full conversation history** on every call. And this is why "system prompt mixing" is impossible — there is only one system prompt per request, and it is the one you explicitly provide.

When the compaction API call uses `PROMPT_COMPACTION`, that is the **only** system prompt the LLM sees. The normal agent system prompt (`"You are a coding agent with tools..."`) is not present — it was part of a **previous, separate** API call.

## Summary

| Question | Answer |
|----------|--------|
| Are system prompts mixed across calls? | No — each API call has exactly one system prompt |
| Does the API echo back the input history? | No — the response is only the new assistant message |
| How does the summary replace old history? | Client code builds a new message array: `[summary as user message, ...recent turns]` |
| Is the old system prompt present in the compaction call? | No — the compaction call uses a different system prompt |
| After compaction, which system prompt is used? | The original agent system prompt is restored |
| Is this enforced by code or LLM compliance? | The message array construction is deterministic code; the summary quality depends on the LLM |

:::{seealso}
For how agents fight instability when the LLM fails to follow compaction instructions, see [Stability Against LLM Drift](/ai_agents/architecture/skills/stability_in_a_probabilistic_substrate_how_agents_fight_llm_drift.md).
:::
