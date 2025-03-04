---
this_file: TODO.md
---

# TODO

Tip: Periodically run `./cleanup.py status` to see results of lints and tests.

This document outlines the remaining tasks for the Opero project.

## Phase 1 - Current Focus

1. [ ] Add comprehensive logging throughout the codebase:
   - [ ] Add debug logging for all major operations
   - [ ] Implement configurable log levels
   - [ ] Add context information to log messages

2. [ ] Improve error handling:
   - [ ] Fix error handling in `retry_async` function to properly handle coroutine objects
   - [ ] Address type compatibility issues in async/sync conversions
   - [ ] Implement proper handling of `AllFailedError` in all fallback scenarios

3. [ ] Fix linter errors in cleanup.py:
   - [ ] Add timezone to datetime.datetime.now() calls (DTZ005)
   - [ ] Fix Boolean-typed positional arguments (FBT001/FBT002)
   - [ ] Address subprocess call security issues (S603/S607)

4. [ ] Update pyproject.toml:
   - [ ] Move 'per-file-ignores' to 'lint.per-file-ignores' section

## Phase 2 - Next Steps

1. [ ] Optimize performance:
   - [ ] Optimize retry logic for better performance
   - [ ] Reduce overhead in the orchestration layer
   - [ ] Improve concurrency management

2. [ ] Enhance test coverage:
   - [ ] Add more unit tests for edge cases in retry mechanism
   - [ ] Create integration tests for complex scenarios combining multiple features
   - [ ] Add performance benchmarks for key operations
   - [ ] Implement stress tests for concurrency and rate limiting

3. [ ] Improve documentation:
   - [ ] Add more usage examples for common patterns
   - [ ] Document best practices for error handling
   - [ ] Add docstrings to all public functions and classes

## Phase 3 - Future Enhancements

1. [ ] Add new features:
   - [ ] Implement middleware support for function transformation
   - [ ] Add metrics collection for performance monitoring
   - [ ] Create a CLI interface using `fire` and `rich`
   - [ ] Add support for distributed task queues
   - [ ] Implement streaming support with backpressure handling

2. [ ] Infrastructure improvements:
   - [ ] Set up CI/CD pipeline for automated testing and deployment
   - [ ] Configure code coverage reporting
   - [ ] Add pre-commit hooks for code quality
   - [ ] Create GitHub Actions workflow for publishing to PyPI
   - [ ] Set up automated dependency updates

3. [ ] Compatibility enhancements:
   - [ ] Ensure compatibility with Python 3.8+
   - [ ] Test with different versions of dependencies
   - [ ] Add explicit support for asyncio event loop policies
   - [ ] Ensure thread safety for shared resources
   - [ ] Test on different operating systems

## Next Release (v0.2.0) Priorities

1. [ ] Fix all linter errors in the codebase
2. [ ] Complete the test suite with 90%+ coverage
3. [ ] Improve error handling and type compatibility
4. [ ] Add comprehensive logging
5. [ ] Create proper API documentation
6. [ ] Optimize performance for high-throughput scenarios

## Completed Tasks

### Phase 1
1. [x] Fixed failing tests in `process` method:
   - Fixed `test_orchestrator_process` - Now returns `['Success: 1', 'Success: 2', 'Success: 3']` instead of `['Success: (1, 2, 3)']`
   - Fixed `test_orchestrator_process_with_concurrency` - Same issue as above
   - Modified `process` method to apply function to each item individually rather than passing all args at once

2. [x] Fixed linter errors:
   - Resolved complexity issues in `core.py:execute` method (C901, PLR0912) by extracting helper methods
   - Fixed loop variable binding issues in `core.py` (B023 for `fallback_func`) by capturing variables in closures
   - Addressed too many arguments in `retry.py:with_retry` function (PLR0913) by using a config object and kwargs

3. [x] Created missing files:
   - Created LOG.md for tracking changes and issues
   - Created .cursor/rules/0project.mdc for project rules
   - Created PROGRESS.md file (now merged into CHANGELOG.md and TODO.md)
