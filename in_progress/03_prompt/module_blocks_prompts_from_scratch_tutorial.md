# Creating Modular Prompts from Scratch

-----

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.1.0  
Birth: 2025-11-23  
Modified: 2025-12-05

-----

Architecture and guidelines are necessary, but without hands on the keyboard, everything will quickly be forgotten. Let's imagine that we are creating a new code project, only instead of Python functions, we will have **modular prompts**.

> Attention\! This guide is not an industry standard and does not comply with our organization's standards. But it contributes to a quick immersion into the topic of creating modular prompts, and at the initial stages, it is advisable for everyone to practice the methods outlined.

## Step-by-Step Plan (with real examples)

### Step 1. Create a Repository

```bash
mkdir prompt-lab
cd prompt-lab
git init
git switch -c main
```

Add a `.gitignore` (for example, for temporary files like `.DS_Store`, `__pycache__`, etc.).

> Tip: Use ready-made templates from [https://www.toptal.com/developers/gitignore](https://www.toptal.com/developers/gitignore)

### Step 2. Folder Structure

```bash
mkdir -p prompts/{system,user,context,docs}
```

  * `prompts/system/` — instructions, roles, response format.
  * `prompts/user/` — user request templates.
  * `prompts/context/` — blocks with additional knowledge.
  * `prompts/docs/` — the guides themselves on *how to write and version prompts*.

### Step 3. First Prompt

Let's create a system prompt for training:

```json
// prompts/system/system_guide_v1.json
{
  "id": "system_guide_v1",
  "content": "You are an AI mentor who helps my team learn how to write and version prompts.\nAlways respond in a structured manner: steps, examples, pitfalls.\nFormat your answers in markdown."
}
```

### Step 4. Simple User Prompt

```json
// prompts/user/ask_about_prompts_v1.json
{
  "id": "ask_about_prompts_v1",
  "template": "Explain how to organize the storage and versioning of prompts in Git.",
  "parameters": {
    "temperature": 0.2
  }
}
```

### Step 5. First Combination

Write a script to assemble the final prompt:

> Attention\! This method is not the intended one in our organization, but it is very useful for understanding how modular prompts are assembled. The code below has not been tested in real-world conditions, so please report the results if you decide to try it out.

```python
# build_prompt.py
import json, sys

def load(file):
    with open(file, "r") as f:
        return json.load(f)

system = load("prompts/system/system_guide_v1.json")["content"]
user = load("prompts/user/ask_about_prompts_v1.json")["template"]

final_prompt = f"{system}\n\n{user}"
print(final_prompt)
```

### Step 6. Versioning and Commits

```bash
git add .
git commit -m "feat: add first modular prompts for guide use-case"
```

Next, you will do `git switch -c feature/new-block`, change/add blocks, and then discuss them with the team via a Pull Request.

## Comparison of Work Styles

| Approach | What it gives | Risks |
| --- | --- | --- |
| Everything in one file | Fast start | Clutter, difficult to version |
| Modular JSON blocks | Flexibility, testability | Need to write an assembler |
| Documents + code (docs + build) | Clear methodology and examples | Higher entry barrier |

## Resources for Starting

See `culture/ai/ai_further_reading.md`.

## Why it is not suitable for production

  * **Too rapid block growth** → without naming rules (`id`, `v1`, `v2`) you will get confused.
  * **No automated tests** → an error in parameters (`{text}` without substitution) will surface only in production.
  * **Manual combination** → it's better to write assembly scripts right away.
  * **No review processes** → without a PR, discipline quickly collapses.
  * **Documents are forgotten to be updated** → version the guides themselves alongside the prompts.
