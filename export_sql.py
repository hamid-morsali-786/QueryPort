"""
SQL Oracle Exporter
Reads .sql files, executes SELECT queries against an Oracle Database using oracledb Thin mode,
and exports results to CSV and/or SQL INSERT statements in per-file subfolders.
"""

import argparse
import csv
import datetime
import decimal
import json
import re
import shlex
import sys
from pathlib import Path


def load_config(config_path: str = "config.json") -> dict:
    """Load database credentials and default settings from JSON config file."""
    cfg_file = Path(config_path)
    if not cfg_file.exists():
        # Fallback to directory where executable/script is located
        exe_dir = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
        fallback = exe_dir / config_path
        if fallback.exists():
            cfg_file = fallback
        else:
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with open(cfg_file, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Execute .sql files on Oracle DB and export SELECT results as CSV / INSERT statements."
    )
    parser.add_argument(
        "--path", "-p",
        dest="input_path",
        help="Path to a .sql file or a directory containing .sql files."
    )
    parser.add_argument(
        "--format", "-f",
        choices=["both", "csv", "insert"],
        dest="format",
        help="Export format: 'both' (default), 'csv', or 'insert'."
    )
    parser.add_argument(
        "--config", "-c",
        default="config.json",
        dest="config_path",
        help="Path to JSON config file (default: config.json)."
    )
    parser.add_argument(
        "--output", "-o",
        dest="output_dir",
        help="Directory to save exported results (default from config)."
    )
    parser.add_argument(
        "--batch-size", "-b",
        type=int,
        dest="batch_size",
        help="Fetch batch size for stream writing (default from config)."
    )
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        dest="dry_run",
        help="Preview and print row counts for each query without creating export files."
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        dest="confirm",
        help="Show row counts for all queries and prompt for confirmation before exporting."
    )
    parser.add_argument(
        "--schema", "-s",
        dest="schema",
        help="Target database schema for queries (defaults to database.schema in config)."
    )
    return parser.parse_args(args)


def resolve_settings(cli_args: argparse.Namespace, config_data: dict) -> dict:
    """Merge CLI arguments with config defaults, giving precedence to CLI options."""
    defaults = config_data.get("export") or config_data.get("defaults") or {}
    db_config = dict(config_data.get("database", {}))
    schema = getattr(cli_args, "schema", None) or db_config.get("schema") or defaults.get("schema")
    if schema:
        db_config["schema"] = schema
    return {
        "input_path": cli_args.input_path or defaults.get("input_path", "test_sql"),
        "output_dir": cli_args.output_dir or defaults.get("output_dir", "exports"),
        "format": cli_args.format or defaults.get("format", "both"),
        "batch_size": cli_args.batch_size or defaults.get("batch_size", 1000),
        "database": db_config
    }


def clean_sql_script(sql_content: str) -> str:
    """Remove SQL comments and non-query directives (PROMPT, SET, SPOOL)."""
    # 1. Remove multi-line block comments /* ... */ replacing with a space to prevent token merging
    cleaned = re.sub(r"/\*.*?\*/", " ", sql_content, flags=re.DOTALL)
    # 2. Remove single-line comments -- ...
    cleaned = re.sub(r"--.*?$", "", cleaned, flags=re.MULTILINE)
    
    # 3. Filter lines starting with SQL*Plus / SQLcl environment directives
    directive_regex = re.compile(
        r"^\s*(?:PROMPT|SPOOL|SET\s+(?:SQLFORMAT|ECHO|FEEDBACK|TIMING|PAGESIZE|LINESIZE|TRIMSPOOL|TERMOUT|DEFINE|SERVEROUTPUT|HEADING))\b.*$",
        flags=re.IGNORECASE
    )
    preserved_lines = [
        line for line in cleaned.splitlines()
        if not directive_regex.match(line)
    ]
    return "\n".join(preserved_lines)


