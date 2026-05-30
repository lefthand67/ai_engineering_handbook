---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.1
kernelspec:
  display_name: Bash
  language: bash
  name: bash
---

---
title: Aider Commands Handout
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: '2026-05-02'
description: Quick reference guide for Aider CLI commands, configuration, and usage
  patterns.
tags:
- agents
- development
options:
  type: guide
  birth: '2025-11-18'
  version: 0.2.1
  token_size: 1528
---
# Aider Commands Handout

Aider is an AI pair programmer that uses your code as context.
:::{seealso} How to set up aider
> [Terminal AI Agents Workflow](/ai_agents/guides/terminal_ai_agents_workflow.ipynb) (to be created — general hybrid strategy and Ollama setup)

+++

## **1. Installation and Setup**

+++

command|description
-|-
**Installation**|
`uv tool install aider-chat`|install aider with uv (faster)
`pipx install aider-chat`|install aider with pipx (traditional way)
`uv tool install aider-chat[browser]`|install browser extension (experimental feature)
`aider -h`|show help message and exit
`aider --version`|Show the version number and exit
**Configuration files**|
`/path/to/project/.aider.conf.yml`|poject level file
`$HOME/.aider.conf.yml`|user level file
`-c /path/to/.aider.conf.yml`|specific file, i.e. project level
**Essential Configuration Flags**|
`--model MODEL`|Specify the LLM to use
`--light-mode`|Use colors suitable for a light terminal background (default: False), env var: `AIDER_LIGHT_MODE`
`--auto-commits`, `--no-auto-commits`|Enable/disable auto commit of LLM changes (default: True) env var: `AIDER_AUTO_COMMITS`

Args that start with `--` can be set in a config file. The config file uses YAML syntax and must represent a YAML 'mapping' (for details, see http://learn.getgrav.org/advanced/yaml). 

:::{important} **Precedence**
In general, command-line values override environment variables which override config file values which override defaults.
:::

+++

## **2. Using proxy**

+++

If your organization requires all external traffic to be routed through the proxy, you can set these environment variables and pass them to the terminal session before starting the aider:

```bash
export HTTPS_PROXY="http://[user:password]@proxy_ip_address:port"
export https_proxy="http://[user:password]@proxy_ip_address:port"
```

You should NOT set `HTTP_PROXY` variable because it breaks the connection between the aider and local ollama through `http://127.0.0.1:11434`.

You can wrap this configuration into a script wrapper `aider_proxy.sh`:

```bash
#!/bin/bash
set -euo pipefail


main() {

    export HTTPS_PROXY="http://[user:password]@proxy_ip_address:port"
    export https_proxy="http://[user:password]@proxy_ip_address:port"

    exec aider "$@"
}


main "$@"
```

Make this script executable and add it to your PATH. Now you can run aider simply:

```bash
$ aider_proxy.sh --model gemini/gemini-3-flash
```

Avoid using proxy if it's not necessary for it adds complexity to the aider configuration.

+++

## **3. Running & Basic Usage**

+++

### Launching aider

+++

command|description
-|-
`aider --model ollama_chat/<model_name>`|run a local model in terminal (get name from `ollama ls`)
`--gui`, `--no-gui`, `--browser`, `--no-browser`|Run aider in your browser (default: False); env var: `AIDER_GUI`
`aider --list-models gemini/`| list available models

+++

(aider-conf-yaml)=
### Core File Management

+++

| Command | Description |
| :--- | :--- |
`--file FILE`|specify a file to edit (can be used multiple times); env var: `AIDER_FILE`
`--read FILE`|specify a read-only file (can be used multiple times); env var: `AIDER_READ`
`/add`|Add files to the chat so aider can edit them or review them in detail.
`/tokens`|Report on the number of tokens used by the current chat context

:::{tip}
Use `/add` to tell Aider a file exists and is available for modification. This way aider knows this file exists and **will write to it**. Otherwise, aider might write the changes to an existing file; [source](https://aider.chat/docs/usage/tips.html)
:::

+++

### Using the Repository Map

+++

command|description
| :--- | :--- |
| `--map-tokens NUM` | **Limit the size** of the Repository Map in tokens (e.g., `aider --map-tokens 500`). |
| `/map` | **Display** the current Repository Map summary. |

The **Repository Map** provides a structural overview (file/function) of your project, helping the AI understand context without loading the entire codebase, thus saving tokens. Use `--map-tokens` to manage this resource (default is 1024 tokens).

+++

### In-Chat Commands

+++

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

+++

## **4. Upgrading**

+++

command|description
| :--- | :--- |
`uv tool --upgrade aider-chat aider-chat[browser]`||
`aider --install-main-branch`|Install the latest version from the main branch; env var: `AIDER_INSTALL_MAIN_BRANCH`. Use for beta features only.
`aider --upgrade, --update`|Upgrade aider to the latest version from PyPI; env var: `AIDER_UPGRADE`
