#!/usr/bin/env python3
# this_file: src/opero/decorators/opmap.py
"""
@opmap decorator for the opero package.

This module provides the @opmap decorator for adding resilience mechanisms
and parallel execution to functions that process an iterable of items.
"""

import asyncio
import functools
import logging
from collections.abc import Callable, Iterable
from typing import Any, TypeVar

from opero.core import (
    get_cache_decorator,
    get_fallback_decorator,
    get_rate_limit_decorator,
    get_retry_decorator,
)
from opero.concurrency import get_parallel_map_decorator

# Type variables
T = TypeVar("T")  # Input type for the wrapped function (single item)
R = TypeVar("R")  # Return type of the wrapped function (single item)

logger = logging.getLogger(__name__)


def opmap(
    # Caching options (applied to the single-item processing function)
    cache: bool = True,
    cache_ttl: int | None = None,
    cache_backend: str = "memory",
    cache_key: Callable | None = None,
    cache_namespace: str = "opero_opmap_item", # Default namespace for item processing
    # Retry options (applied to the single-item processing function)
    retries: int = 3,
    backoff_factor: float = 1.5,
    min_delay: float = 0.1,
    max_delay: float = 30.0,
    retry_on: Any = Exception,
    # Fallback options (applied to the single-item processing function)
    arg_fallback: str | None = None,
    # Rate limiting options (applied to the single-item processing function)
    # Note: Rate limiting individual parallel tasks can be complex.
    # If a global rate limit across all workers is needed, that's a more advanced feature.
    # This rate_limit applies to each task before it's executed by a worker.
    rate_limit: float | None = None,
    # Concurrency options (for twat-mp)
    mode: str = "process",
    workers: int = 4,
    ordered: bool = True,
    progress: bool = True,
    # Additional options for underlying decorators or twat-mp
    **kwargs,
):
    """
    Decorator to add resilience and parallel map capabilities to a function.

    The decorated function should be designed to process a single item.
    This decorator will then apply resilience mechanisms (caching, retry,
    fallback, rate limiting) to that single-item processing logic and
    execute it in parallel over an iterable of items using the specified
    concurrency mode.

    Args:
        # Caching options (for single-item processing)
        cache: Whether to enable caching for each item's processing.
        cache_ttl: Time-to-live for cache entries.
        cache_backend: Cache backend to use.
        cache_key: Custom function to generate cache keys for items.
        cache_namespace: Namespace for cache entries.

        # Retry options (for single-item processing)
        retries: Number of retry attempts for each item.
        backoff_factor: Backoff multiplier.
        min_delay: Minimum delay between retries.
        max_delay: Maximum delay between retries.
        retry_on: Exception types to retry on.

        # Fallback options (for single-item processing)
        arg_fallback: Parameter name in the decorated function containing
                      fallback values for that item's processing.

        # Rate limiting options (for single-item processing)
        rate_limit: Max operations per second for each item's processing attempt.

        # Concurrency options (for twat-mp)
        mode: Concurrency mode ("process", "thread", "async", "async_process").
        workers: Number of parallel workers.
        ordered: Whether to preserve input order in results.
        progress: Whether to show progress (if supported by twat-mp mode).

        # Additional options
        **kwargs: Additional arguments to pass to the underlying resilience
                  decorators or to the twat-mp parallel map function.

    Returns:
        A decorator function that wraps the single-item processing function.
        The wrapped function will expect an iterable of items as its argument
        and will return a list of results.
    """

    def decorator(func: Callable[[T], R]) -> Callable[[Iterable[T]], list[R]]:
        """
        Decorates the single-item processing function.
        """

        # 1. Apply resilience decorators to the original single-item function
        #    The order is: Caching -> Rate Limiting -> Retry -> Fallback

        resilient_func = func

        # Apply Fallback
        # Fallback should be deep inside, applied directly to the user's function logic
        # before retries attempt the same failing primary logic multiple times.
        # Order: Cache -> RateLimit -> Fallback -> Retry seems more logical for fallbacks
        # OR Cache -> RateLimit -> Retry -> Fallback (current @opero order)
        # Let's stick to current @opero order for consistency first.
        # Cache -> Rate Limit -> Retry -> Fallback (for the item processing)

        _kwargs_cache = {k.replace('cache_', ''): v for k,v in kwargs.items() if k.startswith('cache_')}
        _kwargs_retry = {k.replace('retry_', ''): v for k,v in kwargs.items() if k.startswith('retry_')}
        _kwargs_fallback = {k.replace('fallback_', ''): v for k,v in kwargs.items() if k.startswith('fallback_')}
        _kwargs_rate_limit = {k.replace('rate_limit_', ''): v for k,v in kwargs.items() if k.startswith('rate_limit_')}
        _kwargs_concurrency = {k.replace('concurrency_', ''): v for k,v in kwargs.items() if k.startswith('concurrency_')}


        # Apply Caching
        cache_decorator = get_cache_decorator(
            cache=cache,
            cache_ttl=cache_ttl,
            cache_backend=cache_backend,
            cache_key=cache_key,
            cache_namespace=cache_namespace,
            **_kwargs_cache, # Pass only cache-related specific kwargs if any, or all kwargs
        )
        resilient_func = cache_decorator(resilient_func)

        # Apply Rate Limiting
        rate_limit_decorator = get_rate_limit_decorator(
            rate_limit=rate_limit,
            **_kwargs_rate_limit
        )
        resilient_func = rate_limit_decorator(resilient_func)

        # Apply Retry
        retry_decorator = get_retry_decorator(
            retries=retries,
            backoff_factor=backoff_factor,
            min_delay=min_delay,
            max_delay=max_delay,
            retry_on=retry_on,
            **_kwargs_retry,
        )
        resilient_func = retry_decorator(resilient_func)

        # Apply Parameter-based Fallbacks
        fallback_decorator = get_fallback_decorator(
            arg_fallback=arg_fallback,
            **_kwargs_fallback
        )
        resilient_func = fallback_decorator(resilient_func)

        # 2. Get the parallel map decorator from twat-mp, configured with concurrency options
        # This decorator will take our now-resilient single-item function
        # and a list of items, and run it in parallel.

        # Need to handle potential async nature of resilient_func if func was async
        # twat-mp's pmap/amap/apmap handle this. ThreadPool map needs special handling for async funcs.

        parallel_map_decorator_factory = get_parallel_map_decorator(
            mode=mode,
            workers=workers,
            ordered=ordered,
            progress=progress,
            **_kwargs_concurrency, # Pass concurrency-specific kwargs
        )

        # Apply the parallel map decorator factory to our resilient single-item function
        parallel_processing_func = parallel_map_decorator_factory(resilient_func)

        @functools.wraps(func) # Wraps the original user function for metadata
        def map_wrapper(items: Iterable[T], **call_time_kwargs) -> list[R]:
            """
            This is the function that users will call with an iterable of items.
            It uses the pre-configured parallel_processing_func.
            """
            # Pass call-time kwargs to the parallel processing function,
            # which in turn might pass them to pmap/amap/apmap if they support it.
            return parallel_processing_func(items, **call_time_kwargs)

        return map_wrapper

    return decorator
