# Codebase Simplification & Deduplication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor QueryPort according to the `/ponytail-audit` findings by eliminating duplicated code, unifying configurations, replacing hand-rolled loops with Python standard library calls, and removing unneeded dependencies while keeping all 36 tests green.

**Architecture:** Merge dual configurations into a single unified `config.json` schema; share database connection and config loading functions between `export_sql.py` and `import_sql.py`; streamline `process_query` file streaming into a single loop; replace 7-format `strptime` trial loop with stdlib `datetime.fromisoformat`; and clean up repository artifacts and unused dependencies.

**Tech Stack:** Python 3.11+, `oracledb` (Thin Mode), standard library (`unittest`, `csv`, `datetime`, `argparse`, `pathlib`, `shlex`, `json`, `re`).

**Spec:** [docs/superpowers/specs/2026-10-24-codebase-simplification-design.md](docs/superpowers/specs/2026-10-24-codebase-simplification-design.md)

## Global Constraints

- Preserve 100% backward compatibility for existing command-line arguments and configuration keys (`defaults` and `import_settings` fallback).
- Maintain documentation integrity and keep code comments in English.
- No new dependencies added (delete `pytest` dependency; rely strictly on Python's built-in `unittest`).
- Keep all unit tests passing at every task commit.
- Preserve exact whitespace handling in `VARCHAR2` string values.

## Review Focus

- Missing config sections (e.g. `export` or `import` block missing in `config.json`): fallback to legacy `defaults`/`import_settings` or hardcoded defaults gracefully.
- Date parsing with various ISO formats: `YYYY-MM-DD`, `YYYY-MM-DD HH24:MI:SS`, `YYYY/MM/DD`, `YYYY-MM-DD HH24:MI:SS.FF6` must continue parsing accurately with sub-second timestamps.
- Streaming integrity: `both`, `csv`, and `insert` export formats must produce identical byte-for-byte outputs as before (BOM for CSV, `SET DEFINE OFF` and `COMMIT` for INSERT).
- Console interaction: interactive menu choices `[1 / E]` and `[2 / I]` must behave identically.
- Rejection logging: bad rows in `import_sql` must log the exact header, row number, and Oracle error message to `import_errors/<TABLE>_rejected.csv`.

---

### Task 1: Unified Configuration Schema & Resolver Compatibility

**Files:**
- Modify: `config.json`, `config.example.json`
- Delete: `import_config.json`, `import_config.example.json`
- Modify: `export_sql.py:86-100` (`resolve_settings`)
- Modify: `import_sql.py:65-105` (`resolve_import_settings`)
- Test: `test_export_sql.py`, `test_import_sql.py`

**Interfaces:**
- Produces:
  - `export_sql.resolve_settings(cli_args, config_data) -> dict`: checks `config_data.get("export")` then `config_data.get("defaults")`.
  - `import_sql.resolve_import_settings(cli_args, config_data) -> dict`: checks `config_data.get("import")` then `config_data.get("import_settings")`.

- [ ] **Step 1: Write failing test for unified `config.json` reading in `test_export_sql.py` and `test_import_sql.py`**

```python
    def test_resolve_settings_from_unified_export_block(self):
        config_data = {
            "database": {"user": "U", "password": "P"},
            "export": {"input_path": "my_sql", "format": "csv", "batch_size": 2000}
        }
        from export_sql import parse_args, resolve_settings
        args = parse_args([])
        settings = resolve_settings(args, config_data)
        self.assertEqual(settings["input_path"], "my_sql")
        self.assertEqual(settings["format"], "csv")
        self.assertEqual(settings["batch_size"], 2000)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest test_export_sql.py`
Expected: FAIL (falls back to hardcoded default instead of reading `"export"` key)

- [ ] **Step 3: Update `resolve_settings` in `export_sql.py` and `resolve_import_settings` in `import_sql.py`**

Support `"export"` key in `export_sql.py` with fallback to `"defaults"`.
Support `"import"` key in `import_sql.py` with fallback to `"import_settings"`.
Update `config.json` and `config.example.json` with unified `"export"` and `"import"` blocks.
Remove obsolete `import_config.json` and `import_config.example.json`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest discover`
Expected: PASS (all 36 tests green)

- [ ] **Step 5: Commit**

```bash
git add config.json config.example.json export_sql.py import_sql.py test_export_sql.py test_import_sql.py
git rm import_config.json import_config.example.json
git commit -m "refactor(config): unify export and import configuration into single config.json schema"
```

---

### Task 2: Deduplicate Connection Creation & Config Loading

**Files:**
- Modify: `import_sql.py:18-31`, `import_sql.py:288-308`
- Modify: `export_sql.py:18-32`
- Test: `test_import_sql.py`

**Interfaces:**
- `export_sql.py`:
  - `load_config(config_path: str = "config.json") -> dict`
  - `create_connection(db_config: dict) -> oracledb.Connection`
- `import_sql.py`:
  - Imports `load_config` and `create_connection` from `export_sql`.
  - Aliases `load_import_config = load_config` and `create_import_connection = create_connection` for backward compatibility.

- [ ] **Step 1: Write test ensuring `load_import_config` and `create_import_connection` maintain identical behavior**

Run: `python -m unittest test_import_sql.py`

- [ ] **Step 2: Remove duplicated function bodies in `import_sql.py`**

Replace `load_import_config` and `create_import_connection` in `import_sql.py` with direct imports and aliases from `export_sql.py`.

- [ ] **Step 3: Run all unit tests**

Run: `python -m unittest discover`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add import_sql.py export_sql.py
git commit -m "refactor(core): deduplicate connection creation and config loader across modules"
```

---

### Task 3: Fast Native Stdlib Date Parsing in `clean_cell_value`

**Files:**
- Modify: `import_sql.py:115-142` (`clean_cell_value`)
- Test: `test_import_sql.py`

**Interfaces:**
- `clean_cell_value(val: str, col_type: str | None = None) -> Any`

- [ ] **Step 1: Add unit tests for edge-case date strings (slashed dates, ISO timestamps, subseconds)**

```python
    def test_clean_cell_value_iso_and_slashed_dates(self):
        from import_sql import clean_cell_value
        import datetime
        dt1 = clean_cell_value("2026-10-24 12:30:00", col_type="DATE")
        self.assertEqual(dt1, datetime.datetime(2026, 10, 24, 12, 30, 0))
        dt2 = clean_cell_value("2026/10/24 12:30:00", col_type="DATE")
        self.assertEqual(dt2, datetime.datetime(2026, 10, 24, 12, 30, 0))
        dt3 = clean_cell_value("2026/10/24", col_type="DATE")
        self.assertEqual(dt3, datetime.datetime(2026, 10, 24, 0, 0, 0))
```

- [ ] **Step 2: Run test to verify it passes with current implementation**

Run: `python -m unittest test_import_sql.py`
Expected: PASS

- [ ] **Step 3: Replace 7-format `strptime` trial loop with stdlib `datetime.fromisoformat`**

```python
    if col_type:
        upper_type = col_type.upper()
        if "DATE" in upper_type or "TIMESTAMP" in upper_type:
            s = val.strip().replace("/", "-")
            try:
                return datetime.datetime.fromisoformat(s)
            except ValueError:
                return val.strip()
        if "NUMBER" in upper_type or "FLOAT" in upper_type:
            return val.strip()
```

- [ ] **Step 4: Run test suite to verify all date formats pass**

Run: `python -m unittest test_import_sql.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add import_sql.py test_import_sql.py
git commit -m "perf(import): replace 7-format strptime trial loop with stdlib datetime.fromisoformat"
```

---

### Task 4: Streamline `process_query` File Writing & Streaming

**Files:**
- Modify: `export_sql.py:226-277` (`process_query`)
- Test: `test_export_sql.py`

**Interfaces:**
- `process_query(cursor, query_info: tuple[int, str, str], format_type: str, target_dir: Path, batch_size: int = 1000) -> int`

- [ ] **Step 1: Verify existing test coverage for all format types (`both`, `csv`, `insert`)**

Run: `python -m unittest test_export_sql.py`
Expected: PASS

- [ ] **Step 2: Refactor `process_query` to use a single unified fetch loop**

Open files conditionally:
- If `format_type in ("both", "csv")`: open `csv_path` with `utf-8-sig`.
- If `format_type in ("both", "insert")`: open `sql_path` with `utf-8`.
Stream rows once with `cursor.fetchmany(batch_size)`, writing to open handles simultaneously.
Delete nested redundant `row_stream()` generators and duplicate looping logic (~30 lines saved).

- [ ] **Step 3: Run tests to verify all formats produce identical output**

Run: `python -m unittest test_export_sql.py`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add export_sql.py
git commit -m "refactor(export): consolidate format handling into unified streaming loop"
```

---

### Task 5: Deduplicate Rejected-Row Error Logging in `import_single_file`

**Files:**
- Modify: `import_sql.py:340-405` (`import_single_file`)
- Test: `test_import_sql.py`

**Interfaces:**
- `import_single_file(conn, file_path: Path, table_name: str, table_meta: dict, settings: dict) -> dict`

- [ ] **Step 1: Check existing test for fallback logging (`test_import_single_file_skip_and_log_fallback`)**

Run: `python -m unittest test_import_sql.TestImportConfigAndArgs.test_import_single_file_skip_and_log_fallback`
Expected: PASS

- [ ] **Step 2: Extract an inline helper closure `log_bad_row(row_idx, exc, raw_row)` in `import_single_file`**

Centralize `bad_writer` initialization and row formatting in a single local closure instead of duplicating 8 lines in two branches.

- [ ] **Step 3: Run tests to verify error logging remains identical**

Run: `python -m unittest test_import_sql.py`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add import_sql.py
git commit -m "refactor(import): deduplicate bad-row CSV logger in import_single_file"
```

---

### Task 6: Deduplicate Interactive Console Subprompt Loops

**Files:**
- Modify: `export_sql.py:444-531` (`interactive_loop`)
- Test: `test_export_sql.py`

**Interfaces:**
- `interactive_loop()`
- Helper: `_run_subprompt(runner_func, prompt_label: str, config_name: str)`

- [ ] **Step 1: Check interactive loop unit tests in `test_export_sql.py`**

Run: `python -m unittest test_export_sql.TestOrchestrator.test_interactive_loop_default_yes test_export_sql.TestOrchestrator.test_interactive_loop_import_choice`
Expected: PASS

- [ ] **Step 2: Extract `_run_subprompt` helper in `export_sql.py`**

Replace the two 30-line duplicate prompt loops (for export and import) with a single parameterized function taking the runner callable (`main` or `import_sql.main`), prompt label, and config name.

- [ ] **Step 3: Run tests to ensure console behavior is preserved**

Run: `python -m unittest test_export_sql.py`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add export_sql.py
git commit -m "refactor(cli): deduplicate interactive subprompt loop across modes"
```

---

### Task 7: Repository Hygiene & Packaging Cleanup

**Files:**
- Modify: `requirements.txt` (remove `pytest`)
- Modify: `build_exe.bat` (remove dead `--add-data` flags for configs)
- Delete: `QueryPort_Production/` tracked folder
- Modify: `.gitignore` (ignore `QueryPort_Production/` as build output)
- Modify: `README.md`, `README.en.md`, `README.txt` (update config references to single unified `config.json`)

- [ ] **Step 1: Remove `pytest` from `requirements.txt`**

Keep only `oracledb>=2.0.0` and `pyinstaller>=6.0.0`.

- [ ] **Step 2: Clean `build_exe.bat` dead flags**

Remove `--add-data "config.json;."` and `--add-data "import_config.json;."`.

- [ ] **Step 3: Untrack `QueryPort_Production/` and add it to `.gitignore`**

Run: `git rm -r --cached QueryPort_Production`
Add `QueryPort_Production/` to `.gitignore`.

- [ ] **Step 4: Update Documentation with single unified `config.json`**

Update `README.md`, `README.en.md`, and `README.txt` to showcase the unified configuration file.

- [ ] **Step 5: Run full test suite using native `unittest`**

Run: `python -m unittest discover`
Expected: PASS (all 36 tests green)

- [ ] **Step 6: Commit**

```bash
git add requirements.txt build_exe.bat .gitignore README.md README.en.md README.txt
git commit -m "chore: remove pytest dependency, clean dead pyinstaller flags, and untrack production mirror"
```

---

### Task 8: Full Verification, PyInstaller Build & Git Push

**Files:**
- Run: `build_exe.bat`
- Test: `QueryPort.exe --mode export --dry-run` and `QueryPort.exe import --dry-run`
- Push: `origin main`

- [ ] **Step 1: Run full unit test suite**

Run: `python -m unittest discover -v`
Expected: 36 tests pass in < 0.3s.

- [ ] **Step 2: Rebuild standalone `QueryPort.exe`**

Run PyInstaller build to produce updated binary.

- [ ] **Step 3: Verify binary runs both export and import dry-runs**

Run:
`.\dist\QueryPort.exe --mode export --dry-run`
`.\dist\QueryPort.exe import --dry-run`
Expected: Both exit 0 with clean reports.

- [ ] **Step 4: Push to GitHub**

```bash
git push origin main
```
