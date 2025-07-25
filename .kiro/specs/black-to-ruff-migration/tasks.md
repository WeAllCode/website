# Implementation Plan

- [x] 1. Configure Ruff in pyproject.toml

  - Remove existing [tool.black] and [tool.isort] configuration sections
  - Add comprehensive [tool.ruff] configuration with general settings (line-length = 79, target-version = "py311", exclude migrations)
  - Add [tool.ruff.format] section with Black-compatible settings (quote-style = "double", indent-style = "space")
  - Add [tool.ruff.isort] section with Django-aware import sorting (known-django, section-order, combine-as-imports)
  - Add [tool.ruff.lint] section with basic linting rules (select = ["E", "F", "W", "I"])
  - Add Ruff as a development dependency in the "# Development & Debugging" section alongside django-debug-toolbar
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 4.1, 4.2, 4.3, 4.4_

- [x] 2. Update pre-commit configuration

  - Replace Black hook (psf/black) with Ruff formatter hook (charliermarsh/ruff-pre-commit)
  - Replace isort hook (pycqa/isort) with Ruff import sorting hook using --select I flag
  - Maintain existing exclusion patterns for migrations and .vscode folders
  - Keep all other pre-commit hooks unchanged (trailing-whitespace, end-of-file-fixer, etc.)
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 3. Update documentation files
- [x] 3.1 Update .kiro/steering/tech.md

  - Replace Black and isort references with Ruff in Code Quality Tools section
  - Update tool descriptions to reflect Ruff's combined formatting and linting capabilities
  - Maintain 79-character line length documentation
  - _Requirements: 3.1, 3.6_

- [x] 3.2 Update .kiro/steering/structure.md

  - Replace Black formatter references with Ruff in Development Conventions section
  - Update code style documentation to reference Ruff instead of Black and isort
  - Maintain Django-aware import sorting documentation
  - _Requirements: 3.2, 3.6_

- [x] 3.3 Check and update README.md if needed

  - Search for any references to Black or isort in README.md
  - Update developer setup instructions to include Ruff-specific commands if present
  - Ensure consistency with Ruff usage throughout documentation
  - _Requirements: 3.3, 3.4, 3.5_

- [ ] 4. Test Ruff configuration
- [ ] 4.1 Validate formatting compatibility

  - Run `ruff format --check` on existing codebase to verify minimal changes
  - Compare Ruff output with current Black formatting to ensure consistency
  - Test that 79-character line length is maintained
  - Verify migrations are excluded from formatting
  - _Requirements: 1.1, 1.3, 1.4_

- [ ] 4.2 Validate import sorting

  - Run `ruff check --select I` to test import sorting functionality
  - Verify Django-aware section organization is maintained
  - Test that import sorting follows isort-compatible behavior
  - _Requirements: 1.2, 1.5_

- [ ] 4.3 Test pre-commit integration
  - Run pre-commit hooks in isolated environment to verify functionality
  - Test that Ruff hooks execute correctly and maintain exclusion patterns
  - Verify pre-commit performance improvement with Ruff
  - _Requirements: 2.1, 2.2, 2.3, 2.4_
