# Oracle CSV Data Importer Subsystem Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Oracle CSV Data Import Subsystem for QueryPort, enabling validated, chunked streaming ingestion of CSV datasets into Oracle Database tables with pre-execution schema checks, flexible commit modes, and unified CLI integration.

**Architecture:** A standalone, highly cohesive module `import_sql.py` handles configuration, data dictionary pre-validation via `ALL_TAB_COLS`, streaming CSV generation, and bulk insertion with `executemany`. `export_sql.py` acts as a unified orchestrator routing `--mode import` and providing an upgraded dual-mode interactive console.

**Tech Stack:** Python 3.11+, `oracledb` (Thin Mode), standard library (`csv`, `argparse`, `json`, `datetime`, `pathlib`), `pytest` / `unittest`.

**Spec:** `docs/superpowers/specs/2026-10-21-sql-oracle-importer-design.md`

## Global Constraints
- Thin Mode direct TCP connection via `oracledb` (zero Oracle Instant Client dependency).
- Constant memory streaming $O(1)$ when reading large CSV files (e.g. `04_CALENDER.csv` 82MB).
- Unicode preservation: CSV reader must handle `utf-8-sig` with BOM.
- Pre-validation must strictly abort before any table truncation or insertion if schema discrepancies exist.
- Minimal dependencies: reuse existing installed packages (`oracledb`, `pytest`).

## Review Focus
1. Multi-folder traversal with arbitrarily nested subdirectories in `imports/`.
2. CSV column header matching case-insensitively with Oracle column names.
3. Tables with existing data when `existing_data_action` is `truncate`, `append`, or `skip`.
4. Empty strings `""` in CSV properly converting to `None` (Oracle `NULL`).
5. Batches failing in `cursor.executemany` during `skip_and_log` falling back cleanly to row-by-row logging.

---

### Task 1: Configuration & CLI Parsing (`import_config.json` & `import_sql.py`)

**Files:**
- Create: `import_config.json`
- Create: `import_config.example.json`
- Create: `import_sql.py`
- Test: `test_import_sql.py`

**Interfaces:**
- Produces:
  - `load_import_config(path: str = "import_config.json") -> dict`
  - `parse_import_args(argv: list[str] | None = None) -> argparse.Namespace`
  - `resolve_import_settings(cli_args: argparse.Namespace, config_data: dict) -> dict`

- [ ] **Step 1: Write failing tests for import configuration loading and CLI override**

```python
# test_import_sql.py
import unittest
import tempfile
import json
from pathlib import Path
from import_sql import load_import_config, parse_import_args, resolve_import_settings

class TestImportConfigAndArgs(unittest.TestCase):
    def test_load_import_config_defaults(self):
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json") as f:
            json.dump({
                "database": {"user": "APP_USER", "password": "pwd", "host": "127.0.0.1", "port": 1521, "service_name": "XE", "schema": "CORE"},
                "import_settings": {"input_path": "imports", "commit_mode": "batch", "batch_size": 5000, "existing_data_action": "append", "on_error": "abort"}
            }, f)
            cfg_path = f.name
        
        cfg = load_import_config(cfg_path)
        self.assertEqual(cfg["database"]["user"], "APP_USER")
        self.assertEqual(cfg["import_settings"]["commit_mode"], "batch")
        
        args = parse_import_args(["--commit-mode", "all", "--batch-size", "2000", "--existing-data", "truncate", "--on-error", "skip_and_log", "--schema", "CUSTOM_SCHEMA"])
        settings = resolve_import_settings(args, cfg)
        self.assertEqual(settings["commit_mode"], "all")
        self.assertEqual(settings["batch_size"], 2000)
        self.assertEqual(settings["existing_data_action"], "truncate")
        self.assertEqual(settings["on_error"], "skip_and_log")
        self.assertEqual(settings["database"]["schema"], "CUSTOM_SCHEMA")
        Path(cfg_path).unlink(missing_ok=True)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest test_import_sql.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'import_sql'`

- [ ] **Step 3: Implement `import_config.json`, `import_config.example.json`, and config/args parsing in `import_sql.py`**

