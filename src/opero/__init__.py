#!/usr/bin/env python3
# this_file: src/opero/__init__.py
"""
Opero: Resilient, parallel task orchestration for Python.

This package provides a clean, Pythonic interface for orchestrating resilient,
parallelized operations with parameter-based fallbacks, retry logic, rate limiting,
and multiprocessing support.

Key components:
- @opero: Decorator for adding resilience mechanisms to functions
- @operomap: Decorator for adding resilience mechanisms and parallel execution to functions
"""

from opero.__version__ import __version__
from opero.decorators import opero, operomap
from opero.core import (
    get_cache_decorator,
    get_cache_context,
    clear_cache,
    get_retry_decorator,
    get_fallback_decorator,
    FallbackError,
    get_rate_limit_decorator,
    RateLimiter,
)
from opero.concurrency import get_parallel_executor, get_parallel_map_decorator
from opero.utils import (
    is_async_function,
    ensure_async,
    run_async,
    configure_logging,
    get_logger,
    logger,
)

__all__ = [
    # Version
    "__version__",
    # Decorators
    "opero",
    "operomap",
    # Core
    "get_cache_decorator",
    "get_cache_context",
    "clear_cache",
    "get_retry_decorator",
    "get_fallback_decorator",
    "FallbackError",
    "get_rate_limit_decorator",
    "RateLimiter",
    # Concurrency
    "get_parallel_executor",
    "get_parallel_map_decorator",
    # Utils
    "is_async_function",
    "ensure_async",
    "run_async",
    "configure_logging",
    "get_logger",
    "logger",
]
