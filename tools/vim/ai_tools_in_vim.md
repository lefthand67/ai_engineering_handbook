# VIM in AI era: Configure vim for AI-driven tasks.

---

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.2.1  
Birth: 17.11.2025  
Modified: 18.11.2025

---

The best way to set up Vim for the AI era is by adopting a hybrid strategy: use a **Vim plugin** for rapid, in-buffer tasks (like completion and single-file edits) and a **CLI tool** for agentic, multi-file refactoring that leverages the power and stability of the terminal.

This guide focuses on integrating **Ollama** as your local model host with the **`gergap/vim-ollama`** plugin and the **`Aider`** CLI tool.

# 1. Optimized AI Tooling Strategy

| Tool | Type | Core Function | Best For | VS Code Analog |
| :--- | :--- | :--- | :--- | :--- |
| `ggml-org/llama.vim` | Vim Plugin | **Dedicated FIM** (Fill-in-the-Middle) Completion. Highly optimized server connection. | **Lowest latency, fastest inline code completion.** Use when typing new code and maximizing speed is the only goal. | GitHub Copilot (Pure Completion) |
| `gergap/vim-ollama` | Vim Plugin | **Chat, Edit.** Interacts directly with the current buffer. | Single-file refactoring, opening chat buffers, and providing context for selected code. | GitHub Copilot / Inline Chat |
| `Aider` | CLI Agent | **Multi-file Refactoring & Committing.** Reads Git context and makes atomic changes. | Complex refactors, generating new files, fixing tests across the codebase. | Agentic AI (Continue/Cline) |

> > It is highly advised not to use `llama.vim` and `vim-ollama` simultaneously if you enable FIM in both. The reason is that both plugins aggressively try to intercept the same keystrokes and display logic for inline completion, leading to unpredictable behavior and resource conflicts. If you must use `llama.vim` for its optimized FIM, ensure you explicitly disable FIM completion within your `vim-ollama` configuration (`llama.vim` configuration is not covered in this handbook).

# 2. Setting Up the Foundation (Ollama and Aider)

## A. Install Ollama and Pull Models

1.  **Install Ollama:** Follow the official guide to install Ollama on your operating system and start the server.
2.  **Pull Models:** Pull high-quality, code-specific models.
    ```bash
    ollama pull qwen2.5-coder:3b   # fast enough for low-latency FIM/completion
    ollama pull qwen2.5-coder:14B  # better instruction following for complex editing and agentic tasks
    ollama pull gemma3n:e4b        # good for chat
    ```

## B. Install Aider

