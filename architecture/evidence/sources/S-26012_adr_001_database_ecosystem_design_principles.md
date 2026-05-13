---
title: Database Ecosystem Design Principles
description: Establishes shared design principles and technical contracts for database projects, including standardized connector usage, SQL building, schema definitions, and namespacing.
date: 2026-03-17
tags:
- devops
- architecture
options:
  id: S-26012
  model: human
  extracted_into: null
  type: source
  token_size: 2154
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
---

# Database Ecosystem Design Principles

**Status:** Accepted
**Date:** 2026-03-17
**Scope:** All projects under `/projects/databases/`

---

## Context

Multiple database projects live under this directory (`un_votes`, `ved_db`, `!dmss`, …).
Each project scrapes or loads data from a different domain, stores it in PostgreSQL, and
uses psycopg 3 as the database driver. Without a shared contract, each project diverges:
different SQL-building styles, different logging approaches, different schema formats,
different ways to handle credentials. This ADR establishes the rules that apply to all
projects now and in the future.

---

## Decisions

### 1. Shared database library: `postgres_connector` (PyPI)

All projects MUST use `postgres_connector` as their database access layer.
`postgres_connector` is published to PyPI and added as a standard dependency:

```toml
# pyproject.toml / requirements.txt
postgres_connector = ">=X.Y"
```

**Why PyPI, not git submodule:**
- Works cleanly in `uv` projects and containerised builds (`pip install`)
- No `git submodule update` ceremony; version pinning is explicit
- Submodules require every downstream repo to mirror the submodule history

**What `postgres_connector` provides:**
- `PostgresConnector` — DDL and DML operations (connect, create tables, insert, query)
- `ensure_schema()` — detects first run vs incremental using the DB itself as the source of truth
- `MyQuery` — interactive analysis helper (optional; depends on `pandas`)
- Proper logging via `logging.getLogger(__name__)`

Projects MUST NOT re-implement database access logic locally. A thin project-specific
subclass of `PostgresConnector` is acceptable only when the project genuinely needs
bespoke behaviour that cannot be added to the shared library.

---

### 2. SQL must be built with the psycopg `sql` module — no raw string concatenation

**Rule:** Every SQL statement that contains a variable part (table name, column name,
value, schema name) MUST use psycopg's `sql` module:

| Part type       | Correct wrapper      | Wrong                          |
|-----------------|----------------------|--------------------------------|
| Table/column name | `sql.Identifier(...)` | `f"SELECT {col} FROM {tbl}"`  |
| User-supplied value | `sql.Literal(...)`  | `f"WHERE name = '{val}'"`     |
| SQL keyword/fragment | `sql.SQL(...)`     | bare f-string                  |
| Schema + table  | `sql.Identifier(schema, table)` | `f"{schema}.{table}"` |

**Why:**
psycopg composes the final query server-side. `sql.Identifier` properly double-quotes
identifiers; `sql.Literal` binds values as parameters. Neither can be exploited by
injection even if the input contains quotes, dollar signs, or backslashes.

Raw f-strings in CREATE TABLE or ALTER TABLE are acceptable **only** when every
interpolated value comes exclusively from `schemata.py` (internal, trusted code) and the
column/table name is passed through `sql.Identifier`. Type definitions (e.g.
`"INTEGER REFERENCES title(id) ON DELETE CASCADE"`) are SQL fragments and must be wrapped
in `sql.SQL(...)`, not interpolated as bare strings.

---

### 3. Schema definition format: list of tuples

All projects MUST define their tables as a dict of lists of tuples:

```python
# schemata.py
relations: dict[str, list[tuple[str, str]]] = {
    "table_name": [
        ("column_name",     "SQL_TYPE_DEFINITION"),
        ("another_column",  "TEXT UNIQUE"),
        ("CONSTRAINT_TYPE", "CONSTRAINT_DEFINITION"),   # ← always last
    ],
}
```

**Column entries:** `(name, sql_type)` — `name` is an identifier, passed to
`sql.Identifier(name)` by `postgres_connector`. `sql_type` is a SQL fragment
(e.g. `"INTEGER REFERENCES title(id) ON DELETE CASCADE"`), passed to `sql.SQL(sql_type)`.

**Constraint entry — MANDATORY LAST:** each table's list MUST end with exactly one
constraint entry whose first token is a SQL constraint keyword (`PRIMARY KEY`, `UNIQUE`,
`FOREIGN KEY`, `CHECK`). `postgres_connector` detects this via `_is_constraint()` and
handles it separately from column entries.

