#!/usr/bin/env python3
# this_file: src/opero/core/fallback.py
"""
Parameter-based fallback functionality for opero.

This module provides parameter-based fallback mechanisms for function calls in opero decorators.
"""

import asyncio
import functools
import inspect
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
    get_type_hints,
)

P = TypeVar("P")
R = TypeVar("R")

logger = logging.getLogger(__name__)


class FallbackError(Exception):
    """Exception raised when all fallback attempts fail."""

    def __init__(self, message: str, errors: List[Exception]) -> None:
        """
        Initialize the exception.

        Args:
            message: Error message
            errors: List of exceptions from fallback attempts
        """
        self.errors = errors
        super().__init__(f"{message}: {errors}")


def get_fallback_decorator(
    arg_fallback: Optional[str] = None,
) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """
    Get a parameter-based fallback decorator.

    Args:
        arg_fallback: Name of the parameter containing fallback values

    Returns:
        A fallback decorator function
    """
    if not arg_fallback:
        # Return a no-op decorator if fallbacks are disabled
        return lambda func: func

    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        """
        Decorator function.

        Args:
            func: The function to decorate

        Returns:
            The decorated function
        """
        # Get the function signature
        sig = inspect.signature(func)

        # Check if the fallback parameter exists in the function signature
        if arg_fallback not in sig.parameters:
            logger.warning(
                f"Fallback parameter '{arg_fallback}' not found in function signature "
                f"for {func.__name__}. Fallbacks will be disabled."
            )
            return func

        # Get the parameter's type hint
        type_hints = get_type_hints(func)
        param_type = type_hints.get(arg_fallback, Any)

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
                # Get the fallback values
                fallback_values = kwargs.get(arg_fallback, None)

                # If no fallback values are provided, just call the function
                if fallback_values is None:
                    # Check if the parameter is in args
                    param_index = list(sig.parameters).index(arg_fallback)
                    if param_index < len(args):
                        fallback_values = args[param_index]

                # If still no fallback values, just call the function
                if fallback_values is None:
                    return await func(*args, **kwargs)

                # Ensure fallback_values is a list
                if not isinstance(fallback_values, (list, tuple)):
                    fallback_values = [fallback_values]

                # Try each fallback value
                errors = []
                for i, value in enumerate(fallback_values):
                    try:
                        # Create a copy of kwargs with the current fallback value
                        kwargs_copy = kwargs.copy()
                        kwargs_copy[arg_fallback] = value

                        # Call the function with the current fallback value
                        return await func(*args, **kwargs_copy)
                    except Exception as e:
                        logger.warning(
                            f"Fallback attempt {i + 1}/{len(fallback_values)} failed for "
                            f"{func.__name__} with {arg_fallback}={value}: {e}"
                        )
                        errors.append(e)

                # If all fallbacks fail, raise an exception
                raise FallbackError(
                    f"All fallback attempts failed for {func.__name__}", errors
                )

            return async_wrapper
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
                # Get the fallback values
                fallback_values = kwargs.get(arg_fallback, None)

                # If no fallback values are provided, just call the function
                if fallback_values is None:
                    # Check if the parameter is in args
                    param_index = list(sig.parameters).index(arg_fallback)
                    if param_index < len(args):
                        fallback_values = args[param_index]

                # If still no fallback values, just call the function
                if fallback_values is None:
                    return func(*args, **kwargs)

                # Ensure fallback_values is a list
                if not isinstance(fallback_values, (list, tuple)):
                    fallback_values = [fallback_values]

                # Try each fallback value
                errors = []
                for i, value in enumerate(fallback_values):
                    try:
                        # Create a copy of kwargs with the current fallback value
                        kwargs_copy = kwargs.copy()
                        kwargs_copy[arg_fallback] = value

                        # Call the function with the current fallback value
                        return func(*args, **kwargs_copy)
                    except Exception as e:
                        logger.warning(
                            f"Fallback attempt {i + 1}/{len(fallback_values)} failed for "
                            f"{func.__name__} with {arg_fallback}={value}: {e}"
                        )
                        errors.append(e)

                # If all fallbacks fail, raise an exception
                raise FallbackError(
                    f"All fallback attempts failed for {func.__name__}", errors
                )

            return sync_wrapper

    return decorator
