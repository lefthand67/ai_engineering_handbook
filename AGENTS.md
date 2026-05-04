This file provides guidance to AI agents when working with code in this repository.

## Project Overview

AI Engineering Book - a knowledge base for building production-grade AI systems using hybrid LLM+SLM methodology. Content is authored as MyST Markdown notebooks paired with Jupyter notebooks via Jupytext.

## Common Commands

```bash
# Restore environment from lock file
uv sync --frozen

# Sync notebooks after editing .md or .ipynb files
uv run jupytext --sync

# Run link validation tests
uv run pytest tools/tests/test_file.py --cov=tools.tests.test_file --cov-report=term-missing

# Check broken links in markdown files
uv run tools/scripts/check_broken_links.py --pattern "*.md"

# Validate frontmatter against .vadocs/ config chain (ADR-26042)
uv run python -m tools.scripts.check_frontmatter [PATHS...] [--format {md,ipynb}]

# Validate all ADRs and auto-fix index
uv run tools/scripts/check_adr.py --fix

# Validate a commit message (used by commit-msg hook)
uv run tools/scripts/validate_commit_msg.py .git/COMMIT_EDITMSG

# Generate CHANGELOG from git history and prepend to CHANGELOG file
uv run tools/scripts/generate_changelog.py <prev-tag>..HEAD --version <next-version> --prepend CHANGELOG

# Build documentation site
npm install -g mystmd && myst build --html

# Manage external research repos (research/)
uv run tools/scripts/manage_external_repos.py list                          # Show all repos
uv run tools/scripts/manage_external_repos.py update                        # Pull all repos
uv run tools/scripts/manage_external_repos.py update --parallel             # Parallel pull
uv run tools/scripts/manage_external_repos.py setup <url> [--dir <dir>]    # Clone new repo
uv run tools/scripts/manage_external_repos.py list --dirs                   # Show registered directories
uv run tools/scripts/manage_external_repos.py register <path> <desc>        # Register new directory
uv run tools/scripts/manage_external_repos.py unregister <path>             # Remove directory from registry
```

:::{note}
**Breaking change:** `ai_system/` was renamed to `ai_system_layers/`.
`6_agents/` was moved to repo root as `ai_agents/`.
All internal links updated. External references to the old paths are stale.
:::

## Architecture

The repository is organized around a five-layer AI system architecture:

- `0_intro/` - Onboarding and foundational concepts (start with `00_onboarding.ipynb`)
- `ai_system_layers/` - Core content organized by layer:
  - `1_execution/` - CPU/GPU optimization, VRAM/RAM management
  - `2_model/` - SLM selection, tokenization, embeddings
  - `3_prompts/` - Prompts-as-Infrastructure, includes JSON prompt files in `consultants/`
  - `4_orchestration/` - RAG, agent workflows, structured output
  - `5_context/` - Vector stores, hybrid retrieval
- `ai_agents/` - Real-world agent framework analysis. **Agents MUST read [ai_agents/README.md](/ai_agents/README.md) before starting any research or analysis in this directory to align with the "Analyze $\rightarrow$ Save $\rightarrow$ Move" workflow.** External source code is cloned into `research/` as nested git repos — excluded from `.gitignore` and script checks via `tools/scripts/paths.py`. Use `manage_external_repos.py` to clone and update repos. Analysis notebooks live in topic subdirectories (`session_history_management/`, `skills/`, `tooling/`, etc.)
- `architecture/` - Architectural Decision Records (ADRs) and post-mortems
- `security/` - Centralized security policy hub
- `mlops/` - CI/CD and security tooling
- `tools/` - Scripts, tests, and configuration files

## Critical Conventions

When you implemented a plan in /plan mode, save it to misc/plan/plan_<YYYYMMDD>_<descriptive_slug>.md, ONLY then start implementation. After the plan is fully implemented, move it to misc/plan/implemented/. This is needed to save the history of the decisions made between context switches.

**Implementation Plans for Handoff:**
Plans in `misc/plan/` may be executed by another agent that has zero context from the brainstorm session. A plan is a standalone specification — the executing agent must NOT need to re-brainstorm or ask clarifying questions. Every plan must contain:

