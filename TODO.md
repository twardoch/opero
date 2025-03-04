---
this_file: TODO.md
---

# TODO

Tip: Periodically run `python ./cleanup.py status` to see results of lints and tests. Use `uv pip ...` not `pip ...`

## Phase 1

- [ ] Complete the test suite with 90%+ coverage
- [ ] Optimize performance for high-throughput scenarios
- [ ] Add more usage examples for common patterns
- [ ] Document best practices for error handling
- [ ] Add docstrings to all public functions and classes
- [ ] Create API reference documentation

## Phase 2 

- [ ] Add more unit tests for edge cases in retry mechanism
- [ ] Create integration tests for complex scenarios combining multiple features
- [ ] Add performance benchmarks for key operations
- [ ] Implement stress tests for concurrency and rate limiting
- [ ] Optimize retry logic for better performance
- [ ] Reduce overhead in the orchestration layer
- [ ] Improve concurrency management

## Phase 3

- [ ] Implement middleware support for function transformation
- [ ] Add metrics collection for performance monitoring
- [ ] Create a CLI interface using `fire` and `rich`
- [ ] Add support for distributed task queues
- [ ] Implement streaming support with backpressure handling

1. [ ] Infrastructure improvements:
   - [ ] Set up CI/CD pipeline for automated testing and deployment
   - [ ] Configure code coverage reporting
   - [ ] Add pre-commit hooks for code quality
   - [ ] Create GitHub Actions workflow for publishing to PyPI
   - [ ] Set up automated dependency updates

2. [ ] Compatibility enhancements:
   - [ ] Ensure compatibility with Python 3.8+
   - [ ] Test with different versions of dependencies
   - [ ] Add explicit support for asyncio event loop policies
   - [ ] Ensure thread safety for shared resources
   - [ ] Test on different operating systems

