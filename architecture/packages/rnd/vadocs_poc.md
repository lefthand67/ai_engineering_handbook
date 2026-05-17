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
title: vadocs v0.1.0 - Proof of Concept
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: '2026-05-02'
description: Proof of Concept for the vadocs package, demonstrating automated frontmatter
  and ADR validation.
tags:
- architecture
- development
- governance
options:
  type: guide
  version: 0.1.0
  birth: '2026-02-04'
  token_size: 1816
---
# vadocs v0.1.0 - Proof of Concept

+++

## Motivation

The [`ai_engineering_book`](https://github.com/lefthand67/ai_engineering_handbook) repository contains several validation scripts in `tools/scripts/` that share common patterns: YAML frontmatter parsing, configuration loading, validation error reporting. Each script duplicates parsing logic, and the validation functionality cannot be reused in other repositories.

**Solution**: Extract common validation logic into a reusable Python package (`vadocs`) that can be installed via `uv add`.

## Goal

Create a minimal viable package that proves:

1. Installability as a uv dependency from GitHub
2. YAML frontmatter validation works correctly
3. ADR-specific validation (fields, status, tags, sections)
4. Configuration loading from YAML files

## Implementation Summary

- **Core models**: `Document`, `ValidationError`, `SyncField`, `SyncResult`
- **Validators**: `FrontmatterValidator`, `AdrValidator`, `AdrTermValidator`
- **Fixers**: `AdrFixer`, `SyncFixer`
- **Config**: `load_config()` for YAML files
- **Tests**: 79 passing

## What's NOT in v0.1.0

- CLI interface (library-only)
- pyproject.toml `[tool.vadocs]` config loading
- Project scaffolding (`vadocs init`)
- Index sync validation

## Further Steps

- **v0.2.0**: CLI + pyproject.toml config
- **v0.3.0**: Index sync validation
- **v0.4.0**: Additional validators (broken links, jupytext)
- **v1.0.0**: PyPI release, stable API

---

## PoC Validation Checklist

Execute each step manually. Mark `[x]` when passed.

### 1. Installation

```{code-cell}
cd /tmp/test-vadocs
ls -a
```

```{code-cell}
uv init
env -u VIRTUAL_ENV uv add "vadocs @ git+https://github.com/lefthand67/vadocs.git"
```

```{code-cell}
env -u VIRTUAL_ENV uv tree
```

```{code-cell}
cat pyproject.toml
```

```{code-cell}
ls -a
```

- [x] **PASS**: Command completes without errors

### 2. Import verification

```{code-cell}
env -u VIRTUAL_ENV uv run python -c "from vadocs import AdrValidator, Document, load_config, parse_frontmatter; print('OK')"
```

- [x] **PASS**: Prints `OK`

### 3. Config loading

```{code-cell}
env -u VIRTUAL_ENV uv run python -c "
from pathlib import Path
from vadocs import load_config
config = load_config(Path('adr/adr_config.yaml'))
print('statuses:', config.get('statuses'))
print('required_fields:', config.get('required_fields'))
"
```

- [x] **PASS**: Prints statuses list (proposed, accepted, etc.)
- [x] **PASS**: Prints required_fields list (id, title, date, status, tags)

### 4. Valid ADR produces no errors

Pick a known valid ADR file and run:

```{code-cell}
env -u VIRTUAL_ENV uv run python -c "
from pathlib import Path
from vadocs import AdrValidator, Document, load_config, parse_frontmatter

config = load_config(Path('adr/adr_config.yaml'))
adr_path = Path('adr/adr_26017_adr_format_validation_workflow.md')  # <-- change to your ADR
content = adr_path.read_text()
doc = Document(path=adr_path, content=content, frontmatter=parse_frontmatter(content), doc_type='adr')
errors = AdrValidator().validate(doc, config)
print(f'Errors: {len(errors)}')
for e in errors: print(f'  [{e.error_type}] {e.message}')
"
```

- [x] **PASS**: Prints `Errors: 0`

### 5. Missing field detected

Create a test file `/tmp/test_adr.md`:

```{code-cell}
cat > /tmp/test_adr.md <<EOF
---
id: 99999
title: Test ADR
status: accepted
---

# ADR-99999: Test ADR
EOF
```

Run validation:

```{code-cell}
env -u VIRTUAL_ENV uv run python -c "
from pathlib import Path
from vadocs import AdrValidator, Document, load_config, parse_frontmatter

config = load_config(Path('adr/adr_config.yaml'))
content = Path('/tmp/test_adr.md').read_text()
doc = Document(path=Path('/tmp/test_adr.md'), content=content, frontmatter=parse_frontmatter(content), doc_type='adr')
errors = AdrValidator().validate(doc, config)
print(f'Errors: {len(errors)}')
for e in errors: print(f'  [{e.error_type}] {e.message}')
"
```

- [x] **PASS**: Reports `missing_field` for `date`
- [x] **PASS**: Reports `missing_field` for `tags`

### 6. Invalid status detected

Create `/tmp/test_adr_status.md`:

```{code-cell}
cat > /tmp/test_adr_status.md <<EOF
---
id: 99999
title: Test ADR
date: 2024-01-15
status: invalid_status
tags: [architecture]
---

# ADR-99999: Test ADR
EOF
```

Run validation:

```{code-cell}
env -u VIRTUAL_ENV uv run python -c "
from pathlib import Path
from vadocs import AdrValidator, Document, load_config, parse_frontmatter

config = load_config(Path('adr/adr_config.yaml'))
content = Path('/tmp/test_adr_status.md').read_text()
doc = Document(path=Path('/tmp/test_adr_status.md'), content=content, frontmatter=parse_frontmatter(content), doc_type='adr')
errors = AdrValidator().validate(doc, config)
for e in errors: print(f'  [{e.error_type}] {e.message}')
"
```

- [x] **PASS**: Reports `invalid_status` error

### 7. Invalid tag detected

Create `/tmp/test_adr_tag.md`:

```{code-cell}
cat > /tmp/test_adr_tag.md <<EOF
---
id: 99999
title: Test ADR
date: 2024-01-15
status: accepted
tags: [nonexistent_tag]
---

# ADR-99999: Test ADR
EOF
```

Run validation:

```{code-cell}
env -u VIRTUAL_ENV uv run python -c "
from pathlib import Path
from vadocs import AdrValidator, Document, load_config, parse_frontmatter

config = load_config(Path('adr/adr_config.yaml'))
content = Path('/tmp/test_adr_tag.md').read_text()
doc = Document(path=Path('/tmp/test_adr_tag.md'), content=content, frontmatter=parse_frontmatter(content), doc_type='adr')
errors = AdrValidator().validate(doc, config)
for e in errors: print(f'  [{e.error_type}] {e.message}')
"
```

- [x] **PASS**: Reports `invalid_tag` error

---

## Result

**Date**: 2026-02-04

**Tester**: rudakow.wadim@gmail.com

**All criteria passed**: 
- [x] YES 
- [ ] NO

**Notes**: Before conducting the PoC, these actions have been done: [Creating Spoke Packages](/architecture/packages/creating_spoke_packages.md).
