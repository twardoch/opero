#!/usr/bin/env python3
# this_file: src/opero/core/__init__.py
"""
Core functionality for the opero package.

This module provides the core functionality for the opero package,
including cache, retry, fallback, and rate limiting mechanisms.
"""

from opero.core.cache import clear_cache, get_cache_context, get_cache_decorator
from opero.core.fallback import get_fallback_decorator # FallbackError removed
from opero.core.rate_limit import RateLimiter, get_rate_limit_decorator
from opero.core.retry import get_retry_decorator

# AllFailedError (which replaces FallbackError) is exported from opero.exceptions via opero/__init__.py

__all__ = [
    "RateLimiter",
    "clear_cache",
    "get_cache_context",
    "get_cache_decorator",
    "get_fallback_decorator",
    "get_rate_limit_decorator",
    "get_retry_decorator",
]
