"""
Generate crisp, beautiful vector terminal SVG mockups for QueryPort documentation.
Covers 100% of operational scenarios: Interactive, Export, Import, RAC, Fault Tolerance,
Lifecycle Policies, Transaction Commit Modes, and CLI Discoverability.
"""
from pathlib import Path
import html

COLOR_MAP = {
    "prompt": "#38bdf8",     # Sky blue for PS prompt
    "cmd": "#f8fafc",        # Bright white for command
    "flag": "#facc15",       # Amber for CLI flags
    "arg": "#93c5fd",        # Soft blue for arguments
    "dim": "#64748b",        # Slate gray for timestamps/separators
    "text": "#cbd5e1",       # Light gray for standard text
    "bold": "#ffffff",       # Pure white bold
    "info": "#38bdf8",       # Sky blue tag
    "success": "#4ade80",    # Mint green tag
    "warning": "#f59e0b",    # Amber warning
    "purple": "#c084fc",     # Lavender / RAC tag
    "table": "#94a3b8",      # Cool gray for table borders
    "num": "#a7f3d0",        # Mint number
    "err": "#f87171",        # Red for errors
}


def build_terminal_svg(
    title: str,
    lines: list,
    width: int = 920,
    font_size: int = 13,
    line_height: int = 22,
    padding_x: int = 24,
    padding_top: int = 56,
    padding_bottom: int = 24,
) -> str:
    total_height = padding_top + (len(lines) * line_height) + padding_bottom

    svg_parts = []
    svg_parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {total_height}" width="100%" height="100%" '
        f'style="background: transparent; font-family: \'JetBrains Mono\', \'Fira Code\', \'Cascadia Code\', Consolas, monospace;">'
    )
    svg_parts.append("""
    <defs>
      <filter id="card-shadow" x="-5%" y="-5%" width="110%" height="110%">
        <feDropShadow dx="0" dy="12" stdDeviation="16" flood-color="#000000" flood-opacity="0.45" />
      </filter>
    </defs>
    """)

    # Outer Container Window
    svg_parts.append(
        f'  <g filter="url(#card-shadow)">\n'
        f'    <rect x="10" y="10" width="{width - 20}" height="{total_height - 20}" rx="10" ry="10" '
        f'fill="#0a0f18" stroke="#1e293b" stroke-width="1.2" />\n'
        f'  </g>'
    )

    # Window Header Bar
    svg_parts.append(
        f'  <rect x="10" y="10" width="{width - 20}" height="38" rx="10" ry="10" fill="#111827" />\n'
        f'  <!-- Header bottom square fill to preserve round top corners -->\n'
        f'  <rect x="10" y="38" width="{width - 20}" height="10" fill="#111827" />\n'
        f'  <line x1="10" y1="48" x2="{width - 10}" y2="48" stroke="#1e293b" stroke-width="1" />'
    )

    # Window Buttons (macOS style traffic dots)
    svg_parts.append('  <circle cx="32" cy="29" r="6" fill="#ef4444" />')
    svg_parts.append('  <circle cx="52" cy="29" r="6" fill="#f59e0b" />')
    svg_parts.append('  <circle cx="72" cy="29" r="6" fill="#10b981" />')

    # Window Title
    escaped_title = html.escape(title)
    svg_parts.append(
        f'  <text x="{width // 2}" y="33" fill="#94a3b8" font-size="12" font-weight="500" '
        f'text-anchor="middle">{escaped_title}</text>'
    )

    # Terminal Content Lines
    y_pos = padding_top + 16
    for line in lines:
        if not line:  # Empty line
            y_pos += line_height
            continue

        spans_xml = []
        for style, text in line:
            color = COLOR_MAP.get(style, "#cbd5e1")
            font_weight = "bold" if style in ("bold", "cmd", "prompt") else "normal"
            escaped_text = html.escape(text)
            spans_xml.append(
                f'<tspan fill="{color}" font-weight="{font_weight}">{escaped_text}</tspan>'
            )

        full_spans = "".join(spans_xml)
        svg_parts.append(
            f'  <text x="{padding_x}" y="{y_pos}" font-size="{font_size}" xml:space="preserve">{full_spans}</text>'
        )
        y_pos += line_height

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def generate_all_terminal_mockups():
    assets_dir = Path("docs/assets")
    assets_dir.mkdir(parents=True, exist_ok=True)

    # =============================================================
    # 1. Interactive Mode (terminal_interactive.svg)
    # =============================================================
    lines_interactive = [
        [("prompt", "PS C:\\QueryPort> "), ("cmd", ".\\QueryPort.exe")],
        [],
        [("dim", "==================================================")],
        [("bold", "           QueryPort Unified Console              ")],
        [("dim", "==================================================")],
        [("text", "Select Operation:")],
        [("dim", "  [1 / E] : "), ("text", "Export Database queries to CSV / SQL Insert (config.json)")],
        [("dim", "  [2 / I] : "), ("text", "Import CSV datasets into Database tables  (config.json)")],
        [("dim", "  [exit/q]: "), ("text", "Exit program")],
        [],
        [("prompt", "Enter choice: "), ("cmd", "2")],
        [],
        [("info", "=== QueryPort - Oracle CSV Importer ===")],
        [("text", "Target Path    : "), ("bold", "imports/sales_data.csv")],
        [("text", "Target Schema  : "), ("arg", "APP_USER")],
        [("text", "Commit Mode    : "), ("text", "batch (Batch: 5000)")],
        [("text", "Existing Data  : "), ("text", "append")],
        [("text", "Error Strategy : "), ("text", "abort")],
        [("dim", "--------------------------------------------------------------------------------")],
        [("success", "[OK] "), ("text", "Connected to Oracle Database successfully (Thin direct TCP).")],
        [("text", "Running pre-import data dictionary validation...")],
        [("success", "[OK] "), ("text", "All tables and column structures verified successfully.")],
        [],
        [("dim", "    -> [SALES_DATA] Result: "), ("num", "154,200 rows"), ("text", " imported in "), ("success", "6.42s")],
        [],
        [("dim", "================================================================================")],
        [("bold", "                         IMPORT SUMMARY EXECUTION REPORT                        ")],
        [("dim", "================================================================================")],
        [("text", "Target Schema: APP_USER | Commit Mode: batch")],
        [("dim", "--------------------------------------------------------------------------------")],
        [("text", "No.  Table Name                Read Rows    Imported     Failed     Duration  ")],
        [("dim", "--------------------------------------------------------------------------------")],
        [("dim", "01   "), ("text", "SALES_DATA                "), ("num", "154,200      "), ("success", "154,200      "), ("text", "0          "), ("num", "6.42s     ")],
        [("dim", "--------------------------------------------------------------------------------")],
        [("bold", "TOTALS: 1 Tables | 154,200 Read | 154,200 Imported | 0 Failed in 6.42s")],
        [("dim", "================================================================================")],
    ]
    svg_interactive = build_terminal_svg("QueryPort - Unified Interactive Console", lines_interactive, width=900)
    (assets_dir / "terminal_interactive.svg").write_text(svg_interactive, encoding="utf-8")

    # =============================================================
    # 2. Query Export Mode (terminal_export.svg)
    # =============================================================
    lines_export = [
        [
            ("prompt", "PS C:\\QueryPort> "),
            ("cmd", ".\\QueryPort.exe "),
            ("flag", "--path "),
            ("arg", "sql_queries "),
            ("flag", "--format "),
            ("arg", "both "),
            ("flag", "--batch-size "),
            ("num", "10000"),
        ],
        [],
        [("dim", "[10:14:02] "), ("info", "[CONFIG] "), ("text", "Loaded configuration from 'config.json' (Target Schema: APP_USER)")],
        [("dim", "[10:14:02] "), ("info", "[ORACLE] "), ("text", "Connected via direct TCP to "), ("bold", "db-prod.internal:1521/PROD_SRV")],
        [("dim", "[10:14:02] "), ("info", "[DISPATCH] "), ("text", "Discovered 3 SQL scripts in 'sql_queries/':")],
        [("dim", "           -> "), ("arg", "monthly_sales.sql"), ("dim", " (Complex analytical aggregation)")],
        [("dim", "           -> "), ("arg", "customer_audit.sql"), ("dim", " (Compliance transaction audit)")],
        [("dim", "           -> "), ("arg", "inventory_snapshot.sql"), ("dim", " (Warehouse inventory state)")],
        [],
        [("dim", "[10:14:03] "), ("info", "[EXEC]    "), ("text", "Processing [01/03]: 'monthly_sales.sql' [arraysize=10000]...")],
        [("dim", "[10:14:08] "), ("info", "[STREAM]  "), ("arg", "monthly_sales.sql: "), ("num", "100,000"), ("text", " rows fetched "), ("dim", "(Memory: 14.2 MB)")],
        [("dim", "[10:14:14] "), ("info", "[STREAM]  "), ("arg", "monthly_sales.sql: "), ("num", "250,000"), ("text", " rows fetched "), ("dim", "(Memory: 14.8 MB)")],
        [("dim", "[10:14:18] "), ("success", "[SUCCESS] "), ("text", "Exported "), ("arg", "monthly_sales.sql"), ("text", " -> "), ("bold", "exports/monthly_sales/01_SALES.csv"), ("dim", " (284,120 rows) [15.2s]")],
        [("dim", "[10:14:19] "), ("success", "[SUCCESS] "), ("text", "Exported "), ("arg", "monthly_sales.sql"), ("text", " -> "), ("bold", "exports/monthly_sales/01_SALES_insert.sql"), ("dim", " (INSERT Script) [Done]")],
        [("dim", "[10:14:21] "), ("success", "[SUCCESS] "), ("text", "Exported "), ("arg", "customer_audit.sql"), ("text", " -> "), ("bold", "exports/customer_audit/01_AUDIT.csv"), ("dim", " (51,430 rows) [8.1s]")],
        [("dim", "[10:14:26] "), ("success", "[SUCCESS] "), ("text", "Exported "), ("arg", "inventory_snapshot.sql"), ("text", " -> "), ("bold", "exports/inventory_snapshot/01_INVENTORY.csv"), ("dim", " (92,100 rows) [11.4s]")],
        [],
        [("dim", "============================ EXPORT SUMMARY ============================")],
        [("bold", "Total Files   : "), ("text", "3 files processed (100% successful)")],
        [("bold", "Total Records : "), ("num", "427,650 rows"), ("dim", " (Streamed with constant memory footprint)")],
        [("bold", "Execution Time: "), ("num", "23.4 seconds"), ("dim", " | "), ("bold", "Effective Throughput: "), ("success", "18,275 rows/sec")],
        [("dim", "========================================================================")],
    ]
    svg_export = build_terminal_svg("QueryPort - High-Throughput Streaming Export", lines_export, width=920)
    (assets_dir / "terminal_export.svg").write_text(svg_export, encoding="utf-8")

    # =============================================================
    # 3. Export Dry-Run & Confirmation (terminal_export_confirm.svg)
    # =============================================================
    lines_export_confirm = [
        [
            ("prompt", "PS C:\\QueryPort> "),
            ("cmd", ".\\QueryPort.exe "),
            ("flag", "--path "),
            ("arg", "sql_queries "),
            ("flag", "--confirm"),
        ],
        [],
        [("dim", "[11:05:01] "), ("info", "[CONFIG] "), ("text", "Loaded configuration from 'config.json' (Target Schema: APP_USER)")],
        [("dim", "[11:05:01] "), ("info", "[ORACLE] "), ("text", "Connected to Oracle 19c Enterprise Edition via Thin Mode")],
        [("dim", "[11:05:02] "), ("info", "[PREVIEW] "), ("text", "Inspecting queries and checking target row counts...")],
        [("dim", "--------------------------------------------------------------------------------")],
        [("dim", "  [01] "), ("bold", "monthly_sales.sql       "), ("dim", "-> "), ("num", "284,120 rows")],
        [("dim", "  [02] "), ("bold", "customer_audit.sql      "), ("dim", "-> "), ("num", " 51,430 rows")],
        [("dim", "  [03] "), ("bold", "inventory_snapshot.sql  "), ("dim", "-> "), ("num", " 92,100 rows")],
        [("dim", "--------------------------------------------------------------------------------")],
        [("bold", "Total Estimated Rows: "), ("num", "427,650 rows"), ("text", " across 3 queries.")],
        [],
        [("prompt", "Proceed with export? [Y/n]: "), ("cmd", "Y")],
        [],
        [("dim", "[11:05:04] "), ("info", "[EXEC]    "), ("text", "Processing queries and streaming to 'exports/'...")],
        [("dim", "[11:05:12] "), ("success", "[SUCCESS] "), ("text", "Exported 01_SALES (284,120 rows)")],
        [("dim", "[11:05:16] "), ("success", "[SUCCESS] "), ("text", "Exported 02_AUDIT (51,430 rows)")],
        [("dim", "[11:05:22] "), ("success", "[SUCCESS] "), ("text", "Exported 03_INVENTORY (92,100 rows)")],
        [("dim", "[11:05:23] "), ("success", "[DONE]    "), ("bold", "Export completed successfully! "), ("num", "427,650 rows written.")],
    ]
    svg_export_confirm = build_terminal_svg("QueryPort - Export Row Count Preview & Confirmation", lines_export_confirm, width=900)
    (assets_dir / "terminal_export_confirm.svg").write_text(svg_export_confirm, encoding="utf-8")

    # =============================================================
    # 4. Export with Schema Override & INSERT Only (terminal_export_schema.svg)
    # =============================================================
    lines_export_schema = [
        [
            ("prompt", "PS C:\\QueryPort> "),
            ("cmd", ".\\QueryPort.exe "),
            ("flag", "--path "),
            ("arg", "sql_queries/daily_report.sql "),
            ("flag", "--format "),
            ("arg", "insert "),
            ("flag", "--schema "),
            ("purple", "FIN_REPORTING"),
        ],
        [],
        [("dim", "[11:12:10] "), ("info", "[CONFIG]  "), ("text", "Schema override active: "), ("purple", "FIN_REPORTING"), ("dim", " (Default in config was APP_USER)")],
        [("dim", "[11:12:10] "), ("info", "[ORACLE]  "), ("text", "Connected via direct TCP to Oracle 19c")],
        [("dim", "[11:12:11] "), ("purple", "[SESSION] "), ("text", "Executing: "), ("bold", "ALTER SESSION SET CURRENT_SCHEMA = FIN_REPORTING")],
        [("dim", "[11:12:11] "), ("success", "[OK]      "), ("text", "Current session schema switched to "), ("purple", "FIN_REPORTING")],
        [("dim", "[11:12:11] "), ("info", "[EXEC]    "), ("text", "Executing 'daily_report.sql' against FIN_REPORTING...")],
        [("dim", "[11:12:13] "), ("success", "[STREAM]  "), ("text", "Writing Oracle INSERT statements to "), ("bold", "exports/daily_report/01_GL_DAILY_insert.sql")],
        [("dim", "           -> Added "), ("arg", "SET DEFINE OFF;"), ("dim", " header (prevents & prompt triggers)")],
        [("dim", "           -> Handled NULLs, dates (TO_DATE), numbers and escaped single quotes ('')")],
        [("dim", "           -> Appended "), ("arg", "COMMIT;"), ("dim", " statement at script tail")],
        [],
        [("dim", "[11:12:14] "), ("success", "[DONE]    "), ("text", "Exported "), ("num", "15,400 rows"), ("text", " as clean SQL INSERT statements in "), ("num", "1.4s")],
    ]
    svg_export_schema = build_terminal_svg("QueryPort - Export with Schema Override & INSERT Format", lines_export_schema, width=920)
    (assets_dir / "terminal_export_schema.svg").write_text(svg_export_schema, encoding="utf-8")

    # =============================================================
    # 5. Import Dry-Run Pre-Validation (terminal_import_dryrun.svg)
    # =============================================================
    lines_dryrun = [
        [
            ("prompt", "PS C:\\QueryPort> "),
            ("cmd", ".\\QueryPort.exe "),
            ("bold", "import "),
            ("flag", "--path "),
            ("arg", "imports/customers.csv "),
            ("flag", "--dry-run"),
        ],
        [],
        [("dim", "[10:20:11] "), ("info", "[DRY-RUN] "), ("text", "Mode activated: "), ("warning", "NO DATABASE COMMITS OR WRITES WILL OCCUR")],
        [("dim", "[10:20:11] "), ("info", "[DETECT]  "), ("text", "Target table inferred from filename: "), ("bold", "CUSTOMERS")],
        [("dim", "[10:20:12] "), ("info", "[SCHEMA]  "), ("text", "Querying Oracle Data Dictionary (USER_TAB_COLUMNS)...")],
        [("dim", "[10:20:12] "), ("success", "[MATCH]   "), ("text", "Found Oracle table "), ("bold", "CUSTOMERS"), ("dim", " (All 6 CSV headers matched)")],
        [],
        [("table", "+---------------+-----------------+------------------+------------+-------------+")],
        [("table", "| "), ("bold", "CSV HEADER    "), ("table", "| "), ("bold", "ORACLE COLUMN    "), ("table", "| "), ("bold", "ORACLE DATA TYPE "), ("table", "| "), ("bold", "NULLABLE?   "), ("table", "| "), ("bold", "STATUS      "), ("table", "|")],
        [("table", "+---------------+-----------------+------------------+------------+-------------+")],
        [("table", "| "), ("text", "CUST_ID       "), ("table", "| "), ("arg", "CUST_ID         "), ("table", "| "), ("dim", "NUMBER(10)       "), ("table", "| "), ("text", "NO (PK)     "), ("table", "| "), ("success", "OK (Integer)"), ("table", "|")],
        [("table", "| "), ("text", "FULL_NAME     "), ("table", "| "), ("arg", "FULL_NAME       "), ("table", "| "), ("dim", "VARCHAR2(100)    "), ("table", "| "), ("text", "NO          "), ("table", "| "), ("success", "OK (String) "), ("table", "|")],
        [("table", "| "), ("text", "EMAIL         "), ("table", "| "), ("arg", "EMAIL           "), ("table", "| "), ("dim", "VARCHAR2(150)    "), ("table", "| "), ("text", "YES         "), ("table", "| "), ("success", "OK (String) "), ("table", "|")],
        [("table", "| "), ("text", "BALANCE       "), ("table", "| "), ("arg", "BALANCE         "), ("table", "| "), ("dim", "NUMBER(12,2)     "), ("table", "| "), ("text", "YES         "), ("table", "| "), ("success", "OK (Decimal)"), ("table", "|")],
        [("table", "| "), ("text", "CREATED_AT    "), ("table", "| "), ("arg", "CREATED_AT      "), ("table", "| "), ("dim", "DATE             "), ("table", "| "), ("text", "NO          "), ("table", "| "), ("success", "OK (Date/TS)"), ("table", "|")],
        [("table", "| "), ("text", "STATUS_CODE   "), ("table", "| "), ("arg", "STATUS_CODE     "), ("table", "| "), ("dim", "VARCHAR2(10)     "), ("table", "| "), ("text", "YES         "), ("table", "| "), ("success", "OK (String) "), ("table", "|")],
        [("table", "+---------------+-----------------+------------------+------------+-------------+")],
        [],
        [("dim", "[10:20:12] "), ("info", "[PREVIEW] "), ("text", "Parsed and validated first 2 sample records:")],
        [("dim", "           Row 1: "), ("text", "(1001, 'Arash Rad', 'arash@corp.ir', 1450000.00, 2026-03-01, 'ACTIVE')")],
        [("dim", "           Row 2: "), ("text", "(1002, 'Sara Tehrani', 'sara@corp.ir', 820000.50, 2026-03-02, 'ACTIVE')")],
        [],
        [("dim", "[10:20:12] "), ("success", "[VERIFIED] "), ("bold", "Pre-validation Successful!"), ("text", " 0 schema mismatches. Safe to execute full import.")],
    ]
    svg_dryrun = build_terminal_svg("QueryPort - Schema Pre-Validation & Dry-Run", lines_dryrun, width=910)
    (assets_dir / "terminal_import_dryrun.svg").write_text(svg_dryrun, encoding="utf-8")

    # =============================================================
    # 6. Multi-File Parallel Ingestion (terminal_import_multifile.svg)
    # =============================================================
    lines_multifile = [
        [
            ("prompt", "PS C:\\QueryPort> "),
            ("cmd", ".\\QueryPort.exe "),
            ("bold", "import "),
            ("flag", "--path "),
            ("arg", "imports/ "),
            ("flag", "--workers "),
            ("num", "4 "),
            ("flag", "--commit-mode "),
            ("arg", "batch "),
            ("flag", "--batch-size "),
            ("num", "5000"),
        ],
        [],
        [("info", "=== QueryPort - Oracle CSV Importer ===")],
        [("text", "Target Path    : "), ("bold", "imports/ (4 file(s) found)")],
        [("text", "Target Schema  : "), ("arg", "APP_USER")],
        [("text", "Commit Mode    : "), ("text", "batch (Batch: 5000)")],
        [("text", "Existing Data  : "), ("text", "append")],
        [("text", "Error Strategy : "), ("text", "abort")],
        [("text", "Concurrency    : "), ("purple", "4 workers (Inter-File Parallel Ingestion)")],
        [("dim", "--------------------------------------------------------------------------------")],
        [("success", "[OK] "), ("text", "Connected to Oracle Database successfully.")],
        [("text", "Running pre-import data dictionary validation...")],
        [("success", "[OK] "), ("text", "All 4 target tables and column structures verified successfully.")],
        [],
        [("purple", "Parallel Ingestion (4 workers) across 4 files ...")],
        [("dim", "  -> "), ("purple", "[Worker-1] "), ("bold", "CUSTOMERS.csv    : "), ("num", " 50,000 rows"), ("text", " imported in "), ("num", "3.12s")],
        [("dim", "  -> "), ("purple", "[Worker-2] "), ("bold", "PRODUCTS.csv     : "), ("num", " 12,450 rows"), ("text", " imported in "), ("num", "1.05s")],
        [("dim", "  -> "), ("purple", "[Worker-3] "), ("bold", "TRANSACTIONS.csv : "), ("num", "180,000 rows"), ("text", " imported in "), ("num", "9.40s")],
        [("dim", "  -> "), ("purple", "[Worker-4] "), ("bold", "REGIONS.csv      : "), ("num", "    840 rows"), ("text", " imported in "), ("num", "0.18s")],
        [],
        [("dim", "================================================================================")],
        [("bold", "                         IMPORT SUMMARY EXECUTION REPORT                        ")],
        [("dim", "================================================================================")],
        [("text", "Target Schema: APP_USER | Commit Mode: batch")],
        [("dim", "--------------------------------------------------------------------------------")],
        [("text", "No.  Table Name                Read Rows    Imported     Failed     Duration  ")],
        [("dim", "--------------------------------------------------------------------------------")],
        [("dim", "01   "), ("text", "CUSTOMERS                 "), ("num", "50,000       "), ("success", "50,000       "), ("text", "0          "), ("num", "3.12s     ")],
        [("dim", "02   "), ("text", "PRODUCTS                  "), ("num", "12,450       "), ("success", "12,450       "), ("text", "0          "), ("num", "1.05s     ")],
        [("dim", "03   "), ("text", "TRANSACTIONS              "), ("num", "180,000      "), ("success", "180,000      "), ("text", "0          "), ("num", "9.40s     ")],
        [("dim", "04   "), ("text", "REGIONS                   "), ("num", "840          "), ("success", "840          "), ("text", "0          "), ("num", "0.18s     ")],
        [("dim", "--------------------------------------------------------------------------------")],
        [("bold", "TOTALS: 4 Tables | 243,290 Read | 243,290 Imported | 0 Failed in 9.42s")],
        [("dim", "================================================================================")],
    ]
    svg_multifile = build_terminal_svg("QueryPort - Multi-File Parallel Ingestion", lines_multifile, width=900)
    (assets_dir / "terminal_import_multifile.svg").write_text(svg_multifile, encoding="utf-8")

    # =============================================================
    # 7. RAC Affinity & Intra-Table Chunking (terminal_concurrency_rac.svg)
    # =============================================================
    lines_rac = [
        [
            ("prompt", "PS C:\\QueryPort> "),
            ("cmd", ".\\QueryPort.exe "),
            ("bold", "import "),
            ("flag", "--path "),
            ("arg", "imports/tx_huge.csv "),
            ("flag", "--workers "),
            ("num", "4 "),
            ("flag", "--rac-services "),
            ("purple", "APP_NODE1_SRV,APP_NODE2_SRV "),
            ("flag", "--intra-table"),
        ],
        [],
        [("dim", "[10:32:00] "), ("purple", "[RAC CLUSTER] "), ("text", "Detected 2 Oracle RAC services. Dynamic connection dispatch active:")],
        [("dim", "              -> Node 1: "), ("bold", "APP_NODE1_SRV"), ("dim", " (Dedicated Buffer Cache on RAC Node #1)")],
        [("dim", "              -> Node 2: "), ("bold", "APP_NODE2_SRV"), ("dim", " (Dedicated Buffer Cache on RAC Node #2)")],
        [("dim", "[10:32:00] "), ("info", "[PARTITION]   "), ("text", "Intra-table chunking active for 'tx_huge.csv' (1,200,000 rows)")],
        [("dim", "[10:32:00] "), ("info", "[AFFINITY]    "), ("purple", "Worker-1, Worker-3 -> APP_NODE1_SRV"), ("dim", " | "), ("purple", "Worker-2, Worker-4 -> APP_NODE2_SRV")],
        [],
        [("dim", "[10:32:04] "), ("purple", "[Worker-1/Node1] "), ("text", "Chunk #01 (rows 1-25,000) committed via executemany "), ("dim", "[1.9s]")],
        [("dim", "[10:32:04] "), ("purple", "[Worker-2/Node2] "), ("text", "Chunk #02 (rows 25,001-50,000) committed via executemany "), ("dim", "[1.8s]")],
        [("dim", "[10:32:07] "), ("purple", "[Worker-3/Node1] "), ("text", "Chunk #03 (rows 50,001-75,000) committed via executemany "), ("dim", "[2.0s]")],
        [("dim", "[10:32:07] "), ("purple", "[Worker-4/Node2] "), ("text", "Chunk #04 (rows 75,001-100,000) committed via executemany "), ("dim", "[1.9s]")],
        [("dim", "           ... [Stream processing 48 chunks concurrently without GC buffer contention] ...")],
        [("dim", "[10:33:14] "), ("success", "[PROGRESS]       "), ("text", "Completed 1,200,000 / 1,200,000 rows (100%) - "), ("success", "0 Bad Rows")],
        [],
        [("dim", "=========================== RAC INGESTION REPORT ===========================")],
        [("bold", "Total Rows Inserted : "), ("num", "1,200,000 rows"), ("dim", " (Bulk executemany in 5,000 batches)")],
        [("bold", "Bad Records / Errs  : "), ("success", "0 rejected rows"), ("dim", " (Zero errors logged)")],
        [("bold", "RAC Node 1 Load     : "), ("purple", "600,000 rows (50.0%)"), ("dim", " across 24 chunks")],
        [("bold", "RAC Node 2 Load     : "), ("purple", "600,000 rows (50.0%)"), ("dim", " across 24 chunks")],
        [("bold", "Total Execution Time: "), ("num", "74.2 seconds")],
        [("bold", "Effective Throughput: "), ("success", "16,172 rows/sec"), ("dim", " (Zero Global Cache Contention)")],
        [("dim", "============================================================================")],
    ]
    svg_rac = build_terminal_svg("QueryPort - Oracle RAC Concurrency & Intra-Table Load Balancing", lines_rac, width=930)
    (assets_dir / "terminal_concurrency_rac.svg").write_text(svg_rac, encoding="utf-8")

    # =============================================================
    # 8. Fault-Tolerant Ingestion & Bad Rows Logging (terminal_import_skip_and_log.svg)
    # =============================================================
    lines_skip_and_log = [
        [
            ("prompt", "PS C:\\QueryPort> "),
            ("cmd", ".\\QueryPort.exe "),
            ("bold", "import "),
            ("flag", "--path "),
            ("arg", "imports/orders_dirty.csv "),
            ("flag", "--on-error "),
            ("warning", "skip_and_log"),
        ],
        [],
        [("info", "=== QueryPort - Oracle CSV Importer ===")],
        [("text", "Target Path    : "), ("bold", "imports/orders_dirty.csv (1 file)")],
        [("text", "Commit Mode    : "), ("text", "batch (Batch: 1000)")],
        [("text", "Error Strategy : "), ("warning", "skip_and_log (Fault-Tolerant Quarantine Active)")],
        [("dim", "--------------------------------------------------------------------------------")],
        [("success", "[OK] "), ("text", "Connected to Oracle Database successfully.")],
        [("text", "Running pre-import data dictionary validation...")],
        [("success", "[OK] "), ("text", "Table 'ORDERS' verified. Starting ingestion with row-level fallback...")],
        [],
        [("warning", "[WARN] "), ("dim", "Row 1,420: "), ("err", "ORA-01400: cannot insert NULL into (\"APP_USER\".\"ORDERS\".\"CUST_ID\")")],
        [("dim", "       -> Isolated to: "), ("arg", "import_errors/ORDERS_errors_20261027_140522.csv")],
        [("warning", "[WARN] "), ("dim", "Row 8,912: "), ("err", "ORA-00001: unique constraint (APP_USER.PK_ORDERS) violated")],
        [("dim", "       -> Isolated to: "), ("arg", "import_errors/ORDERS_errors_20261027_140522.csv")],
        [],
        [("dim", "================================================================================")],
        [("bold", "                         IMPORT SUMMARY EXECUTION REPORT                        ")],
        [("dim", "================================================================================")],
        [("text", "Target Schema: APP_USER | Error Strategy: skip_and_log")],
        [("dim", "--------------------------------------------------------------------------------")],
        [("text", "No.  Table Name                Read Rows    Imported     Failed     Duration  ")],
        [("dim", "--------------------------------------------------------------------------------")],
        [("dim", "01   "), ("text", "ORDERS                    "), ("num", "50,000       "), ("success", "49,998       "), ("err", "2          "), ("num", "4.15s     ")],
        [("dim", "--------------------------------------------------------------------------------")],
        [("bold", "TOTALS: 1 Tables | 50,000 Read | 49,998 Imported | "), ("err", "2 Failed"), ("bold", " in 4.15s")],
        [("dim", "================================================================================")],
        [("info", "[QUARANTINE] "), ("bold", "2 bad rows isolated in: "), ("arg", "import_errors/ORDERS_errors_20261027_140522.csv")],
    ]
    svg_skip_and_log = build_terminal_svg("QueryPort - Fault-Tolerant Ingestion & Bad Row Quarantine", lines_skip_and_log, width=920)
    (assets_dir / "terminal_import_skip_and_log.svg").write_text(svg_skip_and_log, encoding="utf-8")

    # =============================================================
    # 9. Existing Data Lifecycle: Truncate / Skip (terminal_import_existing_data.svg)
    # =============================================================
    lines_existing_data = [
        [
            ("prompt", "PS C:\\QueryPort> "),
            ("cmd", ".\\QueryPort.exe "),
            ("bold", "import "),
            ("flag", "--path "),
            ("arg", "imports/ref_rates.csv "),
            ("flag", "--existing-data "),
            ("warning", "truncate"),
        ],
        [],
        [("info", "=== QueryPort - Oracle CSV Importer ===")],
        [("text", "Target Path    : "), ("bold", "imports/ref_rates.csv")],
        [("text", "Target Table   : "), ("bold", "REF_RATES")],
        [("text", "Existing Data  : "), ("warning", "truncate (Atomic Table Refresh)")],
        [("dim", "--------------------------------------------------------------------------------")],
        [("success", "[OK] "), ("text", "Connected to Oracle Database successfully.")],
        [("dim", "[11:25:01] "), ("info", "[CHECK]  "), ("text", "Checking existing row count in table 'REF_RATES'...")],
        [("dim", "[11:25:01] "), ("warning", "[FOUND]  "), ("text", "Table 'REF_RATES' currently contains "), ("num", "1,250 rows")],
        [("dim", "[11:25:01] "), ("purple", "[DDL]    "), ("bold", "Executing atomic: TRUNCATE TABLE REF_RATES")],
        [("dim", "[11:25:02] "), ("success", "[OK]     "), ("text", "Table 'REF_RATES' truncated cleanly in "), ("num", "0.04s")],
        [("dim", "[11:25:02] "), ("info", "[INGEST] "), ("text", "Streaming 1,280 fresh reference rows into clean table...")],
        [("dim", "           -> [REF_RATES] Result: "), ("num", "1,280 rows"), ("text", " imported in "), ("success", "0.12s")],
        [],
        [("dim", "[11:25:02] "), ("success", "[SUCCESS] "), ("bold", "Table refresh completed successfully. Zero storage fragmentation.")],
    ]
    svg_existing_data = build_terminal_svg("QueryPort - Existing Data Policy: Atomic Truncate", lines_existing_data, width=900)
    (assets_dir / "terminal_import_existing_data.svg").write_text(svg_existing_data, encoding="utf-8")

    # =============================================================
    # 10. Commit Modes: Atomic 'commit-mode all' (terminal_import_commit_all.svg)
    # =============================================================
    lines_commit_all = [
        [
            ("prompt", "PS C:\\QueryPort> "),
            ("cmd", ".\\QueryPort.exe "),
            ("bold", "import "),
            ("flag", "--path "),
            ("arg", "imports/gl_journal.csv "),
            ("flag", "--commit-mode "),
            ("success", "all"),
        ],
        [],
        [("info", "=== QueryPort - Oracle CSV Importer ===")],
        [("text", "Target Path    : "), ("bold", "imports/gl_journal.csv")],
        [("text", "Commit Mode    : "), ("success", "all (Single Atomic Transaction Guarantee)")],
        [("text", "Existing Data  : "), ("text", "append")],
        [("dim", "--------------------------------------------------------------------------------")],
        [("success", "[OK] "), ("text", "Connected to Oracle Database successfully.")],
        [("dim", "[11:30:00] "), ("info", "[TX]     "), ("text", "Transaction initiated. Auto-commit disabled.")],
        [("dim", "[11:30:01] "), ("info", "[STREAM] "), ("text", "Streaming chunk 1 (rows 1-5,000)... "), ("dim", "[Buffer buffered in Undo]")],
        [("dim", "[11:30:02] "), ("info", "[STREAM] "), ("text", "Streaming chunk 2 (rows 5,001-10,000)... "), ("dim", "[Buffer buffered in Undo]")],
        [("dim", "[11:30:03] "), ("info", "[STREAM] "), ("text", "Streaming chunk 3 (rows 10,001-14,500)... "), ("dim", "[Buffer buffered in Undo]")],
        [("dim", "[11:30:03] "), ("purple", "[VERIFY] "), ("text", "All 14,500 rows inserted without error. Issuing single final COMMIT...")],
        [("dim", "[11:30:04] "), ("success", "[COMMIT] "), ("bold", "Transaction committed atomically. Data integrity guaranteed.")],
        [],
        [("dim", "================================================================================")],
        [("bold", "TOTALS: 1 Tables | 14,500 Read | 14,500 Imported | 0 Failed in 3.65s (Atomic)")],
        [("dim", "================================================================================")],
    ]
    svg_commit_all = build_terminal_svg("QueryPort - Atomic All-or-Nothing Transaction Mode", lines_commit_all, width=900)
    (assets_dir / "terminal_import_commit_all.svg").write_text(svg_commit_all, encoding="utf-8")

    # =============================================================
    # 11. CLI Help & Option Discovery (terminal_help.svg)
    # =============================================================
    lines_help = [
        [("prompt", "PS C:\\QueryPort> "), ("cmd", ".\\QueryPort.exe "), ("bold", "import "), ("flag", "--help")],
        [],
        [("bold", "usage: QueryPort.exe import [-h] [--config CONFIG_PATH] [--path INPUT_PATH]")],
        [("bold", "                            [--commit-mode {batch,row,all}] [--batch-size BATCH_SIZE]")],
        [("bold", "                            [--existing-data {append,truncate,skip}]")],
        [("bold", "                            [--on-error {abort,skip_and_log}] [--schema SCHEMA]")],
        [("bold", "                            [--dry-run] [--workers WORKERS] [--chunk-size CHUNK_SIZE]")],
        [("bold", "                            [--rac-services RAC_SERVICES] [--intra-table]")],
        [],
        [("text", "Validate and import CSV datasets into Oracle Database tables.")],
        [],
        [("bold", "options:")],
        [("flag", "  -h, --help            "), ("text", "show this help message and exit")],
        [("flag", "  --config CONFIG_PATH  "), ("text", "Path to JSON config file (default: config.json)")],
        [("flag", "  --path INPUT_PATH     "), ("text", "Path to import CSV file or directory containing CSV files")],
        [("flag", "  --commit-mode {batch,row,all}")],
        [("dim", "                        "), ("text", "Commit mode: 'batch' (default), 'row', or 'all'")],
        [("flag", "  --batch-size BATCH    "), ("text", "Batch size for bulk insertion (default: 5000)")],
        [("flag", "  --existing-data {append,truncate,skip}")],
        [("dim", "                        "), ("text", "Action on existing data: 'append' (default), 'truncate', or 'skip'")],
        [("flag", "  --on-error {abort,skip_and_log}")],
        [("dim", "                        "), ("text", "Error strategy: 'abort' (default) or 'skip_and_log'")],
        [("flag", "  --schema SCHEMA       "), ("text", "Target database schema for tables (defaults to config)")],
        [("flag", "  --dry-run, -d         "), ("text", "Run pre-validation and row counts without modifying tables")],
        [("flag", "  --workers WORKERS, -w "), ("text", "Number of concurrent worker threads (default: 1)")],
        [("flag", "  --chunk-size CHUNK    "), ("text", "Number of rows per chunk for intra-table parallelism (default: 25000)")],
        [("flag", "  --rac-services RAC    "), ("text", "Comma-separated list of Oracle RAC service names for workload routing")],
        [("flag", "  --intra-table         "), ("text", "Enable parallel intra-table chunk streaming for large CSV files")],
    ]
    svg_help = build_terminal_svg("QueryPort - CLI Help & Flag Matrix", lines_help, width=920)
    (assets_dir / "terminal_help.svg").write_text(svg_help, encoding="utf-8")

    print("[SUCCESS] All 11 terminal SVGs generated successfully in docs/assets/!")


if __name__ == "__main__":
    generate_all_terminal_mockups()
