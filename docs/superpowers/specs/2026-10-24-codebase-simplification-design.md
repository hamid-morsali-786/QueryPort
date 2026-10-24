# Codebase Simplification & Deduplication Design Spec

**Date:** 2026-10-24  
**Author:** Antigravity (Senior Full-Stack Architect & Lazy Senior Dev Mode)  
**Status:** Approved for Implementation  
**Trigger:** `/ponytail-audit` findings  

---

## 1. Problem Statement & Motivation
Following the `/ponytail-audit` inspection, the QueryPort codebase contains ~730 lines of technical debt and over-engineering across several areas:
1. **Redundant Configurations:** Dual JSON files (`config.json` and `import_config.json`) duplicating database credentials.
2. **Duplicate Core Logic:** `create_connection` and `load_config` are copy-pasted verbatim between `export_sql.py` and `import_sql.py`.
3. **Inefficient Standard Library Hand-rolling:** `clean_cell_value` tests 7 date formats sequentially via `try-except ValueError` instead of using Python 3.11's C-accelerated `datetime.fromisoformat`.
4. **Duplicate File Streaming:** `process_query` repeats row fetching and file writing across 3 separate branches (`both`, `csv`, `insert`).
5. **Duplicate Error Logging:** `import_single_file` repeats CSV rejected-row writer initialization and formatting in two places.
6. **Duplicated Console Prompts:** `interactive_loop` repeats terminal interaction, signal handling, and command dispatching across export and import modes.
7. **Unnecessary Dependencies:** `pytest` in `requirements.txt` when built-in `unittest` executes all 36 tests natively in 0.2s.
8. **Dead Build Flags & Duplicate Production Folder:** Dead `--add-data` flags in PyInstaller and tracked mirror files in `QueryPort_Production/`.

---

## 2. Proposed Architectural Solution

### 2.1 Unified Configuration (`config.json`)
Consolidate to a single `config.json` schema:
```json
{
  "database": {
    "user": "YOUR_DB_USER",
    "password": "YOUR_DB_PASSWORD",
    "host": "localhost",
    "port": 1521,
    "service_name": "ORCLPDB1",
    "schema": "TARGET_SCHEMA"
  },
  "export": {
    "input_path": "test_sql",
    "output_dir": "exports",
    "format": "both",
    "batch_size": 1000
  },
  "import": {
    "input_path": "imports",
    "commit_mode": "batch",
    "batch_size": 5000,
    "existing_data_action": "append",
    "on_error": "abort",
    "bad_rows_dir": "import_errors"
  }
}
```
*Backward Compatibility:*
- If `"defaults"` exists instead of `"export"`, `export_sql` falls back to it.
- If `"import_settings"` exists instead of `"import"`, `import_sql` falls back to it.
- If `--config import_config.json` is passed, it continues to read it cleanly.

### 2.2 Shared Utilities & Deduplication
- `load_config(config_path="config.json") -> dict` and `create_connection(db_config: dict)` remain defined in `export_sql.py` (or shared).
- In `import_sql.py`, import `create_connection` and `load_config` directly from `export_sql`.

### 2.3 Native Stdlib Date Parsing
- In `clean_cell_value(val, col_type)`:
  For date/timestamp fields, use `datetime.datetime.fromisoformat(s)`. If a legacy slash format like `YYYY/MM/DD` is present, normalize slashes to hyphens (`s.replace('/', '-')`) before `fromisoformat`. This eliminates the 7-format `strptime` trial loop.

### 2.4 Unified Streaming in `process_query`
- Replace the three separate branches in `process_query` with a single unified stream loop that writes to CSV if `format_type in ("both", "csv")` and SQL INSERT if `format_type in ("both", "insert")`.

### 2.5 Unified Console Subprompt Runner
- In `export_sql.py`, extract `_run_subprompt(runner_func, prompt_label, default_config_name)` to eliminate ~35 lines of duplicate CLI interaction.

### 2.6 Dependency & Repository Hygiene
- Remove `pytest` from `requirements.txt`.
- Remove dead `--add-data` in `build_exe.bat`.
- Remove duplicate tracked files in `QueryPort_Production/` and add automated packaging script or rule.
