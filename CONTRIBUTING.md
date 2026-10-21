# Contributing to QueryPort

Thank you for your interest in contributing to **QueryPort**! 🎉  
We welcome contributions of all kinds: bug reports, performance enhancements, documentation improvements, test cases, and database compatibility fixes.

---

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please treat all contributors and users with kindness, respect, and empathy.

---

## Development Setup

### 1. Prerequisites
- **Python 3.11+**
- Git
- Access to an Oracle Database (19c, 21c, or 23ai) or mock testing suite

### 2. Fork and Clone
```bash
git clone https://github.com/hamid-morsali-786/QueryPort.git
cd QueryPort
```

### 3. Create a Virtual Environment
```bash
# On Linux/macOS
python3 -m venv .venv
source .venv/bin/activate

# On Windows PowerShell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 4. Install Dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## Running Tests

We use Python's built-in `unittest` and `pytest`. Always make sure all unit tests pass before submitting a pull request:

```bash
pytest
# or
python -m unittest test_export_sql.py
```

---

## Contribution Workflow

1. **Check Issues**: Check existing issues first. If none exists, open an issue to discuss your proposed change or bug fix.
2. **Branch from `main`**:
   ```bash
   git checkout -b feat/your-feature-name
   # or
   git checkout -b fix/issue-description
   ```
3. **Commit Messages**: Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat: add parallel query execution option`
   - `fix: resolve escaping for multiline CLOB fields`
   - `docs: update CLI examples in README`
   - `test: add test case for timestamp with timezone`
4. **Push and Open a Pull Request**: Push your branch to GitHub and open a PR against `main`. Provide a descriptive PR summary matching the PR template.

---

## Coding Guidelines

- **Zero Heavy Dependencies**: Keep external runtime dependencies to the absolute minimum (`oracledb` Thin Mode).
- **Streaming by Default**: Never load large result sets into memory with `fetchall()`. Use chunked streaming (`fetchmany()`).
- **Clean Code & LOC**: Keep methods focused and within clean code limits.
- **Unicode & RTL**: Ensure CSV outputs include UTF-8-SIG (BOM) so Excel renders Persian and Arabic characters properly without encoding dialogs.

---

Thank you for helping make database workflows faster and simpler! 🚀