1. **Full context section** — current state analysis with directory trees, file breakdowns (section-by-section with line numbers), and a content mapping table showing what moves where and why
2. **Cross-reference map** — list ALL files that reference the changed files, with exact line numbers, current (broken) paths, and what they should become. Include a final-state cross-reference diagram showing all link relationships
3. **Rationale for each task** — explain WHY each change is being made, not just WHAT to do. The executing agent needs to understand the intent to make correct decisions when edge cases arise
4. **Complete file content** — for new files and rewritten files, provide the FULL content inline in the plan. Never say "create file with appropriate content" or "slim down the file" — show exactly what goes in
5. **Exact edit operations** — for modifying existing files, provide the exact `old_string` (with 3+ lines of context BEFORE and AFTER) and the `new_string` for every `edit` tool call. The executing agent must be able to copy-paste without reading the target file first
6. **Content removal list** — when splitting files, explicitly list which sections are removed, which are kept, and where the removed content went. Use checkmarks (✅ kept, ✗ moved) for clarity
7. **Commands with expected output** — every `git mv`, `ls`, `grep`, verification command must include the expected output so the executing agent can detect failures
8. **Self-review section** — a checklist the plan author ran before handoff: spec coverage, placeholder scan, cross-reference consistency, scope check

Track intentional tech debt in `misc/plan/techdebt.md` with date, location, and migration path.

**MyST Notebooks:**
- `myst.yml` abbreviations must be in alphabetical order
- Never convert `{code-cell}` blocks to standard markdown code blocks
- Always preserve MyST directive syntax exactly
- Notebooks (.ipynb) and markdown (.md) files are paired via Jupytext - editing one requires syncing
- **Always read `.md` files, never `.ipynb`** — `.ipynb` is JSON and expensive to parse; the `.md` Jupytext pair contains the same content
- For internal cross-references within a notebook, use MyST labels and `{ref}` — never `§N` or bare section names. Add `(label)=` above the target heading and reference with `` {ref}`label` ``
- Use MyST admonitions for callout blocks in documentation — never `> blockquotes` for notes, tips, warnings, or insights. Available types: `::{note}`, `::{tip}`, `::{warning}`, `::{seealso}`, `::{important}`. Example:
  ```
  :::{tip}
  Brief actionable insight or context.
  :::
  ```

**Python:**
- Use `pathlib.Path`, never `os` library
- Follow top-down design: main function at the top
- Detect repo root via `git rev-parse --show-toplevel` with `Path(__file__)` fallback, never `Path(".")`
- Script structure order: data classes → configuration → main → validation → discovery → helpers → `if __name__`

**Content Frontmatter (ADR-26042, supersedes ADR-26023):**
- **Structural SSoT:** All structural requirements, including the mandatory **Dual-Block pattern** for Jupytext-paired files, are defined in the `tools/scripts/check_frontmatter.py` specification. Run `uv run python -m tools.scripts.check_frontmatter --help` for the authoritative spec.
- Composable blocks: identity (`title`, `type`, `authors`), discovery (`description`, `tags`, `token_size`), lifecycle (`date`, `birth`, `version`)
- MyST-native fields (top-level): `title`, `authors`, `date`, `description`, `tags` — verified against https://mystmd.org/guide/frontmatter
- All other fields under `options.*` (ecosystem fields invisible to MyST)
- Schema SSoT: `.vadocs/conf.json` (field registry, blocks, type registry, tags with descriptions)
- Author email: `rudakow.wadim@gmail.com` (not `lefthand67@gmail.com`)
- Docs already in production use version `1.0.0`+, not `0.x`

**ADR frontmatter template (canonical field order):**
```yaml
id: <NNNNN>
title: "<Title>"
authors:
  - name: Vadim Rudakov
    email: rudakow.wadim@gmail.com
date: <YYYY-MM-DD>
description: "<one-line elevator pitch>"
tags: [<primary-tag>, ...]
status: <proposed|accepted|rejected|superseded|deprecated>
superseded_by: <ADR-NNNNN or null>
options:
  type: adr
  birth: <YYYY-MM-DD>
  version: <semver>
```
- `id`, `status`, `superseded_by` are ADR-specific top-level fields (not under `options.*` despite being non-MyST)
- `date` = last meaningful update — bump on every commit that touches the file; `options.birth` = creation date, set once, never changes
- `options.version` SemVer: `0.x.y` while proposed, `≥1.0.0` once accepted; patch bump on every edit, minor for content additions, major for decision changes
- When editing any ADR: always update `date` to today and patch-bump `options.version`