def extract_queries(sql_content: str) -> list[tuple[int, str, str]]:
    """
    Parse SQL text and extract individual SELECT statements.
    Returns a list of tuples: (query_index, table_name, query_text).
    """
    cleaned = clean_sql_script(sql_content)
    # Split on semicolons that are NOT inside single-quoted string literals
    raw_statements = re.split(r";(?=(?:[^']*'[^']*')*[^']*$)", cleaned)
    queries: list[tuple[int, str, str]] = []
    query_idx = 1

    table_regex = re.compile(r'\bFROM\s+([a-zA-Z0-9_$."\']+)', flags=re.IGNORECASE)

    for stmt in raw_statements:
        trimmed = stmt.strip()
        if not trimmed:
            continue
        
        # Check if query is a SELECT or starts with a CTE (WITH)
        if re.match(r"^(?:SELECT|WITH)\b", trimmed, flags=re.IGNORECASE):
            # Extract primary table name
            tbl_match = table_regex.search(trimmed)
            if tbl_match:
                raw_table = tbl_match.group(1).strip()
                # Remove schema prefix and any enclosing quotes
                table_name = raw_table.split(".")[-1].strip('"').strip("'")
            else:
                table_name = "QUERY"

            queries.append((query_idx, table_name.upper(), trimmed))
            query_idx += 1

    return queries


def format_oracle_literal(value: any) -> str:
    """Format a Python value as a valid Oracle SQL literal."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float, decimal.Decimal)):
        return str(value)
    if isinstance(value, datetime.datetime):
        if value.microsecond:
            return f"TO_TIMESTAMP('{value.strftime('%Y-%m-%d %H:%M:%S.%f')}', 'YYYY-MM-DD HH24:MI:SS.FF6')"
        return f"TO_TIMESTAMP('{value.strftime('%Y-%m-%d %H:%M:%S')}', 'YYYY-MM-DD HH24:MI:SS')"
    if isinstance(value, datetime.date):
        return f"TO_DATE('{value.strftime('%Y-%m-%d')}', 'YYYY-MM-DD')"
    
    # String or fallback: escape single quotes by doubling them
    escaped_str = str(value).replace("'", "''")
    return f"'{escaped_str}'"


def export_to_csv(rows_generator, columns: list[str], output_path: Path) -> int:
    """Write rows to a CSV file with UTF-8 BOM encoding."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(columns)
        for row in rows_generator:
            writer.writerow(row)
            count += 1
    return count


