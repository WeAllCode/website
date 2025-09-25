# Design Document

## Overview

This design outlines the systematic approach to modernizing the We All Code Django application from Python 3.11 to Python 3.13, incorporating modern language features and replacing custom utility functions with native Python equivalents. The modernization will be performed incrementally to ensure stability and maintainability.

## Architecture

### Python Version Migration Strategy

The migration follows a layered approach:

1. **Infrastructure Layer**: Update Docker, uv configuration, and deployment scripts
2. **Dependency Layer**: Verify and update all Python dependencies for 3.13 compatibility
3. **Code Layer**: Modernize Python syntax and patterns throughout the codebase
4. **Testing Layer**: Ensure all tests pass and add new tests for modernized code

### Compatibility Matrix

| Component  | Current Version | Target Version | Compatibility Status            |
| ---------- | --------------- | -------------- | ------------------------------- |
| Python     | 3.11.9          | 3.13.x         | ✅ Supported                    |
| Django     | 5.2.x           | 5.2.x          | ✅ Python 3.13 compatible       |
| PostgreSQL | 16              | 16             | ✅ No changes needed            |
| Docker     | Current         | Current        | ✅ Python 3.13 images available |

## Components and Interfaces

### 1. Configuration Updates

#### Docker Configuration

- **Dockerfile**: Update base image from `python:3.11.9` to `python:3.13`
- **docker-compose.yml**: No changes required (inherits from Dockerfile)
- **.python-version**: Update from `3.11` to `3.13`

#### Package Configuration

- **pyproject.toml**: Update `requires-python` constraint to `>=3.13,<3.14`
- **uv.lock**: Regenerate lock file for Python 3.13 compatibility

### 2. Code Modernization

#### Type Annotations Enhancement

```python
# Before (Python 3.11 style)
from typing import List, Dict, Optional, Union

def process_items(items: List[str], config: Optional[Dict[str, str]] = None) -> Union[str, None]:
    pass

# After (Python 3.13 style)
def process_items(items: list[str], config: dict[str, str] | None = None) -> str | None:
    pass
```

#### Utility Function Modernization

The `coderdojochi/util.py` file will be updated to replace custom implementations with native Python functions:

```python
# Current custom batches function - REMOVE ENTIRELY
def batches(items, batch_size):
    for start_index in range(0, len(items), batch_size):
        yield items[start_index : start_index + batch_size]

# Replace with native itertools.batched (Python 3.12+)
from itertools import batched

# Usage changes from:
for recipients_batch in batches(recipients, batch_size):
    # process batch

# To:
for recipients_batch in batched(recipients, batch_size):
    # process batch
```

#### Native Function Replacements

**Available Native Replacements:**

- `batches()` → `itertools.batched()` (Python 3.12+)
- Custom list chunking → `itertools.batched()`
- Manual enumeration loops → `enumerate()`
- Index-based iteration → `zip()` or `itertools.zip_longest()`
- Custom grouping → `itertools.groupby()`
- Manual filtering → `filter()` with lambda or comprehensions
- Custom mapping → `map()` or comprehensions
- String joining patterns → `str.join()`
- File path operations → `pathlib.Path` methods

#### Email Function Enhancement

The email utility function will be modernized with:

- Proper type annotations
- Modern union syntax
- Enhanced error handling
- Better parameter validation

### 3. Model Layer Updates

#### Modern Property Decorators

Update model properties to use modern Python features:

```python
# Enhanced with type hints and modern patterns
@property
def end_date(self) -> datetime:
    """Calculate session end date based on course duration."""
    return (self.old_end_date
            if self.old_end_date
            else self.start_date + self.course.duration)
```

#### String Representation

Ensure all `__str__` methods use f-strings consistently:

```python
def __str__(self) -> str:
    date = formats.date_format(self.start_date, "SHORT_DATETIME_FORMAT")
    return f"{self.course.title} | {date}"
```

### 4. Comprehensive Native Function Audit

#### Code Pattern Analysis

A systematic review will identify custom implementations that can be replaced:

**String Operations:**

- Custom string formatting → f-strings and `str.format_map()`
- Manual string joining → `str.join()`
- Custom padding/alignment → `str.center()`, `str.ljust()`, `str.rjust()`

**Collection Operations:**

- Manual list flattening → `itertools.chain.from_iterable()`
- Custom unique filtering → `dict.fromkeys()` or `set()`
- Manual sorting with custom logic → `sorted()` with `key` parameter
- Custom min/max finding → `min()`, `max()` with `key` parameter

