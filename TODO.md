---
this_file: TODO.md
---

# TODO

Tip: Periodically run `python ./cleanup.py status` to see results of lints and tests. Use `uv pip ...` not `pip ...`

## Phase 1 - Immediate Priorities

1. [x] Fix remaining linter errors in cleanup.py:
   - [x] Replace `typing.List` with `list` (UP035)
   - [x] Remove unused imports (F401)
   - [x] Fix Boolean-typed positional arguments (FBT001/FBT002)
   - [x] Address subprocess call security issues (S603/S607)
   - [x] Fix unnecessary `list()` call within `sorted()` (C414)
   - [x] Remove unnecessary mode argument (UP015)
   - [x] Replace `print` with logging (T201)

2. [x] Fix linter errors in src/opero/retry.py:
   - [x] Remove unused imports (F401)
   - [x] Update deprecated typing imports (UP035)
   - [x] Use `X | Y` for type annotations (UP007)
   - [x] Reduce complexity in `retry_async` function (C901, PLR0912)

3. [x] Fix linter errors in src/opero/utils.py:
   - [x] Update deprecated typing imports (UP035)
   - [x] Remove unused imports (F401)
   - [x] Use `X | Y` for type annotations (UP007)
   - [x] Fix Boolean-typed positional arguments (FBT001/FBT002)
   - [x] Use `dict` instead of `Dict` for type annotations (UP006)

4. [x] Fix pyproject.toml schema validation errors:
   - [x] Resolve the "valid under more than one of the schemas listed in the 'oneOf' keyword" errors

5. [ ] Improve documentation:
   - [ ] Add more usage examples for common patterns
   - [ ] Document best practices for error handling
   - [ ] Add docstrings to all public functions and classes
   - [ ] Create API reference documentation

## Phase 2 - Next Steps

1. [ ] Enhance test coverage:
   - [ ] Add more unit tests for edge cases in retry mechanism
   - [ ] Create integration tests for complex scenarios combining multiple features
   - [ ] Add performance benchmarks for key operations
   - [ ] Implement stress tests for concurrency and rate limiting

2. [ ] Optimize performance:
   - [ ] Optimize retry logic for better performance
   - [ ] Reduce overhead in the orchestration layer
   - [ ] Improve concurrency management

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

1. [x] Fix all linter errors in the codebase
2. [ ] Complete the test suite with 90%+ coverage
3. [ ] Create proper API documentation
4. [ ] Optimize performance for high-throughput scenarios

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

4. [x] Added comprehensive logging throughout the codebase:
   - Added debug logging for all major operations
   - Implemented configurable log levels
   - Added context information to log messages

5. [x] Improved error handling:
   - Fixed error handling in `retry_async` function to properly handle coroutine objects
   - Addressed type compatibility issues in async/sync conversions
   - Implemented proper handling of `AllFailedError` in all fallback scenarios

6. [x] Fixed linter errors in cleanup.py, retry.py, and utils.py:
   - Added timezone to datetime.datetime.now() calls (DTZ005)
   - Fixed Boolean-typed positional arguments (FBT001/FBT002)
   - Addressed subprocess call security issues (S603/S607)
   - Reduced complexity in retry_async function by extracting helper methods
   - Updated deprecated typing imports and used modern type annotation syntax

7. [x] Updated pyproject.toml:
   - Fixed schema validation errors by cleaning up the structure
   - Removed extra blank lines between sections

8. [x] Fixed cleanup.py script errors:
   - Fixed the `_print_tree` function issue by removing the nested function and using the tree command directly
   - Simplified the tree generation process to avoid argument handling issues
