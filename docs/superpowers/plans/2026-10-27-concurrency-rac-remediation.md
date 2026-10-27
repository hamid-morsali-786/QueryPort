# Concurrency, RAC Affinity, and Oracle Best-Practices Remediation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remediate all 4 Critical and 4 Important findings from the code review by implementing a bounded Producer-Consumer worker queue with connection reuse, deterministic DDL/skip pre-guards, RAC DSN sanitization, CLI argument registration, and comprehensive concurrency unit tests adhering strictly to Oracle Database 19c documentation and python-oracledb guidelines.

**Architecture:** 
1. Replace unbounded `ThreadPoolExecutor.submit` in intra-table chunk streaming with a bounded Producer-Consumer queue (`queue.Queue(maxsize=workers * 2)`) where each worker thread maintains a single persistent Oracle connection across chunks, guaranteeing strict $O(1)$ RAM and eliminating connection storms.
2. Centralize destructive DDL operations (`TRUNCATE TABLE`) and `--existing-data skip` checks in single-threaded pre-execution phases before spawning worker threads, eliminating table lock contention (`TM-X`) and race conditions.
3. Align CLI interfaces, documentation, and SVG terminal mockups to 100% reflect real capabilities without phantom flags.

**Tech Stack:** Python 3.11+ stdlib (`queue`, `threading`, `concurrent.futures`, `unittest.mock`), `python-oracledb` 2.x Thin Mode, Oracle Database 19c RAC architecture.

**Spec / Review:** 
- Spec: `docs/superpowers/specs/2026-10-27-enterprise-concurrency-rac-design.md`
- Review findings: Subagent Code Review transcript (Critical issues 1-4, Important issues 5-9, Minor issues 10-12).

## Global Constraints

- **Oracle Concurrency Rule:** Never share database connections across threads; each thread must use its own connection (`python-oracledb.md`).
- **Connection Storm Rule:** Never open and close physical database connections in per-chunk loops; connections must be held for the worker's operational lifecycle (`connection-pooling.md`).
- **DDL Lock Safety:** `TRUNCATE TABLE` issues an exclusive table-level lock (`TM-X`); it must NEVER be executed concurrently by multiple worker threads (`destructive-op-guards.md`, `locking-concurrency.md`).
- **Memory Footprint:** The application must maintain bounded $O(1)$ memory regardless of file size (100 MB or 50 GB) by buffering at most `workers * 2` chunks in RAM at any moment.
- **Backward Compatibility:** All existing CLI syntax, default single-threaded behavior (`workers=1`), and JSON configuration formats must remain fully operational.

## Review Focus

1. **Unbounded chunk queue causing MemoryError on 20M+ row files:** Handled by `queue.Queue(maxsize=workers * 2)` backpressure on CSV generator.
2. **Connection storm (hundreds of connection handshakes on RAC nodes):** Handled by 1 persistent connection per worker thread in queue loop.
3. **Concurrent TRUNCATE causing `ORA-00054` or data loss in multi-file imports:** Handled by single-threaded pre-truncate stage before pool launch.
4. **`--existing-data skip` ignored in intra-table parallel import:** Handled by upfront `SELECT COUNT(*)` check before chunking starts.
5. **Phantom flags in terminal docs/SVGs breaking CLI execution:** Handled by registering `--intra-table` and updating SVG scripts to match exact codebase capabilities.

---

### Task 1: Bounded Queue & Connection Reuse Architecture in `import_sql.py`

**Files:**
- Modify: `import_sql.py:470-580`
- Test: `test_import_sql.py`

**Interfaces:**
- Consumes: `stream_csv_chunks(filepath, chunk_size)`, `create_import_connection(cfg)`, `get_worker_connection_config(base_db, w_idx, rac_services)`
- Produces: `import_single_file_parallel(filepath, base_db_config, import_settings, concurrency_settings) -> dict`

- [ ] **Step 1: Write failing unit test for bounded queue and connection reuse**

```python
def test_import_single_file_parallel_connection_reuse_and_queue(self):
    # Verify that exactly 'workers' connections are created, NOT one per chunk
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest test_import_sql.TestImportConfigAndArgs.test_import_single_file_parallel_connection_reuse_and_queue -v`
Expected: FAIL (current implementation creates connections inside per-chunk process_chunk)

