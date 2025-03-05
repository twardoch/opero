#!/usr/bin/env python3
# this_file: src/opero/core/__init__.py
"""
Core functionality for the opero package.

This module provides the core functionality for the opero package,
including cache, retry, fallback, and rate limiting mechanisms.
"""

from opero.core.cache import get_cache_decorator, get_cache_context, clear_cache
from opero.core.retry import get_retry_decorator
from opero.core.fallback import get_fallback_decorator, FallbackError
from opero.core.rate_limit import get_rate_limit_decorator, RateLimiter

__all__ = [
    "get_cache_decorator",
    "get_cache_context",
    "clear_cache",
    "get_retry_decorator",
    "get_fallback_decorator",
    "FallbackError",
    "get_rate_limit_decorator",
    "RateLimiter",
]
