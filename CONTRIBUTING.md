# Contributing Guidelines

Thank you for your interest in contributing to the **Expense Tracker App using Data Science**.

## Project Maintainer & Author
- **Author**: Akash Das

---

## Getting Started

1. **Clone the Repository**:
   Clone the project to your local machine.

2. **Set Up the Virtual Environment**:
   Create and activate a local virtual environment named `.venv`:
   ```bash
   python -m venv .venv
   ```
   Activate on Windows PowerShell:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install Dependencies**:
   ```bash
   python -m pip install -r requirements.txt
   ```

---

## Development Standards

- **Code Style**: Follow PEP 8 guidelines. Keep functions modular and typed with docstrings.
- **Testing**: Add unit tests under `tests/` for any new functionality or bug fixes.
- **Branching**: Use descriptive branch names (`feature/...`, `bugfix/...`).
- **Commits**: Write concise, descriptive commit messages adhering to standard conventional commit practices.

---

## Submitting Pull Requests

1. Ensure all tests pass:
   ```bash
   pytest tests/
   ```
2. Verify formatting and linting.
3. Open a pull request with a clear description of the changes made and testing performed.