- [ ] **Step 3: Implement Bounded Producer-Consumer Worker Loop in `import_sql.py`**

Refactor `import_single_file_parallel`:
1. Create `task_queue = queue.Queue(maxsize=workers * 2)` and `abort_event = threading.Event()`.
2. Define a worker function `_parallel_chunk_worker(w_idx, task_queue, results_list, abort_event, ...)`:
   - Derives `worker_cfg = get_worker_connection_config(base_db, w_idx, rac_services)`.
   - Opens **ONE** persistent connection: `with create_import_connection(worker_cfg) as conn:`
   - Loops pulling `(hdrs, c_idx, c_rows)` from `task_queue` until `None` sentinel or `abort_event.is_set()`.
   - Executes batch insertion on the persistent connection cursor.
   - If an unhandled exception or abort condition occurs, sets `abort_event.set()` and exits cleanly.
3. Producer in main thread iterates `stream_csv_chunks(filepath, chunk_size)` and puts chunks into `task_queue`. Bounded `maxsize` automatically pauses disk reading when workers are busy (guaranteeing $O(1)$ memory).
4. Send `None` sentinel for each worker and wait for worker threads (`thread.join()`).

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest test_import_sql.TestImportConfigAndArgs.test_import_single_file_parallel_connection_reuse_and_queue -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add import_sql.py test_import_sql.py
git commit -m "fix(import): implement bounded queue and connection reuse in parallel chunk ingestion"
```

---

### Task 2: Deterministic Pre-Execution Guards (`truncate` and `skip`)

**Files:**
- Modify: `import_sql.py:470-510, 620-660`
- Test: `test_import_sql.py`

**Interfaces:**
- Consumes: `create_import_connection(base_db)`, `existing_data_action`
- Produces: Single-threaded pre-truncate stage in `run_import`, upfront row count check in `import_single_file_parallel`.

- [ ] **Step 1: Write failing tests for `--existing-data skip` and pre-truncate**

```python
def test_parallel_existing_data_skip_honored(self):
    # Verify that if target table has rows and action is skip, 0 rows are imported and file is marked skipped
    ...

def test_run_import_multi_file_single_threaded_truncate(self):
    # Verify truncate is executed only once per table before threadpool
    ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest test_import_sql.TestImportConfigAndArgs.test_parallel_existing_data_skip_honored -v`
Expected: FAIL

- [ ] **Step 3: Implement guards in `import_sql.py`**

1. In `import_single_file_parallel`:
   - If `existing_action == "skip"`:
     Open connection, query `SELECT COUNT(*) FROM {table}`. If count > 0, print skip message and immediately return `{"read": 0, "imported": 0, "failed": 0, "skipped": True, "duration": ...}`.
2. In `run_import`:
   - If `workers > 1 and len(file_plan) > 1 and existing_data_action == "truncate"`:
     Find unique tables across `file_plan`. Run `TRUNCATE TABLE` on each table single-threaded upfront before launching `ThreadPoolExecutor`.
     Pass `already_truncated=True` in an internal option to `import_single_file` so workers do not execute concurrent DDL.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest test_import_sql.TestImportConfigAndArgs.test_parallel_existing_data_skip_honored test_import_sql.TestImportConfigAndArgs.test_run_import_multi_file_single_threaded_truncate -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add import_sql.py test_import_sql.py
git commit -m "fix(import): add deterministic skip check and single-threaded truncate pre-guard"
```

---

### Task 3: RAC DSN Disambiguation & Thread-Safe Error Log Isolation

**Files:**
- Modify: `import_sql.py:25-35, 335-370, 115-135`
- Test: `test_import_sql.py`

**Interfaces:**
- Consumes: `cfg` with potential `"dsn"`, `ThreadSafeErrorLogger`
- Produces: Sanitized RAC connection dict, lazy thread-safe error logger with append mode.

- [ ] **Step 1: Write failing tests for RAC DSN stripping and lazy error logger**

```python
def test_rac_service_routing_clears_stale_dsn(self):
    cfg = {"user": "u", "dsn": "host:1521/OLD_SRV", "service_name": "OLD_SRV"}
    out = get_worker_connection_config(cfg, 0, ["RAC1_SRV", "RAC2_SRV"])
    self.assertEqual(out["service_name"], "RAC1_SRV")
    self.assertNotIn("dsn", out)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest test_import_sql.TestImportConfigAndArgs.test_rac_service_routing_clears_stale_dsn -v`
