---
this_file: CHANGELOG.md
---

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure and core functionality (from original base)

### Changed
- **Refactored `src/opero/core/fallback.py`**:
  - Modified `get_fallback_decorator` (both `async_wrapper` and `sync_wrapper`) to correctly implement parameter-based fallbacks.
  - The decorator now iterates through the list of values provided in the function argument specified by `arg_fallback`.
  - For each value in that list, it calls the decorated function with the `arg_fallback` parameter set to that specific value.
  - This fixes the previous limitation where it only replaced the first positional argument.
- **Consolidated Fallback Exceptions**:
  - Enhanced `opero.exceptions.AllFailedError` to store a list of underlying errors.
  - Removed `opero.core.fallback.FallbackError`.
  - Updated `opero.core.fallback.get_fallback_decorator` to use the enhanced `AllFailedError`.
  - Updated `opero/__init__.py` and `opero/core/__init__.py` to reflect this change in exported exceptions.
- Verified `**kwargs` pass-through in `src/opero/core/cache.py`:
  - `get_cache_decorator` correctly passes extra arguments to `twat_cache.ucache`.
  - `get_cache_context` correctly passes extra arguments to `twat_cache.CacheContext`.
- Verified `**kwargs` pass-through in `src/opero/core/retry.py`:
  - `get_retry_decorator` correctly passes extra arguments to `tenacity.Retrying` and `tenacity.AsyncRetrying`.
- Verified `src/opero/core/rate_limit.py`:
  - `get_rate_limit_decorator` initializes `asynciolimiter.Limiter` with the `rate`. `asynciolimiter.Limiter` doesn't have other relevant constructor kwargs for MVP. No changes needed for `**kwargs` pass-through.
- Reviewed `src/opero/concurrency/pool.py`:
  - Confirmed `**kwargs` are passed correctly to `pmap`, `amap`, `apmap` underlying `twat-mp` functions.
  - Clarified (by removing unused `**kwargs` and `**kw`) that for `mode="thread"`, `ThreadPool` is primarily configured by `workers`, simplifying the API for MVP. Other `ThreadPool` args were not exposed via `**kwargs`.
  - Kept all concurrency modes ("process", "thread", "async", "async_process") as their complexity is managed by `twat-mp`.
- Evaluated `src/opero/utils/logging.py`:
  - Confirmed that while `ruff` flags `A005` (shadowing), the current usage is a common pattern and unlikely to cause issues for MVP. No changes made.
- Standardized versioning:
  - Removed manual `VERSION.txt`.
  - Configured `hatch-vcs` in `pyproject.toml` to write version to `src/opero/__version__.py`.
- Reviewed dependencies in `pyproject.toml`:
  - Confirmed essential dependencies are correct for MVP.
  - Optional dependencies align with `twat-mp`'s needs; no changes deemed necessary for `opero`'s MVP.
- Addressed testing environment:
  - Added `klepto` to test dependencies in `pyproject.toml` to resolve potential `ModuleNotFoundError` during test collection originating from `twat-cache`.
- Improved docstring for `get_fallback_decorator` in `src/opero/core/fallback.py` to reflect its behavior with `arg_fallback` as a parameter name.
- Reviewed `@opero` decorator parameters (`src/opero/decorators/opero.py`):
  - Confirmed current parameter list is suitable for MVP.
  - Confirmed `arg_fallback` (string name) is correctly passed to `get_fallback_decorator`.
  - Confirmed `**kwargs` are passed to underlying `get_X_decorator` functions, which is an acceptable pattern. No changes made to `@opero` decorator signature or direct logic.
- Created initial structure for `@opmap` decorator in `src/opero/decorators/opmap.py`:
  - Defined parameters for resilience (caching, retry, fallback, rate limiting) and concurrency.
  - Set up the flow to apply resilience to a single-item processing function, then use `get_parallel_map_decorator` for parallel execution.
  - Updated `src/opero/decorators/__init__.py` to export `@opmap`.
- Deferred linting fixes for `cleanup.py` script as lower priority for library MVP.

### Fixed
- Corrected the logic for parameter-based fallbacks to use the named argument as the source of multiple values to try, rather than always targeting the first positional argument.

## [0.1.0] - TBD (Placeholder from original)

### Added
- Initial release of the `opero` package
- Core functionality:
  - `@opero` decorator
  - `@opmap` decorator
  - Parameter-based fallbacks
  - Retry mechanism
  - Rate limiting
  - Async support
- Basic documentation and examples
