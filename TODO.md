---
this_file: TODO.md
---

# TODO

Tip: Periodically run `python ./cleanup.py status` to see results of lints and tests. Use `uv pip ...` not `pip ...`

## High Priority Tasks

- [ ] Complete the test suite with 90%+ coverage
  - [ ] Add tests for edge cases in retry mechanism
  - [ ] Create integration tests for complex scenarios
  - [ ] Add tests for error handling in concurrent operations
  - [ ] Implement test coverage reporting

- [ ] Optimize performance for high-throughput scenarios
  - [ ] Profile code to identify bottlenecks
  - [ ] Reduce overhead in the orchestration layer
  - [ ] Optimize retry logic for better performance
  - [ ] Improve concurrency management

- [ ] Fix remaining type issues in pyproject.toml
  - [ ] Resolve schema validation errors in hatch configuration
  - [ ] Update deprecated settings

## Medium Priority Tasks

- [ ] Add performance benchmarks
  - [ ] Create benchmark suite for key operations
  - [ ] Implement stress tests for concurrency and rate limiting
  - [ ] Add comparison benchmarks against similar libraries

- [ ] Infrastructure improvements
  - [ ] Set up CI/CD pipeline for automated testing and deployment
  - [ ] Configure code coverage reporting
  - [ ] Add pre-commit hooks for code quality
  - [ ] Create GitHub Actions workflow for publishing to PyPI
  - [ ] Set up automated dependency updates

- [ ] Compatibility enhancements
  - [ ] Test with different versions of dependencies
  - [ ] Add explicit support for asyncio event loop policies
  - [ ] Ensure thread safety for shared resources
  - [ ] Test on different operating systems

## Low Priority Tasks

- [ ] Feature enhancements
  - [ ] Implement middleware support for function transformation
  - [ ] Add metrics collection for performance monitoring
  - [ ] Create a CLI interface using `fire` and `rich`
  - [ ] Add support for distributed task queues
  - [ ] Implement streaming support with backpressure handling

## Completed Tasks

- [x] Fix all linter errors in the codebase
- [x] Create proper API documentation
- [x] Improve documentation
  - [x] Add more usage examples for common patterns
  - [x] Document best practices for error handling
  - [x] Add docstrings to all public functions and classes
  - [x] Create API reference documentation
- [x] Fix parameter order in retry function calls
- [x] Add fallback mechanism for handling None configurations
- [x] Fix type incompatibility issues in async/sync conversions
- [x] Enhance structured logging with context support

## Next Release (v0.2.0) Priorities

1. [x] Fix all linter errors in the codebase
2. [ ] Complete the test suite with 90%+ coverage
3. [x] Create proper API documentation
4. [ ] Optimize performance for high-throughput scenarios
5. [ ] Fix remaining type issues in pyproject.toml

