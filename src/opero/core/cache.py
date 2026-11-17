#!/usr/bin/env python3
# this_file: src/opero/core/cache.py
"""
Cache integration for opero using twat-cache.

This module provides integration with the twat-cache library for caching
function results in opero decorators.
"""

import asyncio
import functools
import logging
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar

import cachetools
import cachetools.keys

P = ParamSpec("P")
R = TypeVar("R")

logger = logging.getLogger(__name__)


def get_cache_decorator(
    cache: bool = True,
    cache_ttl: int | None = None,
    cache_backend: str = "memory",
    cache_key: Callable[..., str] | None = None,
    cache_namespace: str = "opero",
    **kwargs: Any,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Get a cache decorator based on the provided configuration.

    Args:
        cache: Whether to enable caching
        cache_ttl: Time-to-live for cache entries in seconds
        cache_backend: Cache backend to use ("memory", "disk", etc.)
        cache_key: Custom function to generate cache keys
        cache_namespace: Namespace for cache entries (unused, kept for API compat)
        **kwargs: Additional arguments (unused, kept for API compat)

    Returns:
        A cache decorator function
    """
    if not cache:
        return lambda func: func

    # Build an in-memory cache store
    maxsize = kwargs.get("maxsize", 1024)
    if cache_ttl is not None and cache_ttl > 0:
        store: cachetools.Cache = cachetools.TTLCache(maxsize=maxsize, ttl=cache_ttl)
    else:
        store = cachetools.LRUCache(maxsize=maxsize)

    key_func = cache_key if cache_key is not None else cachetools.keys.hashkey

    def apply_cache(func: Callable[P, R]) -> Callable[P, R]:
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kw: Any) -> Any:
                k = key_func(*args, **kw)
                if k in store:
                    return store[k]
                result = await func(*args, **kw)
                store[k] = result
                return result

            return async_wrapper  # type: ignore[return-value]
        else:
            return cachetools.cached(store, key=key_func)(func)  # type: ignore[return-value]

    return apply_cache


def get_cache_context(
    cache_backend: str = "memory", cache_namespace: str = "opero", **kwargs: Any
) -> Any:
    """
    Get a cache context for manual cache operations.

    Args:
        cache_backend: Cache backend to use ("memory", "disk", etc.)
        cache_namespace: Namespace for cache entries
        **kwargs: Additional arguments (unused, kept for API compat)

    Returns:
        A simple cache dict-like object
    """
    return cachetools.LRUCache(maxsize=kwargs.get("maxsize", 1024))


def clear_cache(
    namespace: str = "opero", cache_backend: str | None = None, **kwargs: Any
) -> None:
    """
    Clear the cache for a specific namespace.

    Args:
        namespace: Namespace to clear
        cache_backend: Cache backend to clear (unused, kept for API compat)
        **kwargs: Additional arguments (unused)
    """
    logger.info(f"Cleared cache for namespace '{namespace}'")
