"""
SQL Oracle Importer
Reads CSV files from directories, validates schema in Oracle Database,
and bulk inserts data using oracledb Thin mode with configurable commit strategies.
"""

import argparse
import csv
import datetime
import json
import re
import sys
from pathlib import Path
from typing import Any, Generator


def extract_table_name(file_name: str) -> str:
    """Extract clean Oracle table name from CSV filename, stripping numeric prefix and extension."""
    stem = Path(file_name).stem
    match = re.match(r"^\d+_(.+)$", stem)
    tbl = match.group(1) if match else stem
    return tbl.strip().upper()


def clean_cell_value(val: str, col_type: str | None = None) -> Any:
    """Clean and cast a single CSV cell value according to Oracle expectations."""
    if val is None:
        return None
    s = val.strip()
    if not s:
        return None

    if col_type and ("DATE" in col_type.upper() or "TIMESTAMP" in col_type.upper()):
        for fmt in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d",
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
        ):
            try:
                return datetime.datetime.strptime(s, fmt)
            except ValueError:
                continue
    return s


def stream_csv_batches(file_path: Path, batch_size: int = 5000) -> Generator[tuple[list[str], list[list[Any]]], None, None]:
    """
    Generator streaming CSV rows in chunked batches of batch_size with O(1) memory.
    Yields (headers, list_of_raw_rows).
    """
    with open(file_path, "r", encoding="utf-8-sig", newline="", errors="replace") as f:
        reader = csv.reader(f)
        try:
            raw_headers = next(reader)
        except StopIteration:
            return
        headers = [h.strip().upper() for h in raw_headers]
        batch = []
        for row in reader:
            batch.append(row)
            if len(batch) >= batch_size:
                yield headers, batch
                batch = []
        if batch:
            yield headers, batch


def discover_import_files(input_path: Path) -> list[tuple[Path, str]]:
    """
    Discover all target CSV files and their inferred table names.
    Returns sorted list of (file_path, table_name).
    """
    if input_path.is_file():
        return [(input_path, extract_table_name(input_path.name))]
    elif input_path.is_dir():
        files = sorted(input_path.glob("**/*.csv"), key=lambda p: str(p).lower())
        return [(p, extract_table_name(p.name)) for p in files]
    return []


def fetch_schema_metadata(conn, target_schema: str) -> dict[str, dict[str, dict]]:
    """
    Fetch table and column metadata for the target schema from ALL_TAB_COLS.
    Returns: {TABLE_NAME: {COLUMN_NAME: {"data_type": str, "nullable": str, "data_default": str|None}}}
    """
    metadata: dict[str, dict[str, dict]] = {}
    schema_upper = target_schema.strip().upper()
    sql = """
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
    ORDER BY c.TABLE_NAME, c.COLUMN_ID
    """
    with conn.cursor() as cursor:
        cursor.execute(sql, target_schema=schema_upper)
        for tbl, col, dtype, nullable, default_val in cursor.fetchall():
            tbl_up = tbl.upper()
            col_up = col.upper()
            if tbl_up not in metadata:
                metadata[tbl_up] = {}
            def_str = str(default_val).strip() if default_val is not None else None
            metadata[tbl_up][col_up] = {
                "data_type": dtype,
                "nullable": nullable,
                "data_default": def_str
            }
    return metadata


def validate_import_plan(schema_metadata: dict, file_plan: list[tuple[Path, str]]) -> list[dict]:
    """
    Validate that each file's target table exists, CSV headers match Oracle columns,
    and no mandatory NOT NULL column without a DEFAULT is omitted from the CSV.
    Returns a list of error dictionaries.
    """
    errors: list[dict] = []
    for file_path, table_name in file_plan:
        tbl_upper = table_name.upper()
        if tbl_upper not in schema_metadata:
            errors.append({
                "file": file_path.name,
                "table": tbl_upper,
                "error_type": "MISSING_TABLE",
                "details": f"Target table '{tbl_upper}' does not exist in target database schema."
            })
            continue

        table_cols = schema_metadata[tbl_upper]
        
        try:
            with open(file_path, "r", encoding="utf-8-sig", newline="", errors="replace") as f:
                reader = csv.reader(f)
                headers = [h.strip().upper() for h in next(reader)]
        except Exception as exc:
            errors.append({
                "file": file_path.name,
                "table": tbl_upper,
                "error_type": "CORRUPT_CSV",
                "details": f"Could not read CSV headers: {exc}"
            })
            continue

        for h in headers:
            if h not in table_cols:
                errors.append({
                    "file": file_path.name,
                    "table": tbl_upper,
                    "error_type": "UNKNOWN_COLUMN_IN_CSV",
                    "details": f"CSV contains column '{h}' which does not exist in table '{tbl_upper}'."
                })

        header_set = set(headers)
        for col_name, col_meta in table_cols.items():
            if col_name not in header_set:
                if col_meta.get("nullable") == "N" and not col_meta.get("data_default"):
                    errors.append({
                        "file": file_path.name,
                        "table": tbl_upper,
                        "error_type": "MISSING_MANDATORY_COLUMN",
                        "details": f"Column '{col_name}' is NOT NULL in database without a DEFAULT value, but is missing from CSV."
                    })
    return errors


