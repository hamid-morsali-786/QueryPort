# Architecture Design Spec: Enterprise Concurrency, RAC Affinity & Hybrid Chunking Engine

- **Author:** Senior Full-Stack Architect & Senior Oracle DBA
- **Status:** Proposed / Under Review
- **Date:** 2026-10-27
- **Target Platform:** Python 3.11+ / Oracle Database 19c, 21c, 23ai (Single Instance & RAC)
- **Primary Modules:** `import_sql.py`, `export_sql.py`, `config.json`

---

## 1. Executive Summary & Problem Statement

QueryPort is currently a lightweight, portable, and reliable bidirectional Oracle data transfer engine. It utilizes constant memory $O(1)$ streaming via `cursor.executemany` (Array Ingestion) and automated pre-validation against the Oracle Data Dictionary (`ALL_TABLES`, `ALL_TAB_COLS`).

However, for enterprise database administrators and data engineers managing multi-gigabyte datasets (e.g. 20 million rows or dozens of separate tables) on high-throughput **Oracle 19c RAC (Real Application Clusters)**, single-threaded processing has constraints:
1. **Network & Core Underutilization:** Single-threaded execution cannot fully saturate modern 10GbE/25GbE cluster interconnects and multi-node compute resources.
2. **Cluster Contention Risk:** Naive multi-threading on RAC without **Data/Node Affinity** causes severe **Cache Fusion Block Pinging** (`gc buffer busy acquire`, `gc current block busy`, `enq: TX - index contention`).
3. **Simplicity Preservation Constraint:** Casual users, operators, and junior DBAs must not be burdened with complex concurrency configurations or thread tuning. Double-clicking `QueryPort.exe` must remain 100% intuitive and backward-compatible.

---

## 2. Design Principles & Progressive Disclosure

1. **Zero Degradation of Simplicity (Progressive Disclosure):**
   - The default configuration maintains `--workers 1` and single-threaded sequential execution.
   - No prompts or new mandatory inputs are introduced in the interactive console.
   - Advanced concurrency features are activated **only** when explicitly requested via CLI arguments (e.g. `--workers`, `--rac-services`) or via the optional `"concurrency"` block in `config.json`.
2. **Zero External Dependencies:**
   - Implementation relies strictly on the Python 3.11 standard library (`concurrent.futures`, `threading`, `queue`) and `python-oracledb`. No external multiprocessing message brokers (Celery, Redis) or heavy libraries.
3. **Deterministic Safety:**
   - DDL actions (`TRUNCATE TABLE`) and schema pre-validations (`validate_import_plan`) **always** execute single-threaded prior to worker thread initialization.

---

## 3. High-Level Architecture (Hybrid Concurrency Model)

The engine implements a **Hybrid Concurrency Model** operating at two levels:

```
                            [QueryPort CLI / Config]
                                       |
                                       v
                    [Pre-Validation Engine (Single-Threaded)]
                     - ALL_TABLES / ALL_TAB_COLS Checks
                     - Mandatory NOT NULL Column Audit
                     - One-time TRUNCATE execution (if enabled)
                                       |
                                       v
                        [Workload Dispatcher Router]
                                    /     \
                                   /       \
   [Level 1: Multi-File Parallelism]        [Level 2: Intra-Table Chunking]
    (When multiple CSV files exist)          (When a single large CSV exists)
                 |                                        |
                 v                                        v
   [Worker Thread per File/Table]             [Chunk Stream Producer]
   - Table A -> Worker 1 -> Node 1 (Service A) - Rows 00M..05M -> Worker 1 -> Node 1
   - Table B -> Worker 2 -> Node 2 (Service B) - Rows 05M..10M -> Worker 2 -> Node 2
   - Table C -> Worker 3 -> Node 3 (Service C) - Rows 10M..15M -> Worker 3 -> Node 3
                 \                                        /
                  \                                      /
                   v                                    v
                  [Thread-Safe Aggregated Telemetry & Metrics]
                  [Thread-Safe Bad-Row Error CSV Logger]
```

### Level 1: Table/File-Level Parallelism
- Used when the input directory contains multiple CSV files.
- Each worker thread claims an entire table/file.
- **RAC Advantage:** Zero Cache Fusion contention because different cluster nodes insert into completely independent physical segments (tables).

### Level 2: Intra-Table Chunking (Single Giant File)
- Used when a single CSV dataset contains millions of rows and `--workers > 1` is configured.
- The coordinator produces sliced row batches (e.g. 25,000 to 50,000 rows per chunk).
- A bounded queue delivers chunks to worker threads without reading the entire 20M rows into memory.
- **RAC Guidance:** Best used on **Range/List-Partitioned tables** or routed through designated Oracle RAC services to balance load while monitoring ITL slot allocation.

