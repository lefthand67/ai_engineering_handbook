---
title: "Moving a Package to a Dedicated Repository"
authors:
  - name: Vadim Rudakov
    email: rudakow.wadim@gmail.com
date: "2026-05-03"
description: "Guide for extracting a spoke package from the monorepo into a dedicated repository."
tags: [development, governance, workflow]
---
---
options:
  type: guide
  version: 1.0.0
  birth: '2026-03-02'
  token_size: 721
---
# Moving a Package to a Dedicated Repository

A step-by-step guide for extracting a spoke package from the monorepo into its own repository.

## Step 1: Create the new repository

```bash
mkdir ~/projects/<package_name>
cd ~/projects/<package_name>
git init
```

## Step 2: Copy package files

```bash
# Copy the package contents (not the parent directory)
cp -r /path/to/ai_engineering_book/packages/<package_name>/* ~/projects/<package_name>/

# Remove the local .venv (you'll create a new one)
rm -rf ~/projects/<package_name>/.venv
```

## Step 3: Initialize the new repository

```bash
cd ~/projects/<package_name>

# Create .gitignore
cat > .gitignore << 'EOF'
__pycache__/
*.py[cod]
.venv/
dist/
*.egg-info/
.pytest_cache/
.coverage
EOF

# Initialize uv and install dependencies
uv sync
uv pip install -e ".[dev]"

# Verify tests pass
uv run pytest tests/ -v
```

```bash
uv run pytest tests/ --cov=. --cov-report=term-missing -q
```

## Step 4: Create initial commit

```bash
git add .
git commit -m "feat: Initial <package_name> package

<Brief description of the package.>

Features:
- <Feature 1>
- <Feature 2>
- <Feature N>"
```

## Step 5: Push to GitHub

```bash
# Option A: Using GitHub CLI
gh repo create <package_name> --public --source=. --push

# Option B: Manual
git remote add origin git@github.com:<USERNAME>/<package_name>.git
git push -u origin main
```

If `gh` is not installed:

```bash
sudo dnf install gh

gh auth login
```

## Step 6: Test installation in target project

Conduct a PoC validation to verify the package installs and works correctly from the new repository.

## Step 7: Clean up original location

```bash
rm -rf /path/to/ai_engineering_book/packages/<package_name>
```

## Optional: Tag a release

```bash
cd ~/projects/<package_name>
git tag v0.1.0
git push origin v0.1.0
```

Then install a specific version:

```bash
uv add "<package_name> @ git+https://github.com/<USERNAME>/<package_name>.git@v0.1.0"
```

## Next Steps

- [Transfer the repo to the GitHub organization](/tools/docs/git/transferring_repo_to_github_org.md)
- [Set up GitHub Pages for documentation hosting](/tools/docs/website/01_github_pages_deployment.ipynb) (per {term}`ADR-26022`)