Create `import_config.example.json` with standard schema and `import_config.json` with local defaults.
In `import_sql.py`:
Implement `load_import_config(path: str = "import_config.json") -> dict`, `parse_import_args(argv: list[str] | None = None) -> argparse.Namespace`, and `resolve_import_settings(cli_args, config_data) -> dict`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest test_import_sql.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add import_config.json import_config.example.json import_sql.py test_import_sql.py
git commit -m "feat(import): add configuration schema and CLI argument parsing"
```

---

### Task 2: File Discovery, Table Resolution & Data Cleaning Generator

**Files:**
- Modify: `import_sql.py`
- Test: `test_import_sql.py`

**Interfaces:**
- Produces:
  - `discover_import_files(input_path: Path) -> list[tuple[Path, str]]` (returns `(file_path, table_name)`)
  - `extract_table_name(file_name: str) -> str`
  - `stream_csv_batches(file_path: Path, batch_size: int) -> Generator[tuple[list[str], list[list[Any]]]]`
  - `clean_cell_value(val: str, col_type: str | None = None) -> Any`

- [ ] **Step 1: Write failing tests for table extraction, discovery and data cleaning**

```python
    def test_extract_table_name(self):
        from import_sql import extract_table_name
        self.assertEqual(extract_table_name("02_BANKPARAMETERS.csv"), "BANKPARAMETERS")
        self.assertEqual(extract_table_name("04_CALENDER.csv"), "CALENDER")
        self.assertEqual(extract_table_name("CUSTOMERS.csv"), "CUSTOMERS")
        self.assertEqual(extract_table_name("01_SUB_SYS_TABLE.CSV"), "SUB_SYS_TABLE")

    def test_clean_cell_value(self):
        from import_sql import clean_cell_value
        import datetime
        # Empty strings become None (NULL)
        self.assertIsNone(clean_cell_value(""))
        self.assertIsNone(clean_cell_value("   "))
        # Standard strings preserved
        self.assertEqual(clean_cell_value("IRR"), "IRR")
        # Dates converted
        dt = clean_cell_value("1995-01-01 00:00:00", col_type="DATE")
        self.assertEqual(dt, datetime.datetime(1995, 1, 1, 0, 0, 0))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest test_import_sql.py`
Expected: FAIL with `ImportError: cannot import name 'extract_table_name'`

- [ ] **Step 3: Implement discovery, table extraction, and data cleaning in `import_sql.py`**

Implement regex matching for table names, file discovery walking subdirectories recursively and sorting by file path, and `stream_csv_batches` using `csv.reader` with `utf-8-sig`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest test_import_sql.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add import_sql.py test_import_sql.py
git commit -m "feat(import): add file discovery, table extraction, and streaming csv generator"
```

---

### Task 3: Oracle Data Dictionary Pre-Validation Engine

**Files:**
- Modify: `import_sql.py`
- Test: `test_import_sql.py`

**Interfaces:**
- Produces:
  - `fetch_schema_metadata(conn, target_schema: str) -> dict[str, dict[str, dict]]`
    Returns `{TABLE_NAME: {COLUMN_NAME: {"data_type": str, "nullable": str, "data_default": str|None}}}`
  - `validate_import_plan(schema_metadata: dict, file_plan: list[tuple[Path, str]]) -> list[dict]`
    Returns list of validation error dictionaries: `{"file": str, "table": str, "error_type": str, "details": str}`
  - `format_validation_report(errors: list[dict]) -> str`

- [ ] **Step 1: Write failing tests for pre-validation rules**

```python
    def test_pre_validation_table_missing(self):
        from import_sql import validate_import_plan
        schema_metadata = {"EXISTING_TABLE": {"COL1": {"nullable": "Y", "data_default": None}}}
        file_plan = [(Path("01_NON_EXISTENT.csv"), "NON_EXISTENT")]
        errors = validate_import_plan(schema_metadata, file_plan)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["error_type"], "MISSING_TABLE")

    def test_pre_validation_missing_mandatory_not_null_column(self):
        from import_sql import validate_import_plan
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".csv", encoding="utf-8") as f:
            f.write("COL1,COL2\nval1,val2\n")
            f_path = Path(f.name)
        schema_metadata = {
            "MY_TABLE": {
                "COL1": {"nullable": "Y", "data_default": None},
                "COL2": {"nullable": "Y", "data_default": None},
                "MANDATORY_COL": {"nullable": "N", "data_default": None}  # Missing & No Default!
            }
        }
        errors = validate_import_plan(schema_metadata, [(f_path, "MY_TABLE")])
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["error_type"], "MISSING_MANDATORY_COLUMN")
        f_path.unlink(missing_ok=True)

    def test_pre_validation_not_null_with_default_passes(self):
        from import_sql import validate_import_plan
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".csv", encoding="utf-8") as f:
            f.write("COL1\nval1\n")
            f_path = Path(f.name)
        schema_metadata = {
            "MY_TABLE": {
                "COL1": {"nullable": "Y", "data_default": None},
                "CREATED_AT": {"nullable": "N", "data_default": "SYSDATE"}  # Not in CSV, but has DEFAULT!
            }
        }
        errors = validate_import_plan(schema_metadata, [(f_path, "MY_TABLE")])
        self.assertEqual(len(errors), 0)  # Passes!
        f_path.unlink(missing_ok=True)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest test_import_sql.py`