def export_to_insert(rows_generator, columns: list[str], table_name: str, output_path: Path) -> int:
    """Write rows as SQL INSERT statements ending with COMMIT;."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    col_str = ", ".join(columns)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"-- Exported data for table: {table_name}\n")
        f.write("SET DEFINE OFF;\n\n")
        for row in rows_generator:
            val_str = ", ".join(format_oracle_literal(v) for v in row)
            f.write(f"INSERT INTO {table_name} ({col_str}) VALUES ({val_str});\n")
            count += 1
        f.write("\nCOMMIT;\n")
    return count


def create_connection(db_config: dict):
    """Establish a connection to Oracle Database using oracledb Thin mode."""
    import oracledb

    # Return string/bytes for LOB columns directly rather than LOB locators
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


def process_query(cursor, query_info: tuple[int, str, str], format_type: str, target_dir: Path, batch_size: int = 1000) -> int:
    """Execute a query and stream results into CSV and/or INSERT files."""
    query_idx, table_name, query_text = query_info
    cursor.arraysize = batch_size
    cursor.execute(query_text)

    columns = [col[0] for col in cursor.description]
    prefix = f"{query_idx:02d}_{table_name}"
    csv_path = target_dir / f"{prefix}.csv"
    sql_path = target_dir / f"{prefix}_insert.sql"

    target_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    col_str = ", ".join(columns)

    write_csv = format_type in ("both", "csv")
    write_sql = format_type in ("both", "insert")

    f_csv = open(csv_path, "w", encoding="utf-8-sig", newline="") if write_csv else None
    f_sql = open(sql_path, "w", encoding="utf-8") if write_sql else None

    try:
        csv_writer = csv.writer(f_csv, quoting=csv.QUOTE_MINIMAL) if f_csv else None
        if csv_writer:
            csv_writer.writerow(columns)
        if f_sql:
            f_sql.write(f"-- Exported data for table: {table_name}\nSET DEFINE OFF;\n\n")

        while True:
            rows = cursor.fetchmany(batch_size)
            if not rows:
                break
            for row in rows:
                if csv_writer:
                    csv_writer.writerow(row)
                if f_sql:
                    val_str = ", ".join(format_oracle_literal(v) for v in row)
                    f_sql.write(f"INSERT INTO {table_name} ({col_str}) VALUES ({val_str});\n")
                count += 1

        if f_sql:
            f_sql.write("\nCOMMIT;\n")
    finally:
        if f_csv:
            f_csv.close()
        if f_sql:
            f_sql.close()

    return count


def get_query_row_count(cursor, query_text: str) -> int:
    """Execute SELECT COUNT(*) wrapper to get total rows without fetching data."""
    cleaned_query = query_text.strip().rstrip(";")
    cursor.execute(f"SELECT COUNT(*) FROM ({cleaned_query})")
    row = cursor.fetchone()
    return row[0] if row else 0


def inspect_sql_files(conn, sql_files: list[Path]) -> int:
    """
    Inspect queries across sql files, print row counts preview table.
    Returns total estimated row count.
    """
    print("\n========================================================================")
    print("[PREVIEW] Query Row Counts & Estimates")
    print("========================================================================")
    total_rows = 0
    total_queries = 0

    with conn.cursor() as cursor:
        for sql_file in sql_files:
            content = sql_file.read_text(encoding="utf-8", errors="replace")
            queries = extract_queries(content)
            if not queries:
                continue
            print(f"File: {sql_file.name}")
            for q_idx, tbl_name, q_sql in queries:
                try:
                    count = get_query_row_count(cursor, q_sql)
                    print(f"  [{q_idx:02d}] {tbl_name:<25} : {count:,} rows")
                    total_rows += count
                    total_queries += 1
                except Exception as exc:
                    print(f"  [{q_idx:02d}] {tbl_name:<25} : [ERROR] {exc}")
            print("------------------------------------------------------------------------")

    print(f"Total Queries: {total_queries} | Total Estimated Rows: {total_rows:,}")
    print("========================================================================\n")
    return total_rows


def process_sql_file(file_path: Path, conn, output_root: Path, format_type: str, batch_size: int = 1000) -> int:
    """Process all SELECT statements in a single .sql file into a subfolder."""
    content = file_path.read_text(encoding="utf-8", errors="replace")
    queries = extract_queries(content)

    if not queries:
        print(f"  [INFO] No SELECT queries found in '{file_path.name}'. Skipping.")
        return 0

    subfolder = output_root / file_path.stem
    subfolder.mkdir(parents=True, exist_ok=True)
    processed_count = 0

    with conn.cursor() as cursor:
        for q_info in queries:
            q_idx, tbl_name, q_sql = q_info
            try:
                rows_written = process_query(cursor, q_info, format_type, subfolder, batch_size)
                print(f"    -> [{q_idx:02d}] {tbl_name}: {rows_written} rows exported ({format_type})")
                processed_count += 1
            except Exception as exc:
                print(f"    [!] Error executing query #{q_idx} ({tbl_name}): {exc}")

    return processed_count


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point."""
    args_list = list(sys.argv[1:] if argv is None else argv)
    if args_list and args_list[0].lower() == "import":
        import import_sql
        return import_sql.main(args_list[1:])
    if "--mode" in args_list:
        idx = args_list.index("--mode")
        if idx + 1 < len(args_list) and args_list[idx + 1].lower() == "import":
            import import_sql
            remaining = args_list[:idx] + args_list[idx + 2:]
            return import_sql.main(remaining)
        elif idx + 1 < len(args_list) and args_list[idx + 1].lower() == "export":
            args_list = args_list[:idx] + args_list[idx + 2:]

    args = parse_args(args_list)
    try:
        config_data = load_config(args.config_path)
    except Exception as exc:
        print(f"[ERROR] Failed to load configuration: {exc}", file=sys.stderr)
        return 1

    settings = resolve_settings(args, config_data)
    input_path = Path(settings["input_path"])
    output_root = Path(settings["output_dir"])
    format_type = settings["format"]
    batch_size = settings["batch_size"]

    # Gather target .sql files
    if input_path.is_file():
        sql_files = [input_path]
    elif input_path.is_dir():
        sql_files = sorted(input_path.glob("*.sql"))
    else:
        print(f"[ERROR] Specified path does not exist: {input_path}", file=sys.stderr)
        return 1

    if not sql_files:
        print(f"[WARNING] No .sql files found in '{input_path}'", file=sys.stderr)
        return 0

    print(f"=== SQL Oracle Exporter ===")
    print(f"Target Path : {input_path} ({len(sql_files)} file(s))")
    print(f"Output Dir  : {output_root}")
    print(f"Format      : {format_type}")
    print(f"Batch Size  : {batch_size}")
    if settings["database"].get("schema"):
        print(f"Schema      : {settings['database']['schema']}")
    print("--------------------------------------------------")

    try:
        conn = create_connection(settings["database"])
        print("[OK] Connected to Oracle Database successfully.")
    except Exception as exc:
        print(f"[ERROR] Could not connect to Oracle DB: {exc}", file=sys.stderr)
        print("Please verify connection settings in your config.json.", file=sys.stderr)
        return 2

    # Check for dry-run or interactive confirmation preview
    if getattr(args, "dry_run", False) or getattr(args, "confirm", False):
        try:
            inspect_sql_files(conn, sql_files)
        except Exception as exc:
            print(f"[ERROR] Error during query preview: {exc}", file=sys.stderr)
        
        if getattr(args, "dry_run", False):
            print("Dry-run preview complete. No files were created.")
            conn.close()
            return 0

        if getattr(args, "confirm", False):
            try:
                answer = input("Proceed with export? [y/N]: ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                print("\nExport cancelled by user.")
                conn.close()
                return 0
            if answer not in ("y", "yes"):
                print("Export cancelled by user.")
                conn.close()
                return 0

    total_exported = 0
    try:
        for sql_file in sql_files:
            print(f"\nProcessing file: {sql_file.name}")
            queries_done = process_sql_file(sql_file, conn, output_root, format_type, batch_size)
            total_exported += queries_done
    finally:
        conn.close()

    print("\n--------------------------------------------------")
    print(f"Export completed. Total queries processed: {total_exported}")
    print(f"Output saved in: {output_root.resolve()}")
    return 0


def _run_subprompt(runner_func, prompt_label: str, config_name: str = "config.json"):
    """Handle interactive subprompt for export or import operation."""
    try:
        choice = input(f"\nExecute {prompt_label} with default {config_name} settings? [Y/n]: ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        return

    if choice in ("", "y", "yes"):
        try:
            runner_func([])
        except SystemExit:
            pass
        try:
            input("\nExecution finished. Press Enter to exit...")
        except (KeyboardInterrupt, EOFError):
            pass
        return

    print(f"\nEnter {prompt_label} command or arguments (e.g. --path ... --dry-run).")
    print("Type 'exit' or 'q' to quit:\n")
    while True:
        try:
            cmd = input(f"QueryPort ({prompt_label})> ").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if not cmd or cmd.lower() in ("exit", "quit", "q"):
            break

        parts = shlex.split(cmd)
        if parts and parts[0].lower().endswith((".exe", "export_sql.py", "import_sql.py")):
            parts = parts[1:]

        try:
            runner_func(parts)
        except SystemExit:
            pass


def interactive_loop():
    """Interactive unified console prompt when launched with no arguments."""
    print("==================================================")
    print("           QueryPort Unified Console              ")
    print("==================================================")
    print("Select Operation:")
    print("  [1 / E] : Export Database queries to CSV / SQL Insert (config.json)")
    print("  [2 / I] : Import CSV datasets into Database tables  (config.json)")
    print("  [exit / q] : Exit program\n")
    try:
        op = input("Enter choice [1/2] (Default: 1): ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        return

    if op in ("exit", "quit", "q"):
        return

    if op in ("2", "i", "import"):
        import import_sql
        _run_subprompt(import_sql.main, "import")
    else:
        _run_subprompt(main, "export")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        interactive_loop()
    else:
        sys.exit(main())
