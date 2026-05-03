---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.1
kernelspec:
  name: python3
  display_name: Python 3 (ipykernel)
  language: python
---

---
title: vim-ollama Plugin Setup
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: '2026-05-02'
description: Installation and configuration guide for the vim-ollama plugin, focusing
  on in-editor AI completion and refactoring.
tags:
- agents
- development
options:
  type: guide
  birth: '2026-01-01'
  version: 1.0.0
  token_size: 1808
---
# vim-ollama Plugin Setup

+++

:::{seealso}
See [Terminal AI Agents Workflow](/ai_agents/guides/terminal_ai_agents_workflow.ipynb) for the general hybrid strategy, workflow patterns, and when to use editor plugins vs CLI agents.
:::

+++

This guide covers the installation and configuration of the `gergap/vim-ollama` plugin, which provides in-editor AI functionality for code completion, refactoring, and general chat.

+++

## **1. Plugin Installation (using `vim-plug`)**

+++

Add the following to your `~/.vimrc`:

```vim
call plug#begin()
Plug 'gergap/vim-ollama'
" ... other plugins
call plug#end()
```

Run `:PlugInstall` within Vim to download and install the plugin.

After installation, run in VIM:

```
:Ollama setup
```

General settings like context lines or model selection should be placed in this dedicated file.

+++

## **2. Initial Plugin Settings**

+++

To prevent potential errors upon startup, define the `g:ollama_debug` variable, which handles the plugin's internal logging level, to any integer value.

**In `~/.vim/config/ollama.vim`:**

```vim
" Define and initialize the debug variable to prevent E121/E116 errors.
" Set to 0 to disable logging.
let g:ollama_debug = 0
```

> - E121: Undefined variable: g:ollama_debug, and
> - E116: Invalid arguments for function ollama#logger#PythonLogLevel(g:ollama_debug).

+++

## **3. Configure Key Mappings**

+++

This section covers core commands (Normal/Visual Mode) and suggestion handling (Insert Mode). Read the official documentation for advanced options: `:help vim-ollama-maps`.

+++

### Define a `<Leader>` key

+++

Define your leader key (if you haven't already, **`<Space>`** is recommended):

```vimrc
" --- Vim Core Configuration ---
let mapleader = " "        " Set Leader key to Spacebar
```

+++

### Custom Mappings for Chat, Review, and Edit (Normal and Visual Modes)

+++

We will **disable default mappings** to prevent conflicts, then define custom ones (you can choose one keys).

**In your `~/.vimrc`:**

```vimrc
" --- Ollama Plugin Configuration ---

" !! IMPORTANT !! Disable all default plugin mappings
" This prevents conflicts and ensures only your custom mappings are used.
let g:ollama_no_maps = 1

" Normal Mode
" Use for general chat
nnoremap <Leader>c :OllamaChat<CR>
" Toggle FIM completion on/off (Mapped to default key)
nnoremap <Leader>t :Ollama toggle<CR>

" Visual Mode
" Use for refactoring selected code (Mapped to default key)
vnoremap <Leader>e :OllamaEdit
" Use for reviewing selected code
vnoremap <Leader>or :OllamaReview
```

+++

### Suggestion Mappings (Insert Mode)

+++

**Freeing the `<Tab>` Key**

The default behavior is for **`<Tab>`** to accept the full suggestion.

If you **must** use `<Tab>` for indenting instead, you need to explicitly disable the plugin's mapping:

**Add this line to your `~/.vimrc`:**

```vimrc
" Do not map <Tab> to accept the entire completion
" This restores <Tab> to its default function.
let g:ollama_no_tab_map = v:true
```

**Setting New Custom Acceptance Mappings**

If you disabled `<Tab>`, or if you prefer simpler keys for line/word acceptance, use the following official `<Plug>` mappings shown in the documentation:

```vimrc
" Accept Full Block Control-A
inoremap <C-a> <Plug>(ollama-tab-completion)

" Accept Next Line Control-J
inoremap <C-j> <Plug>(ollama-insert-line)

" Accept Next Word Control-L
inoremap <C-l> <Plug>(ollama-insert-word)

" Dismiss the current suggestion (Mapped to default Control-])
inoremap <C-]> <Plug>(ollama-dismiss)
```

By using these official `<Plug>` mappings, you are calling the internal plugin functions directly, guaranteeing stability and avoiding the unreliable terminal transmission of `<M-Right>` or `<M-C-Right>`.

+++

:::{caution}
Don't run `llama.vim` and `vim-ollama` simultaneously if you enable FIM in both.

Both plugins aggressively intercept the same keystrokes and display logic for inline completion, leading to unpredictable behavior and resource conflicts. If you must use `llama.vim` for its optimized FIM, explicitly disable FIM completion within your `vim-ollama` configuration (`llama.vim` configuration is not covered in this handbook).
:::

+++

## **4. Workflow: In-Vim Refactoring**

+++

The typical vim-ollama workflow for single-file tasks:

1.  **Visual Select:** Use **`V`** or **`v`** to select the function block you want to change.
2.  **Execute Edit:** Press **`<Space>e`**.
3.  **Prompt:** A prompt appears. Type your instruction, e.g., `"Rewrite this function to use list comprehension for performance."` Press `<Enter>`.
4.  **Diff Review:** The plugin opens a split with the AI's proposed changes, allowing you to use `vimdiff` commands to accept or reject line-by-line.

For multi-file refactoring and git-aware commits, use a CLI agent like Aider instead.

:::{seealso}
> - [Terminal AI Agents Workflow](/ai_agents/guides/terminal_ai_agents_workflow.ipynb) — general hybrid strategy
> - [Aider Commands Handout](/ai_agents/guides/aider/aider_commands_handout.ipynb) — CLI agent reference
:::

+++

## **5. Troubleshooting: Python & Connection Errors**

+++

Common issues often stem from how Fedora/Linux handles Python virtual environments or how `localhost` resolves in the terminal.

+++

### **Issue: ModuleNotFoundError: No module named 'requests'**

+++

If you see this error in the Vim status line or logs, your virtual environment is either missing or "hollow" (missing internal management tools).

**The "Modern" Fix (using `uv`):**
The most reliable way to ensure a functional, isolated environment is using `uv`.
```bash
# 1. Remove the broken environment
rm -rf ~/.vim/venv/ollama

# 2. Create a fresh venv using uv
uv venv ~/.vim/venv/ollama

# 3. Install dependencies specifically into that path
uv pip install requests httpx jinja2 mistralai openai -p $HOME/.vim/venv/ollama
```

+++

### **Issue: Debugging and Logs**

+++

If the plugin is behaving unexpectedly, enable logging to see the raw communication between Vim and the Python helper scripts.

1. **Create the log directory:** `mkdir -p /tmp/logs`
2. **Enable logging in `~/.vim/config/ollama.vim`:**
   ```vim
   let g:ollama_debug = 4
   let g:ollama_logfile = '/tmp/logs/vim-ollama.log'
   ```
3. **Monitor the logs in a separate terminal:**
   ```bash
   tail -f /tmp/logs/vim-ollama.log
   ```
