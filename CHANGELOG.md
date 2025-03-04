---
this_file: CHANGELOG.md
---

# Changelog

All notable changes to the Opero project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive logging throughout the codebase with configurable log levels
- Context information to log messages for better debugging
- Proper timezone handling in datetime operations

### Changed
- Modified `process` method to apply function to each item individually
- Improved error handling in async/sync conversions
- Optimized retry logic and fallback mechanisms
- Restructured code to reduce complexity in core functions

### Fixed
- Fixed failing tests in `process` method
- Resolved complexity issues in `core.py:execute` method
- Fixed loop variable binding issues in `core.py`
- Addressed too many arguments in `retry.py:with_retry` function
- Fixed error handling in `retry_async` function
- Fixed linter errors in cleanup.py including:
  - Added timezone to datetime.datetime.now() calls
  - Fixed Boolean-typed positional arguments
  - Addressed subprocess call security issues
- Updated pyproject.toml configuration for proper linting

## [0.1.0] - Initial Release

### Added
- Fallback chains for automatic alternative function execution
- Automatic retries with configurable backoff strategies
- Rate limiting to control operation frequency
- Parallel processing with configurable limits
- Async-first design with full support for sync functions
- Unified interface with both class-based and decorator-based APIs
- Comprehensive type hints for better IDE integration
