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
import time
from pathlib import Path
from typing import Any, Generator


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
        default="config.json",
        dest="config_path",
        help="Path to JSON config file (default: config.json)."
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
    defaults = config_data.get("import") or config_data.get("import_settings") or {}
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


def extract_table_name(file_name: str) -> str:
    """Extract clean Oracle table name from CSV filename, stripping numeric prefix and extension."""
    stem = Path(file_name).stem
    match = re.match(r"^\d+_(.+)$", stem)
    tbl = match.group(1) if match else stem
    return tbl.strip().upper()


def clean_cell_value(val: str, col_type: str | None = None) -> Any:
    """Clean and cast a single CSV cell value according to Oracle expectations."""
    if val is None or not val.strip():
        return None

    if col_type:
        upper_type = col_type.upper()
        if "DATE" in upper_type or "TIMESTAMP" in upper_type:
            s = val.strip()
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
        if "NUMBER" in upper_type or "FLOAT" in upper_type:
            return val.strip()

    return val


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
            if not row or all(cell.strip() == "" for cell in row):
                continue
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


def create_import_connection(db_config: dict):
    """Establish connection to Oracle Database using oracledb Thin mode."""
    import oracledb
    oracledb.defaults.fetch_lobs = False
    user = db_config.get("user")
    password = db_config.get("password")
    host = db_config.get("host", "localhost")
    port = db_config.get("port", 1521)
    service_name = db_config.get("service_name", "XE")
    dsn = db_config.get("dsn") or f"{host}:{port}/{service_name}"
    conn = oracledb.connect(user=user, password=password, dsn=dsn)
    schema = db_config.get("schema")
    if schema:
        conn.current_schema = schema
    return conn


def import_single_file(conn, file_path: Path, table_name: str, table_meta: dict, settings: dict) -> dict:
    """
    Import a single CSV file into target Oracle table according to commit_mode, existing_data_action, and on_error.
    Returns stats dict: {"read": int, "imported": int, "failed": int, "skipped": bool, "duration": float}
    """
    t0 = time.time()
    existing_action = settings.get("existing_data_action", "append")
    commit_mode = settings.get("commit_mode", "batch")
    batch_size = settings.get("batch_size", 5000)
    on_error = settings.get("on_error", "abort")
    bad_rows_dir = Path(settings.get("bad_rows_dir", "import_errors"))

    tbl_upper = table_name.upper()

    with conn.cursor() as cursor:
        if existing_action == "truncate":
            cursor.execute(f"TRUNCATE TABLE {tbl_upper}")
        elif existing_action == "skip":
            cursor.execute(f"SELECT COUNT(*) FROM {tbl_upper}")
            row = cursor.fetchone()
            if row and row[0] > 0:
                return {"read": 0, "imported": 0, "failed": 0, "skipped": True, "duration": time.time() - t0}

        count_read = 0
        count_imported = 0
        count_failed = 0
        bad_file = None
        bad_writer = None

        for headers, raw_batch in stream_csv_batches(file_path, batch_size):
            count_read += len(raw_batch)
            cols_str = ", ".join(headers)
            binds_str = ", ".join(f":{i+1}" for i in range(len(headers)))
            insert_sql = f"INSERT INTO {tbl_upper} ({cols_str}) VALUES ({binds_str})"

            cleaned_batch = []
            for row in raw_batch:
                cleaned_row = []
                for idx, col_name in enumerate(headers):
                    val = row[idx] if idx < len(row) else None
                    col_type = table_meta.get(col_name, {}).get("data_type")
                    cleaned_row.append(clean_cell_value(val, col_type))
                cleaned_batch.append(cleaned_row)

            if commit_mode == "row":
                for row_idx, row in enumerate(cleaned_batch):
                    try:
                        cursor.execute(insert_sql, row)
                        conn.commit()
                        count_imported += 1
                    except Exception as exc:
                        count_failed += 1
                        if on_error == "abort":
                            conn.rollback()
                            raise
                        if bad_writer is None:
                            bad_rows_dir.mkdir(parents=True, exist_ok=True)
                            bad_file = open(bad_rows_dir / f"{tbl_upper}_rejected.csv", "w", encoding="utf-8-sig", newline="")
                            bad_writer = csv.writer(bad_file)
                            bad_writer.writerow(["ROW_NUM", "ERROR"] + headers)
                        bad_writer.writerow([count_read - len(raw_batch) + row_idx + 1, str(exc)] + raw_batch[row_idx])
            else:
                try:
                    cursor.executemany(insert_sql, cleaned_batch)
                    count_imported += len(cleaned_batch)
                    if commit_mode == "batch":
                        conn.commit()
                except Exception as exc:
                    if on_error == "abort":
                        conn.rollback()
                        raise
                    for row_idx, row in enumerate(cleaned_batch):
                        try:
                            cursor.execute(insert_sql, row)
                            count_imported += 1
                        except Exception as row_exc:
                            count_failed += 1
                            if bad_writer is None:
                                bad_rows_dir.mkdir(parents=True, exist_ok=True)
                                bad_file = open(bad_rows_dir / f"{tbl_upper}_rejected.csv", "w", encoding="utf-8-sig", newline="")
                                bad_writer = csv.writer(bad_file)
                                bad_writer.writerow(["ROW_NUM", "ERROR"] + headers)
                            bad_writer.writerow([count_read - len(raw_batch) + row_idx + 1, str(row_exc)] + raw_batch[row_idx])
                    if commit_mode == "batch":
                        conn.commit()

        if commit_mode == "all":
            conn.commit()

        if bad_file:
            bad_file.close()

        return {
            "read": count_read,
            "imported": count_imported,
            "failed": count_failed,
            "skipped": False,
            "duration": time.time() - t0
        }


