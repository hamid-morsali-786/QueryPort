# Technical Specification: SQL Oracle Exporter

- **Date:** 2026-10-21
- **Status:** Approved / Ready for Implementation
- **Component:** `export_sql.py` (CLI Database Migration & Export Utility)

---

## 1. Overview & Objectives

The goal is to build a minimal, high-efficiency Python CLI utility that reads `.sql` script files, extracts individual `SELECT` queries, executes them against an Oracle Database using `oracledb` Thin mode, and exports results into organized folders per SQL file in user-selected formats: CSV and/or SQL `INSERT` statements.

### Key Requirements
1. **Per-file Folder Structure:** For each processed SQL file (e.g. `01_SYSTEM_AND_BRANCH_PARAMETERS.sql`), create a dedicated subfolder in the output directory.
2. **Selective Export Formats:** Allow outputting CSV, SQL INSERT scripts, or both (`both`, `csv`, `insert`).
3. **Structured Output Naming:** Combine a 2-digit sequential index with the detected target table name (e.g. `01_BANKPARAMETERS.csv` and `01_BANKPARAMETERS_insert.sql`).
4. **Configuration-driven with CLI Overrides:** Database credentials and default paths reside in `config.json`, while CLI arguments can override the target file/folder or export format.
5. **Zero External Binaries:** Rely exclusively on standard Python 3.11 libraries and `oracledb` Thin mode (no Oracle Instant Client required).

---

## 2. Architecture & Component Design

The utility is structured in `export_sql.py` with cleanly separated concerns:

```text
+-----------------------------------------------------------+
|                        CLI / Config                       |
|   - Parse CLI arguments (argparse)                        |
|   - Load defaults & credentials from config.json          |
+-----------------------------+-----------------------------+
                              |
                              v
+-----------------------------------------------------------+
|                        SqlParser                          |
|   - Strip single-line (--) and multi-line (/* */) comments |
|   - Filter out PROMPT, SET, SPOOL statements              |
|   - Split statements by delimiter (;)                     |
|   - Retain only SELECT and CTE (WITH ... SELECT) queries  |
|   - Extract primary table name from FROM clause           |
+-----------------------------+-----------------------------+
                              |
                              v
+-----------------------------------------------------------+
|                      OracleExecutor                       |
|   - Establish thin-mode connection via oracledb           |
|   - Execute query stream with fetchmany(batch_size)       |
|   - Extract column metadata from cursor.description       |
+-----------------------------+-----------------------------+
                              |
               +--------------+--------------+
               |                             |
               v                             v
+-----------------------------+ +---------------------------+
|         CsvExporter         | |       InsertExporter      |
| - UTF-8 with BOM (utf-8-sig)| | - SET DEFINE OFF; header  |
| - Minimal escaping & quotes | | - Literal formatting:     |
| - Stream rows to disk       | |     NULL, Numbers, Strings|
|                             | |     TO_DATE, TO_TIMESTAMP |
|                             | | - Periodic COMMIT         |
+-----------------------------+ +---------------------------+
```

---

## 3. Configuration & CLI Specification

### 3.1 Configuration File (`config.json`)
Located by default in the working directory:
```json
{
  "database": {
    "user": "YOUR_DB_USER",
    "password": "YOUR_DB_PASSWORD",
    "host": "localhost",
    "port": 1521,
    "service_name": "ORCLPDB1"
  },
  "defaults": {
    "input_path": "Basic_Information_Tables",
    "output_dir": "exports",
    "format": "both",
    "batch_size": 1000
  }
}
```

### 3.2 CLI Options
`python export_sql.py [options]`
- `--path`, `-p`: Path to a specific `.sql` file or directory containing `.sql` files. (Defaults to `defaults.input_path` in `config.json`).
- `--format`, `-f`: Output format: `both`, `csv`, or `insert`. (Defaults to `defaults.format` in `config.json`).
- `--config`, `-c`: Path to custom config file. (Defaults to `config.json`).
- `--output`, `-o`: Custom output directory. (Defaults to `defaults.output_dir`).

---

## 4. SQL Parsing & Query Extraction

