#!/usr/bin/env python3
# this_file: src/opero/concurrency/pool.py
"""
Concurrency functionality for opero using twat-mp.

This module provides integration with the twat-mp library for parallel execution
in opero decorators.
"""

import asyncio
import functools
import logging
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    TypeVar,
    Union,
    cast,
    Iterable,
    Iterator,
    Awaitable,
)

# Import from twat-mp
from twat_mp import pmap, tmap, amap, apmap

T = TypeVar("T")  # Input type
R = TypeVar("R")  # Return type

logger = logging.getLogger(__name__)


def get_parallel_executor(
    mode: str = "process",
    workers: int = 4,
    ordered: bool = True,
    progress: bool = True,
    **kwargs,
) -> Callable[[Callable[[T], R], Iterable[T]], List[R]]:
    """
    Get a parallel executor function based on the provided configuration.

    Args:
        mode: Concurrency mode ("process", "thread", or "async")
        workers: Number of workers
        ordered: Whether to preserve input order in results
        progress: Whether to show progress
        **kwargs: Additional arguments to pass to the executor

    Returns:
        A parallel executor function
    """
    if mode == "process":

        def process_executor(func: Callable[[T], R], items: Iterable[T]) -> List[R]:
            """
            Process-based parallel executor.

            Args:
                func: Function to execute
                items: Items to process

            Returns:
                List of results
            """
            return list(
                pmap(func)(
                    items, workers=workers, ordered=ordered, progress=progress, **kwargs
                )
            )

        return process_executor

    elif mode == "thread":

        def thread_executor(func: Callable[[T], R], items: Iterable[T]) -> List[R]:
            """
            Thread-based parallel executor.

            Args:
                func: Function to execute
                items: Items to process

            Returns:
                List of results
            """
            return list(
                tmap(func)(
                    items, workers=workers, ordered=ordered, progress=progress, **kwargs
                )
            )

        return thread_executor

    elif mode == "async":

        def async_executor(func: Callable[[T], R], items: Iterable[T]) -> List[R]:
            """
            Async-based parallel executor.

            Args:
                func: Function to execute
                items: Items to process

            Returns:
                List of results
            """
            # If we're already in an event loop, use it
            try:
                loop = asyncio.get_running_loop()
                return loop.run_until_complete(
                    amap(func)(
                        items,
                        workers=workers,
                        ordered=ordered,
                        progress=progress,
                        **kwargs,
                    )
                )
            except RuntimeError:
                # No event loop running, create one
                return asyncio.run(
                    amap(func)(
                        items,
                        workers=workers,
                        ordered=ordered,
                        progress=progress,
                        **kwargs,
                    )
                )

        return async_executor

    elif mode == "async_process":

        def async_process_executor(
            func: Callable[[T], R], items: Iterable[T]
        ) -> List[R]:
            """
            Async process-based parallel executor.

            Args:
                func: Function to execute
                items: Items to process

            Returns:
                List of results
            """
            # If we're already in an event loop, use it
            try:
                loop = asyncio.get_running_loop()
                return loop.run_until_complete(
                    apmap(func)(
                        items,
                        workers=workers,
                        ordered=ordered,
                        progress=progress,
                        **kwargs,
                    )
                )
            except RuntimeError:
                # No event loop running, create one
                return asyncio.run(
                    apmap(func)(
                        items,
                        workers=workers,
                        ordered=ordered,
                        progress=progress,
                        **kwargs,
                    )
                )

        return async_process_executor

    else:
        raise ValueError(f"Unknown concurrency mode: {mode}")


def get_parallel_map_decorator(
    mode: str = "process",
    workers: int = 4,
    ordered: bool = True,
    progress: bool = True,
    **kwargs,
) -> Callable[[Callable[[T], R]], Callable[[Iterable[T]], List[R]]]:
    """
    Get a parallel map decorator based on the provided configuration.

    Args:
        mode: Concurrency mode ("process", "thread", "async", or "async_process")
        workers: Number of workers
        ordered: Whether to preserve input order in results
        progress: Whether to show progress
        **kwargs: Additional arguments to pass to the executor

    Returns:
        A parallel map decorator function
    """
    if mode == "process":
        return lambda func: lambda items, **kw: list(
            pmap(func)(
                items,
                workers=workers,
                ordered=ordered,
                progress=progress,
                **{**kwargs, **kw},
            )
        )

    elif mode == "thread":
        return lambda func: lambda items, **kw: list(
            tmap(func)(
                items,
                workers=workers,
                ordered=ordered,
                progress=progress,
                **{**kwargs, **kw},
            )
        )

    elif mode == "async":

        def decorator(func: Callable[[T], R]) -> Callable[[Iterable[T]], List[R]]:
            """
            Decorator function.

            Args:
                func: The function to decorate

            Returns:
                The decorated function
            """
            decorated = amap(func)

            def wrapper(items: Iterable[T], **kw: Any) -> List[R]:
                """
                Wrapper function.

                Args:
                    items: Items to process
                    **kw: Additional keyword arguments

                Returns:
                    List of results
                """
                # If we're already in an event loop, use it
                try:
                    loop = asyncio.get_running_loop()
                    return loop.run_until_complete(
                        decorated(
                            items,
                            workers=workers,
                            ordered=ordered,
                            progress=progress,
                            **{**kwargs, **kw},
                        )
                    )
                except RuntimeError:
                    # No event loop running, create one
                    return asyncio.run(
                        decorated(
                            items,
                            workers=workers,
                            ordered=ordered,
                            progress=progress,
                            **{**kwargs, **kw},
                        )
                    )

            return wrapper

        return decorator

    elif mode == "async_process":

        def decorator(func: Callable[[T], R]) -> Callable[[Iterable[T]], List[R]]:
            """
            Decorator function.

            Args:
                func: The function to decorate

            Returns:
                The decorated function
            """
            decorated = apmap(func)

            def wrapper(items: Iterable[T], **kw: Any) -> List[R]:
                """
                Wrapper function.

                Args:
                    items: Items to process
                    **kw: Additional keyword arguments

                Returns:
                    List of results
                """
                # If we're already in an event loop, use it
                try:
                    loop = asyncio.get_running_loop()
                    return loop.run_until_complete(
                        decorated(
                            items,
                            workers=workers,
                            ordered=ordered,
                            progress=progress,
                            **{**kwargs, **kw},
                        )
                    )
                except RuntimeError:
                    # No event loop running, create one
                    return asyncio.run(
                        decorated(
                            items,
                            workers=workers,
                            ordered=ordered,
                            progress=progress,
                            **{**kwargs, **kw},
                        )
                    )

            return wrapper

        return decorator

    else:
        raise ValueError(f"Unknown concurrency mode: {mode}")
