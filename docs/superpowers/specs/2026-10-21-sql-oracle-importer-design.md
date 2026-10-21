# Design Specification: Oracle CSV Data Importer Subsystem for QueryPort

- **Date:** 2026-10-21
- **Author:** Hamid Morsali / QueryPort Development Team
- **Status:** Approved (Ready for Implementation Planning)
- **Target Release:** QueryPort v1.1.0

---

## 1. Overview & Objectives

QueryPort currently excels at extracting and exporting Oracle SQL query results into CSV and SQL INSERT scripts. This specification defines the **Import Subsystem** (`import_sql.py` and unified `QueryPort.exe import`), enabling high-performance, validated, chunked streaming ingestion of CSV datasets into Oracle Database tables.

### Key Goals
1. **Directory & File Ingestion**: Traverse nested directories (e.g. `imports/`) folder-by-folder and file-by-file in sorted order.
2. **Table Name Resolution**: Automatically infer target table names from CSV filenames (e.g., `02_BANKPARAMETERS.csv` -> `BANKPARAMETERS`).
3. **Dedicated Configuration**: Separate `import_config.json` with sensible defaults.
4. **Pre-Execution Data Dictionary Validation**:
   - Verify table exists in the target schema.
   - Verify all CSV headers match existing columns in Oracle.
   - Detect and flag mandatory `NOT NULL` columns in the Oracle table that are missing from the CSV and do not have a `DATA_DEFAULT`.
   - Strict abort on validation failure before modifying any table.
5. **High-Performance Chunked Streaming**:
   - $O(1)$ constant memory usage, handling files up to hundreds of megabytes (e.g. `04_CALENDER.csv` ~82MB).
   - Parameterized batch execution using native `cursor.executemany`.
6. **Flexible Commit Modes**:
   - `batch`: Commit every $N$ records (default: 5,000).
   - `row`: Commit after every single inserted row.
   - `all`: Single commit at the end of each table.
7. **Existing Data Actions**:
   - `append`: Keep existing rows and insert new rows.
   - `truncate`: Truncate table prior to inserting.
   - `skip`: Skip importing if the table already contains rows.
8. **Error Handling & Bad-Row Logging**:
   - `abort`: Stop immediately on error and rollback open transaction.
   - `skip_and_log`: Fallback to row-by-row on batch failure, log rejected rows to `import_errors/<TABLE>_rejected.csv`, and continue.
9. **Unified CLI & Console**:
   - Direct: `python import_sql.py [options]`
   - Unified: `QueryPort.exe import [options]` / `QueryPort.exe --mode import`
   - Interactive console choice on double-click (`[1] Export`, `[2] Import`).

---

## 2. Configuration Schema (`import_config.json`)

The importer uses a dedicated JSON configuration file:

```json
{
  "database": {
    "user": "TARGET_SCHEMA",
    "password": "your_password",
    "host": "localhost",
    "port": 1521,
    "service_name": "ORCLPDB1",
    "schema": "TARGET_SCHEMA"
  },
  "import_settings": {
    "input_path": "imports",
    "commit_mode": "batch",
    "batch_size": 5000,
    "existing_data_action": "append",
    "on_error": "abort",
    "bad_rows_dir": "import_errors"
  }
}
```

### Configuration Fields
| Field | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `database.user` | string | required | Oracle username |
| `database.password` | string | required | Oracle password |
| `database.host` | string | `"localhost"` | Oracle DB host |
| `database.port` | integer | `1521` | Listener port |
| `database.service_name` | string | `"XE"` | Service name / PDB |
| `database.schema` | string | optional | Target schema (`CURRENT_SCHEMA`) |
| `import_settings.input_path` | string | `"imports"` | Path to directory or single CSV |
| `import_settings.commit_mode` | string | `"batch"` | `"batch"`, `"row"`, or `"all"` |
| `import_settings.batch_size` | integer | `5000` | Fetch/insert batch size |
| `import_settings.existing_data_action` | string | `"append"` | `"append"`, `"truncate"`, or `"skip"` |
| `import_settings.on_error` | string | `"abort"` | `"abort"` or `"skip_and_log"` |
| `import_settings.bad_rows_dir` | string | `"import_errors"` | Directory for rejected records |

---

## 3. Data Dictionary Pre-Execution Validation

Before starting any transaction, the importer queries Oracle metadata for all target tables in the selected schema.

### Oracle Metadata Query
```sql
SELECT 
    c.TABLE_NAME, 
    c.COLUMN_NAME, 
    c.DATA_TYPE, 
    c.NULLABLE, 
    c.DATA_DEFAULT
FROM ALL_TAB_COLS c
JOIN ALL_TABLES t ON c.OWNER = t.OWNER AND c.TABLE_NAME = t.TABLE_NAME
WHERE c.OWNER = :target_schema
  AND c.HIDDEN_COLUMN = 'NO'
```

### Validation Rules
1. **Table Existence**: Target table (derived from filename) must exist in the target schema.
2. **Column Presence**: Every header in the CSV file must exist as a column in the Oracle table. Case-insensitive matching maps to Oracle uppercase identifiers.
3. **Mandatory Column Completeness**:
   If an Oracle table column has `NULLABLE == 'N'`, it MUST either:
   - Be present in the CSV headers, OR
   - Have a non-empty `DATA_DEFAULT` in Oracle (e.g., `'0'`, `SYSDATE`, sequence, etc.).
   If a column is `NOT NULL`, has NO `DATA_DEFAULT`, and is missing from the CSV, validation fails with `MISSING_MANDATORY_COLUMN`.

### Abort Policy
If any validation error is discovered across any of the files in `input_path`, QueryPort outputs a detailed validation report and terminates with returncode `1` before touching the database.

