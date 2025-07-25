# Implementation Plan

- [x] 1. Configure Ruff in pyproject.toml

  - Remove existing [tool.black] and [tool.isort] configuration sections
  - Add comprehensive [tool.ruff] configuration with general settings (target-version = "py311", exclude migrations)
  - Add Ruff as a development dependency in the "# Development & Debugging" section alongside django-debug-toolbar
  - Add [tool.ruff.lint] section with comprehensive linting rules
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 4.1, 4.2, 4.3, 4.4_

- [x] 2. Update pre-commit configuration

  - Replace Black hook (psf/black) with Ruff formatter hook (charliermarsh/ruff-pre-commit)
  - Replace isort hook (pycqa/isort) with Ruff import sorting hook using ruff-check
  - Maintain existing exclusion patterns for migrations and .vscode folders
  - Keep all other pre-commit hooks unchanged (trailing-whitespace, end-of-file-fixer, etc.)
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 3. Update documentation files
- [x] 3.1 Update .kiro/steering/tech.md

  - Replace Black and isort references with Ruff in Code Quality Tools section
  - Update tool descriptions to reflect Ruff's combined formatting and linting capabilities
  - _Requirements: 3.1, 3.6_

- [x] 3.2 Update .kiro/steering/structure.md

  - Replace Black formatter references with Ruff in Development Conventions section
  - Update code style documentation to reference Ruff instead of Black and isort
  - Maintain Django-aware import sorting documentation
  - _Requirements: 3.2, 3.6_

- [x] 3.3 Check and update README.md if needed

  - Search for any references to Black or isort in README.md (none found)
  - Update developer setup instructions to include Ruff-specific commands if present (none needed)
  - Ensure consistency with Ruff usage throughout documentation
  - _Requirements: 3.3, 3.4, 3.5_

- [ ] 4. Enhance Ruff configuration for complete migration
- [ ] 4.1 Complete pyproject.toml Ruff configuration

  - Add exclude patterns for migrations and other directories
  - Add [tool.ruff.isort] section with Django-aware import sorting (known-django, section-order, combine-as-imports)
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 5. Test Ruff configuration
- [ ] 5.1 Validate formatting compatibility

  - Run `docker compose run --rm app uv run ruff format --check .` on existing codebase to verify minimal changes
  - Compare Ruff output with current formatting to ensure consistency
  - Verify migrations are excluded from formatting (configured in pyproject.toml)
  - _Requirements: 1.1, 1.3, 1.4_

- [ ] 5.2 Validate import sorting

  - Run `docker compose run --rm app uv run ruff check --select I .` to test import sorting functionality
  - Verify Django-aware section organization is maintained
  - Test that import sorting follows isort-compatible behavior using `docker compose run --rm app uv run ruff check --select I --fix .`
  - _Requirements: 1.2, 1.5_

- [ ] 5.3 Test pre-commit integration
  - Run `docker compose run --rm app pre-commit run --all-files` to test pre-commit hooks in containerized environment
  - Test that Ruff hooks execute correctly and maintain exclusion patterns
  - Verify pre-commit performance improvement with Ruff using `docker compose run --rm app pre-commit run ruff-format ruff-check`
  - _Requirements: 2.1, 2.2, 2.3, 2.4_
