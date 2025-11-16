# VIM in AI era: Configure vim for AI-driven tasks.

---

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.1.0  
Birth: 17.11.2025  
Modified: 17.11.2025

---

The best way to set up Vim for the AI era is by adopting a hybrid strategy: use a **Vim plugin** for rapid, in-buffer tasks (like completion and single-file edits) and a **CLI tool** for agentic, multi-file refactoring that leverages the power and stability of the terminal.

This guide focuses on integrating **Ollama** as your local model host with the **`gergap/vim-ollama`** plugin and the **`Aider`** CLI tool.

# 1. AI Tool Comparison: CLI vs. Plugin

| Tool | Type | Core Function | Best For | VS Code Analog |
| :--- | :--- | :--- | :--- | :--- |
| **`gergap/vim-ollama`** | Vim Plugin | **FIM, Chat, Edit.** Interacts directly with the current buffer. | Single-file refactoring, inline completion, quickly asking questions about the current file. | GitHub Copilot / Inline Chat |
| **`Aider`** | CLI Agent | **Multi-file Refactoring & Committing.** Reads Git context and makes atomic changes. | Complex refactors, generating new files, fixing tests across the codebase. | Agentic AI (Continue/Cline) |

# 2. Setting Up the Foundation (Ollama and Aider)

## A. Install Ollama and Pull Models

1.  **Install Ollama:** Follow the official guide to install Ollama on your operating system and start the server.
2.  **Pull Models:** Pull high-quality, code-specific models.
    ```bash
    ollama pull starcoder2:3b   # Good for quick FIM completion
    ollama pull qwen2.5-coder:3b # Good for single-file editing
    ollama pull llama3.1:8b      # Good for chat/reasoning
    ```

## B. Install Aider

Aider is installed using Python's package manager, `pip`. It's best to install it in a dedicated virtual environment.

1.  **Install Aider:**
    ```bash
    # Use pip to install the Aider CLI tool
    python -m pip install aider-chat
    ```
2.  **Configure Aider for Ollama:** Aider needs to know which local model to use. Run Aider from your terminal, specifying the Ollama model:
    ```bash
    # Navigate to your Git repository first
    cd /path/to/my/project

    # Run Aider, specifying a capable Ollama model
    aider --model ollama_chat/qwen2.5-coder:3b
    ```
    This will launch the Aider chat interface, allowing you to ask it to change files in the current repository. When Aider makes changes, Vim will detect the file modification and prompt you to reload the buffer.

# 3. Configuring `gergap/vim-ollama`

> The section verified.

This plugin provides the essential in-editor AI functionality.

## A. Plugin Installation (using `vim-plug`)

Add the following to your `~/.vimrc`:

```vim
call plug#begin()
Plug 'gergap/vim-ollama'
" ... other plugins
call plug#end()
```

Run `:PlugInstall` within Vim to download the plugin.

## B. Essential Configuration and Key Mappings

Read: `:help vim-ollama-maps`.

Define your leader key (if you haven't already, **`<Space>`** is recommended) and the model settings in your `~/.vimrc`:

```vim
" --- Vim Core Configuration ---
set clipboard+=unnamedplus " Use system clipboard for yanks/deletes (like VSCodeVim)
let mapleader = " "        " Set Leader key to Spacebar

" --- Ollama Plugin Configuration ---
" Assign different models based on their task strength
let g:ollama_model = 'starcoder2:3b'   " FIM completion model (fast)
let g:ollama_edit_model = 'qwen2.5-coder:3b'  " Code editing model
let g:ollama_chat_model = 'llama3.1:8b'  " General chat/Q&A model

" Map the key commands
" NNNNNormal Mode: Use for general chat
nnoremap <Leader>oc :OllamaChat<CR>

" VVVVVVisual Mode: Use for refactoring selected code
vnoremap <Leader>oe :OllamaEdit<CR>

" Toggle FIM completion on/off (you can pick your own key)
nnoremap <Leader>ot :<C-u>OllamaToggle
```

## C. Acceptance Mappings

### Freeing the `<Tab>` Key

You must use the variable **`g:ollama_no_tab_map`** to explicitly stop the plugin from hijacking the `<Tab>` key.

Add this line to your **`~/.vimrc`**:

```vim
" Explicitly tell vim-ollama not to create the default <Tab> mapping.
let g:ollama_no_tab_map = v:true
```

The documentation states: "If this variable is defined, the default `<tab>` mapping will not be created." By setting it to `v:true`, you bypass the intrusive, hidden mapping that caused the conflicts.

After adding this line and **restarting Vim**, your `<Tab>` key will be restored to its default function (inserting an indent character), and the `E31: No such mapping` error will be resolved.

### Setting New Custom Acceptance Mappings

Now that `<Tab>` is free, you can define clear, non-conflicting mappings for the specific acceptance functions you need, using the official `<Plug>` mappings shown in the documentation.

Use the following lines in your **`~/.vimrc`** to map the functions to easy-to-press keys in **Insert Mode**:

| Action | New Key | `~/.vimrc` Mapping | Purpose |
| :--- | :--- | :--- | :--- |
| **Accept Full Block** | **`<C-y>`** (Control-Y) | `inoremap <C-y> <Plug>(ollama-tab-completion)` | Accepts the entire suggested code block. |
| **Accept Next Line** | **`<C-j>`** (Control-J) | `inoremap <C-j> <Plug>(ollama-insert-line)` | **Line-by-line acceptance.** (The function previously on `<M-Right>`) |
| **Accept Next Word** | **`<C-l>`** (Control-L) | `inoremap <C-l> <Plug>(ollama-insert-word)` | Word-by-word acceptance. (The function previously on `<M-C-Right>`) |

**Recommended Mappings to Add:**

```vim
" --- New, Non-Conflicting AI Completion Mappings ---

" 1. Full Acceptance (using standard Vim <C-y> key for acceptance)
inoremap <C-y> <Plug>(ollama-tab-completion)

" 2. Line-by-Line Acceptance (using Control-J)
inoremap <C-j> <Plug>(ollama-insert-line)

" 3. Word-by-Word Acceptance (using Control-L)
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

If you'd like to see Aider in action, this video provides a great overview of how it works as a coding assistant. [Aider vs. Cline vs. Continue: The Ultimate Coding Assistant for Developers?](https://www.youtube.com/watch?v=wFWoSvLijSE)

http://googleusercontent.com/youtube_content/2














































