#!/usr/bin/env python3
# this_file: src/opero/core/rate_limit.py
"""
Rate limiting functionality for opero.

This module provides rate limiting mechanisms for function calls in opero decorators.
"""

import asyncio
import functools
import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar

import asynciolimiter

P = TypeVar("P")
R = TypeVar("R")

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for controlling function call frequency.
    
    This class provides both synchronous and asynchronous rate limiting
    capabilities. It ensures that operations don't exceed a specified
    rate limit (calls per second).
    
    Attributes:
        rate_limit: Maximum number of operations per second.
        min_interval: Minimum time interval between operations.
        last_call_time: Timestamp of the last operation (for sync mode).
        async_limiter: Async rate limiter instance.
    
    Example:
        # Create a rate limiter for 5 calls per second
        limiter = RateLimiter(5.0)
        
        # Synchronous usage
        for i in range(10):
            limiter.wait()
            print(f"Operation {i}")
            
        # Asynchronous usage
        async def rate_limited_operation():
            await limiter.wait_async()
            return await some_async_operation()
    """

    def __init__(self, rate_limit: float) -> None:
        """Initialize the rate limiter with a specified rate.

        Args:
            rate_limit: Maximum number of operations per second.
                If <= 0, no rate limiting is applied.
        """
        self.rate_limit = rate_limit
        self.min_interval = 1.0 / rate_limit if rate_limit > 0 else 0
        self.last_call_time = 0.0
        self.async_limiter = asynciolimiter.Limiter(rate_limit)

    def wait(self) -> None:
        """Wait synchronously until the rate limit allows another operation.
        
        This method blocks the current thread if necessary to maintain
        the configured rate limit. It uses time.sleep() for delays.
        
        Note:
            For async code, use wait_async() instead.
        """
        if self.rate_limit <= 0:
            return

        current_time = time.time()
        elapsed = current_time - self.last_call_time

        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            time.sleep(sleep_time)

        self.last_call_time = time.time()

    async def wait_async(self) -> None:
        """Wait asynchronously until the rate limit allows another operation.
        
        This method uses asyncio-compatible rate limiting, allowing other
        coroutines to run while waiting for the rate limit.
        
        Note:
            For synchronous code, use wait() instead.
        """
        if self.rate_limit <= 0:
            return

        await self.async_limiter.acquire()  # type: ignore[attr-defined]


def get_rate_limit_decorator(
    rate_limit: float | None = None,
) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """
    Get a rate limit decorator based on the provided configuration.

    Args:
        rate_limit: Maximum number of operations per second

    Returns:
        A rate limit decorator function
    """
    if not rate_limit or rate_limit <= 0:
        # Return a no-op decorator if rate limiting is disabled
        return lambda func: func

    # Create a rate limiter
    limiter = RateLimiter(rate_limit)

    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        """
        Decorator function.

        Args:
            func: The function to decorate

        Returns:
            The decorated function
        """
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> R:
                """
                Async wrapper function.

                Args:
                    *args: Positional arguments to pass to the function
                    **kwargs: Keyword arguments to pass to the function

                Returns:
                    The result of the function call
                """
                await limiter.wait_async()
                result = await func(*args, **kwargs)
                return result  # type: ignore[no-any-return]

            return async_wrapper  # type: ignore[return-value]
        else:

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> R:
                """
                Sync wrapper function.

                Args:
                    *args: Positional arguments to pass to the function
                    **kwargs: Keyword arguments to pass to the function

                Returns:
                    The result of the function call
                """
                limiter.wait()
                return func(*args, **kwargs)

            return sync_wrapper

    return decorator