def format_validation_report(errors: list[dict]) -> str:
    """Format validation errors into a structured user-facing report."""
    if not errors:
        return "[OK] Pre-import schema validation passed successfully."
    
    lines = [
        "================================================================================",
        "                    PRE-IMPORT VALIDATION REPORT (FAILED)",
        "================================================================================",
        f"[!] {len(errors)} issue(s) detected across target schema. No modifications were made.",
        ""
    ]
    for idx, err in enumerate(errors, 1):
        lines.append(f"[{idx:02d}] File: {err.get('file')} | Table: {err.get('table')}")
        lines.append(f"     Type   : {err.get('error_type')}")
        lines.append(f"     Details: {err.get('details')}")
        lines.append("")
    lines.append("================================================================================")
    lines.append("[ABORT] Import cancelled. Please align CSV files with database schema.")
    return "\n".join(lines)


def load_import_config(config_path: str = "import_config.json") -> dict:
    """Load database credentials and import settings from JSON config file."""
    cfg_file = Path(config_path)
    if not cfg_file.exists():
        exe_dir = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
        fallback = exe_dir / config_path
        if fallback.exists():
            cfg_file = fallback
        else:
            raise FileNotFoundError(f"Import configuration file not found: {config_path}")
    with open(cfg_file, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_import_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments for import operation."""
    parser = argparse.ArgumentParser(
        description="Validate and import CSV datasets into Oracle Database tables."
    )
    parser.add_argument(
        "--config", "-c",
        default="import_config.json",
        dest="config_path",
        help="Path to JSON import config file (default: import_config.json)."
    )
    parser.add_argument(
        "--path", "-p",
        dest="input_path",
        help="Path to import CSV file or directory containing CSV files."
    )
    parser.add_argument(
        "--commit-mode",
        choices=["batch", "row", "all"],
        dest="commit_mode",
        help="Commit mode: 'batch' (default), 'row', or 'all'."
    )
    parser.add_argument(
        "--batch-size", "-b",
        type=int,
        dest="batch_size",
        help="Batch size for bulk insertion and batch commits (default from config)."
    )
    parser.add_argument(
        "--existing-data",
        choices=["append", "truncate", "skip"],
        dest="existing_data_action",
        help="Action on existing table data: 'append' (default), 'truncate', or 'skip'."
    )
    parser.add_argument(
        "--on-error",
        choices=["abort", "skip_and_log"],
        dest="on_error",
        help="Error strategy: 'abort' (default) or 'skip_and_log'."
    )
    parser.add_argument(
        "--schema", "-s",
        dest="schema",
        help="Target database schema for tables (defaults to database.schema in config)."
    )
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        dest="dry_run",
        help="Run pre-validation and row counts without modifying database tables."
    )
    return parser.parse_args(args)


def resolve_import_settings(cli_args: argparse.Namespace, config_data: dict) -> dict:
    """Merge CLI arguments with import config defaults, giving precedence to CLI options."""
    defaults = config_data.get("import_settings", {})
    db_config = dict(config_data.get("database", {}))

    schema = getattr(cli_args, "schema", None) or db_config.get("schema")
    if schema:
        db_config["schema"] = schema

    return {
        "input_path": getattr(cli_args, "input_path", None) or defaults.get("input_path", "imports"),
        "commit_mode": getattr(cli_args, "commit_mode", None) or defaults.get("commit_mode", "batch"),
        "batch_size": getattr(cli_args, "batch_size", None) or defaults.get("batch_size", 5000),
        "existing_data_action": getattr(cli_args, "existing_data_action", None) or defaults.get("existing_data_action", "append"),
        "on_error": getattr(cli_args, "on_error", None) or defaults.get("on_error", "abort"),
        "bad_rows_dir": defaults.get("bad_rows_dir", "import_errors"),
        "dry_run": getattr(cli_args, "dry_run", False),
        "database": db_config
    }
