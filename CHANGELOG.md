# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-10-21

### Added
- Initial public release of **QueryPort** — High-speed Oracle SQL Export & Migration Utility.
- Thin Mode Oracle connectivity via `python-oracledb` (zero Oracle Client / Instant Client or TNS configuration required).
- Streaming chunked export engine (`fetchmany`) for low memory footprint on million-row tables.
- Dual export formats:
  - **CSV**: UTF-8-SIG (BOM) encoded with RFC-4180 quoting for seamless Persian, Arabic, and multilingual viewing in Excel.
  - **SQL**: Standard ANSI / Oracle `INSERT INTO` statements with escaped strings, `SET DEFINE OFF;`, and periodic `COMMIT;`.
- Batch directory parsing: Scans folders for `.sql` files, strips comments (`--`, `/* ... */`), SQL*Plus commands (`PROMPT`, `SET`, `SPOOL`), and groups outputs into organized subfolders per SQL file.
- Smart table name detection supporting schema prefixes (e.g., `SCHEMA.TABLE`).
- Dry-run mode (`--dry-run`): Simulates execution and counts output rows using `COUNT(*)` wrapping without generating output files.
- Interactive Console Mode: Interactive terminal prompt for standalone Windows `.exe` double-click execution with user confirmation (`Y/n`), custom command input, or exit.
- Full test suite with 16 unit tests covering parsing, streaming, format conversions, CLI overrides, and interactive mode.
- Standalone portable Windows executable (`QueryPort.exe`) bundled with PyInstaller.
