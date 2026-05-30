---
title: Transferring a Repository to a GitHub Organization
authors:
  - name: Vadim Rudakov
    email: rudakow.wadim@gmail.com
date: "2026-05-03"
description: A step-by-step guide for moving any repository from a personal GitHub account to a GitHub organization.
tags:
  - git
  - workflow
---
---
options:
  type: guide
  version: 1.0.0
  birth: '2026-05-03'
  token_size: 517
---
# Transferring a Repository to a GitHub Organization

A step-by-step guide for moving any repository from a personal GitHub account to a GitHub organization.

## Prerequisites

- Target organization must already exist (create at <https://github.com/organizations/plan>)
- You must be an **owner** of the target organization
- The repo name must not already be taken in the target org

## Option A: GitHub UI

1. Go to the repo on GitHub
2. **Settings** > scroll to **Danger Zone** > **Transfer repository**
3. Type the organization name and confirm
4. Repeat for each repo

## Option B: GitHub CLI

```bash
gh api repos/<OWNER>/<REPO>/transfer \
  --method POST \
  --field new_owner=<ORG_NAME>
```

> **Note:** `gh repo transfer` exists in newer `gh` versions (2.40+).
> If your version doesn't have it, use `gh api` as shown above.

## After Transfer: Update Git Remotes

GitHub creates redirects from old URLs, but update your local remotes explicitly:

```bash
# SSH
git remote set-url origin git@github.com:<ORG_NAME>/<REPO>.git

# HTTPS
git remote set-url origin https://github.com/<ORG_NAME>/<REPO>.git
```

Verify:

```bash
git remote -v
```

## What Gets Preserved

- All commits, branches, tags
- Issues, PRs, wiki
- Stars, watchers
- GitHub automatically redirects old URLs to the new location

## What to Update Manually

- References to old URLs in `README.md`, `CLAUDE.md`, config files (e.g. `myst.yml`)
- CI/CD workflows that hardcode the old owner/org
- Badge URLs, documentation links
- `pyproject.toml` entries that reference the repo by URL (local path installs are unaffected)
