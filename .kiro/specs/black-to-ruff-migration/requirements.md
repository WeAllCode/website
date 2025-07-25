# Requirements Document

## Introduction

This feature involves migrating the We All Code Django project from using Black (code formatter) and isort (import sorter) to Ruff, which is a faster, all-in-one Python linter and formatter that can replace both tools. Ruff provides the same formatting capabilities as Black while also offering linting and import sorting functionality in a single, faster tool.

## Requirements

### Requirement 1: Tool Replacement

**User Story:** As a developer, I want to use Ruff instead of Black and isort, so that I have faster code formatting and linting with a single tool.

#### Acceptance Criteria

1. WHEN the project is configured THEN Ruff SHALL replace Black as the code formatter
2. WHEN the project is configured THEN Ruff SHALL replace isort for import sorting
3. WHEN Ruff is configured THEN it SHALL exclude migrations from formatting (same as current Black config)
4. WHEN Ruff is configured THEN it SHALL maintain Django-aware import sorting sections with proper separation of Django imports from other third-party libraries

### Requirement 2: Pre-commit Integration

**User Story:** As a developer, I want the pre-commit hooks updated to use Ruff, so that code quality checks run automatically before commits.

#### Acceptance Criteria

1. WHEN pre-commit hooks are updated THEN they SHALL use Ruff instead of Black and isort
2. WHEN pre-commit runs THEN it SHALL format code using Ruff
3. WHEN pre-commit runs THEN it SHALL sort imports using Ruff
4. WHEN pre-commit runs THEN it SHALL maintain the same exclusion patterns as before

### Requirement 3: Documentation Updates

**User Story:** As a developer, I want all project documentation updated to reflect the Ruff migration, so that new contributors understand the current tooling and existing developers have accurate reference materials.

#### Acceptance Criteria

1. WHEN documentation is updated THEN .kiro/steering/tech.md SHALL reference Ruff instead of Black and isort in the Code Quality Tools section
2. WHEN documentation is updated THEN .kiro/steering/structure.md SHALL reference Ruff formatting conventions instead of Black
3. WHEN documentation is updated THEN README.md SHALL be updated if it contains references to Black or isort
4. WHEN documentation is updated THEN any developer setup instructions SHALL include Ruff-specific commands
5. WHEN documentation is updated THEN all references to code formatting tools SHALL be consistent with Ruff usage

### Requirement 4: Dependency Management

**User Story:** As a developer, I want Ruff to be added as a project dependency, so that it's available in the development environment.

#### Acceptance Criteria

1. WHEN dependencies are updated THEN Ruff SHALL be added to pyproject.toml
2. WHEN dependencies are updated THEN Black and isort SHALL be removed from dependencies (if present)
3. WHEN Ruff is added THEN it SHALL be in the appropriate dependency group for development tools
4. WHEN the configuration is complete THEN Ruff SHALL be usable via uv commands