def run_import(settings: dict) -> int:
    """Execute complete import workflow with pre-validation and execution reporting."""
    input_path = Path(settings["input_path"])
    file_plan = discover_import_files(input_path)
    if not file_plan:
        print(f"[WARNING] No CSV files found in '{input_path}'.", file=sys.stderr)
        return 0

    target_schema = settings["database"].get("schema") or settings["database"].get("user")
    print("=== QueryPort - Oracle CSV Importer ===")
    print(f"Target Path    : {input_path} ({len(file_plan)} file(s))")
    print(f"Target Schema  : {target_schema}")
    print(f"Commit Mode    : {settings['commit_mode']} (Batch: {settings['batch_size']})")
    print(f"Existing Data  : {settings['existing_data_action']}")
    print(f"Error Strategy : {settings['on_error']}")
    print("--------------------------------------------------------------------------------")

    try:
        conn = create_import_connection(settings["database"])
        print("[OK] Connected to Oracle Database successfully.")
    except Exception as exc:
        print(f"[ERROR] Could not connect to Oracle DB: {exc}", file=sys.stderr)
        return 2

    try:
        print("Running pre-import data dictionary validation...")
        meta = fetch_schema_metadata(conn, target_schema)
        errors = validate_import_plan(meta, file_plan)
        if errors:
            print(format_validation_report(errors), file=sys.stderr)
            return 1

        print("[OK] All tables and column structures verified successfully.\n")

        if settings.get("dry_run"):
            print("================================================================================")
            print("                       IMPORT DRY-RUN PREVIEW SUMMARY")
            print("================================================================================")
            for idx, (fpath, tbl) in enumerate(file_plan, 1):
                col_count = len(meta.get(tbl, {}))
                print(f"  [{idx:02d}] Table: {tbl:<25} | File: {fpath.name:<30} | Cols: {col_count}")
            print("================================================================================")
            print("[INFO] Dry-run completed. All structures are valid. No data was modified.")
            return 0

        summary_results = []
        total_read = 0
        total_imported = 0
        total_failed = 0
        t_start = time.time()

        for idx, (fpath, tbl) in enumerate(file_plan, 1):
            print(f"Processing [{idx:02d}/{len(file_plan):02d}]: {fpath.name} -> {tbl} ...")
            tbl_meta = meta.get(tbl, {})
            res = import_single_file(conn, fpath, tbl, tbl_meta, settings)
            res["table"] = tbl
            res["file"] = fpath.name
            summary_results.append(res)
            total_read += res["read"]
            total_imported += res["imported"]
            total_failed += res["failed"]
            status = "SKIPPED" if res["skipped"] else f"{res['imported']:,} rows imported"
            print(f"    -> Result: {status} in {res['duration']:.2f}s")

        t_total = time.time() - t_start

        print("\n================================================================================")
        print("                         IMPORT SUMMARY EXECUTION REPORT")
        print("================================================================================")
        print(f"Target Schema: {target_schema} | Commit Mode: {settings['commit_mode']}")
        print("--------------------------------------------------------------------------------")
        print(f"{'No.':<4} {'Table Name':<25} {'Read Rows':<12} {'Imported':<12} {'Failed':<10} {'Duration':<10}")
        print("--------------------------------------------------------------------------------")
        for idx, r in enumerate(summary_results, 1):
            dur_str = f"{r['duration']:.2f}s"
            status_read = f"{r['read']:,}" if not r["skipped"] else "SKIPPED"
            print(f"{idx:02d}   {r['table']:<25} {status_read:<12} {r['imported']:<12,} {r['failed']:<10,} {dur_str:<10}")
        print("--------------------------------------------------------------------------------")
        print(f"TOTALS: {len(summary_results)} Tables | {total_read:,} Read | {total_imported:,} Imported | {total_failed:,} Failed in {t_total:.2f}s")
        print("================================================================================\n")

    finally:
        conn.close()

    return 0 if total_failed == 0 else 1


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for importer."""
    args = parse_import_args(argv)
    try:
        config_data = load_import_config(args.config_path)
    except Exception as exc:
        print(f"[ERROR] Failed to load import configuration: {exc}", file=sys.stderr)
        return 1

    settings = resolve_import_settings(args, config_data)
    return run_import(settings)


if __name__ == "__main__":
    sys.exit(main())