[Read documentation](https://aider.chat/docs/).

1.  **Install Aider:**
    ```bash
    # Use uv to install the Aider CLI tool
    uv tool install aider-chat
    ```

2.  **Configure Aider for Ollama:** Aider needs to know which local model to use. Run Aider from your terminal, specifying the Ollama model:
    ```bash
    # Navigate to your Git repository first
    cd /path/to/my/project

    # Run Aider, specifying a capable Ollama model
    aider --model ollama_chat/qwen2.5-coder:14B
    ```
    This will launch the Aider chat interface, allowing you to ask it to change files in the current repository. When Aider makes changes, Vim will detect the file modification and prompt you to reload the buffer.
    
    > You can also run aider in an experimental web browser form: 
    ```bash
    # install aider for browser
    uv tool install aider-chat[browser]
    
    # launch aider
    aider --gui --model ollama_chat/qwen2.5-coder:14B
    ```

# 3. Configuring `gergap/vim-ollama`

This plugin provides the essential in-editor AI functionality.

## A. Plugin Installation (using `vim-plug`)

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

This command creates the dedicated configuration file at `~/.vim/config/ollama.vim`. All additional configurations (like, lines of context, or if you want to change the models) should be placed in this file, not in your main `~/.vimrc`.

## B. Essential Configuration and Key Mappings

Read: `:help vim-ollama-maps`.

Define your leader key (if you haven't already, **`<Space>`** is recommended) and the model settings in your `~/.vimrc` (you can pick your own keys):

```vimrc
" --- Vim Core Configuration ---
set clipboard=unnamedplus  " Use system clipboard for yanks/deletes (like VSCodeVim)
let mapleader = " "        " Set Leader key to Spacebar

" --- Ollama Plugin Configuration ---

" Map the key commands
" NNNNNormal Mode: Use for general chat
nnoremap <Leader>oc :OllamaChat<CR>

" Toggle FIM completion on/off
nnoremap <Leader>ot :Ollama toggle<CR>
" VVVVVVisual Mode: Use for refactoring selected code
vnoremap <Leader>oe :<C-u>OllamaEdit
```

## C. Acceptance Mappings

### Freeing the `<Tab>` Key

You must use the variable **`g:ollama_no_tab_map`** to explicitly stop the plugin from hijacking the `<Tab>` key.

Add this line to your **`~/.vimrc`**:

```vimrc
" Do not map tab to accept entire completion
" This helps to use Tab as your regular key
let g:ollama_no_tab_map=v:true
```

The documentation states: "If this variable is defined, the default `<tab>` mapping will not be created." By setting it to `v:true`, you bypass the intrusive, hidden mapping that caused the conflicts.

After adding this line and **restarting Vim**, your `<Tab>` key will be restored to its default function (inserting an indent character).

### Setting New Custom Acceptance Mappings

Now that `<Tab>` is free, you can define clear, non-conflicting mappings for the specific acceptance functions you need, using the official `<Plug>` mappings shown in the documentation.

Use the following lines in your `~/.vimrc` to map the functions to easy-to-press keys in **Insert Mode**:

| Action | New Key | `~/.vimrc` Mapping | Purpose |
| :--- | :--- | :--- | :--- |
| **Accept Full Block** | **`<C-y>`** (Control-Y) | `inoremap <C-y> <Plug>(ollama-tab-completion)` | Accepts the entire suggested code block. |
| **Accept Next Line** | **`<C-j>`** (Control-J) | `inoremap <C-j> <Plug>(ollama-insert-line)` | **Line-by-line acceptance.** (The function previously on `<M-Right>`) |
| **Accept Next Word** | **`<C-l>`** (Control-L) | `inoremap <C-l> <Plug>(ollama-insert-word)` | Word-by-word acceptance. (The function previously on `<M-C-Right>`) |

**Recommended Mappings to Add:**

```vimrc
" 1. Accept Full Block Control-Y
inoremap <C-y> <Plug>(ollama-tab-completion)
" 2. Accept Next Line Control-J
inoremap <C-j> <Plug>(ollama-insert-line)
" 3. Accept Next Word Control-L
inoremap <C-l> <Plug>(ollama-insert-word)
```

By using these official `<Plug>` mappings, you are calling the internal plugin functions directly, guaranteeing stability and avoiding the unreliable terminal transmission of `<M-Right>` or `<M-C-Right>`.

# 4. Workflow and Usage

The key to the Vim AI workflow is knowing when to use the plugin and when to use the CLI tool:

## A. In-Vim Task (Plugin): Refactoring a Function

1.  **Visual Select:** Use **`V`** or **`v`** to select the function block you want to change.
2.  **Execute Edit:** Press **`<Space>oe`**.
3.  **Prompt:** A prompt appears. Type your instruction, e.g., `"Rewrite this function to use list comprehension for performance."`
4.  **Diff Review:** The plugin opens a split with the AI's proposed changes, allowing you to use `vimdiff` commands to accept or reject line-by-line.

## B. Terminal Task (Aider): Multi-File Feature Implementation

1.  **Open Terminal:** Use a terminal split in Vim or switch to a terminal (e.g., in tmux/Konsole).
2.  **Run Aider:** Start the agent: `aider --model ollama_chat/qwen2.5-coder:3b`.
3.  **Add Files to Context:** Tell Aider what to work on: `/add main.py utils.py tests/test_utils.py`
4.  **Prompt:** Give a high-level instruction: `Implement caching in utils.py and update main.py to use it. Also, write a new test case in test_utils.py.`
5.  **Vim Reload:** Aider modifies the files on disk. Vim detects the change and prompts you to **reload** the buffers. You approve, and the changes appear instantly.

This hybrid approach gives you the **stability and speed of native Vim** and the **agentic power of modern AI tools**.