---

## 4. Oracle RAC Service & Workload Affinity Routing

Rather than binding workers directly to fragile physical IP addresses, QueryPort introduces standard Oracle Service-Name affinity:

### Configuration Schema (`config.json` Extension)

```json
{
  "database": {
    "user": "APP_USER",
    "password": "APP_PASSWORD",
    "host": "scan-cluster.corp.local",
    "port": 1521,
    "service_name": "ORCLPDB1",
    "schema": "DATA_STAGE"
  },
  "concurrency": {
    "workers": 4,
    "intra_table_chunk_size": 25000,
    "rac_services": [
      "APP_NODE1_SRV",
      "APP_NODE2_SRV",
      "APP_NODE3_SRV",
      "APP_NODE4_SRV"
    ]
  },
  "import": {
    "input_path": "imports",
    "commit_mode": "batch",
    "batch_size": 5000,
    "existing_data_action": "append",
    "on_error": "skip_and_log",
    "bad_rows_dir": "import_errors"
  }
}
```

### Worker-to-Service Binding Mechanism
- If `rac_services` contains $M$ services, worker thread $i$ connects to `rac_services[i % M]`.
- If `rac_services` is omitted, all workers connect through the default database connection parameters, allowing Oracle SCAN / Connection Director to manage connection balancing.

---

## 5. Detailed Component Specifications

### 5.1 `ThreadSafeErrorLogger`
When running in multi-worker mode with `--on-error skip_and_log`, multiple threads may encounter rejected rows simultaneously.
- A local `threading.Lock` protects the CSV file handle.
- Flushes are synchronized to avoid interleaved or garbled CSV lines in `import_errors/<TABLE>_rejected.csv`.

### 5.2 `ChunkStreamProducer`
- Streams CSV lines in chunks of `intra_table_chunk_size` using Python's standard `itertools.islice`.
- Feeds a `queue.Queue(maxsize=workers * 2)` to enforce backpressure, preventing disk read buffers from exceeding designated memory limits.
- Memory remains bounded at $O(\text{workers} \times \text{batch\_size})$.

### 5.3 `LiveTelemetryTracker`
- Tracks overall progress:
  - Total records processed across all threads.
  - Current throughput (rows/sec).
  - Active worker threads and per-node status.
  - Thread-safe atomic counters (`threading.Lock` or atomic integer accumulation).

---

## 6. CLI Interface Extensions

New optional flags (preserving all existing flags without modification):

| Flag | Short | Default | Description |
| :--- | :---: | :---: | :--- |
| `--workers` | `-w` | `1` | Number of concurrent worker threads (1 = single-threaded sequential). |
| `--chunk-size` | - | `25000` | Number of rows per chunk when splitting a single large CSV file. |
| `--rac-services` | - | `None` | Comma-separated list of Oracle RAC services for node affinity routing. |

---

## 7. Edge Case & Failure Analysis

1. **Deadlock Detection (`ORA-00060`):**
   - In intra-table chunking on unpartitioned tables with foreign keys or unique indexes, concurrent worker inserts could encounter index block contention.
   - **Mitigation:** QueryPort catches `ORA-00060` and retries with exponential backoff up to 3 times before applying the configured `--on-error` strategy (`abort` or `skip_and_log`).
2. **Partial Batch Failures:**
   - In `skip_and_log` mode, if worker 2 fails on row 12,504, it logs the error to the thread-safe error logger, commits valid rows, and continues processing without halting sibling workers.
3. **Abrupt Termination (Ctrl+C / SIGINT):**
   - Coordinator intercepts `KeyboardInterrupt`, sets a `threading.Event` stop flag, drains pending worker queues, issues rollback on in-flight batches, and cleanly closes Oracle database connections.

---

## 8. Verification & QA Plan

1. **Unit Test Suite (Mock-Based):**
   - Test `ThreadSafeErrorLogger` concurrency under 10 simultaneous threads.
   - Test `ChunkStreamProducer` row count parity (ensuring chunk sum exactly equals source CSV row count with zero dropped or duplicate lines).
   - Test `WorkerPoolCoordinator` single-worker fallback (`--workers 1` matches original sequential execution trace).
   - Test CLI argument resolution (`--workers`, `--rac-services`, `--chunk-size`).
2. **Compatibility Verification:**
   - Full regression test run: all 39 existing unit tests must pass without regression.
   - PyInstaller packaging test: rebuild standalone executable and verify dual-mode CLI.
