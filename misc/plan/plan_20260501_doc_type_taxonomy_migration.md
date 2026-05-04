# Document Type Hierarchical Taxonomy Transition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transition document type governance from a flat namespace to a hierarchical `category.subtype` model (e.g., `architecture.analysis` vs `research.analysis`) to resolve semantic collision and centralize type resolution.

**Architecture:**
- **SSoT Resolver:** Centralize all type-to-config mapping in `tools/scripts/paths.py`.
- **Dot-Notation:** Use `category.subtype` in `options.type`.
- **Resolution Flow:** `Frontmatter Type` $\rightarrow$ `paths.resolve_spoke_type()` $\rightarrow$ `Spoke Config Key` $\rightarrow$ `Config Path`.

**Tech Stack:** Python 3.13, JSON, YAML, Regex.

---

### Phase 1: Governance Anchor

**Goal:** Establish a binding decision for the new taxonomy.

- [ ] **Step 1: Create ADR-260XX**
Create a new ADR in `architecture/adr/` that formally accepts the hierarchical taxonomy.
    - **Decision:** Define the mapping (Architecture: adr, analysis, retrospective; Research: source, tutorial, guide, etc.).
    - **Rationale:** Explain the semantic collision between formal evidence and technical research.
    - **Impact:** Update `date` and `version` of the ADR upon acceptance.

---

### Phase 2: Infrastructure Update (`paths.py`)

**Goal:** Create a Single Source of Truth (SSoT) for type resolution to prevent distributed logic debt.

**Files:**
- Modify: `tools/scripts/paths.py`

- [ ] **Step 1: Implement `resolve_spoke_type()`**
Add a function that extracts the subtype from a hierarchical type string.
```python
def resolve_spoke_type(doc_type: str) -> str:
    """
    Resolves a hierarchical doc_type (e.g., 'architecture.analysis') 
    to its spoke config key (e.g., 'analysis').
    """
    return doc_type.split('.')[-1] if '.' in doc_type else doc_type
```

- [ ] **Step 2: Update `get_config_path()`**
Modify `get_config_path` to use `resolve_spoke_type()` before looking up the path. This ensures any script using `paths.py` is immediately compatible with dot-notation.

- [ ] **Step 3: Commit**
```bash
git add tools/scripts/paths.py
git commit -m "refactor: centralize doc-type resolution in paths.py"
```

---

### Phase 3: Validator Alignment

**Goal:** Update all validation scripts to use the new resolver and recognize new type identities.

**Files:**
- Modify: `tools/scripts/check_frontmatter.py`
- Modify: `tools/scripts/check_adr.py`
- Modify: `tools/scripts/check_evidence.py`

- [ ] **Step 1: Update `check_frontmatter.py`**
Replace any local string-splitting logic in `load_config_chain` with a call to `paths.resolve_spoke_type()`.

- [ ] **Step 2: Update `check_adr.py`**
Ensure the script correctly identifies itself as the validator for `architecture.adr`.

- [ ] **Step 3: Update `check_evidence.py`**
Ensure the script correctly handles `architecture.analysis` and `architecture.retrospective`.

- [ ] **Step 4: Commit**
```bash
git add tools/scripts/check_frontmatter.py tools/scripts/check_adr.py tools/scripts/check_evidence.py
git commit -m "fix: align validators with hierarchical taxonomy resolver"
```

---

### Phase 4: Verification (TDD)

**Goal:** Ensure the resolver and validators work correctly before migrating data.

**Files:**
- Modify: `tools/tests/test_check_frontmatter.py`

- [ ] **Step 1: Write tests for hierarchical resolution**
Add test cases for:
    - `architecture.adr` $\rightarrow$ loads `adr.conf.json`
    - `research.guide` $\rightarrow$ loads `guide.conf.json`
    - `legacy_type` (flat) $\rightarrow$ still loads correct config (backward compatibility).

- [ ] **Step 2: Run and Verify**
Run: `uv run pytest tools/tests/test_check_frontmatter.py`
Expected: PASS.

- [ ] **Step 3: Commit**
```bash
git add tools/tests/test_check_frontmatter.py
git commit -m "test: verify hierarchical type resolution and validation"
```

---

### Phase 5: Repository-wide Migration

**Goal:** Atomically update all artifacts to the new taxonomy.

**Files:**
- Create: `tools/scripts/migrate_taxonomy.py`

- [ ] **Step 1: Implement robust migration script**
The script must:
1. Use a hardcoded mapping of `old_type` $\rightarrow$ `new_type`.
2. Only replace `type: <old>` if it occurs within a YAML frontmatter block (start of file).
3. Process both `.md` and `.ipynb` files.

- [ ] **Step 2: Execute migration**
Run: `uv run python tools/scripts/migrate_taxonomy.py`

- [ ] **Step 3: Commit migrated files**
```bash
git add .
git commit -m "chore: migrate all doc types to hierarchical taxonomy"
```

- [ ] **Step 4: Cleanup**
Remove `tools/scripts/migrate_taxonomy.py`.

---

### Phase 6: Final Audit

**Goal:** Zero-regression verification.

- [ ] **Step 1: Run Triple-Check Audit**
Run the following in sequence:
1. `uv run python -m tools.scripts.check_frontmatter`
2. `uv run python -m tools.scripts.check_adr`
3. `uv run python -m tools.scripts.check_evidence`
Expected: All exit 0.

- [ ] **Step 2: Final Commit**
```bash
git commit -m "chore: verify final state of hierarchical taxonomy migration"
```

---

### Self-Review
- **Spec coverage:** Now includes binding governance (ADR) and global infrastructure fix (`paths.py`).
- **SVA Check:** Centralizing the resolver in `paths.py` prevents the "Distributed Resolver Debt" identified during audit.
- **Risk Mitigation:** TDD phase (Phase 4) ensures the "brain" of the system works before we change thousands of lines of metadata.
