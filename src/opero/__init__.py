#!/usr/bin/env python3
# this_file: src/opero/__init__.py
"""Opero: Resilient, parallel task orchestration for Python.

This package provides a clean, Pythonic interface for orchestrating resilient,
parallelized operations with parameter-based fallbacks, retry logic, rate limiting,
and multiprocessing support.

Key Features:
    - **Automatic Retries**: Handle transient failures with exponential backoff
    - **Parameter Fallbacks**: Try alternative values (e.g., backup API keys)
    - **Rate Limiting**: Respect API limits and prevent overload
    - **Caching**: Reduce redundant operations with flexible caching
    - **Parallel Processing**: Execute operations concurrently across workers
    - **Async Support**: Full support for both sync and async functions

Main Components:
    - @opero: Decorator for adding resilience mechanisms to functions
    - @opmap: Decorator for adding resilience and parallel execution

Quick Example:
    from opero import opero, opmap

    # Add resilience to a single function
    @opero(retries=3, cache=True, rate_limit=10.0)
    def fetch_data(url):
        return requests.get(url).json()

    # Add resilience and parallel processing
    @opmap(mode="thread", workers=10, retries=2)
    def process_item(item):
        return expensive_operation(item)
    
    # Process many items in parallel
    results = process_item(list_of_items)
"""

from opero.__version__ import __version__
from opero.concurrency import get_parallel_executor, get_parallel_map_decorator
from opero.core import (
    RateLimiter, # FallbackError removed from core exports
    clear_cache,
    get_cache_context,
    get_cache_decorator,
    get_fallback_decorator,
    get_rate_limit_decorator,
    get_retry_decorator,
)
from opero.decorators import opero, opmap
# Import AllFailedError from exceptions
from opero.exceptions import OperoError, AllFailedError
from opero.utils import (
    configure_logging,
    ensure_async,
    get_logger,
    is_async_function,
    logger,
    run_async,
)

__all__ = [
    "OperoError",
    "AllFailedError", # Added AllFailedError
    "RateLimiter",
    # Version
    "__version__",
    "clear_cache",
    "configure_logging",
    "ensure_async",
    "get_cache_context",
    # Core
    "get_cache_decorator",
    "get_fallback_decorator",
    "get_logger",
    # Concurrency
    "get_parallel_executor",
    "get_parallel_map_decorator",
    "get_rate_limit_decorator",
    "get_retry_decorator",
    # Utils
    "is_async_function",
    "logger",
    # Decorators
    "opero",
    "opmap",
    "run_async",
]