**Tool Configuration (ADR-26029, ADR-26036):**
- Config discovery: `pyproject.toml [tool.vadocs].config_dir` → `.vadocs/` (single entry point)
- Scripts resolve configs via `paths.get_config_path(repo_root, "evidence")` — convention encoded once
- Governance configs live in `.vadocs/` directory at project root (ADR-26036, scope-isolated pattern)
- Config hierarchy: `.vadocs/conf.json` (hub vocabulary) → `.vadocs/types/<doc_type>.conf.json` (spoke rules) via `parent_config` pointer
- Config format: JSON + JSON Schema (ADR-26054). Document frontmatter stays YAML (embedded in markdown)
- Operational rules (excludes, patterns) go in `.vadocs/validation/`
- Shared utilities: `tools/scripts/git.py` (repo root, staged files), `tools/scripts/paths.py` (config discovery, exclusion constants)

**ADRs and Evidence Artifacts:**
- To validate artifacts, run the script (e.g., `check_evidence.py`). Only run the script's test suite (`pytest test_check_evidence.py`) when the script itself was modified
- Writing quality standards, evidence pipeline, status transitions, and operational rules: see [Architecture Decision Workflow](/architecture/architecture_decision_workflow_guide.md)
- Evidence artifact sections are validated by `check_evidence.py` against `.vadocs/types/evidence.conf.json`
- `check_adr.py` operates on all ADRs at once (no file arguments)
- ADR frontmatter `status` determines index section placement (see `.vadocs/types/adr.conf.json`)
- ADR index uses two-level sectioning: `## status` → `### primary_tag`. The first tag in `tags:` is the primary tag and determines the sub-section. Choose the most specific domain tag first (e.g., `[devops]` not `[architecture, devops]`). Keep `architecture` as primary only for genuinely structural ADRs
- ADR `description` field (one-line elevator pitch) appears in the index under the title link when present
- ADR filenames use truncated slugs — always glob (`architecture/adr/adr_26NNN*.md`) to verify the exact filename before creating links
- Internal file references must use markdown links `[Title](/repo-root-relative/path)` — backtick paths bypass `check_broken_links.py` validation. Example paths in docs must use patterns from `BROKEN_LINKS_EXCLUDE_LINK_STRINGS` in `tools/scripts/paths.py` to avoid false positives
- **Cross-references between articles must use absolute paths** (`/ai_agents/context_management/file.ipynb`), never relative paths (`../context_management/file.ipynb` or `./file.ipynb`). Relative paths break when articles are in different subdirectories. This applies to all `{seealso}`, `{tip}`, and inline links between persistent artifacts
- Persistent artifacts (ADRs, analyses, retrospectives) must always be referenced via markdown links `[A-26009](/repo-root-relative/path)`, never plain backtick IDs — md links are navigable by both agents and humans
- Backtick references are for ephemeral files (sources in `evidence/sources/`, files in `misc/`) AND config files (`.vadocs/` configs change paths on restructuring — use backtick filenames like `adr.conf.json`, never markdown links)
- When linking to a Jupytext-paired file, always use the `.ipynb` extension — `check-link-format` hook rejects `.md` links when a paired `.ipynb` exists
- Before committing, run `uv run tools/scripts/check_broken_links.py` and `uv run tools/scripts/check_link_format.py` to find stale links — fix them proactively instead of waiting for hook failures
- Never link from persistent artifacts (ADRs, analyses) to ephemeral files (`misc/plan/`, `misc/todo.md`, `evidence/sources/`) — use backtick references instead
- Never reference "planned ADR-NNNNN" in documents — either link to an existing ADR or reference the problem/tracking location (e.g., `techdebt.md`)
- **ADR Decision sections must be concise statements, NOT implementation details.** No bash commands, no code blocks showing how to run things, no specific tool invocations. Evidence details and measurements belong in Consequences. Risk mitigations should not name specific implementations (e.g., "Traefik handles routing") — use generic descriptions
- When ADRs reference external projects (e.g., `mentor_generator`, `vadocs`), provide inline context — ADRs are long-living documents read without prior session knowledge
- Evidence source files: `S-YYNNN_<slug>.md` naming with frontmatter fields `id`, `title`, `date`, `model`, `extracted_into` (see `.vadocs/types/evidence.conf.json`)
- When given a raw LLM dialogue file, save it as a proper source artifact (`S-YYNNN`) with frontmatter, then create an analysis (`A-YYNNN`) extracting actionable insights
- One ADR = one decision. If two concerns have independent justifications and alternatives, split them
- ADR examples should be generic (e.g., `project_alpha`), not tied to specific ecosystem projects — ADRs outlive current project details
- Do not import external evaluation frameworks (e.g., WRC scores) into ADRs — reference conclusions, not foreign metrics
- Do not include unverified benchmark numbers — either cite the source or remove
- ADR cross-references: use `` {term}`ADR-NNNNN` `` — renders titles automatically from adr_index.md glossary. **MyST-rendered files only** (ADRs, articles, `README.md`). In GitHub-only files (`RELEASE_NOTES.md`, `CHANGELOG`) use plain markdown links — `{term}` renders as literal text on GitHub

