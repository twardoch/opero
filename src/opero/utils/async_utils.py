#!/usr/bin/env python3
# this_file: src/opero/utils/async_utils.py
"""
Async utility functions for the opero package.

This module provides utility functions for async operations in the opero package.
"""

import asyncio
import functools
import inspect
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

T = TypeVar("T")
R = TypeVar("R")


def is_async_function(func: Callable[..., Any]) -> bool:
    """Check if a function is async (coroutine function).

    This function checks whether the provided callable is an async function
    that returns a coroutine when called.

    Args:
        func: The function to check.

    Returns:
        True if the function is async, False otherwise.

    Example:
        async def async_func():
            await asyncio.sleep(1)
            
        def sync_func():
            time.sleep(1)
            
        print(is_async_function(async_func))  # True
        print(is_async_function(sync_func))   # False
    """
    return asyncio.iscoroutinefunction(func) or inspect.isawaitable(func)


def ensure_async(func: Callable[..., R]) -> Callable[..., Coroutine[Any, Any, R]]:
    """Convert a sync function to async if needed.

    This utility ensures that any function can be used in an async context.
    If the function is already async, it's returned unchanged. If it's sync,
    it's wrapped to become awaitable.

    Args:
        func: Function to potentially convert to async.

    Returns:
        An async version of the function that can be awaited.

    Example:
        def sync_add(x, y):
            return x + y
            
        async def async_add(x, y):
            await asyncio.sleep(0.1)
            return x + y
            
        # Both can now be used in async context
        async_sync_add = ensure_async(sync_add)
        async_async_add = ensure_async(async_add)
        
        async def main():
            result1 = await async_sync_add(1, 2)  # Works
            result2 = await async_async_add(3, 4)  # Also works
    """
    if asyncio.iscoroutinefunction(func):
        return func

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> R:
        """
        Async wrapper function.

        Args:
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            The result of the function call
        """
        return func(*args, **kwargs)

    return wrapper


def run_async(
    func: Callable[..., Coroutine[Any, Any, R]], *args: Any, **kwargs: Any
) -> R:
    """Run an async function synchronously.

    This utility allows running async functions from synchronous code.
    It handles event loop creation and cleanup properly, avoiding common
    pitfalls with asyncio.run() in nested contexts.

    Args:
        func: Async function to run.
        *args: Positional arguments for the function.
        **kwargs: Keyword arguments for the function.

    Returns:
        The result of the async function.

    Example:
        async def fetch_data(url):
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return await response.text()
        
        # Run from sync code
        data = run_async(fetch_data, "https://api.example.com/data")
        print(data)
        
    Note:
        This function will use an existing event loop if one is running,
        otherwise it creates a new one. This makes it safe to use in
        various contexts including Jupyter notebooks.
    """
    # If we're already in an event loop, use it
    try:
        loop = asyncio.get_running_loop()
        return loop.run_until_complete(func(*args, **kwargs))
    except RuntimeError:
        # No event loop running, create one
        return asyncio.run(func(*args, **kwargs))