Expected: FAIL

- [ ] **Step 3: Implement fixes in `import_sql.py`**

1. In `get_worker_connection_config`:
   - If `rac_services` is non-empty:
     Pop `"dsn"` from `cfg` (`cfg.pop("dsn", None)`) so `create_connection` uses `host`, `port`, and the routed `service_name`.
2. In `ThreadSafeErrorLogger`:
   - Make file opening **lazy**: do not open the file or write CSV headers until the first call to `log_error()`.
   - Open file with mode `"a"` (append) with UTF-8 encoding. If file does not exist or has size 0, write the CSV header row.
3. In `resolve_concurrency_settings`:
   - Use defensive fallback: `concurrency_cfg.get("workers") or 1`, `concurrency_cfg.get("chunk_size") or 25000`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest test_import_sql.TestImportConfigAndArgs.test_rac_service_routing_clears_stale_dsn -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add import_sql.py test_import_sql.py
git commit -m "fix(import): sanitize rac dsn routing, make error logger lazy, and harden null config"
```

---

### Task 4: CLI Argument Registration, Documentation & SVG Mockup Alignment

**Files:**
- Modify: `import_sql.py:440-465, 650-660`, `scripts/generate_terminal_svgs.py`, `docs/terminal_guide.md`, `README.md`, `README.en.md`
- Test: Run `python scripts/generate_terminal_svgs.py` and validate XML.

**Interfaces:**
- Consumes: CLI parser definitions, terminal guide text, SVG templates
- Produces: `--intra-table` flag registered in `import_sql.py`, accurate `terminal_export.svg`, accurate `docs/terminal_guide.md`

- [ ] **Step 1: Write test for `--intra-table` argument parsing**

```python
def test_intra_table_cli_flag_parsed(self):
    args = parse_import_args(["import", "--intra-table"])
    self.assertTrue(args.intra_table)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest test_import_sql.TestImportConfigAndArgs.test_intra_table_cli_flag_parsed -v`
Expected: FAIL (`unrecognized arguments: --intra-table`)

- [ ] **Step 3: Register flag and fix SVG mockups & documentation**

1. In `import_sql.py`:
   - Add `--intra-table` to `parse_import_args` (`action="store_true"`, help="Enable parallel intra-table chunk streaming for large CSV files").
   - In `run_import`: Sort `summary_results` by table name before rendering the execution summary report.
2. In `scripts/generate_terminal_svgs.py`:
   - Update `terminal_export.svg`: Show realistic export command `.\QueryPort.exe --path sql_queries --format both --batch-size 10000` (remove phantom `--workers` and `.xlsx` mentions; reflect CSV and SQL INSERT outputs).
3. In `docs/terminal_guide.md`:
   - Correct Export scenario to reflect actual `--format both` (CSV + SQL INSERT).
   - In Flag Matrix, change `--bad-records-file` to `--bad-rows-dir`.
4. Re-run `python scripts/generate_terminal_svgs.py` to regenerate all SVGs.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest test_import_sql.TestImportConfigAndArgs.test_intra_table_cli_flag_parsed -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add import_sql.py scripts/generate_terminal_svgs.py docs/ README.md README.en.md
git commit -m "fix(cli): register --intra-table flag and harmonize terminal mockups with real features"
```

---

### Task 5: End-to-End Test Suite Verification & Binary Rebuild

**Files:**
- Test: Full test suite `python -m unittest discover -v`
- Rebuild: `QueryPort.exe` via PyInstaller

- [ ] **Step 1: Run all unit tests**

Run: `python -m unittest discover -v`
Expected: All tests pass (>= 50 tests).

- [ ] **Step 2: Rebuild standalone executable**

Run: `pyinstaller QueryPort.spec --clean -y`
Expected: Standalone binary `QueryPort.exe` generated with 0 errors.

- [ ] **Step 3: Verify binary smoke test**

Run: `.\QueryPort.exe --help` and `.\QueryPort.exe import --help`
Expected: Clean help output displaying `--intra-table`, `--workers`, `--rac-services`.

- [ ] **Step 4: Final commit and push**

```bash
git add QueryPort.exe
git commit -m "build: update QueryPort standalone binary with concurrency and rac remediation fixes"
git push origin main
```
