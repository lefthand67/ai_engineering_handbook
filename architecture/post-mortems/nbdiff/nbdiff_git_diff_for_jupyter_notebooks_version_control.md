---
title: "nbdiff: 'git diff' for Jupyter Notebooks Version Control"
authors:
  - name: Vadim Rudakov
    email: rudakow.wadim@gmail.com
date: "2026-05-13"
description: "Guide on using nbdime and nbdiff to manage and review Jupyter Notebook changes while filtering JSON noise."
tags: [development, documentation, architecture]
---
---
options:
  type: guide
  version: 0.3.1
  birth: '2025-12-28'
  token_size: 2425
---
# nbdiff: "git diff" for Jupyter Notebooks Version Control


Owner: Vadim Rudakov, lefthand67@gmail.com
Version: 0.3.1
Birth: 2025-12-28
Last Modified: 2025-12-31
options:
  token_size: 2275
---
This guide explains how to use `nbdime` (specifically `nbdiff`) to manage Jupyter Notebooks effectively. Standard git diffs are notoriously difficult to read because notebooks are stored as dense JSON files containing metadata, cell IDs, and execution counts that obscure actual logic changes.

## 1. What is `nbdiff` and Why We Use It

Jupyter Notebooks (.ipynb) are JSON documents. When you change a single line of code or simply re-run a cell, a standard `git diff` shows a mess of structural changes.

We use `nbdiff` because it is **content-aware**. It understands the notebook structure and filters out the "noise" to show you only what matters:

* **Markdown Changes:** Clear text diffs of documentation and rendered math.
* **Code Changes:** Logical changes to Python inputs, ignoring the JSON wrapper.
* **Ignore Metadata:** It can ignore execution counts so you don't see diffs just because you clicked "Run."

**The Strategy: "Keep the Data, Filter the View"**

We treat `.ipynb` files as **Flat Files**. Unlike standard software engineering where we strip all "artifacts," in research, the **outputs are the evidence**.

We store the full notebook (metadata and plots) in Git, but we use `nbdiff` externally to avoid being blinded by JSON noise during manual reviews or when prompting AI tools like **Aider**.

## 2. Installation with `uv`

We use `uv` for fast, reliable Python tool management. To install the `nbdime` suite (which includes `nbdiff`) as a globally accessible tool:

```bash
uv tool install nbdime
```

This installs the following CLI tools:

* `nbdiff`: Terminal-based notebook comparison.
* `nbdiff-web`: Opens a side-by-side visual diff in your browser (best for Math/LaTeX).
* `nbmerge`: Tools for resolving notebook merge conflicts.

## 3. How to Use `nbdiff`

### Common CLI Commands

| Command | Description |
| --- | --- |
| `nbdiff HEAD path/to/notebook.ipynb` | Compare current changes to the last commit. |
| `nbdiff 351b33e HEAD -- path/to/nb.ipynb` | Compare two specific commits. |
| `nbdiff-web 351b33e HEAD -- path/to/nb.ipynb` | View changes in a rich browser UI (Highly Recommended). |

### Integrating with `aider`

`aider` is a pair-programming tool that works best when it can see clean diffs.  To help the AI write meaningful commit messages or understand your logic, feed it a "clean" text stream:

1. **Check the diff:** If you want the AI to review your work, run:

```bash
/run nbdiff --ignore-metadata HEAD path/to/notebook.ipynb
```
 or even cleaner:

```bash
# Within aider, use /run to provide context
/run nbdiff --ignore-metadata --ignore-outputs HEAD path/to/notebook.ipynb
```

**Why?** This tells the AI: "Ignore the 5,000 lines of base64 image data and focus on the 5 lines of Python code I changed."

2. **Targeted Edits:** If Aider struggles to find a cell, use `nbdiff-web` to find the **Cell Index** and prompt:

> *"In cell index 14, please update the LaTeX formula to include the bias term ."*

## 4. Advanced Setup: "Documentation-First" Aliases

If you are working on a research paper or documentation, you likely want to hide all code execution noise (output blobs and run counts) to focus on the text and logic.

### Create a "Clean" Alias

Add a "clean" version of nbdiff to your `~/.bashrc` :

```bash
# Add the alias
echo 'alias nbclean="nbdiff --ignore-metadata --ignore-outputs"' >> ~/.bashrc
# Refresh your shell
source ~/.bashrc
```

Now, running `nbclean` will hide all image data and execution numbers, showing only the code and markdown changes.

**When to use `nbclean`:**

1. **Before Committing:** Run `nbclean HEAD` to ensure you didn't leave a "print(x)" or a temporary debug variable in your code.
2. **Aider Context:** Use it to copy-paste clean code diffs into your chat if `/run` is unavailable.

