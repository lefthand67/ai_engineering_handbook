# Aider Commands Handout

---

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.1.1  
Birth: 18.11.2025  
Modified: 18.11.2025

---

Aider is an AI pair programmer that uses your code as context. 

## Installation and Setup

command|description
-|-
`uv tool install aider-chat`|install aider with uv (faster)
`pipx install aider-chat`|install aider with pipx (traditional way)
`uv tool install aider-chat[browser]`|install browser extension (experimental feature)
`aider -h`|show help message and exit
`aider --version`|Show the version number and exit

## Configuration

### Configuration File Locations

command|description
-|-
`/path/to/project/.aider.conf.yml`|poject level file
`$HOME/.aider.conf.yml`|user level file
`-c /path/to/.aider.conf.yml`|specific file

Args that start with `--` can be set in a config file. The config file uses YAML syntax and must represent a YAML 'mapping' (for details, see http://learn.getgrav.org/advanced/yaml). 

**Precedence**: In general, command-line values override environment variables which override config file values which override defaults.

### Essential Configuration Flags

command|description
-|-
`--model MODEL`|Specify the LLM to use
`--light-mode`|Use colors suitable for a light terminal background (default: False), env var: `AIDER_LIGHT_MODE`
`--auto-commits`, `--no-auto-commits`|Enable/disable auto commit of LLM changes (default: True) env var: `AIDER_AUTO_COMMITS`

## Running & Basic Usage

### Launching aider

command|description
-|-
`aider --model ollama_chat/<model_name>`|run a local model in terminal (get name from `ollama ls`)
`--gui`, `--no-gui`, `--browser`, `--no-browser`|Run aider in your browser (default: False); env var: `AIDER_GUI`

### Core File Management

| Command | Description |
| :--- | :--- |
`--file FILE`|specify a file to edit (can be used multiple times); env var: `AIDER_FILE`
`--read FILE`|specify a read-only file (can be used multiple times); env var: `AIDER_READ`
`/add`|Add files to the chat so aider can edit them or review them in detail.
`/tokens`|Report on the number of tokens used by the current chat context

> 💡 **Tip:** Use `/add` to tell Aider a file exists and is available for modification. This way aider knows this file exists and **will write to it**. Otherwise, aider might write the changes to an existing file; [source](https://aider.chat/docs/usage/tips.html)

### Using the Repository Map

command|description
| :--- | :--- |
| `--map-tokens NUM` | **Limit the size** of the Repository Map in tokens (e.g., `aider --map-tokens 500`). |
| `/map` | **Display** the current Repository Map summary. |

The **Repository Map** provides a structural overview (file/function) of your project, helping the AI understand context without loading the entire codebase, thus saving tokens. Use `--map-tokens` to manage this resource (default is 1024 tokens).

## In-Chat Commands

command|description
| :--- | :--- |
| `/help` | Ask questions about Aider's features and usage. Aider's help is context-aware, i.e. it can answer questions about itself.|
| `/clear` | **Clear the chat history** (saves tokens). |
| `/run COMMAND` | Run an **arbitrary shell command** and share the output with the LLM. |
| `/undo` | **Undo the last Git commit** (only works for Aider's auto-commits). |
| `/web URL` | **Scrape a webpage**, convert to markdown and send in a message. |
| `/diff` | Show the **difference** between the current files and the last Aider commit. |
| `/commit MESSAGE` | Manually commit the current changes with a specific message. |
| `/exit` or `/quit` | Exit Aider. |

## Upgrading
command|description
| :--- | :--- |
`aider --install-main-branch`|Install the latest version from the main branch; env var: `AIDER_INSTALL_MAIN_BRANCH`. Use for beta features only.
`aider --upgrade, --update`|Upgrade aider to the latest version from PyPI; env var: `AIDER_UPGRADE`