**File and Path Operations:**

- `os.path` usage → `pathlib.Path` methods
- Manual file reading loops → `Path.read_text()`, `Path.read_bytes()`
- Custom directory traversal → `Path.glob()`, `Path.rglob()`

**Data Processing:**

- Custom aggregation → `statistics` module functions
- Manual counting → `collections.Counter`
- Custom caching → `functools.lru_cache`, `functools.cache`
- Manual memoization → `functools.cached_property`

**Validation and Type Checking:**

- Custom type validation → `isinstance()` with union types
- Manual None checking → walrus operator and modern patterns
- Custom default handling → `getattr()` with defaults

#### Search Strategy

Use automated tools to find replacement opportunities:

```bash
# Find custom implementations that might have native equivalents
ruff check --select FURB  # flake8-refurb for modernization suggestions
ruff check --select UP    # pyupgrade for syntax modernization
```

## Data Models

### Type System Integration

The modernization will introduce consistent type annotations across:

- **Model Fields**: Add type hints to custom model methods
- **View Methods**: Enhance view methods with proper return type annotations
- **Utility Functions**: Complete type annotation coverage
- **Form Handling**: Type-safe form processing

### Generic Types Usage

Replace typing module imports with built-in generics:

- `List[T]` → `list[T]`
- `Dict[K, V]` → `dict[K, V]`
- `Tuple[T, ...]` → `tuple[T, ...]`
- `Optional[T]` → `T | None`
- `Union[A, B]` → `A | B`

## Error Handling

### Modern Exception Patterns

Implement enhanced exception handling using Python 3.13 features:

```python
# Enhanced exception handling with context
try:
    msg.send()
except Exception as e:
    logger.error("Email sending failed", extra={
        "recipient_count": len(recipients_batch),
        "template": template_name,
        "error": str(e)
    })
    raise EmailDeliveryError("Failed to send email batch") from e
```

### Validation Improvements

Use modern validation patterns:

- Leverage `match` statements where appropriate
- Use walrus operator for assignment expressions
- Implement better type checking with `isinstance()` improvements

## Testing Strategy

### Compatibility Testing

1. **Unit Tests**: Ensure all existing tests pass on Python 3.13
2. **Integration Tests**: Verify Django application functionality
3. **Performance Tests**: Benchmark improvements from Python 3.13
4. **Regression Tests**: Confirm no functionality is broken

### New Test Coverage

Add tests for:

- Type annotation correctness
- Modernized utility functions
- Error handling improvements
- Performance characteristics

### Test Environment Setup

```bash
# Test matrix for different Python versions
python3.11 -m pytest  # Baseline
python3.13 -m pytest  # Target version
```

## Performance Considerations

### Expected Improvements

Python 3.13 provides several performance benefits:

- **Faster startup time**: Improved import system
- **Better memory usage**: Enhanced garbage collection
- **Optimized operations**: Faster string operations and comprehensions

### Benchmarking Plan

Measure performance impact on:

- Application startup time
- Email batch processing
- Database query performance
- Template rendering speed

## Security Enhancements

### Modern Security Patterns

- Use `secrets` module for cryptographic operations
- Leverage improved SSL/TLS handling in Python 3.13
- Implement better input validation with modern type checking

## Migration Path

### Phase 1: Infrastructure

1. Update Docker configuration
2. Update Python version files
3. Regenerate dependency locks
4. Test basic application startup

### Phase 2: Core Utilities

1. Modernize `util.py` functions
2. Add comprehensive type annotations
3. Update error handling patterns
4. Test email functionality

### Phase 3: Models and Views

1. Add type hints to model methods
2. Modernize view implementations
3. Update template context handling
4. Test user-facing functionality

### Phase 4: Testing and Validation

1. Run comprehensive test suite
2. Performance benchmarking
3. Security validation
4. Documentation updates

## Rollback Strategy

### Contingency Plan

If issues arise during migration:

1. **Quick Rollback**: Revert Docker image to Python 3.11.9
2. **Dependency Issues**: Use previous uv.lock file
3. **Code Issues**: Git revert specific commits
4. **Testing**: Maintain parallel testing environments

### Risk Mitigation

- Maintain separate branches for each migration phase
- Use feature flags for gradual rollout
- Implement comprehensive monitoring
- Prepare rollback procedures for each component
