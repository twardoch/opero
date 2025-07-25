# Changelog

All notable changes to Opero will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive documentation with mkdocs-material
- API reference documentation with examples
- Testing guide for contributors
- Best practices guide for production usage

### Changed
- Improved type hints throughout the codebase
- Enhanced error messages with more context

### Fixed
- Fixed cache key generation for complex arguments
- Resolved async context manager cleanup issues

## [0.2.0] - 2024-01-15

### Added
- `@opmap` decorator for parallel processing with resilience
- Support for parameter-based fallbacks via `arg_fallback`
- Rate limiting functionality with `rate_limit` parameter
- Async function support in all decorators
- Comprehensive logging throughout the library
- `AllFailedError` exception with detailed error tracking

### Changed
- Refactored fallback mechanism to use parameter names
- Improved cache key generation for better performance
- Updated dependencies to latest versions

### Fixed
- Fixed thread safety issues in rate limiter
- Resolved memory leaks in long-running processes
- Fixed async function detection edge cases

## [0.1.0] - 2023-12-01

### Added
- Initial release
- `@opero` decorator with retry functionality
- Cache support with multiple backends
- Basic retry with exponential backoff
- Integration with tenacity for retry logic
- Integration with twat-cache for caching
- Support for both sync and async functions

[Unreleased]: https://github.com/twardoch/opero/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/twardoch/opero/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/twardoch/opero/releases/tag/v0.1.0