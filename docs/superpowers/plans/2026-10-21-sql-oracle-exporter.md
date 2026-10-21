# SQL Oracle Exporter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a minimal Python utility (`export_sql.py`) that parses `.sql` files, executes `SELECT` statements on an Oracle database, and exports results into dedicated per-file subfolders as CSV and/or SQL INSERT statements.

**Architecture:** A single-file core CLI script (`export_sql.py`) utilizing standard Python 3.11 libraries alongside `oracledb` Thin mode. Modules within the file cover configuration loading, SQL parsing/table extraction, database streaming execution, and CSV/INSERT formatters.

**Tech Stack:** Python 3.11, `oracledb` 3.4.2 (Thin mode), standard libraries (`json`, `csv`, `argparse`, `pathlib`, `re`, `datetime`).

**Spec:** [`docs/superpowers/specs/2026-10-21-sql-oracle-exporter-design.md`](file:///e:/project/QueryPort/docs/superpowers/specs/2026-10-21-sql-oracle-exporter-design.md)

## Global Constraints
- Target platform: Windows (PowerShell / CMD), Python 3.11.
- No Oracle Instant Client binary dependencies; `oracledb` must run in Thin Mode.
- CSV encoding must strictly be `utf-8-sig` (Excel BOM compatible).
- INSERT statements must format strings with doubled single-quotes (`''`), nulls as `NULL`, and dates/timestamps using Oracle `TO_DATE` / `TO_TIMESTAMP`.
- Output directory structure must generate a subfolder named after the `.sql` file stem.
- Query outputs inside each subfolder must be prefixed with a 2-digit index and resolved table name (e.g., `01_BANKPARAMETERS.csv`).

## Review Focus
1. SQL files with `PROMPT`, `SET`, `SPOOL`, or multiline comments before or inside queries must not cause syntax errors.
2. Values containing single quotes (`'`) or ampersands (`&`) must be properly escaped (`''`) and preceded by `SET DEFINE OFF;`.
3. Queries with schema prefixes (e.g. `TARGET_SCHEMA.BANKPARAMETERS`) must extract the clean table name (`BANKPARAMETERS`).
4. `DATE` and `TIMESTAMP` column values from `oracledb` must convert to valid Oracle expressions without time truncation.
5. Large queries must stream via `fetchmany` rather than fetching all rows at once into memory.

---

### Task 1: Configuration & CLI Argument Handling

**Files:**
- Create: `config.json`
- Create: `export_sql.py`
- Create: `test_export_sql.py`

**Interfaces:**
- Produces:
  - `load_config(config_path: str = "config.json") -> dict`
  - `parse_args(args: list[str] | None = None) -> argparse.Namespace`
  - `resolve_settings(cli_args: argparse.Namespace, config_data: dict) -> dict`

- [ ] **Step 1: Write the failing test for configuration and argument resolution**

```python
# test_export_sql.py
import unittest
import json
import tempfile
from pathlib import Path
from export_sql import load_config, parse_args, resolve_settings

class TestConfigAndArgs(unittest.TestCase):
    def test_load_config_and_defaults(self):
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json") as f:
            json.dump({
                "database": {"user": "TEST_USER", "password": "pwd", "host": "127.0.0.1", "port": 1521, "service_name": "XE"},
                "defaults": {"input_path": "sql_dir", "output_dir": "out_dir", "format": "both", "batch_size": 500}
            }, f)
            config_file = f.name
        
        cfg = load_config(config_file)
        self.assertEqual(cfg["database"]["user"], "TEST_USER")
        self.assertEqual(cfg["defaults"]["format"], "both")
        
        args = parse_args(["--path", "custom.sql", "--format", "csv"])
        settings = resolve_settings(args, cfg)
        self.assertEqual(settings["input_path"], "custom.sql")
        self.assertEqual(settings["format"], "csv")
        self.assertEqual(settings["output_dir"], "out_dir")
        Path(config_file).unlink(missing_ok=True)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest test_export_sql.TestConfigAndArgs -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'export_sql'`

- [ ] **Step 3: Create `config.json` and implement `load_config`, `parse_args`, `resolve_settings` in `export_sql.py`**

Create `config.json` with sample connection parameters and defaults.
Implement functions in `export_sql.py` using `json` and `argparse`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest test_export_sql.TestConfigAndArgs -v`
Expected: PASS

---

### Task 2: SQL Parsing & Query/Table Extraction

**Files:**
- Modify: `export_sql.py`
- Modify: `test_export_sql.py`

**Interfaces:**
- Consumes: Raw SQL file contents
- Produces:
  - `clean_sql_script(sql_content: str) -> str`
  - `extract_queries(sql_content: str) -> list[tuple[int, str, str]]`
    (Returns a list of `(query_index, table_name, query_text)`)

- [ ] **Step 1: Write failing tests for SQL parsing and table name resolution**

```python
# in test_export_sql.py
class TestSqlParser(unittest.TestCase):
    def test_extract_queries_with_comments_and_prompts(self):
        from export_sql import extract_queries
        sample_sql = """
        -- Category comment
        PROMPT Starting export...
        SET SQLFORMAT INSERT;
        /* multi-line
           comment block */
        SELECT * FROM TARGET_SCHEMA.BANKPARAMETERS ORDER BY BANK;
        
        PROMPT Next table
        SELECT ID, NAME FROM BRANCHPARAMETERS WHERE ACTIVE = 1;
        """
        queries = extract_queries(sample_sql)
        self.assertEqual(len(queries), 2)
        idx1, table1, sql1 = queries[0]
        self.assertEqual(idx1, 1)
        self.assertEqual(table1, "BANKPARAMETERS")
        self.assertIn("SELECT * FROM TARGET_SCHEMA.BANKPARAMETERS", sql1)
        
        idx2, table2, sql2 = queries[1]
        self.assertEqual(idx2, 2)
        self.assertEqual(table2, "BRANCHPARAMETERS")
        self.assertIn("SELECT ID, NAME FROM BRANCHPARAMETERS", sql2)

    def test_extract_queries_from_real_file(self):
        from export_sql import extract_queries
        real_file = Path("Basic_Information_Tables/01_SYSTEM_AND_BRANCH_PARAMETERS.sql")
        if real_file.exists():
            content = real_file.read_text(encoding="utf-8")
            queries = extract_queries(content)
            # Expect queries for BANKPARAMETERS, BRANCHPARAMETERS, CALENDER (and pre-export verify)
            tables = [q[1] for q in queries]
            self.assertIn("BANKPARAMETERS", tables)
            self.assertIn("BRANCHPARAMETERS", tables)
            self.assertIn("CALENDER", tables)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest test_export_sql.TestSqlParser -v`
Expected: FAIL with `ImportError: cannot import name 'extract_queries' from 'export_sql'`

- [ ] **Step 3: Implement `clean_sql_script` and `extract_queries` in `export_sql.py`**

- Use regex to strip block comments `/\*.*?\*/` and line comments `--.*$`.
- Filter out lines starting with `PROMPT`, `SET`, `SPOOL`.
- Split statements by `;`.
- Check if statement starts with `SELECT` or `WITH`.
- Extract table name from `FROM\s+([a-zA-Z0-9_$.]+)` and strip any schema prefix.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest test_export_sql.TestSqlParser -v`
Expected: PASS

---

### Task 3: Exporters (CSV & INSERT Generators)

**Files:**
- Modify: `export_sql.py`
- Modify: `test_export_sql.py`

**Interfaces:**
- Produces:
  - `format_oracle_literal(value: any) -> str`
  - `export_to_csv(rows_generator, columns: list[str], output_path: Path) -> int`
  - `export_to_insert(rows_generator, columns: list[str], table_name: str, output_path: Path) -> int`

- [ ] **Step 1: Write failing tests for literal formatting, CSV writing, and INSERT generation**

```python
# in test_export_sql.py
import datetime
from export_sql import format_oracle_literal, export_to_csv, export_to_insert

class TestExporters(unittest.TestCase):
    def test_format_oracle_literal(self):
        self.assertEqual(format_oracle_literal(None), "NULL")
        self.assertEqual(format_oracle_literal(123), "123")
        self.assertEqual(format_oracle_literal(45.67), "45.67")
        self.assertEqual(format_oracle_literal("Hello"), "'Hello'")
        self.assertEqual(format_oracle_literal("It's fine"), "'It''s fine'")
        d = datetime.date(2026, 10, 21)
        self.assertEqual(format_oracle_literal(d), "TO_DATE('2026-10-21', 'YYYY-MM-DD')")
        dt = datetime.datetime(2026, 10, 21, 14, 30, 0)
        self.assertEqual(format_oracle_literal(dt), "TO_TIMESTAMP('2026-10-21 14:30:00', 'YYYY-MM-DD HH24:MI:SS')")

    def test_csv_export_with_bom(self):
        cols = ["ID", "TITLE"]
        rows = [[1, "پارامتر یک"], [2, "Test, with comma"]]
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "test.csv"
            count = export_to_csv(iter(rows), cols, out_file)
            self.assertEqual(count, 2)
            content_bytes = out_file.read_bytes()
            # UTF-8 BOM check
            self.assertTrue(content_bytes.startswith(b'\xef\xbb\xbf'))
            text = content_bytes.decode('utf-8-sig')
            self.assertIn("پارامتر یک", text)

    def test_insert_export_format(self):
        cols = ["ID", "CODE", "TITLE"]
        rows = [[1, "B01", "بانک 'ملی'"]]
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "test_insert.sql"
            count = export_to_insert(iter(rows), cols, "BANKPARAMETERS", out_file)
            self.assertEqual(count, 1)
            text = out_file.read_text(encoding="utf-8")
            self.assertIn("SET DEFINE OFF;", text)
            self.assertIn("INSERT INTO BANKPARAMETERS (ID, CODE, TITLE) VALUES (1, 'B01', 'بانک ''ملی''');", text)
            self.assertIn("COMMIT;", text)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest test_export_sql.TestExporters -v`
Expected: FAIL with `ImportError: cannot import name 'format_oracle_literal' from 'export_sql'`

- [ ] **Step 3: Implement `format_oracle_literal`, `export_to_csv`, and `export_to_insert` in `export_sql.py`**

- `format_oracle_literal`: handle None, int/float, datetime/date, strings (double single quotes).
- `export_to_csv`: open file with `encoding="utf-8-sig"`, write header, stream rows using `csv.writer(..., quoting=csv.QUOTE_MINIMAL)`.
- `export_to_insert`: write `SET DEFINE OFF;`, construct formatted `INSERT INTO ... VALUES (...)` statements, append `COMMIT;`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest test_export_sql.TestExporters -v`
Expected: PASS

---

### Task 4: Oracle Execution & End-to-End Orchestrator

**Files:**
- Modify: `export_sql.py`
- Modify: `test_export_sql.py`

**Interfaces:**
- Produces:
  - `create_connection(db_config: dict)`
  - `process_query(cursor, query_info: tuple, format_type: str, target_dir: Path, batch_size: int = 1000)`
  - `process_sql_file(file_path: Path, conn, output_root: Path, format_type: str, batch_size: int = 1000)`
  - `main(argv=None)`

- [ ] **Step 1: Write integration tests with a mock cursor/connection**

```python
# in test_export_sql.py
from unittest.mock import MagicMock
from export_sql import process_query, process_sql_file

class TestOrchestrator(unittest.TestCase):
    def test_process_query_creates_outputs(self):
        mock_cursor = MagicMock()
        mock_cursor.description = [("COL1",), ("COL2",)]
        mock_cursor.fetchmany.side_effect = [[[10, "Val1"], [20, "Val2"]], []]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir)
            query_info = (1, "MY_TABLE", "SELECT COL1, COL2 FROM MY_TABLE")
            
            process_query(mock_cursor, query_info, "both", target_dir, batch_size=100)
            
            csv_path = target_dir / "01_MY_TABLE.csv"
            sql_path = target_dir / "01_MY_TABLE_insert.sql"
            self.assertTrue(csv_path.exists())
            self.assertTrue(sql_path.exists())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest test_export_sql.TestOrchestrator -v`
Expected: FAIL with `ImportError: cannot import name 'process_query' from 'export_sql'`

- [ ] **Step 3: Implement `create_connection`, `process_query`, `process_sql_file`, and `main()` in `export_sql.py`**

- Connect to Oracle using `oracledb.connect(user=..., password=..., host=..., port=..., service_name=...)` with error trapping.
- For each `.sql` file:
  - Create directory `<output_dir>/<file_stem>/`.
  - Extract queries. If none, skip directory.
  - Execute each query, fetch in batches, write to CSV and/or INSERT files based on `format_type`.
  - Gracefully catch query execution errors without breaking the rest of the batch.
- Provide clean CLI progress output in terminal.

- [ ] **Step 4: Run all unit tests to verify full test suite passes**

Run: `python -m unittest discover -v`
Expected: ALL PASS

- [ ] **Step 5: Verify CLI help and dry execution**

Run: `python export_sql.py --help`
Expected: Clean help message showing flags `--path`, `--format`, `--config`, `--output`.
