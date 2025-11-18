# VIM in AI era: Configure vim for AI-driven tasks.

---

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.3.0  
Birth: 17.11.2025  
Modified: 19.11.2025

---

The best way to set up Vim for the AI era is by adopting a hybrid strategy: use a **Vim plugin** for rapid, in-buffer tasks (like completion and single-file edits) and a **CLI tool** for agentic, multi-file refactoring that leverages the power and stability of the terminal.

This guide focuses on integrating **Ollama** as your local model host with the **`gergap/vim-ollama`** plugin and the **`Aider`** CLI tool.

## 1. Optimized AI Tooling Strategy

| Tool | Type | Core Function | Best For | VS Code Analog |
| :--- | :--- | :--- | :--- | :--- |
| `ggml-org/llama.vim` | Vim Plugin | **Dedicated FIM** (Fill-in-the-Middle) Completion. Highly optimized server connection. | **Lowest latency, fastest inline code completion.** Use when typing new code and maximizing speed is the only goal. | GitHub Copilot (Pure Completion) |
| `gergap/vim-ollama` | Vim Plugin | **Chat, Edit.** Interacts directly with the current buffer. | Single-file refactoring, opening chat buffers, and providing context for selected code. | GitHub Copilot / Inline Chat |
| `Aider` | CLI Agent | **Multi-file Refactoring & Committing.** Reads Git context and makes atomic changes. | Complex refactors, generating new files, fixing tests across the codebase. | Agentic AI (Continue/Cline) |

> It is highly advised not to use `llama.vim` and `vim-ollama` simultaneously if you enable FIM in both. The reason is that both plugins aggressively try to intercept the same keystrokes and display logic for inline completion, leading to unpredictable behavior and resource conflicts. If you must use `llama.vim` for its optimized FIM, ensure you explicitly disable FIM completion within your `vim-ollama` configuration (`llama.vim` configuration is not covered in this handbook).

## 2. Setting Up the Foundation: Ollama

Install ollama and pull models:

1.  **Install Ollama:** Follow the official guide to install Ollama on your operating system and start the server.
2.  **Pull Models:** Pull high-quality, code-specific models.
    ```bash
    ollama pull qwen2.5-coder:3b   # fast enough for low-latency FIM/completion
    ollama pull qwen2.5-coder:14B  # better instruction following for complex editing and agentic tasks
    ollama pull gemma3n:e4b        # good for chat
    ```

## 3. Setting Up Aider

Now let's configure the CLI agent. [Read documentation](https://aider.chat/docs/) for more details.

1.  **Install Aider:**
    ```bash
    # Use uv to install the Aider CLI tool
    uv tool install aider-chat
    ```
    
    or more traditional way:
    ```bash
    pipx install aider-chat
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
    > ```bash
    > # install aider for browser
    > uv tool install aider-chat[browser]
    > 
    > # launch aider
    > aider --gui --model ollama_chat/qwen2.5-coder:14B
    > ```

## 4. Configuring `gergap/vim-ollama`

This plugin provides the essential in-editor AI functionality for code completion, refactoring, and general chat.

### 4.1 Plugin Installation (using `vim-plug`)

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

### 4.2 Initial Plugin Settings

To prevent potential errors upon startup, define the `g:ollama_debug` variable, which handles the plugin's internal logging level, to any integer value.

**In `~/.vim/config/ollama.vim`:**

```vim
" Define and initialize the debug variable to prevent E121/E116 errors.
" Set to 0 to disable logging.
let g:ollama_debug = 0
```

> - E121: Undefined variable: g:ollama_debug, and 
> - E116: Invalid arguments for function ollama#logger#PythonLogLevel(g:ollama_debug).

### 4.3 Configure Key Mappings

This section covers core commands (Normal/Visual Mode) and suggestion handling (Insert Mode). Read the official documentation for advanced options: `:help vim-ollama-maps`.

#### Define a `<Leader>` key

Define your leader key (if you haven't already, **`<Space>`** is recommended):

```vimrc
" --- Vim Core Configuration ---
let mapleader = " "        " Set Leader key to Spacebar
```

#### Custom Mappings for Chat, Review, and Edit (Normal and Visual Modes)

We will **disable default mappings** to prevent conflicts, then define custom ones (you can choose one keys).

**In your `~/.vimrc`:**

```vimrc
" --- Ollama Plugin Configuration ---

" !! IMPORTANT !! Disable all default plugin mappings
" This prevents conflicts and ensures only your custom mappings are used.
let g:ollama_no_maps = 1

" NNNNNormal Mode
" Use for general chat
nnoremap <Leader>c :OllamaChat<CR>
" Toggle FIM completion on/off (Mapped to default key)
nnoremap <Leader>t :Ollama toggle<CR>

" VVVVVVisual Mode
" Use for refactoring selected code (Mapped to default key)
vnoremap <Leader>e :<C-u>OllamaEdit
" Use for reviewing selected code
vnoremap <Leader>or :<C-u>OllamaReview
```

#### Suggestion Mappings (Insert Mode)

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

## 5. Workflow and Usage

The key to the Vim AI workflow is knowing when to use the plugin and when to use the CLI tool:

### 5.1 In-Vim Task (Plugin): Refactoring a Function

1.  **Visual Select:** Use **`V`** or **`v`** to select the function block you want to change.
2.  **Execute Edit:** Press **`<Space>oe`**.
3.  **Prompt:** A prompt appears. Type your instruction, e.g., `"Rewrite this function to use list comprehension for performance."`
4.  **Diff Review:** The plugin opens a split with the AI's proposed changes, allowing you to use `vimdiff` commands to accept or reject line-by-line.

## 5.2 Terminal Task (Aider): Multi-File Feature Implementation

1.  **Open Terminal:** Use a terminal split in Vim or switch to a terminal (e.g., in tmux/Konsole).
2.  **Run Aider:** Start the agent: `aider --model ollama_chat/qwen2.5-coder:3b`.
3.  **Add Files to Context:** Tell Aider what to work on: `/add main.py utils.py tests/test_utils.py`
4.  **Prompt:** Give a high-level instruction: `Implement caching in utils.py and update main.py to use it. Also, write a new test case in test_utils.py.`
5.  **Vim Reload:** Aider modifies the files on disk. Vim detects the change and prompts you to **reload** the buffers. You approve, and the changes appear instantly.

This hybrid approach gives you the **stability and speed of native Vim** and the **agentic power of modern AI tools**.
