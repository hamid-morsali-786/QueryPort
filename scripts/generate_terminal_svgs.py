"""
Generate crisp, beautiful vector terminal SVG mockups for QueryPort documentation.
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
    "err": "#f87171",        # Red
}


def build_terminal_svg(
    title: str,
    lines: list,
    width: int = 900,
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

    # -------------------------------------------------------------
    # 1. Interactive Mode (terminal_interactive.svg)
    # -------------------------------------------------------------
    lines_interactive = [
        [("prompt", "PS C:\\QueryPort> "), ("cmd", ".\\QueryPort.exe")],
        [],
        [("dim", "==========================================================================")],
        [("bold", "  QueryPort - Oracle Database High-Performance ETL Engine (v2.0)")],
        [("dim", "==========================================================================")],
        [("info", "[i] "), ("text", "Connected to : "), ("bold", "PROD_ORACLE_DB"), ("dim", " (Oracle 19c Enterprise Edition Release 19.3.0.0.0)")],
        [("info", "[i] "), ("text", "Database Role: "), ("bold", "RAC Primary Cluster"), ("dim", " (2 Active Nodes detected)")],
        [("info", "[i] "), ("text", "Session Mode : "), ("success", "Thin Client (Direct TCP)"), ("dim", " | Character Set: AL32UTF8")],
        [],
        [("bold", "Select execution mode:")],
        [("dim", "  [1] "), ("text", "Export SQL Queries to CSV / Excel")],
        [("dim", "  [2] "), ("text", "Import Files into Database (Table Auto-Detect)")],
        [("dim", "  [3] "), ("text", "Validate Schema & Dry-Run Ingestion (Zero Risk)")],
        [("dim", "  [4] "), ("text", "Exit")],
        [],
        [("prompt", "Enter choice [1-4] (default: 1): "), ("bold", "2")],
        [("prompt", "Directory path to import [default: imports]: "), ("arg", "data/sales_q3")],
        [("prompt", "Target table name [default: auto-detect from filename]: "), ("bold", "SALES_ORDERS")],
        [("prompt", "Enter concurrency level (workers) [default: 4]: "), ("bold", "4")],
        [("prompt", "Enable intra-table chunk streaming? [Y/n]: "), ("bold", "Y")],
        [("prompt", "Batch size for executemany [default: 1000]: "), ("bold", "5000")],
        [],
        [("info", "[*] Initializing 4 parallel worker threads with streaming queues...")],
        [("success", "[+] Ready. Ingestion started successfully.")],
    ]

    svg_interactive = build_terminal_svg(
        title="QueryPort - Interactive Console Mode",
        lines=lines_interactive,
        width=880,
    )
    (assets_dir / "terminal_interactive.svg").write_text(svg_interactive, encoding="utf-8")

    # -------------------------------------------------------------
    # 2. Query Export Mode (terminal_export.svg)
    # -------------------------------------------------------------
    lines_export = [
        [
            ("prompt", "PS C:\\QueryPort> "),
            ("cmd", ".\\QueryPort.exe "),
            ("flag", "--path "),
            ("arg", "sql_queries "),
            ("flag", "--format "),
            ("arg", "both "),
            ("flag", "--batch-size "),
            ("num", "10000 "),
            ("flag", "--workers "),
            ("num", "4"),
        ],
        [],
        [("dim", "[10:14:02] "), ("info", "[CONFIG] "), ("text", "Loaded configuration from 'config.json' (Environment: Production)")],
        [("dim", "[10:14:02] "), ("info", "[ORACLE] "), ("text", "Connected via direct TCP to "), ("bold", "db-prod.internal:1521/SRV_REPORTING")],
        [("dim", "[10:14:02] "), ("info", "[DISPATCH] "), ("text", "Discovered 3 SQL scripts in 'sql_queries/':")],
        [("dim", "           -> "), ("arg", "monthly_sales.sql"), ("dim", " (Complex analytical aggregation)")],
        [("dim", "           -> "), ("arg", "customer_audit.sql"), ("dim", " (Compliance transaction audit)")],
        [("dim", "           -> "), ("arg", "inventory_snapshot.sql"), ("dim", " (Warehouse inventory state)")],
        [],
        [("dim", "[10:14:03] "), ("purple", "[Worker-1] "), ("text", "Executing 'monthly_sales.sql' [arraysize=10000]...")],
        [("dim", "[10:14:03] "), ("purple", "[Worker-2] "), ("text", "Executing 'customer_audit.sql' [arraysize=10000]...")],
        [("dim", "[10:14:03] "), ("purple", "[Worker-3] "), ("text", "Executing 'inventory_snapshot.sql' [arraysize=10000]...")],
        [],
        [("dim", "[10:14:08] "), ("info", "[STREAM]  "), ("arg", "monthly_sales.sql: "), ("num", "100,000"), ("text", " rows fetched "), ("dim", "(Memory: 14.2 MB)")],
        [("dim", "[10:14:14] "), ("info", "[STREAM]  "), ("arg", "monthly_sales.sql: "), ("num", "250,000"), ("text", " rows fetched "), ("dim", "(Memory: 14.8 MB)")],
        [("dim", "[10:14:18] "), ("success", "[SUCCESS] "), ("text", "Exported "), ("arg", "monthly_sales.sql"), ("text", " -> "), ("bold", "exports/monthly_sales.csv"), ("dim", " (284,120 rows) [15.2s]")],
        [("dim", "[10:14:19] "), ("success", "[SUCCESS] "), ("text", "Exported "), ("arg", "monthly_sales.sql"), ("text", " -> "), ("bold", "exports/monthly_sales.xlsx"), ("dim", " (Formatted Sheet) [Done]")],
        [("dim", "[10:14:21] "), ("success", "[SUCCESS] "), ("text", "Exported "), ("arg", "customer_audit.sql"), ("text", " -> "), ("bold", "exports/customer_audit.csv"), ("dim", " (51,430 rows) [8.1s]")],
        [("dim", "[10:14:26] "), ("success", "[SUCCESS] "), ("text", "Exported "), ("arg", "inventory_snapshot.sql"), ("text", " -> "), ("bold", "exports/inventory_snapshot.csv"), ("dim", " (92,100 rows) [11.4s]")],
        [],
        [("dim", "============================ EXPORT SUMMARY ============================")],
        [("bold", "Total Files   : "), ("text", "3 files processed (100% successful)")],
        [("bold", "Total Records : "), ("num", "427,650 rows"), ("dim", " (Streamed with constant memory footprint)")],
        [("bold", "Execution Time: "), ("num", "23.4 seconds"), ("dim", " | "), ("bold", "Effective Throughput: "), ("success", "18,275 rows/sec")],
        [("dim", "========================================================================")],
    ]

    svg_export = build_terminal_svg(
        title="QueryPort - High-Throughput Parallel Export",
        lines=lines_export,
        width=920,
    )
    (assets_dir / "terminal_export.svg").write_text(svg_export, encoding="utf-8")

    # -------------------------------------------------------------
    # 3. Dry-Run Schema Pre-Validation (terminal_import_dryrun.svg)
    # -------------------------------------------------------------
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

    svg_dryrun = build_terminal_svg(
        title="QueryPort - Schema Pre-Validation & Dry-Run",
        lines=lines_dryrun,
        width=910,
    )
    (assets_dir / "terminal_import_dryrun.svg").write_text(svg_dryrun, encoding="utf-8")

    # -------------------------------------------------------------
    # 4. RAC Affinity & Parallel Concurrency (terminal_concurrency_rac.svg)
    # -------------------------------------------------------------
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
        [("bold", "Bad Records / Errs  : "), ("success", "0 rejected rows"), ("dim", " (Logged to bad_records.log)")],
        [("bold", "RAC Node 1 Load     : "), ("purple", "600,000 rows (50.0%)"), ("dim", " across 24 chunks")],
        [("bold", "RAC Node 2 Load     : "), ("purple", "600,000 rows (50.0%)"), ("dim", " across 24 chunks")],
        [("bold", "Total Execution Time: "), ("num", "74.2 seconds")],
        [("bold", "Effective Throughput: "), ("success", "16,172 rows/sec"), ("dim", " (Zero Global Cache Contention)")],
        [("dim", "============================================================================")],
    ]

    svg_rac = build_terminal_svg(
        title="QueryPort - Oracle RAC Concurrency & Intra-Table Load Balancing",
        lines=lines_rac,
        width=930,
    )
    (assets_dir / "terminal_concurrency_rac.svg").write_text(svg_rac, encoding="utf-8")

    print("[SUCCESS] All 4 terminal SVGs generated successfully in docs/assets/")


if __name__ == "__main__":
    generate_all_terminal_mockups()
