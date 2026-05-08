---
title: Qwen Code `run_shell_command` — How It Works
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: 2026-05-06
description: Deep-dive into the technical implementation of the run_shell_command
  tool in Qwen Code, focusing on PTY emulation, process management, and safety.
tags:
- agents
- architecture
options:
  type: guide
  birth: 2026-05-06
  version: 1.0.0
  token_size: 1728
---
# Qwen Code `run_shell_command` — How It Works

## Overview

`run_shell_command` is a built-in tool in Qwen Code that lets the AI agent execute shell commands. It is **more sophisticated** than Python's `subprocess.call`, featuring pseudo-terminal (PTY) emulation, real-time streaming, binary detection, auto-encoding, and graceful timeout/escalation.

## Architecture

The implementation spans two main files:

| File | Role |
|------|------|
| `packages/core/src/tools/shell.ts` | Tool definition (`ShellTool` extends `BaseDeclarativeTool`) and invocation logic |
| `packages/core/src/services/shellExecutionService.ts` | Actual process spawning and management |

## Execution Mechanism

There are **two execution paths**, selected by the `shouldUseNodePty` config flag:

### Path 1: PTY-based (default on Unix / Windows 10+)

- Uses `node-pty` (`@lydell/node-pty` or `node-pty` fallback) to spawn a **real pseudo-terminal**
- Output is fed through a headless xterm.js terminal (`Terminal` from `@xterm/headless`) for proper ANSI rendering, color preservation, and terminal state
- Supports **interactive commands** like `vim`, `htop`, `git rebase -i`
- Throttled render (~100ms) prevents UI flooding during rapid output

### Path 2: `child_process.spawn` (fallback)

- Used when PTY is unavailable, disabled, or fails
- Simpler pipe-based stdout/stderr streaming
- `stdio: ['ignore', 'pipe', 'pipe']` — stdin is ignored, stdout/stderr are piped
- `detached: !isWindows` — on Unix, the child leads its own process group (enables `kill -- -PGID`)

**Shell auto-detection:**
- Unix: `bash -c <command>`
- Windows: Git Bash (`bash -c`), PowerShell (`-NoProfile -Command`), or cmd.exe (`/d /s /c`)

## stdin / stdout / stderr Handling

| Stream | PTY Path | child_process Path |
|--------|----------|-------------------|
| **stdin** | Ignored (PTY handles interactive input internally) | Ignored (`'ignore'`) |
| **stdout** | Merged with stderr naturally (as a real terminal would) | Piped, merged in code |
| **stderr** | Merged with stdout naturally | Piped, merged in code |

**Additional features:**
- **Binary detection:** Sniffs first 4096 bytes using `isBinary()`. If binary output is detected, streaming is halted with a "Binary output detected" message.
- **Auto-encoding:** Text encoding is auto-detected from the first chunk via `getCachedEncodingForBuffer()` (handles GBK, UTF-8, etc.)
- **Real-time streaming:** Both paths emit `ShellOutputEvent` objects for real-time UI updates:
  - `{ type: 'data', chunk: string | AnsiOutput }` — text or ANSI output
  - `{ type: 'binary_detected' }` — binary stream detected
  - `{ type: 'binary_progress', bytesReceived: number }` — binary receive progress

## Timeout & Cancellation

```typescript
// Default: 2 minutes for foreground, no timeout for background
const DEFAULT_FOREGROUND_TIMEOUT_MS = 120000; // 2 minutes
const effectiveTimeout = is_background
  ? undefined
  : (timeout ?? DEFAULT_FOREGROUND_TIMEOUT_MS);  // configurable up to 600000ms

// Uses AbortSignal for cancellation
const timeoutSignal = AbortSignal.timeout(effectiveTimeout);
const combinedSignal = AbortSignal.any([userCancelSignal, timeoutSignal]);
```

**Process termination on abort (SIGTERM → SIGKILL escalation):**

```typescript
// On Unix: kill entire process group
process.kill(-child.pid, 'SIGTERM');
await new Promise((res) => setTimeout(res, 200)); // SIGKILL_TIMEOUT_MS
if (!exited) {
  process.kill(-child.pid, 'SIGKILL');
}

// On Windows: taskkill /t (tree/recursive)
cpSpawn('taskkill', ['/pid', child.pid.toString(), '/f', '/t']);
```

The result distinguishes between user cancellation and timeout in the final message.

## Environment Variables

The shell execution service injects additional environment variables:

```typescript
{
  QWEN_CODE: '1',       // Signals to child processes that they run under Qwen Code
  TERM: 'xterm-256color', // Terminal type for ANSI/color support
  PAGER: 'cat',         // Disable pagers (e.g., for git, man)
}
```

Plus path normalization for Windows compatibility.

## Comparison with Python's `subprocess.call`

| Feature | Qwen Code `run_shell_command` | Python `subprocess.call` |
|---------|-------------------------------|--------------------------|
| **Execution** | PTY (real terminal emulation) or `child_process.spawn` | fork/exec, no terminal emulation |
| **stdin** | Always ignored | Inherits parent stdin by default |
| **stdout/stderr** | Merged + streamed in real-time to UI | Collected after process exits |
| **ANSI colors** | Preserved via xterm.js headless terminal | Raw bytes (no interpretation) |
| **Binary detection** | Auto-detects and halts on binary output | None |
| **Timeout** | Built-in (default 2 min), SIGTERM → SIGKILL escalation | No built-in timeout (need `subprocess.run(timeout=...)`) |
| **Background mode** | Native `is_background` param | Need `subprocess.Popen` (different API) |
| **Process groups** | `detached: true`, killed via `kill -- -PGID` | No automatic process group management |
| **Encoding** | Auto-detects from output bytes | System locale or explicit `encoding=` param |
| **Shell** | Auto-detects per platform (bash/cmd/PowerShell) | Requires `shell=True` |
| **API shape** | Declarative tool with schema invoked by AI agent | Imperative function called directly from code |
| **Security** | `QWEN_CODE=1` env var; permission manager; command restrictions via config | No built-in security; full shell injection risk with `shell=True` |
| **Cancellation** | AbortSignal-based; integrates with agent's cancellation | No built-in cancellation; must track Popen and kill manually |

## Tool Schema

The tool is defined with a declarative schema including these parameters:

- `command` (string, required) — The shell command to execute
- `is_background` (boolean, optional) — Run in background, return immediately with PID
- `timeout` (number, optional) — Timeout in milliseconds (max 600000 = 10 min)
- `description` (string, optional) — Human-readable description of what the command does
- `directory` (string, optional) — Working directory for the command

## Key Takeaways for Agent Design

1. **PTY emulation is superior for CLI tools** — it preserves colors, handles interactive commands, and merges stdout/stderr naturally
2. **AbortSignal is Node.js's native cancellation primitive** — combines timeout and user cancellation cleanly
3. **Graceful process killing matters** — SIGTERM first, wait, then SIGKILL prevents orphan processes
4. **Binary detection early** — prevents wasting resources on non-text output
5. **Detached process groups** — enables killing entire process trees, not just the shell
