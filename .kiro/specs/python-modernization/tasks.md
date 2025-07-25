# Implementation Plan

- [ ] 1. Update Python version configuration files

  - Update `.python-version` from `3.11` to `3.13`
  - Update `pyproject.toml` requires-python constraint to `>=3.13,<3.14`
  - Update `Dockerfile` base image from `python:3.11.9` to `python:3.13`
  - _Requirements: 1.1, 4.1, 4.2, 4.3_

- [ ] 2. Regenerate dependency lock file for Python 3.13

  - Run `docker compose run --rm app uv lock --upgrade` to regenerate uv.lock for Python 3.13
  - Test that all dependencies resolve correctly with `docker compose run --rm app uv sync --frozen`
  - Verify no compatibility issues with existing dependencies
  - _Requirements: 5.1, 5.2_

- [ ] 3. Replace custom batches function with native itertools.batched

  - Remove the custom `batches()` function from `coderdojochi/util.py`
  - Replace all usage of `batches()` with `itertools.batched()` in the email function
  - Add import for `itertools.batched` at the top of the file
  - Test email batch processing functionality
  - _Requirements: 3.1, 6.4_

- [ ] 4. Add comprehensive type annotations to util.py

  - Add type annotations to the `email()` function parameters and return type
  - Use modern union syntax (`|` instead of `Union`) for optional parameters
  - Replace `typing.List` with built-in `list` type
  - Add proper type hints for all function parameters
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ] 5. Modernize email function parameter validation

  - Replace manual type checking with modern `isinstance()` patterns
  - Use walrus operator where beneficial for assignment expressions
  - Implement better error messages with f-string formatting
  - Add type-safe parameter validation
  - _Requirements: 3.3, 6.1, 6.2_

- [ ] 6. Update model methods with type annotations

  - Add return type annotations to all `@property` methods in `Session` model
  - Add type hints to `__str__` methods across all models
  - Use modern union syntax for optional return types
  - Ensure all model methods have proper type annotations
  - _Requirements: 2.1, 2.2, 2.3_

- [ ] 7. Modernize view classes with type annotations

  - Add type annotations to view methods in `SessionDetailView`
  - Update context data methods with proper return types
  - Use modern type hints for Django model and queryset types
  - Add type annotations to all view helper methods
  - _Requirements: 2.1, 2.2_

- [ ] 8. Replace custom string operations with native functions

  - Audit codebase for custom string formatting and replace with f-strings
  - Replace manual string joining with `str.join()` where applicable
  - Update any custom padding/alignment with native string methods
  - Ensure consistent f-string usage throughout the codebase
  - _Requirements: 3.2, 6.4_

- [ ] 9. Replace custom collection operations with native functions

  - Find and replace custom list flattening with `itertools.chain.from_iterable()`
  - Replace custom unique filtering with `dict.fromkeys()` or `set()`
  - Update manual sorting with `sorted()` and proper `key` parameters
  - Replace custom min/max finding with native `min()`/`max()` functions
  - _Requirements: 3.3, 6.4_

- [ ] 10. Update file operations to use pathlib

  - Replace `os.path` usage with `pathlib.Path` methods where found
  - Update file reading operations to use `Path.read_text()` where applicable
  - Replace custom directory traversal with `Path.glob()` methods
  - Ensure consistent pathlib usage across the codebase
  - _Requirements: 3.4, 6.4_

- [ ] 11. Enhance error handling with modern patterns

  - Update exception handling in email function to use exception chaining
  - Implement better error context with structured logging
  - Add proper exception types for better error handling
  - Use modern exception patterns throughout the codebase
  - _Requirements: 6.1, 6.3_

- [ ] 12. Run automated modernization tools

  - Execute `docker compose run --rm app ruff check --select UP --fix` to apply pyupgrade modernizations
  - Run `docker compose run --rm app ruff check --select FURB --fix` for refurb modernization suggestions
  - Apply any additional modernization suggestions from ruff
  - Verify all automated changes are correct
  - _Requirements: 6.4_

- [ ] 13. Update imports to use built-in generic types

  - Replace `from typing import List, Dict, Tuple, Optional, Union` with built-in types
  - Update all type annotations to use `list`, `dict`, `tuple` instead of typing equivalents
  - Replace `Optional[T]` with `T | None` syntax
  - Replace `Union[A, B]` with `A | B` syntax
  - _Requirements: 2.2, 2.4_

- [ ] 14. Test application startup and basic functionality

  - Build Docker container with Python 3.13
  - Test application startup without errors
  - Verify database connections work correctly
  - Test basic page rendering and functionality
  - _Requirements: 1.4, 5.3, 5.4_

- [ ] 15. Test email functionality with modernized code

  - Test email sending with new itertools.batched implementation
  - Verify batch processing works correctly
  - Test error handling in email function
  - Confirm all email templates render properly
  - _Requirements: 3.1, 5.3_

- [ ] 16. Run comprehensive test suite

  - Execute all existing unit tests on Python 3.13
  - Run integration tests to verify functionality
  - Test Django admin interface functionality
  - Verify all user-facing features work correctly
  - _Requirements: 5.3, 5.4_

- [ ] 17. Update development documentation
  - Update README.md with Python 3.13 requirements
  - Update development setup instructions
  - Document any new dependencies or requirements
  - Update Docker development instructions
  - _Requirements: 1.4, 4.4_
