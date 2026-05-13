---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.1
---

jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.1
kernelspec:
  name: bash
  display_name: Bash
  language: bash
options:
  type: source
---
title: Evidence Sources
author: Vadim Rudakov, rudakow.wadim@gmail.com
date: 2026-03-07
options:
  type: guide
  version: 0.1.0
  birth: 2026-03-07
  token_size: 761
---

+++

This directory holds **ephemeral source material** --- dialogue transcripts, meeting notes, and raw research inputs --- that feed into analyses (`evidence/analyses/`) and ultimately produce ADRs (`decisions/`).

+++

## Lifecycle

+++

Sources follow a three-commit workflow:

1.  **Commit 1 --- Capture:** Add the transcript to `evidence/sources/S-YYNNN_slug.md`
2.  **Commit 2 --- Extract:** Write the analysis to `evidence/analyses/A-YYNNN_slug.md` with `sources: [S-YYNNN]`. Update the source's `extracted_into` field to point at the analysis.
3.  **Commit 3 --- Delete:** Remove the source file. Git history preserves it at a predictable path.

**Rule:** A source is only deleted AFTER its `extracted_into` field points to a committed analysis.

The commit 1 and 2 can be combined into 1 commit if the analysis is done in the same session when the source is saved.

+++

## Naming Convention

+++

`S-YYNNN_descriptive_slug.md` where:

-   `S` = Source namespace prefix
-   `YY` = Two-digit year (e.g., `26` for 2026)
-   `NNN` = Sequential number within the year (e.g., `001`)
-   `_descriptive_slug` = Kebab-style description

+++

## Frontmatter Schema

+++

``` yaml

title: Claude — AKB Taxonomy Discussion
date: 2026-02-26
options:
  id: S-26001
  model: claude-opus-4
  extracted_into: A-26001
  type: source
---
```

+++

## Git Archaeology

+++

Sources are designed to be committed and then deleted. The git history preserves them permanently at predictable paths.

**Get the list of all source files in Git history:**

```{code-cell}
cd ../../../
ls
```

```{code-cell}
sources="architecture/evidence/sources/"; git log --oneline --name-only -- "${sources}" | grep  "${sources}" | grep -v "${sources}/README.md" | sort -u | tail -n3
```

**Search for deleted transcripts:**

```{code-cell}
git log --all --full-history -- architecture/evidence/sources/ | head -n20
```

**Recover a specific deleted transcript:**

```bash
git show <commit-hash>:architecture/evidence/sources/S-YYNNN_slug.md
```

**Find which commit deleted a file:**

```bash
git log --diff-filter=D -- architecture/evidence/sources/S-26001_slug.md
```