**Configuration:**
- Use placeholders like `[IP_ADDRESS]` or `[DOMAIN]` instead of real values

**Containerization:**
- Use Podman, never Docker — Podman is the production tool in this ecosystem
- Use Kube YAML manifests runnable via `systemctl --user`, never Docker Compose or Podman Compose (ADR-26040)

**Ephemeral Files:**
- `misc/todo.md` is plain text (no markdown formatting) — treat as an ephemeral scratch notebook
- `misc/insights.md` is plain text — ephemeral scratch file for session insights, same conventions as `todo.md`

**Living Documents:**
- `RELEASE_NOTES.md` is a living document that users navigate — links in release entries must always be updated when referenced files are renamed or moved. Do NOT treat it as historical/archival.
- `CHANGELOG` is auto-generated from commit history — do NOT edit manually (ADR-26024)

**Evidence Source Hygiene:**
- Raw source files (`.txt`, `.json`) in `evidence/sources/` must be deleted once content is captured in a `S-YYNNN` artifact — never leave both coexisting
- `S-YYNNN` files must live directly in `architecture/evidence/sources/`, not in subdirectories

**PyYAML Token Gotcha:**
- `yaml.dump()` defaults to `width=80` (line wrapping) — adds ~100 tokens vs yq on a 150-line prompt and can flip format rankings; specify `width` explicitly when comparing serializers
- YAML format cost rankings (e.g., "YAML Literal is most expensive") are serializer-dependent — always qualify with the tool used

## CI/CD Pipeline

Two GitHub Actions workflows:

1. **quality.yml** - Runs on all pushes/PRs:
   - Runs check_broken_links tests when script, tests, or `paths.py` change
   - Runs jupytext tests when sync/verify scripts, tests, or `paths.py` change
   - Validates links in changed `.md` files
2. **deploy.yml** - Validates notebook sync on all branches, deploys to GitHub Pages on main only

The pipeline verifies that .md and .ipynb pairs are synchronized before allowing deployment.

## Development Workflow

Jupytext sync runs as a pre-commit lint step. The `.aider.conf.yml` also configures auto-linting for Aider sessions.

**Tooling & Quality Gates:**
- When creating or modifying validation scripts or quality gates in `tools/scripts/`, strictly adhere to the standards defined in [validation_standards.md](./tools/scripts/validation_standards.md) and [testing_standards.md](./tools/scripts/testing_standards.md).

Python version: 3.13+ (locked in `.python-version`)
Package manager: `uv` (never use pip directly)

**Tool-Driven Instructional Feedback (ADR-26050):**
- **Scripts are Instructors:** Treat validation script errors (hooks) not as mere failures, but as Just-In-Time (JIT) instructions.
- **Follow the Guidance:** When a hook fails, prioritize the specific "How-to-Fix" instructions provided in the error message over general documentation.
- **Reporting Contract:** Errors follow the format `file_path:field — <Instructional Message> [config_source]`.
- **Actionable Correction:** If a script tells you to move a line, change a value to a specific approved option, or add a missing tag, perform that exact action to resolve the violation.