---

## 4. Ingestion & Streaming Engine

### File and Table Discovery
- Walk `input_path` recursively.
- Match `.csv` files.
- Extract table name using regex: `r"^(?:\d+_)?(.+?)(?:\.csv)?$"`
  - `02_BANKPARAMETERS.csv` -> `BANKPARAMETERS`
  - `04_CALENDER.csv` -> `CALENDER`
  - `CUSTOMERS.csv` -> `CUSTOMERS`

### Streaming Chunk Generator
```python
def stream_csv_batches(file_path: Path, batch_size: int):
    with open(file_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        headers = [h.strip().upper() for h in next(reader)]
        batch = []
        for row in reader:
            batch.append(row)
            if len(batch) >= batch_size:
                yield headers, batch
                batch = []
        if batch:
            yield headers, batch
```

### Data Cleansing & Type Binding
1. Empty string `""` -> `None` (mapped to Oracle `NULL`).
2. Datetime conversion: Check column metadata. If `DATA_TYPE` in (`DATE`, `TIMESTAMP`), parse strings matching ISO/Oracle formats (`YYYY-MM-DD HH:MI:SS`, `YYYY/MM/DD`, `YYYY-MM-DDTHH:MM:SS`) into `datetime.datetime` objects.
3. Number coercion: Numeric strings are left to Python/oracledb automatic type conversion or sanitized.

### Bulk Execution
Parameterized SQL statement:
```sql
INSERT INTO {table_name} ({columns_csv}) VALUES ({bind_vars})
```
Executed via:
```python
cursor.executemany(sql, cleaned_batch)
```

---

## 5. Commit and Error Strategies

### Commit Modes
- **`batch`**: After `cursor.executemany(sql, batch)`, execute `conn.commit()`.
- **`all`**: Execute `cursor.executemany(sql, batch)` for all batches, then execute `conn.commit()` once at the end of the table. If an error occurs, execute `conn.rollback()`.
- **`row`**: Execute row-by-row with `cursor.execute(sql, row)` followed immediately by `conn.commit()`.

### Existing Data Handling (`existing_data_action`)
- **`append`**: No prior action. Rows are inserted alongside existing rows.
- **`truncate`**: Execute `TRUNCATE TABLE {table_name}` before streaming rows.
- **`skip`**: Run `SELECT COUNT(*) FROM {table_name}`. If count > 0, log skip notice and proceed to next file.

### Error Handling (`on_error`)
- **`abort`**: Any `DatabaseError` causes immediate `conn.rollback()` and program exit with error details.
- **`skip_and_log`**:
  If a batch fails in `cursor.executemany`, the engine catches the exception and falls back to executing that single batch row-by-row:
  - Valid rows are inserted.
  - Invalid rows are caught, formatted with row number + error message, and written to `import_errors/{table_name}_rejected.csv`.

---

## 6. Execution Reporting

At completion, the engine prints a comprehensive summary table:

```text
================================================================================
                         IMPORT SUMMARY EXECUTION REPORT
================================================================================
Target Schema: TARGET_SCHEMA | Commit Mode: batch (5,000)
--------------------------------------------------------------------------------
No.  Table Name             Read Rows    Imported     Failed    Duration    Rate
---  --------------------  -----------  -----------  --------  ----------  ---------
01   BANKPARAMETERS        1            1            0         0.05s       20 r/s
02   BRANCHPARAMETERS      450          450          0         0.18s       2,500 r/s
03   CALENDER              350,000      350,000      0         4.20s       83,333 r/s
--------------------------------------------------------------------------------
TOTALS: 3 Tables | 350,451 Rows Read | 350,451 Imported | 0 Failed in 4.43s
================================================================================
```

---

## 7. CLI & Interactive Console Design

### Command-Line Arguments (`import_sql.py` and `QueryPort.exe import`)
- `--config`, `-c`: Path to config file (default: `import_config.json`).
- `--path`, `-p`: Path to imports directory or single CSV file.
- `--commit-mode`: `batch`, `row`, `all`.
- `--batch-size`, `-b`: Chunk size (default: 5000).
- `--existing-data`: `append`, `truncate`, `skip`.
- `--on-error`: `abort`, `skip_and_log`.
- `--schema`, `-s`: Target schema.
- `--dry-run`, `-d`: Run pre-validation and row counts without inserting data.

### Interactive Console Mode (Double-click `QueryPort.exe`)
When executed with no arguments:
```text
==================================================
              QueryPort Unified Console           
==================================================
Select Operation:
  [1 / E] : Export Database queries to CSV / SQL Insert (config.json)
  [2 / I] : Import CSV datasets into Database tables  (import_config.json)
  [exit / q] : Exit

Enter choice [1/2] (Default: 1): 
```

---

## 8. Verification & Test Plan

1. **Unit Tests (`test_import_sql.py`)**:
   - `test_load_import_config_and_defaults`
   - `test_resolve_import_settings_cli_overrides`
   - `test_table_name_extraction_from_filenames`
   - `test_pre_validation_table_not_found`
   - `test_pre_validation_unknown_column_in_csv`
   - `test_pre_validation_missing_mandatory_not_null_column`
   - `test_pre_validation_missing_not_null_with_default_passes`
   - `test_clean_row_values_empty_strings_to_null`
   - `test_clean_row_values_date_parsing`
   - `test_batch_streaming_generator_chunking`
   - `test_commit_mode_batch_all_row`
   - `test_skip_and_log_error_fallback`
   - `test_dry_run_validation_only`
2. **Integration Verification**:
   - Run import dry-run against the local Oracle database `TARGET_SCHEMA`.
   - Run sample import on test tables.
