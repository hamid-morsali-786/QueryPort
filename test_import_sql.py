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

    def test_dry_run_flag(self):
        args = parse_import_args(["--dry-run"])
        self.assertTrue(args.dry_run)

    def test_resolve_concurrency_settings_defaults(self):
        cfg = {"database": {"user": "APP_USER"}}
        args = parse_import_args([])
        settings = resolve_import_settings(args, cfg)
        self.assertIn("concurrency", settings)
        self.assertEqual(settings["concurrency"]["workers"], 1)
        self.assertEqual(settings["concurrency"]["chunk_size"], 25000)
        self.assertEqual(settings["concurrency"]["rac_services"], [])

    def test_resolve_concurrency_settings_from_config_and_cli(self):
        cfg = {
            "database": {"user": "APP_USER"},
            "concurrency": {
                "workers": 2,
                "chunk_size": 10000,
                "rac_services": ["SRV1", "SRV2"]
            }
        }
        args = parse_import_args(["--workers", "4", "--rac-services", "SRV_A,SRV_B", "--chunk-size", "50000"])
        settings = resolve_import_settings(args, cfg)
        self.assertEqual(settings["concurrency"]["workers"], 4)
        self.assertEqual(settings["concurrency"]["chunk_size"], 50000)
        self.assertEqual(settings["concurrency"]["rac_services"], ["SRV_A", "SRV_B"])

    def test_resolve_import_settings_from_unified_import_block(self):
        cfg = {
            "database": {"user": "APP_USER", "password": "pwd"},
            "import": {"input_path": "my_imports", "commit_mode": "row", "batch_size": 2500}
        }
        from import_sql import parse_import_args, resolve_import_settings
        args = parse_import_args([])
        settings = resolve_import_settings(args, cfg)
        self.assertEqual(settings["input_path"], "my_imports")
        self.assertEqual(settings["commit_mode"], "row")
        self.assertEqual(settings["batch_size"], 2500)

    def test_extract_table_name(self):
        from import_sql import extract_table_name
        self.assertEqual(extract_table_name("02_BANKPARAMETERS.csv"), "BANKPARAMETERS")
        self.assertEqual(extract_table_name("04_CALENDER.csv"), "CALENDER")
        self.assertEqual(extract_table_name("CUSTOMERS.csv"), "CUSTOMERS")
        self.assertEqual(extract_table_name("01_SUB_SYS_TABLE.CSV"), "SUB_SYS_TABLE")

    def test_clean_cell_value(self):
        from import_sql import clean_cell_value
        import datetime
        self.assertIsNone(clean_cell_value(""))
        self.assertIsNone(clean_cell_value("   "))
        self.assertEqual(clean_cell_value("IRR"), "IRR")
        dt = clean_cell_value("1995-01-01 00:00:00", col_type="DATE")
        self.assertEqual(dt, datetime.datetime(1995, 1, 1, 0, 0, 0))

    def test_clean_cell_value_iso_and_slashed_dates(self):
        from import_sql import clean_cell_value
        import datetime
        dt1 = clean_cell_value("2026-10-24 12:30:00", col_type="DATE")
        self.assertEqual(dt1, datetime.datetime(2026, 10, 24, 12, 30, 0))
        dt2 = clean_cell_value("2026/10/24 12:30:00", col_type="DATE")
        self.assertEqual(dt2, datetime.datetime(2026, 10, 24, 12, 30, 0))
        dt3 = clean_cell_value("2026/10/24", col_type="DATE")
        self.assertEqual(dt3, datetime.datetime(2026, 10, 24, 0, 0, 0))
        dt4 = clean_cell_value("2026-10-24 12:30:00.123456", col_type="TIMESTAMP")
        self.assertEqual(dt4, datetime.datetime(2026, 10, 24, 12, 30, 0, 123456))

    def test_thread_safe_error_logger_concurrency(self):
        from import_sql import ThreadSafeErrorLogger
        import concurrent.futures
        import csv

        with tempfile.TemporaryDirectory() as tmpdir:
            bad_path = Path(tmpdir) / "test_rejected.csv"
            logger = ThreadSafeErrorLogger(bad_path, ["ID", "NAME"])

            def worker(thread_id):
                for i in range(50):
                    logger.log(thread_id * 100 + i, Exception("Simulated error"), [i, f"Name_{i}"])

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(worker, t) for t in range(10)]
                concurrent.futures.wait(futures)

            logger.close()

            with open(bad_path, "r", encoding="utf-8-sig") as f:
                rows = list(csv.reader(f))

            # 1 header row + 500 data rows
            self.assertEqual(len(rows), 501)
            self.assertEqual(rows[0], ["ROW_NUM", "ERROR", "ID", "NAME"])

    def test_stream_csv_batches(self):
        from import_sql import stream_csv_batches
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".csv", encoding="utf-8-sig") as f:
            f.write("ID,NAME\n1,A\n2,B\n\n,,,\n3,C\n4,D\n5,E\n")
            csv_path = Path(f.name)
        
        batches = list(stream_csv_batches(csv_path, batch_size=2))
        self.assertEqual(len(batches), 3)

    def test_stream_csv_chunks(self):
        from import_sql import stream_csv_chunks
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".csv", encoding="utf-8-sig") as f:
            lines = ["ID,NAME"] + [f"{i},Name_{i}" for i in range(1, 11)]
            f.write("\n".join(lines) + "\n")
            csv_path = Path(f.name)
        
        chunks = list(stream_csv_chunks(csv_path, chunk_size=4))
        csv_path.unlink(missing_ok=True)
        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0][1], 0)  # chunk_idx
        self.assertEqual(len(chunks[0][2]), 4)
        self.assertEqual(chunks[1][1], 1)
        self.assertEqual(len(chunks[1][2]), 4)
        self.assertEqual(chunks[2][1], 2)
        self.assertEqual(len(chunks[2][2]), 2)
        total_rows = sum(len(c[2]) for c in chunks)
        self.assertEqual(total_rows, 10)

    def test_get_worker_connection_config_rac_routing(self):
        from import_sql import get_worker_connection_config
        base_cfg = {"user": "U", "service_name": "DEFAULT_SRV"}
        rac_services = ["NODE1_SRV", "NODE2_SRV"]

        cfg0 = get_worker_connection_config(base_cfg, rac_services, 0)
        self.assertEqual(cfg0["service_name"], "NODE1_SRV")

        cfg1 = get_worker_connection_config(base_cfg, rac_services, 1)
        self.assertEqual(cfg1["service_name"], "NODE2_SRV")

        cfg2 = get_worker_connection_config(base_cfg, rac_services, 2)
        self.assertEqual(cfg2["service_name"], "NODE1_SRV")

        # Fallback when rac_services is empty
        cfg_default = get_worker_connection_config(base_cfg, [], 0)
        self.assertEqual(cfg_default["service_name"], "DEFAULT_SRV")

    def test_discover_import_files(self):
        from import_sql import discover_import_files
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            sub1 = root / "folder1"
            sub1.mkdir()
            f1 = sub1 / "01_TABLE_A.csv"
            f1.write_text("COL1\n1\n", encoding="utf-8")
            f2 = root / "02_TABLE_B.csv"
            f2.write_text("COL2\n2\n", encoding="utf-8")

            discovered = discover_import_files(root)
            self.assertEqual(len(discovered), 2)
            tbl_names = [t[1] for t in discovered]
            self.assertIn("TABLE_A", tbl_names)
            self.assertIn("TABLE_B", tbl_names)

    def test_pre_validation_table_missing(self):
        from import_sql import validate_import_plan
        schema_metadata = {"EXISTING_TABLE": {"COL1": {"nullable": "Y", "data_default": None}}}
        file_plan = [(Path("01_NON_EXISTENT.csv"), "NON_EXISTENT")]
        errors = validate_import_plan(schema_metadata, file_plan)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["error_type"], "MISSING_TABLE")

    def test_pre_validation_unknown_column(self):
        from import_sql import validate_import_plan
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".csv", encoding="utf-8") as f:
            f.write("COL1,STRANGE_COL\n1,2\n")
            f_path = Path(f.name)
        schema_metadata = {
            "MY_TABLE": {
                "COL1": {"nullable": "Y", "data_default": None}
            }
        }
        errors = validate_import_plan(schema_metadata, [(f_path, "MY_TABLE")])
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["error_type"], "UNKNOWN_COLUMN_IN_CSV")
        f_path.unlink(missing_ok=True)

    def test_pre_validation_missing_mandatory_not_null_column(self):
        from import_sql import validate_import_plan
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".csv", encoding="utf-8") as f:
            f.write("COL1,COL2\nval1,val2\n")
            f_path = Path(f.name)
        schema_metadata = {
            "MY_TABLE": {
                "COL1": {"nullable": "Y", "data_default": None},
                "COL2": {"nullable": "Y", "data_default": None},
                "MANDATORY_COL": {"nullable": "N", "data_default": None}
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
                "CREATED_AT": {"nullable": "N", "data_default": "SYSDATE"}
            }
        }
        errors = validate_import_plan(schema_metadata, [(f_path, "MY_TABLE")])
        self.assertEqual(len(errors), 0)
        f_path.unlink(missing_ok=True)

    def test_format_validation_report(self):
        from import_sql import format_validation_report
        errors = [{
            "file": "test.csv",
            "table": "TEST_TBL",
            "error_type": "MISSING_TABLE",
            "details": "Table does not exist"
        }]
        report = format_validation_report(errors)
        self.assertIn("PRE-IMPORT VALIDATION REPORT", report)
        self.assertIn("MISSING_TABLE", report)

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
        self.assertEqual(mock_conn.commit.call_count, 2)
        csv_path.unlink(missing_ok=True)

    def test_import_single_file_commit_all(self):
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
            "commit_mode": "all",
            "batch_size": 1,
            "existing_data_action": "append",
            "on_error": "abort",
            "bad_rows_dir": "errors"
        }
        res = import_single_file(mock_conn, csv_path, "TEST_TABLE", table_meta, settings)
        self.assertEqual(res["imported"], 2)
        self.assertEqual(mock_conn.commit.call_count, 1)
        csv_path.unlink(missing_ok=True)

    def test_import_single_file_existing_data_truncate(self):
        from unittest.mock import MagicMock
        from import_sql import import_single_file
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".csv", encoding="utf-8") as f:
            f.write("ID\n1\n")
            csv_path = Path(f.name)
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        table_meta = {"ID": {"data_type": "NUMBER"}}
        settings = {
            "commit_mode": "all",
            "batch_size": 100,
            "existing_data_action": "truncate",
            "on_error": "abort",
            "bad_rows_dir": "errors"
        }
        import_single_file(mock_conn, csv_path, "TEST_TABLE", table_meta, settings)
        mock_cursor.execute.assert_any_call("TRUNCATE TABLE TEST_TABLE")
        csv_path.unlink(missing_ok=True)

    def test_import_single_file_skip_and_log_fallback(self):
        from unittest.mock import MagicMock
        from import_sql import import_single_file
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "data.csv"
            csv_path.write_text("ID\n1\n2\n", encoding="utf-8")
            
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.executemany.side_effect = Exception("Bulk insert failure")
            mock_cursor.execute.side_effect = [None, Exception("ORA-00001: unique constraint")]
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            
            err_dir = Path(tmpdir) / "errors"
            table_meta = {"ID": {"data_type": "NUMBER"}}
            settings = {
                "commit_mode": "batch",
                "batch_size": 100,
                "existing_data_action": "append",
                "on_error": "skip_and_log",
                "bad_rows_dir": str(err_dir)
            }
            res = import_single_file(mock_conn, csv_path, "TEST_TABLE", table_meta, settings)
            self.assertEqual(res["imported"], 1)
            self.assertEqual(res["failed"], 1)
            bad_file = err_dir / "TEST_TABLE_rejected.csv"
            self.assertTrue(bad_file.exists())
            content = bad_file.read_text(encoding="utf-8")
            self.assertIn("ORA-00001", content)


if __name__ == "__main__":
    unittest.main()