Expected: FAIL with `ImportError: cannot import name 'validate_import_plan'`

- [ ] **Step 3: Implement metadata fetching and validation in `import_sql.py`**

Implement `fetch_schema_metadata`, `validate_import_plan`, and `format_validation_report`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest test_import_sql.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add import_sql.py test_import_sql.py
git commit -m "feat(import): implement data dictionary pre-validation engine"
```

---

### Task 4: Ingestion Execution Engine with Commit Modes & Error Logging

**Files:**
- Modify: `import_sql.py`
- Test: `test_import_sql.py`

**Interfaces:**
- Produces:
  - `import_single_file(conn, file_path: Path, table_name: str, table_meta: dict, settings: dict) -> dict`
  - `run_import(settings: dict) -> int` (main execution coordinator)

- [ ] **Step 1: Write failing tests for ingestion with commit modes, truncate, and error logging**

```python
    def test_import_single_file_batch_commit(self):
        from unittest.mock import MagicMock
        from import_sql import import_single_file
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".csv", encoding="utf-8") as f:
            f.write("ID,NAME\n1,Alice\n2,Bob\n")
            csv_path = Path(f.name)
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        table_meta = {"ID": {"data_type": "NUMBER"}, "NAME": {"data_type": "VARCHAR2"}}
        settings = {
            "commit_mode": "batch",
            "batch_size": 1,
            "existing_data_action": "append",
            "on_error": "abort",
            "bad_rows_dir": "errors"
        }
        res = import_single_file(mock_conn, csv_path, "TEST_TABLE", table_meta, settings)
        self.assertEqual(res["imported"], 2)
        self.assertEqual(mock_conn.commit.call_count, 2)  # batch size 1 with 2 rows = 2 commits
        csv_path.unlink(missing_ok=True)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest test_import_sql.py`
Expected: FAIL with `ImportError: cannot import name 'import_single_file'`

- [ ] **Step 3: Implement `import_single_file` and `run_import` in `import_sql.py`**

Implement parameterized `INSERT INTO ... VALUES (:1, :2, ...)`, `cursor.executemany`, commit modes (`batch`, `row`, `all`), existing data actions (`append`, `truncate`, `skip`), error logging for `skip_and_log`, and summary reporting.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest test_import_sql.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add import_sql.py test_import_sql.py
git commit -m "feat(import): implement bulk insertion, commit modes, and error logging"
```

---

### Task 5: Unified CLI Routing & Interactive Console Mode

**Files:**
- Modify: `export_sql.py`
- Test: `test_export_sql.py`

**Interfaces:**
- Updates `export_sql.py` to:
  - Route `--mode import` or subcommand `import` to `import_sql.main()`.
  - Present unified dual-mode interactive prompt `[1 / E] Export`, `[2 / I] Import`.

- [ ] **Step 1: Write failing test in `test_export_sql.py` for mode routing**

```python
    def test_mode_routing_import(self):
        from unittest.mock import patch
        import export_sql
        with patch("import_sql.main") as mock_import_main:
            export_sql.main(["--mode", "import", "--dry-run"])
            mock_import_main.assert_called_once_with(["--dry-run"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest test_export_sql.py`
Expected: FAIL with unrecognized arguments or lack of routing

- [ ] **Step 3: Implement mode routing and unified interactive console in `export_sql.py`**

Update `parse_args` and `main` in `export_sql.py` to intercept `--mode import` or `import` as first positional arg, and upgrade `interactive_loop()` with dual choices.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest test_export_sql.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add export_sql.py test_export_sql.py
git commit -m "feat(cli): add unified import/export mode routing and interactive console"
```

---

### Task 6: Documentation, Production Sync & PyInstaller Build Verification

**Files:**
- Modify: `README.md`, `README.en.md`, `README.txt`
- Modify: `QueryPort_Production/`
- Run: `pyinstaller` build to produce updated `QueryPort.exe`

- [ ] **Step 1: Update `README.md`, `README.en.md`, and `README.txt`**
Add import commands, parameters table, config guide, and validation descriptions.

- [ ] **Step 2: Copy `import_config.json`, `import_config.example.json`, and updated docs to `QueryPort_Production/`**

- [ ] **Step 3: Rebuild `QueryPort.exe` using `build_exe.bat`**
Bundle with `--collect-all oracledb --collect-all cryptography --add-data "config.json;." --add-data "import_config.json;."`.

- [ ] **Step 4: Run full verification test suite**
Run `pytest -v` and test `QueryPort.exe --mode import --dry-run` against local Oracle database.

- [ ] **Step 5: Commit and push to GitHub**

```bash
git add .
git commit -m "docs & build: update documentation and rebuild standalone QueryPort binary with import feature"
git push origin main
```
