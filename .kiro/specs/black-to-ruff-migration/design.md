# Design Document

## Overview

This design outlines the migration from Black and isort to Ruff for the We All Code Django project. Ruff is a fast Python linter and formatter written in Rust that can replace both Black (formatting) and isort (import sorting) with a single tool. The migration will maintain existing code style preferences while consolidating tooling and improving performance.

## Architecture

### Tool Replacement Strategy

The migration follows a direct replacement approach:

- **Black** → **Ruff formatter** (maintains Black-compatible formatting)
- **isort** → **Ruff import sorting** (maintains isort-compatible import organization)

### Configuration Approach

Ruff will be configured in `pyproject.toml` using the `[tool.ruff]` section with subsections for:

- General settings (line length, target Python version, exclusions)
- Formatter settings (`[tool.ruff.format]`)
- Import sorting settings (`[tool.ruff.isort]`)
- Linting rules (`[tool.ruff.lint]`)

## Components and Interfaces

### Configuration Files

#### pyproject.toml Updates

**Rationale**: Centralizing all tool configuration in pyproject.toml follows Python packaging standards and simplifies maintenance.

- Remove `[tool.black]` section
- Remove `[tool.isort]` section
- Add comprehensive `[tool.ruff]` configuration
- Add Ruff as a development dependency in the "# Development & Debugging" section alongside django-debug-toolbar
- Remove Black and isort from dependencies if present

#### Pre-commit Configuration Updates

**Rationale**: Maintaining pre-commit integration ensures code quality checks remain automated and consistent across the development team.

- Replace Black hook (currently using psf/black rev 23.3.0) with Ruff formatter hook
- Replace isort hook (currently using pycqa/isort rev 5.12.0) with Ruff import sorting hook
- Maintain existing exclusion patterns for migrations and .vscode folders
- Keep all other pre-commit hooks unchanged (trailing-whitespace, end-of-file-fixer, etc.)

#### Documentation Updates

**Rationale**: Comprehensive documentation updates ensure all team members and new contributors understand the current tooling and maintain consistency across the project.

- Update `.kiro/steering/tech.md` Code Quality Tools section to reference Ruff instead of Black and isort
- Update `.kiro/steering/structure.md` Development Conventions section to reference Ruff formatting
- Check and update `README.md` if it contains references to Black or isort
- Update any developer setup instructions to include Ruff-specific commands
- Ensure all documentation maintains consistency with Ruff usage

### Ruff Configuration Sections

Based on the current Black and isort configuration, Ruff will be configured as follows:

#### Core Settings

```toml
[tool.ruff]
target-version = "py311"
exclude = [migrations, build artifacts, etc.]
```

#### Import Sorting Settings

**Rationale**: Django-aware import sorting maintains the existing project's import organization patterns while leveraging Ruff's performance benefits. This ensures proper separation of Django imports from other third-party libraries, maintaining the project's existing import organization standards.



## Data Models

No data models are affected by this migration as it only changes development tooling configuration.

## Error Handling

### Migration Validation

- Verify Ruff produces equivalent formatting to Black on existing codebase
- Ensure import sorting maintains Django-aware section organization
- Test pre-commit hooks function correctly with new configuration

### Rollback Strategy

- Keep backup of original Black/isort configuration
- Document steps to revert if issues are discovered
- Maintain git history for easy rollback

## Testing Strategy

### Configuration Testing

1. **Format Consistency Test**: Run Ruff formatter on existing codebase and verify minimal changes
2. **Import Sorting Test**: Verify Ruff import sorting maintains Django section organization
3. **Pre-commit Integration Test**: Test pre-commit hooks with Ruff configuration
4. **Exclusion Pattern Test**: Verify migrations and other excluded files are not processed

### Validation Steps

**Rationale**: These validation steps ensure the migration maintains code quality and formatting consistency while verifying all requirements are met.

1. Install Ruff and configure in pyproject.toml
2. Run `docker compose run --rm app uv run ruff format --check .` on codebase to verify compatibility (respects pyproject.toml settings)
3. Run `docker compose run --rm app uv run ruff check --select I .` to test import sorting (respects pyproject.toml settings)
4. Test pre-commit hooks in containerized environment using `docker compose run --rm app pre-commit run --all-files`
5. Compare output with existing Black/isort formatting to ensure consistency
6. Verify uv commands work correctly with Ruff (addresses Requirement 4.4)
7. Confirm migrations are properly excluded from formatting and linting

### Performance Verification

- Measure formatting speed improvement with Ruff vs Black+isort
- Verify pre-commit hook execution time improvement

## Implementation Considerations

### Dependency Management

**Rationale**: Proper dependency management ensures Ruff is available in all development environments and follows the project's existing organizational patterns.

- Ruff will be added to the "# Development & Debugging" section in pyproject.toml dependencies (addresses Requirement 4.1, 4.3)
- Black and isort configurations will be removed from pyproject.toml (addresses Requirement 4.2)
- uv will handle Ruff installation and version management (addresses Requirement 4.4)
- Ruff will be placed appropriately within the development tools section to maintain logical grouping

### Backward Compatibility

- Ruff's Black-compatible formatter ensures existing code style is maintained
- Django-aware import sorting preserves current import organization
- Line length and exclusion patterns remain unchanged

### Team Adoption

- Developers will need to update their local pre-commit hooks
- IDE integrations may need to be updated to use Ruff instead of Black
- Documentation will guide developers through the transition

## Requirements Traceability

This design addresses all requirements from the requirements document:

**Requirement 1 (Tool Replacement)**: Addressed through pyproject.toml configuration sections that replace Black and isort with Ruff while maintaining migration exclusions, and Django-aware import sorting.

**Requirement 2 (Pre-commit Integration)**: Addressed through pre-commit configuration updates that replace Black and isort hooks with Ruff equivalents while maintaining existing exclusion patterns.

**Requirement 3 (Documentation Updates)**: Addressed through systematic updates to steering documents, README, and developer setup instructions to reflect Ruff usage consistently.

**Requirement 4 (Dependency Management)**: Addressed through adding Ruff to development dependencies and removing Black/isort configurations, with uv handling installation and version management.
