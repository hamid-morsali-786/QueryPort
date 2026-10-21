## Summary

Briefly explain the goal of this pull request and what issues or enhancements it covers.

Closes # (issue number if applicable)

## Type of Change

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🎨 Code refactoring or performance improvement
- [ ] 🧪 Tests / QA additions

## Changes Made

- Detail 1
- Detail 2

## How Has This Been Tested?

- [ ] Automated unit tests passed (`pytest` or `python -m unittest test_export_sql.py`)
- [ ] Oracle DB connection and streaming export verified
- [ ] UTF-8-SIG CSV verified with Persian / Unicode characters in Excel
- [ ] SQL INSERT file verified with Oracle SQL*Plus / SQLcl / PL/SQL Developer
- [ ] Standalone EXE verified in interactive and non-interactive modes

## Checklist

- [ ] My code follows the clean code standards of this repository.
- [ ] I have performed a self-review of my own changes.
- [ ] I have commented my code, particularly in complex SQL parsing/regex logic.
- [ ] I have updated corresponding documentation (`README.md`).
- [ ] All automated tests pass without errors.
