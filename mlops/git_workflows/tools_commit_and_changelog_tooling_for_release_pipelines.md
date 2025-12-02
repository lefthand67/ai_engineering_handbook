# Tools: Commit & Changelog Tooling for Release Pipelines

-----

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.1.1  
Birth: 2025-12-02  
Last Modified: 2025-12-02

-----

## 1. Purpose

This handbook **eliminates confusion** around the sprawling ecosystem of Git commit and changelog tooling by prescribing a **minimal, deterministic, and maintainable stack** that aligns with the **Small Language Model (SLLM)-based release documentation pipeline**.

We **do not adopt** the JavaScript/Node.js tooling ecosystem (e.g., `commitizen`, `semantic-release`) due to its complexity, fragility, and mismatch with the Linux-first, containerized, resource-constrained MLOps environment.

Instead, we enforce a **two-tool standard** that is:
- **Language-agnostic**
- **CLI-native**
- **Zero runtime dependencies** (or pure Python/Go)
- **Fully compatible with `pre-commit` and CI**
- **Deterministic and reproducible**

## 2. The Tooling Standard

| Stage | Tool | Type | Why It’s Chosen |
|-------|------|------|-----------------|
| **Stage 1: Commit Message Enforcement** | [`gitlint`](https://jorisroovers.com/gitlint/) | Python CLI | Validates Conventional Commits **at commit time** via `pre-commit`. No interactivity. No Node.js. |
| **Stage 2: Changelog Generation** | [`git-chglog`](https://github.com/git-chglog/git-chglog) | Go binary | Parses structured commits into `CHANGELOG.md` **without parsing code, diffs, or configs**. Fast, idempotent, templatable. |

> **This is the only approved stack.** Deviations require Architecture Review Board (ARB) approval.

## 3. Why We Reject the JavaScript Ecosystem

| Tool | Problem | Impact |
|------|--------|--------|
| `commitizen` | Interactive CLI, requires `cz-cli`, `inquirer`, `adapter` config | Breaks automation; forces developers into wizard flows; adds npm bloat |
| `conventional-changelog` | Requires `package.json`, `conventional-changelog-cli`, parsers | Couples changelog logic to JS project structure—even in Python/C repos |
| `semantic-release` | Auto-publishes to npm/GitHub; assumes CI owns versioning | Over-automates; violates the **human-in-the-loop audit gates**; not idempotent |

> 🚫 **These tools assume a frontend/JS monorepo workflow.** They are **incompatible** with the bare-metal, multi-language, SLLM-constrained pipeline.

---

## 4. Stage 1: Commit Message Enforcement with `gitlint`

### 4.1 What It Does
- Validates that every commit message conforms to **Conventional Commits (Tier 2 or 3)**:
  ```
  <type>[optional scope]: <short summary>
  <BLANK LINE>
  <optional body>
  ```
- Blocks non-compliant commits **before they enter Git history**.

### 4.2 Integration

**Install via `pre-commit`:**
```yaml
# .pre-commit-config.yaml
- repo: https://github.com/jorisroovers/gitlint
  rev: v0.19.1
  hooks:
    - id: gitlint
      stages: [commit-msg]
```

**Run manually (for testing):**
```bash
gitlint --msg-filename .git/COMMIT_EDITMSG
```

### 4.3 Configuration
Use the default Conventional Commits rules. **Do not customize** unless adding team-specific scopes (e.g., `docs`, `sllm`, `infra`). Store config in `.gitlint`:
```ini
[general]
contrib = CC

[CC1]
# Enforce type case: feat, fix, perf, etc.
```

> ⚠️ **Never disable `gitlint` in CI or local hooks.** Broken commits break the entire pipeline.

---

## 5. Stage 2: Changelog Generation with `git-chglog`

### 5.1 What It Does
- Reads **only Git commit history** (no file content, no diffs).
- Filters and groups commits by Conventional Commit `type`.
- Renders a clean, standard `CHANGELOG.md` using a Go template.

### 5.2 Installation
Download the single binary:
```bash
# Linux x86_64
wget https://github.com/git-chglog/git-chglog/releases/latest/download/git-chglog_linux_amd64.tar.gz
tar -xzf git-chglog_linux_amd64.tar.gz
sudo mv git-chglog /usr/local/bin/
```

> ✅ No Go runtime needed. No `go.mod`. No dependencies.

### 5.3 Configuration

**`.chglog/config.yml`** (minimal):
```yaml
style: github
template: .chglog/CHANGELOG.tpl.md
output: CHANGELOG.md
commits:
  filters:
    Type:
      - feat
      - fix
      - perf
      - refactor
```

**`.chglog/CHANGELOG.tpl.md`** (standard template):
```markdown
# Changelog

{{ range .Versions }}
## {{ if .Tag }}{{ .Tag }}{{ else }}Unreleased{{ end }}

{{ range .CommitGroups -}}
### {{ .Title }}

{{ range .Commits -}}
- {{ .Subject }} ({{ .Hash.Short }})
{{ end }}
{{ end }}
{{ end }}
```

### 5.4 Usage
```bash
# Generate full changelog
git-chglog

# Generate from vX.Y.Z onward
git-chglog --next-tag v1.2.0 vX.Y.Z
```

> 🔁 **Output is 100% reproducible** given the same Git history and config.

---

## 6. Architectural Alignment

| Principle | How This Stack Complies |
|---------|--------------------------|
| **Decoupling** | Commit linting (dev) ≠ changelog gen (tool) ≠ release notes (SLLM) |
| **Determinism** | `gitlint` and `git-chglog` produce identical output across runs |
| **Low Overhead** | No interpreters, no lockfiles, no network calls |
| **Auditability** | Every commit is validated; every changelog entry maps to a real commit |
| **SLLM Efficiency** | Stage 2 output is clean, structured Markdown → minimal SLLM context |

---

## 7. Anti-Patterns to Avoid

| Anti-Pattern | Consequence |
|-------------|-------------|
| Using `commitizen` in CI | Interactive prompts hang CI; non-idempotent |
| Generating changelogs from `git log --oneline` + regex | Fragile parsing; misses scope/type structure |
| Feeding raw `git diff` to SLLM for changelog | VRAM explosion; OOM; non-reproducible output |
| Custom Python changelog scripts | Reinventing the wheel; introduces drift and bugs |

---

## 8. Summary: The Golden Path

1. **Developer writes code** → stages changes.
2. **`git commit`** → `pre-commit` runs `gitlint` → enforces Conventional Commits.
3. **On release prep**, CI runs `git-chglog` → produces `CHANGELOG.md`.
4. **SLLM (7B–14B)** consumes **only the relevant `CHANGELOG.md` section** → generates audience-tailored release notes.
5. **Engineer reviews** both changelog and SLLM output before publish.

> ✅ **This is the only supported workflow.** Keep it simple. Keep it deterministic. Keep SLLMs where they add unique value—**not for parsing Git history**.

---  
**Appendix**:  
- [Conventional Commits Spec (Tier 2/3)](./conventional_commits_tier2.md)  
- [Pre-commit Hook Setup Guide](./precommit_setup.md)  
- [Sample `.chglog` Config Repository](https://git.internal.yourorg/chglog-templates)
