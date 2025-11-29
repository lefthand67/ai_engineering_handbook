# Developer Changelog Generator Prompt

---

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.1.0  
Birth: 29.11.2025
Last Modified: 29.11.2025

---

This directory contains a highly structured JSON prompt designed for AI agents (specifically tested with `aider`) to generate concise, technically detailed, and traceable changelog entries from raw `git diff` output.

## 🎯 Purpose

The primary goal of this prompt is to synthesize complex code changes into a **structured, consistent, and traceable Markdown format** suitable for internal development teams.

It enforces strict adherence to:

1.  **Traceability:** Mandatory inclusion of the commit range or architectural tag (`Ref:`).
2.  **Scoping:** Clear filtering of non-functional (cosmetic) changes.
3.  **Standardization:** Strict use of a defined `[TYPE]` and `[COMPONENT]` taxonomy.

## 🛠️ Requirements & Dependencies

  * **AI Agent:** Requires an AI coding assistant capable of processing large system instructions and interacting with files. **Tested and optimized for `aider`**.
  * **Prompt File:** `changelog_prompt.json` (This file).
  * **Target File:** `CHANGELOG.md` (Must exist in the repository).

## 🚀 Usage Workflow (Recommended with `aider`)

This workflow requires you to first determine the exact commit range (e.g., from the last tag `v1.0.0` to `HEAD`) and then pass that range to the AI agent explicitly for substitution.

### Step 1: Initialize and Define the Range

Before starting the agent session, define the commit range in your shell environment.

```bash
# 1. Start the aider session
aider

# 2. Inside the `aider` session determine the range (e.g., from the last tag to the current state)
# get the last tag name as start and HEAD as end commit
/run export COMMIT_RANGE="$(git describe --tags --abbrev=0)..HEAD" && echo "${COMMIT_RANGE}"
```

### Step 2: Load the Prompt and Provide Input

Lload the prompt and supply the raw `git diff` output.

```
/add CHANGELOG.md changelog_prompt.json
/run git diff "{$COMMIT_RANGE}"
```

### Step 3: Trigger Generation and Inject Traceability

Crucially, you must explicitly tell the agent the commit range so it can substitute the `$COMMIT_RANGE$` placeholder defined in the prompt's instructions.

```
/ask The commit range is $COMMIT_RANGE. Now, generate a changelog record using the changelog_prompt.json instructions.
```

*(Replace `$COMMIT\_RANGE` with the actual range from Step 1, e.g., `v1.0.0..HEAD`)*

### Step 4: Apply and Commit Changes

Use `aider`'s powerful `/code` command to automatically insert the generated Markdown into `CHANGELOG.md` and commit the change to your repository.

```
/code add the generated changelog record to CHANGELOG.md and commit the changes
```

## 📄 Output Schema and Constraints

The prompt strictly enforces the following structure. Failure to adhere to these constraints should be treated as a bug in the AI's execution.

### Mandatory Template

The final output is a Markdown bullet point following this exact template:

```markdown
* [TYPE: feat|fix|perf|refactor|chore] [COMPONENT: <Affected Component Name>] <Detailed technical description> (Ref: <Commit Range/Architectural Tag>)
```

### Required `TYPE` Categories

| Type | Description |
| :--- | :--- |
| `feat` | A new feature or capability. |
| `fix` | A corrected bug or error. |
| `perf` | A change that improves performance (speed, memory). |
| `refactor` | A change to the code structure/organization without altering functionality. |
| `chore` | Maintenance tasks, dependency updates, build changes, or non-functional file system changes. |

### Example Output

The AI's generated output will start with the current release header and contain entries categorized under the required sub-headings:

```markdown
## unreleased - 2025-11-29
### Added
* [TYPE: feat] [COMPONENT: Documentation] New ai_consultant.json prompt added... (Ref: Range: 3f8f1a2..5d2fra1)
### Changed
* [TYPE: refactor] [COMPONENT: Prompt Organization] File naming conventions updated... (Ref: #REFACTOR-MIGRATION)
### Fixed
* [TYPE: fix] [COMPONENT: File Structure] RELEASE_NOTES file renamed... (Ref: Range: 3f8f1a2..5d2fra1)
### Removed
* [TYPE: chore] [COMPONENT: Deprecated Prompts] changelog_prompt.md removed... (Ref: #DEPRECATION-PLANNED)
```
