import unittest
import datetime
import decimal
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

    def test_dry_run_and_confirm_flags(self):
        args = parse_args(["--dry-run", "--confirm"])
        self.assertTrue(args.dry_run)
        self.assertTrue(args.confirm)

    def test_schema_config_and_cli_override(self):
        cfg = {
            "database": {"user": "APP_USER", "password": "pwd", "schema": "CORE_SCHEMA"},
            "defaults": {}
        }
        # 1. Config default
        args = parse_args([])
        settings = resolve_settings(args, cfg)
        self.assertEqual(settings["database"]["schema"], "CORE_SCHEMA")

        # 2. CLI override via --schema / -s
        args_cli = parse_args(["--schema", "CUSTOM_SCHEMA"])
        settings_cli = resolve_settings(args_cli, cfg)
        self.assertEqual(settings_cli["database"]["schema"], "CUSTOM_SCHEMA")

    def test_create_connection_sets_current_schema(self):
        from unittest.mock import patch, MagicMock
        from export_sql import create_connection

        mock_conn = MagicMock()
        with patch("oracledb.connect", return_value=mock_conn) as mock_connect:
            db_cfg = {"user": "U", "password": "P", "dsn": "localhost/XE", "schema": "TARGET_SCHEMA"}
            conn = create_connection(db_cfg)
            self.assertEqual(conn.current_schema, "TARGET_SCHEMA")

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

    def test_comment_removal_preserves_spacing(self):
        from export_sql import clean_sql_script
        sql = "SELECT/*comment*/COL1 FROM T;"
        cleaned = clean_sql_script(sql)
        self.assertEqual(cleaned.strip(), "SELECT COL1 FROM T;")

    def test_semicolon_inside_string_literal(self):
        from export_sql import extract_queries
        sql = "SELECT * FROM T WHERE MSG = 'A; B'; SELECT * FROM T2;"
        queries = extract_queries(sql)
        self.assertEqual(len(queries), 2)
        self.assertIn("WHERE MSG = 'A; B'", queries[0][2])

    def test_quoted_table_name_extraction(self):
        from export_sql import extract_queries
        sql = 'SELECT * FROM "TARGET_SCHEMA"."BANKPARAMETERS";'
        queries = extract_queries(sql)
        self.assertEqual(queries[0][1], "BANKPARAMETERS")

    def test_set_column_not_stripped(self):
        from export_sql import clean_sql_script
        sql = "SELECT\nID,\nSET,\nNAME\nFROM T;"
        cleaned = clean_sql_script(sql)
        self.assertIn("SET", cleaned)


class TestExporters(unittest.TestCase):
    def test_format_oracle_literal(self):
        from export_sql import format_oracle_literal
        self.assertEqual(format_oracle_literal(None), "NULL")
        self.assertEqual(format_oracle_literal(123), "123")
        self.assertEqual(format_oracle_literal(45.67), "45.67")
        self.assertEqual(format_oracle_literal("Hello"), "'Hello'")
        self.assertEqual(format_oracle_literal("It's fine"), "'It''s fine'")
        d = datetime.date(2026, 10, 21)
        self.assertEqual(format_oracle_literal(d), "TO_DATE('2026-10-21', 'YYYY-MM-DD')")
        dt = datetime.datetime(2026, 10, 21, 14, 30, 0)
        self.assertEqual(format_oracle_literal(dt), "TO_TIMESTAMP('2026-10-21 14:30:00', 'YYYY-MM-DD HH24:MI:SS')")
        dt_micro = datetime.datetime(2026, 10, 21, 14, 30, 0, 123456)
        formatted_micro = format_oracle_literal(dt_micro)
        self.assertIn("14:30:00.123456", formatted_micro)
        self.assertIn("FF6", formatted_micro)
        dec = decimal.Decimal("123.45")
        self.assertEqual(format_oracle_literal(dec), "123.45")

    def test_csv_export_with_bom(self):
        from export_sql import export_to_csv
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
        from export_sql import export_to_insert
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


class TestOrchestrator(unittest.TestCase):
    def test_process_query_creates_outputs(self):
        from unittest.mock import MagicMock
        from export_sql import process_query
        
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

    def test_process_sql_file_creates_subfolder(self):
        from unittest.mock import MagicMock
        from export_sql import process_sql_file
        
        mock_cursor = MagicMock()
        mock_cursor.description = [("ID",)]
        mock_cursor.fetchmany.side_effect = [[[1]], []]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        with tempfile.TemporaryDirectory() as tmpdir:
            sql_file = Path(tmpdir) / "01_SAMPLE_DATA.sql"
            sql_file.write_text("SELECT ID FROM MY_TABLE;", encoding="utf-8")
            
            out_root = Path(tmpdir) / "exports"
            process_sql_file(sql_file, mock_conn, out_root, "csv", batch_size=100)
            
            expected_folder = out_root / "01_SAMPLE_DATA"
            expected_file = expected_folder / "01_MY_TABLE.csv"
            self.assertTrue(expected_folder.is_dir())
            self.assertTrue(expected_file.exists())

    def test_get_query_row_count(self):
        from unittest.mock import MagicMock
        from export_sql import get_query_row_count
        
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (42,)
        count = get_query_row_count(mock_cursor, "SELECT * FROM MY_TABLE;")
        mock_cursor.execute.assert_called_with("SELECT COUNT(*) FROM (SELECT * FROM MY_TABLE)")
        self.assertEqual(count, 42)

    def test_interactive_loop_exit(self):
        from unittest.mock import patch
        from export_sql import interactive_loop
        
        # Test choice 'n' followed by 'q'
        with patch("builtins.input", side_effect=["n", "q"]):
            # Should enter custom command mode and exit cleanly
            interactive_loop()

    def test_interactive_loop_default_yes(self):
        from unittest.mock import patch
        from export_sql import interactive_loop
        
        with patch("builtins.input", side_effect=["y", ""]):
            with patch("export_sql.main") as mock_main:
                interactive_loop()
                mock_main.assert_called_once_with([])


if __name__ == "__main__":
    unittest.main()