**TDD Approach (Tests First):**
- **IMPORTANT: Always write tests FIRST, then implement the functionality to make them pass (Red → Green → Refactor)**
- For new features or refactoring: write failing tests first, then implement until tests pass
- Scripts require comprehensive test suites (e.g., prepare_prompt.py has 96 tests)
- Tests live in `tools/tests/` with `test_<script_name>.py` naming
- Run tests with `uv run pytest tools/tests/test_<script_name>.py`
- Pre-commit hooks automatically run relevant tests on commit

**Test Quality Standards (Non-Brittle Tests):**
- **Test contracts, not implementation**: Verify exit codes, return types, and side effects—not exact message strings or output formatting
- **Avoid asserting on specific wording**: Use `assert exit_code == 1` instead of `assert "specific error text" in output`
- **Test behavior boundaries**: One broken ref → exit 1, zero broken refs → exit 0. Don't test message content
- **Use semantic assertions**: `assert len(errors) > 0` or `assert adr_number in {found_numbers}` instead of exact counts when the exact count isn't the contract
- **Avoid exact call counts in mocks**: Don't use `assert mock.call_count == N` — use `side_effect` lists that implicitly enforce short-circuiting (extra calls raise `StopIteration`)
- **Parameterize inputs**: Test varied scenarios (edge cases, empty inputs, multiple items) without duplicating test logic
- **Parametrize from config, not hardcoded lists**: Import `VALID_TYPES`, `TYPE_TO_SECTION`, etc. from scripts — they load from `pyproject.toml` SSoT
- **No hardcoded paths in tests**: Resolve config paths via `pyproject.toml` → config → parent_config chain, never hardcode directory structures
- **Import module once**: Use `import tools.scripts.X as _module` at top of test file; access all functions via `_module.func()` — single point to update on package rename
- **Config-driven test helpers**: Build valid test data (frontmatter, filenames) dynamically from config structure, not hardcoded field→value mappings
- **Document the contract**: Each test class should have a docstring explaining what contract it verifies

**Quality & Testing Standards (Adversary Testing):**
- **Adversary Testing**: For any scripts created to support this research (e.g., extraction tools), use comprehensive "adversary" testing.
- **Semantic Validation**: Do not rely on code coverage as a sole proxy for correctness. Explicitly test boundary conditions, structural edge cases (e.g., empty files, malformed JSON), and valid syntax that produces unexpected types.
- **Verification**: Ensure every architectural claim is grounded in a specific, verified code snippet.

**Commit Conventions (ADR-26024):**
- Use conventional commits with prefixes from `pyproject.toml [tool.commit-convention]` `valid-types`
- `pr:` prefix is for promotional/announcement posts
- There is no `revert:` type — use `docs:`, `chore:`, or `fix:` depending on what the revert corrects
- Keep commit subjects concise (50 chars max), focusing on the "what"
- Commit body format: [Structured Commit Body Format](/tools/docs/git/01_production_git_workflow_standards.ipynb) — main bullets (`- <Verb>: <file-path> — <what_and_why>`) with optional sub-bullets (`    — <lowercase_verb> <detail>`)
- CHANGELOG is generated from commit history, not manually curated
- Commit bullets mentioning changelog exclusion patterns (e.g., `CLAUDE.md`, `misc/`) will be self-filtered — describe intent instead of listing literal pattern values; verify with `uv run tools/scripts/generate_changelog.py --verbose HEAD~1..HEAD 1>/dev/null`
- When some bullets are excluded, the commit subject becomes the changelog section header for only the surviving bullets. Write the subject to match changelog-visible bullets only — a subject summarising excluded work produces a misleading changelog entry where the header promises more than the bullets deliver
- Merge policy: Squash-and-Merge (1 PR = 1 Commit on trunk)

**Pre-commit Hooks:**
- Extensive validation runs before each commit (see `.pre-commit-config.yaml`)
- Includes: broken links check, link format check, jupytext sync/verify, API key detection, JSON validation, script tests
- Post-commit `changelog-preview` hook shows the CHANGELOG entry for the just-created commit
- All hooks use `uv run` for Python execution
- YAML gotcha: `entry` values with `: ` (colon-space) must be double-quoted in `.pre-commit-config.yaml` — YAML interprets unquoted `: ` as a mapping separator

