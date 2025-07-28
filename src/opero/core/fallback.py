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
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar, get_type_hints

P = TypeVar("P")
R = TypeVar("R")

logger = logging.getLogger(__name__)

# Import AllFailedError from the central exceptions module
from opero.exceptions import AllFailedError


def get_fallback_decorator(
    arg_fallback: str | None = None,
) -> Callable[[Callable[..., R]], Callable[..., R | Coroutine[Any, Any, R]]]:
    """
    Get a parameter-based fallback decorator.

    This decorator modifies a function to try different values for a specified
    argument if the initial call fails. The specified argument in the decorated
    function's signature is expected to receive a list or tuple of potential values.
    The decorator will then iterate through these values, calling the decorated
    function with each one until a call succeeds or all values are exhausted.

    Args:
        arg_fallback: The name of the parameter in the decorated function
                      that will contain the list of fallback values.

    Returns:
        A decorator function that, when applied, enables parameter-based fallbacks.
        It returns the result of the first successful call, or raises an
        AllFailedError if all attempts fail.
        The returned callable will be async if the original function was async.

    Example:
        @get_fallback_decorator(arg_fallback="api_key")
        def call_api(data: dict, api_key: str): # api_key will be one value from the list at runtime
            # ... call API with api_key ...
            if api_key == "bad_key":
                raise ValueError("Invalid API Key")
            return f"Success with {api_key}"

        # Usage:
        # await call_api({"data": "info"}, api_key=["bad_key", "good_key"])
        # This would first try with "bad_key", fail, then try with "good_key" and succeed.
    """
    if not arg_fallback:
        # Return a no-op decorator if fallbacks are disabled
        return lambda func: func

    def decorator(func: Callable[..., R]) -> Callable[..., R | Coroutine[Any, Any, R]]:
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
        type_hints.get(arg_fallback, Any)

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
                # Extract the list of fallback values for the designated argument
                # The decorated function is expected to receive this list.
                # We use .pop() to get the original list and remove it from kwargs for the actual func call,
                # to avoid func receiving a list when it expects a single value.
                # If it's a positional arg, it's more complex, for now, assume it's a kwarg.

                original_fallback_values_list = kwargs.pop(arg_fallback, None)

                if not isinstance(original_fallback_values_list, (list, tuple)):
                    logger.warning(
                        f"Fallback argument '{arg_fallback}' in {func.__name__} is not a list or tuple. Fallback disabled."
                    )
                    # Restore if popped, then call original function once
                    if original_fallback_values_list is not None: # only restore if it was popped
                        kwargs[arg_fallback] = original_fallback_values_list
                    result = await func(*args, **kwargs)
                    return result  # type: ignore[no-any-return]

                if not original_fallback_values_list:
                    logger.warning(
                        f"Fallback argument '{arg_fallback}' in {func.__name__} is empty. Fallback disabled."
                    )
                    # Call original function once (arg_fallback might be an empty list passed intentionally)
                    kwargs[arg_fallback] = original_fallback_values_list # ensure it's passed as empty list
                    result = await func(*args, **kwargs)
                    return result  # type: ignore[no-any-return]

                errors = []
                # Try with each value from the fallback list
                for fallback_value_attempt in original_fallback_values_list:
                    try:
                        # Create a mutable copy of kwargs for this attempt
                        current_kwargs = kwargs.copy()
                        current_kwargs[arg_fallback] = fallback_value_attempt
                        logger.debug(f"Attempting call for {func.__name__} with {arg_fallback}={fallback_value_attempt}")
                        result = await func(*args, **current_kwargs)
                        return result  # type: ignore[no-any-return]
                    except Exception as e:
                        errors.append(e)
                        logger.warning(
                            f"Call failed for {func.__name__} with {arg_fallback}={fallback_value_attempt}: {e!s}"
                        )

                # If all fallback attempts fail
                msg = f"All fallback attempts for {arg_fallback} failed for {func.__name__}"
                raise AllFailedError(msg, errors=errors)

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
                # Get fallback values from kwargs or initialize with default
                fallback_values = kwargs.get(arg_fallback, ["fallback"])
                if not isinstance(fallback_values, list | tuple):
                    fallback_values = [fallback_values]

                # Try the original call first
                try:
                    # Pass the fallback values to the function
                    kwargs[arg_fallback] = fallback_values
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"Original call failed for {func.__name__}: {e!s}")

                    # Try each fallback value
                    errors = [e]
                    for fallback_value in fallback_values:
                        try:
                            # Replace the first argument with the fallback value
                            new_args = (fallback_value,) + args[1:]
                            return func(*new_args, **kwargs)
                        except Exception as e:
                            errors.append(e)
                            logger.warning(
                                f"Fallback call failed for {func.__name__} with value {fallback_value}: {e!s}"
                            )

                    # If all fallbacks fail, raise an AllFailedError with all errors
                    msg = f"All fallback attempts failed for {func.__name__}"
                    raise AllFailedError(
                        msg,
                        errors=errors,
                    )

            return sync_wrapper

    return decorator