:::{caution} Be aware!
:class: dropdown
:open: false
Sometimes the output *is* the point of the commit (e.g., a final loss curve or a summary table). If you ignore outputs during the diff, you might miss that a code change broke the resulting data.

Also, if you ignore metadata during a merge, you might accidentally overwrite important kernel specifications required to run the notebook on another machine.
:::

:::{hint} Pro-Tip
Selective Clearing > If you have a specific cell that generates a massive amount of text (like a long training log), clear the output of just that cell in Jupyter before saving/committing. This keeps your "Flat File" lean without losing the important summary plots in other cells.
:::

## 5. Comparison of Workflows

| Method | Best for... | Why? |
| --- | --- | --- |
| **`git diff`** | **Data Integrity** | Shows the "Truth." Confirms if binary data/metadata was actually changed. |
| **`nbdiff`** | **Manual Review** | Shows the "Logic." Filters out execution counts so you can read the code. |
| **`nbdiff-web`** | **Visual Audit** | Shows the "Result." Best for checking if a LaTeX formula or Plot changed. |
| **`nbclean`** | **AI / Aider** | Provides "Pure Context." Strips everything but code for the LLM. |

## Summary Reference

| Task | Command |
| --- | --- |
| **Install** | `uv tool install nbdime` |
| **List configuration** | `nbdime --config` |
| **Simple Diff** | `nbdiff old.ipynb new.ipynb` |
| **Visual/Web Diff** | `nbdiff-web <hash> HEAD <file>` |
| **Ignore Noise** | `nbdiff --ignore-metadata --ignore-outputs` |
| **Git Integration** | `nbdime config-git --enable` |

## Appendix A. If you want Git integration

### 1. Configuration: Native Git Integration

Instead of running a separate command, you can configure Git to use `nbdiff` automatically whenever you run `git diff` on a `.ipynb` file.

**To enable global Git integration:**

```bash
nbdime config-git --enable --global
```

Now, a standard `git diff` will output a clean, readable notebook summary instead of raw JSON.

You can always see the nbdime configuration like this:

```bash
nbdime --config
```

> [!NOTE]
> This configuration effectively makes `git diff` behave like your `nbclean` alias by default.

### 2. Configure "No-Noise" Git Defaults

To ensure your Git history remains clean and your diffs focus only on code changes, configure `nbdime` to ignore noise globally.

Run these commands to tell the Git driver to skip metadata and outputs:

```bash
git config --global diff.jupyternotebook.command "git-nbdiffdriver diff --ignore-metadata --ignore-outputs"
```

To verify your settings are active, run:

```bash
nbdime --config
```

> [!NOTE]
> This configuration effectively makes `git diff` behave like your `nbclean` alias by default.

### Why it is not a good idea to use ignore flags for daily work

While integrating `--ignore-metadata` and `--ignore-outputs` into your global Git configuration significantly cleans up your workflow, there are several "blind spots" and technical risks you should include in your handbook.

#### 1. The "False Clean" Security Risk

When you ignore metadata/outputs in `git diff`, you are only changing what you **see** in the terminal or browser. You are **not** cleaning the file itself.

* **The Problem:** You might run a `git diff`, see "No changes," and assume the file is clean. However, the file may still contain 50MB of binary plots or sensitive data in the outputs.
* **The Result:** You accidentally push massive files or private data to GitHub because your "glasses" (the diff tool) were programmed to ignore them.

#### 2. Loss of "Result Provenance"

In many data science contexts, the **output is the evidence**.

* **The Problem:** If a colleague changes a hyperparameter and the accuracy drops, an "ignore-outputs" diff will only show the code change. It won't show the resulting drop in the metric or the broken visualization.
* **The Risk:** You might approve a Pull Request that technically "works" but produces incorrect or degraded results because you suppressed the output diff.

#### 3. Merge Conflict "Shadows"

Merging is more dangerous than diffing with these flags.

* **The Problem:** If two people change the kernel metadata (e.g., one uses Python 3.9 and another 3.10), Git will flag a conflict.
* **The Risk:** Since your diff tool ignores these fields, `git diff` might show "No differences," but the repository is locked. You'll be stuck in a "phantom conflict" where your tools say everything is fine, but the repository is locked.

#### 4. Broken Interactive Workflows (`git add -p`)

If you use interactive staging (`git add -p` or `git add -e`), Git expects a "dumb" line-by-line diff.

* **The Problem:** External drivers like `git-nbdiffdriver` often struggle with Git's interactive patch mode.
* **The Result:** You may find that you can no longer stage specific "hunks" of a notebook; it becomes an "all or nothing" commit.

:::{important}
Use the alias `nbclean` for daily work, but not to make it the global mandatory driver unless you also use a pre-commit hook like `nbstripout`. Combining them ensures that what you see (clean code) matches what you store (clean files).
:::
