---
this_file: LOG.md
---

# Change Log

This file tracks changes and issues in the Opero project.

## 2025-03-04

### Fixed
- Fixed `process` method in `Orchestrator` class to apply function to each item individually
- Refactored `execute` method in `Orchestrator` class to reduce complexity
- Fixed loop variable binding issues in `core.py` for `fallback_func`
- Refactored `with_retry` function in `retry.py` to use a config object to reduce the number of arguments

### Added
- Added `has_fallbacks` method to `FallbackChain` class
- Created LOG.md file for tracking changes and issues

### Changed
- Improved error handling in the `FallbackChain` class
- Enhanced type annotations throughout the codebase

## Known Issues
- Need to improve error handling in `retry_async` function to properly handle coroutine objects
- Need to implement proper handling of `AllFailedError` in all fallback scenarios
- Need to optimize retry logic for better performance 