```python
# postgres_connector internal helper
_CONSTRAINT_KEYWORDS = frozenset({"PRIMARY", "UNIQUE", "FOREIGN", "CHECK", "EXCLUDE"})

def _is_constraint(attr: str) -> bool:
    return attr.split()[0].upper() in _CONSTRAINT_KEYWORDS
```

**Why tuples, not plain strings:**
Tuples keep the column name and type definition separate so `sql.Identifier(name)` can be
applied to the name without string parsing. Plain strings (`"id SERIAL"`) require splitting
on whitespace to extract the identifier, which is fragile and inconsistent with the
psycopg-API-only rule above.

**`attributes_dict` convention:**
`postgres_connector.create_attributes_dict()` builds `{table: [col_name, ...]}` by
filtering out constraint entries (using `_is_constraint()`). This dict is used by the
pipeline to build INSERT column lists. Do NOT use positional slicing (`[:-1]`) — use the
`_is_constraint()` filter instead.

---

### 4. PostgreSQL schema namespacing

Each project stores its data in a dedicated PostgreSQL schema (namespace), not in
`public`. The schema name is project-specific and set via an environment variable:

```python
# info.py (every project)
import os

schema = os.environ.get("DB_SCHEMA", "project_default")
```

| Project    | Default schema |
|------------|----------------|
| `un_votes` | `un`           |
| `ved_db`   | `ved`          |
| `!dmss`    | `dmss`         |

All table references in SQL use two-part `sql.Identifier(schema, table)`, never
bare table names. This allows cross-schema queries in future without ambiguity:

```python
# Correct
sql.Identifier(schema, "resolution")   # → "un"."resolution"

# Wrong — depends on search_path, breaks in multi-schema queries
sql.Identifier("resolution")           # → "resolution"
```

`postgres_connector` stores the schema on the instance (`self.schema`) and applies it
in every method that generates SQL. The caller passes `schema=info.schema` at
instantiation.

`CREATE SCHEMA IF NOT EXISTS` is called by `ensure_schema()` before any table creation.

---

### 5. Logging: Python standard `logging` module

All modules MUST use:

```python
import logging
logger = logging.getLogger(__name__)
```

**No `print()` for operational output.** `print()` is acceptable only for temporary
debugging that is removed before commit.

Log level conventions:

| Level     | Use for                                                         |
|-----------|-----------------------------------------------------------------|
| `DEBUG`   | SQL query strings, per-row outcomes, verbose trace              |
| `INFO`    | Milestones: connection opened, schema created, table populated  |
| `WARNING` | Unexpected but recoverable state                                |
| `ERROR`   | Failures: row not found, count mismatch, transaction rolled back |

In Scrapy projects, `logging.getLogger(__name__)` integrates with Scrapy's log
infrastructure automatically. Verbosity is controlled by the `LOG_LEVEL` Scrapy setting
or by the standard Python `logging` configuration — no `verbose=True` flags in method
signatures.

---

### 6. No `pexpect` for database CLI commands

`pexpect` was historically used to interactively type passwords for `pg_dump`, `psql`,
`createdb`. This is replaced by the `PGPASSWORD` environment variable:

```bash
PGPASSWORD="$DB_PASSWORD" pg_dump -h "$DB_HOST" -U "$DB_USER" "$DB_NAME" > dump.sql
```

`pexpect` MUST NOT be added to any project's `requirements.txt`. Dump and restore
operations live in `start.sh` (container entrypoint), not in Python code.

---

### 7. Container deployment: ADR-26040

All containerised runs follow ADR-26040 (Podman Kube YAML as deployment standard).
See: `/projects/soviar-systems/ai_engineering_book/architecture/adr/adr_26040_podman_kube_yaml_as_deployment_standard.md`

Key points relevant here:
- One-shot Pod: `restartPolicy: Never`; postgres + spider share a network namespace
- `PGPASSWORD` injected via Pod env; no credentials in images
- `start.sh` entrypoint: wait for postgres → optional restore from dump → crawl → pg_dump
- Periodic runs via `podman-kube@.service` + systemd timer (own server) or GitHub Actions
  cron (public repos, incremental runs ≤ 6 h)

---

## Consequences

- `postgres_connector` must be kept stable and versioned; breaking changes require a
  version bump and updates in all dependent projects
- Every new database project starts by importing `postgres_connector`, creating an
  `info.py` with its own schema name, and writing a `schemata.py` in the tuple format
- Cross-schema queries (e.g. joining `un.resolution` with `ved.entry`) work without
  `search_path` hacks because all references are fully qualified
- `pexpect` and `pandas` are removed from core project requirements; `pandas` remains
  optional in `postgres_connector` for `MyQuery` only