### 4.1 Statement Sanitization
1. **Comment Removal:**
   - Multi-line comments matching `/\*[\s\S]*?\*/` are stripped.
   - Single-line comments matching `--.*$` are stripped.
2. **Environment Directives:**
   - Lines starting with `PROMPT`, `SET`, `SPOOL` (case-insensitive) are ignored.
3. **Query Extraction:**
   - Split remaining text by `;` (or newline `/`).
   - Trim whitespace.
   - Filter queries that begin with `SELECT` or `WITH`.

### 4.2 Table Name Resolution
- A regex matches the first occurrence of `FROM\s+([a-zA-Z0-9_$.]+)` after the `SELECT` clause (ignoring subqueries if possible, or extracting the first candidate table).
- Any schema prefix is stripped (e.g. `MY_SCHEMA.BANKPARAMETERS` -> `BANKPARAMETERS`).
- If no valid table name can be derived (e.g., complex multi-table join or expressions), fallback to `QUERY`.
- The final query identifier is formatted as `{:02d}_{table_name}` (e.g., `01_BANKPARAMETERS`).

---

## 5. Output Generation

### 5.1 Directory Layout
For each input file `filename.sql`, an output folder `exports/<filename>/` is ensured:
```text
exports/
  01_SYSTEM_AND_BRANCH_PARAMETERS/
    01_BANKPARAMETERS.csv
    01_BANKPARAMETERS_insert.sql
    02_BRANCHPARAMETERS.csv
    02_BRANCHPARAMETERS_insert.sql
    03_CALENDER.csv
    03_CALENDER_insert.sql
```

### 5.2 CSV Exporter
- Encoding: `utf-8-sig` (Excel-compatible with UTF-8 BOM).
- Uses standard Python `csv.writer`.
- First line contains column names from `cursor.description`.
- Streamed in chunks (`batch_size`) to minimize RAM consumption.

### 5.3 INSERT Exporter
- File starts with:
  ```sql
  -- Generated by QueryPort Exporter
  -- Source Table: BANKPARAMETERS
  -- Date: <timestamp>
  SET DEFINE OFF;
  ```
- Formats each row into:
  ```sql
  INSERT INTO BANKPARAMETERS (COL1, COL2, ...) VALUES (VAL1, VAL2, ...);
  ```
- Value conversion rules:
  - `None` -> `NULL`
  - `int` / `float` -> `123` / `45.67`
  - `datetime.datetime` -> `TO_TIMESTAMP('YYYY-MM-DD HH24:MI:SS', 'YYYY-MM-DD HH24:MI:SS')`
  - `datetime.date` -> `TO_DATE('YYYY-MM-DD', 'YYYY-MM-DD')`
  - `str` -> `'string with ''escaped'' quotes'`
  - Boolean / other types -> mapped to integer or string representation.
- Writes a `COMMIT;` statement at the end of the file.

---

## 6. Error Handling & Edge Cases

1. **Missing / Malformed `config.json`:** Display clear error message indicating missing configuration and path.
2. **Database Connection Failure:** Catch `oracledb.Error`, display descriptive message (host, port, service, error code), and terminate cleanly.
3. **Execution Failure on Individual Query:** Log warning/error with query index and query snippet, continue processing remaining queries in the file.
4. **Files with no `SELECT` queries:** Log info message and do not create empty output directories.
5. **Special Characters in String values:** Double single-quotes (`'`) so SQL execution succeeds without syntax errors.

---

## 7. Verification & Testing

1. **Unit Testing (`test_export_sql.py`):**
   - Test SQL parser with realistic scripts (e.g., `01_SYSTEM_AND_BRANCH_PARAMETERS.sql` and `00_EXPORT_ALL_BASE_TABLES.sql`).
   - Test table name extraction on standard and prefixed queries.
   - Test INSERT formatting for types: null, string with quotes, int, float, date, timestamp.
   - Test CSV writing and UTF-8-SIG encoding.
2. **Integration Verification:**
   - Execute script against sample `.sql` files in `Basic_Information_Tables` and verify output directories and files.
