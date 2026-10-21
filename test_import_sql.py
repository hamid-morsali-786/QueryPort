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

    def test_stream_csv_batches(self):
        from import_sql import stream_csv_batches
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".csv", encoding="utf-8-sig") as f:
            f.write("ID,NAME\n1,A\n2,B\n3,C\n4,D\n5,E\n")
            csv_path = Path(f.name)
        
        batches = list(stream_csv_batches(csv_path, batch_size=2))
        self.assertEqual(len(batches), 3)
        headers, rows1 = batches[0]
        self.assertEqual(headers, ["ID", "NAME"])
        self.assertEqual(len(rows1), 2)
        _, rows2 = batches[1]
        self.assertEqual(len(rows2), 2)
        _, rows3 = batches[2]
        self.assertEqual(len(rows3), 1)
        csv_path.unlink(missing_ok=True)

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


if __name__ == "__main__":
    unittest.main()
