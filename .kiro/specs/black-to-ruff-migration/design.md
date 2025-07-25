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

- Remove `[tool.black]` section
- Remove `[tool.isort]` section
- Add comprehensive `[tool.ruff]` configuration
- Add Ruff as a development dependency in the "# Development & Debugging" section alongside django-debug-toolbar

#### Pre-commit Configuration Updates

- Replace Black hook (currently using psf/black rev 23.3.0) with Ruff formatter hook
- Replace isort hook (currently using pycqa/isort rev 5.12.0) with Ruff import sorting hook
- Maintain existing exclusion patterns for migrations and .vscode folders
- Keep all other pre-commit hooks unchanged (trailing-whitespace, end-of-file-fixer, etc.)

#### Documentation Updates

- Update `.kiro/steering/tech.md` Code Quality Tools section to reference Ruff instead of Black and isort
- Update `.kiro/steering/structure.md` Development Conventions section to reference Ruff formatting
- Check and update `README.md` if it contains references to Black or isort
- Update any developer setup instructions to include Ruff-specific commands
- Ensure all documentation maintains consistency with Ruff usage and 79-character line length

### Ruff Configuration Sections

Based on the current Black and isort configuration, Ruff will be configured as follows:

#### Core Settings

```toml
[tool.ruff]
line-length = 79
target-version = "py311"
exclude = [migrations, build artifacts, etc.]
```

#### Formatter Settings

```toml
[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-source-first-line = false
line-ending = "auto"
```

#### Import Sorting Settings

```toml
[tool.ruff.isort]
known-django = ["django"]
section-order = ["future", "standard-library", "django", "third-party", "first-party", "local-folder"]
combine-as-imports = true
force-wrap-aliases = true
split-on-trailing-comma = true
```

#### Linting Rules

```toml
[tool.ruff.lint]
select = ["E", "F", "W", "I"]  # Basic error, warning, and import rules
ignore = []  # Project-specific ignores if needed
```

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

1. Install Ruff and configure in pyproject.toml
2. Run `ruff format --check` on codebase to verify compatibility
3. Run `ruff check --select I` to test import sorting
4. Test pre-commit hooks in isolated environment
5. Compare output with existing Black/isort formatting

### Performance Verification

- Measure formatting speed improvement with Ruff vs Black+isort
- Verify pre-commit hook execution time improvement

## Implementation Considerations

### Dependency Management

- Ruff will be added to the "# Development & Debugging" section in pyproject.toml dependencies (following the existing organizational pattern where development tools like django-debug-toolbar are grouped)
- Black and isort configurations will be removed from pyproject.toml (they are not explicitly listed as dependencies, only configured)
- uv will handle Ruff installation and version management
- Ruff will be placed appropriately within the development tools section to maintain logical grouping

### Backward Compatibility

- Ruff's Black-compatible formatter ensures existing code style is maintained
- Django-aware import sorting preserves current import organization
- Line length and exclusion patterns remain unchanged

### Team Adoption

- Developers will need to update their local pre-commit hooks
- IDE integrations may need to be updated to use Ruff instead of Black
- Documentation will guide developers through the transition
