# Enterprise Concurrency, RAC Affinity & Hybrid Chunking Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement enterprise concurrency in QueryPort with multi-file parallelism, intra-table CSV chunking, and Oracle RAC service routing while strictly preserving $O(1)$ memory streaming and zero-friction single-threaded defaults for standard users.

**Architecture:** Extend `import_sql.py` with standard library `concurrent.futures.ThreadPoolExecutor`, `threading.Lock`, and a sliced batch generator. Route workers across RAC services via connection configuration overrides.

**Tech Stack:** Python 3.11+ stdlib (`concurrent.futures`, `threading`, `itertools`, `csv`, `unittest`), `python-oracledb`.

**Spec:** [`docs/superpowers/specs/2026-10-27-enterprise-concurrency-rac-design.md`](file:///e:/project/QueryPort/docs/superpowers/specs/2026-10-27-enterprise-concurrency-rac-design.md)

## Global Constraints
- Python 3.11+ standard library only for concurrency (no external libraries like celery/multiprocessing-queue servers).
- Default execution (`workers=1`) must execute identically to current code with zero performance or behavior regressions.
- Schema pre-validation and `TRUNCATE TABLE` must execute single-threaded before any worker starts.
- Thread-safe bad-row error logging to `import_errors/<TABLE>_rejected.csv`.

## Review Focus
- Single large file chunk sum must match exact total CSV rows without missing or duplicate rows.
- Thread-safe error logger must handle concurrent exceptions from multiple threads without CSV line corruption.
- RAC service round-robin must wrap index correctly (`worker_idx % len(rac_services)`).
- Single-worker mode (`--workers 1`) must run with zero thread synchronization overhead.
- Ctrl+C / KeyboardInterrupt must cleanly terminate worker pools.

---

### Task 1: Concurrency Settings Resolution & CLI Arguments

**Files:**
- Modify: `import_sql.py:40-95`
- Test: `test_import_sql.py`

**Interfaces:**
- Produces: `settings["concurrency"] = {"workers": int, "chunk_size": int, "rac_services": list[str]}`
- Consumes: `config.json`, CLI arguments (`--workers`, `--chunk-size`, `--rac-services`)

- [ ] **Step 1: Write the failing tests in `test_import_sql.py`**
  - `test_resolve_concurrency_settings_defaults`: returns `workers=1`, `chunk_size=25000`, `rac_services=[]`.
  - `test_resolve_concurrency_settings_from_config_and_cli`: verifies CLI flags override config values.
- [ ] **Step 2: Run tests to verify failure**
  Run: `python -m unittest test_import_sql.py`
- [ ] **Step 3: Implement concurrency parsing in `resolve_import_settings` and `build_import_parser`**
- [ ] **Step 4: Run tests to verify they pass**
  Run: `python -m unittest discover`
- [ ] **Step 5: Commit**
  `git commit -m "feat(import): add concurrency and rac routing settings resolution"`

---

### Task 2: Thread-Safe Bad Row Error Logger

**Files:**
- Modify: `import_sql.py`
- Test: `test_import_sql.py`

**Interfaces:**
- Produces: `ThreadSafeErrorLogger(bad_rows_path, headers)` with `log(row_idx, row_values, error_msg)` method.

- [ ] **Step 1: Write failing test in `test_import_sql.py`**
  - Test concurrent logging from 10 threads writing 50 rows each to verify exactly 500 lines plus header are written with no garbled output.
- [ ] **Step 2: Run test to verify failure**
- [ ] **Step 3: Implement `ThreadSafeErrorLogger` with `threading.Lock`**
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit**
  `git commit -m "feat(import): implement thread-safe bad row error logger"`

---

### Task 3: Sliced CSV Stream Generator for Intra-Table Chunking

**Files:**
- Modify: `import_sql.py`
- Test: `test_import_sql.py`

**Interfaces:**
- Produces: `stream_csv_chunks(file_path, chunk_size, batch_size)` yielding chunk iterators.

- [ ] **Step 1: Write failing test in `test_import_sql.py`**
  - Verify that slicing a 1,000-row CSV into chunks of 250 rows produces 4 distinct chunks whose total row count equals 1,000.
- [ ] **Step 2: Run test to verify failure**
- [ ] **Step 3: Implement `stream_csv_chunks` in `import_sql.py` using `itertools.islice`**
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit**
  `git commit -m "feat(import): add zero-copy sliced chunk streaming generator"`

---

### Task 4: RAC Service Connection Dispatcher

**Files:**
- Modify: `import_sql.py`
- Test: `test_import_sql.py`

**Interfaces:**
- Produces: `get_worker_connection_config(base_db_config, rac_services, worker_index)` returning tailored DB connection dict with specific `service_name`.

- [ ] **Step 1: Write failing test in `test_import_sql.py`**
  - Verify worker 0, 1, 2, 3 cycle through `["SRV1", "SRV2"]` as `SRV1, SRV2, SRV1, SRV2`.
- [ ] **Step 2: Run test to verify failure**
- [ ] **Step 3: Implement `get_worker_connection_config`**
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit**
  `git commit -m "feat(import): implement rac service connection dispatcher"`

---

### Task 5: Multi-Worker Orchestration in `run_import`

**Files:**
- Modify: `import_sql.py`
- Test: `test_import_sql.py`

**Interfaces:**
- Integrates `ThreadPoolExecutor` in `run_import`:
  - When `file_plan` has multiple files and `workers > 1`: files dispatched to thread pool.
  - When `file_plan` has 1 giant file and `workers > 1`: chunks dispatched to thread pool.
  - When `workers == 1`: runs existing fast sequential path.

- [ ] **Step 1: Write failing test in `test_import_sql.py`**
  - Test multi-file parallel import mock execution with 2 workers.
- [ ] **Step 2: Run test to verify failure**
- [ ] **Step 3: Implement parallel worker pool dispatch in `run_import`**
- [ ] **Step 4: Run test to verify all tests pass**
- [ ] **Step 5: Commit**
  `git commit -m "feat(import): integrate multi-worker thread pool in run_import"`

---

### Task 6: Full Verification, Documentation & Packaging

**Files:**
- Modify: `README.md`, `README.en.md`, `README.txt`, `config.example.json`
- Test: Full unit test suite (`python -m unittest discover -v`)

- [ ] **Step 1: Update documentation and example configs with `--workers`, `--chunk-size`, `--rac-services`**
- [ ] **Step 2: Run full unit test suite**
- [ ] **Step 3: Rebuild standalone executable with PyInstaller**
- [ ] **Step 4: Test standalone executable with `--help` and dry-run**
- [ ] **Step 5: Push commits to GitHub `main` branch**
