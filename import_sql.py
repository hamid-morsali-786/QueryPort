"""
SQL Oracle Importer
Reads CSV files from directories, validates schema in Oracle Database,
and bulk inserts data using oracledb Thin mode with configurable commit strategies.
"""

import argparse
import json
import sys
from pathlib import Path


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