**Safe Editing:**
- When doing bulk `replace_all` on artifact IDs (e.g., `S-26007` → `A-26009`), review each match for semantic correctness — some occurrences may be examples or format illustrations where the original prefix is intentional

**Precise Targeting Protocol (Anti-Extrapolation Rule):**
When resolving validation errors (e.g., from `check-link-format.py` or `check_frontmatter.py`):
1. **No Global Cleanups:** Never assume a few errors in one file imply a systemic issue in a directory. Do NOT run "fix-all" scripts followed by global `git add` commands (e.g., `git add path/**/*.md`) to resolve point-errors.
2. **Mandatory Error-to-Pair Mapping:** Before staging any fix, the agent MUST explicitly list the mapping:
   `Error in [File A]` $\rightarrow$ `Fix [File A]` $\rightarrow$ `Stage [File A] AND [Paired File A.ipynb]`.
3. **Minimum Viable Stage:** Stage ONLY the files explicitly mentioned in the error logs and their mandatory Jupytext pairs. 
4. **Forbidden Globs:** The use of glob patterns in `git add` to fix specific validation errors is strictly prohibited unless the error log explicitly lists every file in that glob as broken.


**Safe Git Commands:**
- Use `git restore <file>` to discard changes, never `git checkout -- <file>` (ambiguous between branch and file operations)
- Use `git restore --staged <file>` to unstage files, never `git reset HEAD <file>`
- **NEVER use `git reset` for any operation; use `git restore` or `git switch` as appropriate**
- Use `rm` (not `git rm`) for untracked files — `git rm` fails on files not in the index
- Use `git switch <branch>` to change branches, never `git checkout <branch>`
- Never use `git reset --hard`, `git push --force`, or `git clean -f` without explicit user request
- **NEVER use the `sed` command for file modifications.** Use the provided `edit` or `write_file` tools. `sed` is prohibited due to risk of corruption and lack of precise targeting.
- **NEVER use the `--no-verify` flag when committing.** This is strictly prohibited as it bypasses essential pre-commit hooks and validation scripts, leading to failures in the remote CI/CD pipeline. Resolve all hook failures locally before attempting to commit.
- **Never use `git add -A`** — always stage files explicitly with `git add <specific-paths>` to avoid accidentally adding unrelated or untracked files

**Symlinks:**
- Use `ln -sfr <absolute_target> <absolute_link_path>` — the `-r` flag creates relative symlinks, making them resilient to directory moves
- Both arguments must be absolute paths — the target and link location are computed from the filesystem root, not CWD

**Design Principles:**
- Prefer reusing existing tools over writing new code — check if an existing script already does what you need before creating new functions/classes
- Hook-specific UX (tips, warnings) belongs in the hook entry, not in the reusable script — scripts may be called in contexts where the tip is nonsensical
- Question the plan: if the implementation seems disproportionate to the goal, step back and look for a simpler approach

**Documentation:**
- Avoid duplicating information across docs — use cross-references to the authoritative source
- Doc 02 (`02_pre_commit_hooks_and_staging_instruction_for_devel.md`) is the authoritative source for hook installation instructions

**Script Suite (ADR-26045, supersedes ADR-26011):**
- Scripts require a matching test file (dyad: script + test). No separate doc file required — contract docstrings in the script are the documentation
- Pre-commit hook enforces the dyad: when modifying a script, the corresponding test in `tools/tests/` must also be staged (and vice versa)

## Telegram Channel Posts

Posts for the `@ai_learning` Telegram channel are stored in `misc/pr/tg_channel_ai_learning/`.

**Naming convention:** `YYYY_MM_DD_<topic_slug>.md`

**Language:** Russian

**Post structure:**
1. Bold headline
2. Problem statement (with 💡 icon)
3. Technical explanation (with 🧠 icon if applicable)
4. Solution description (with ⚙️ icon)
5. Key features list (with ✅ checkmarks)
6. Usage examples in code blocks
7. Documentation link
8. Hashtags (e.g., #Python #LLM #ai_engineering_handbook)
