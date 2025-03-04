#!/usr/bin/env python3
# this_file: src/opero/retry.py
"""
Retry functionality for the opero package.

This module provides retry capabilities built on top of the tenacity library,
with support for both synchronous and asynchronous functions.
"""

from __future__ import annotations

import asyncio
import functools
import inspect
from collections.abc import Callable
from dataclasses import asdict, dataclass
from typing import Any, ParamSpec, TypeVar, cast

from tenacity import (
    RetryError,
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from opero.utils import ContextAdapter, get_logger

# Define type variables for generic function types
P = ParamSpec("P")
R = TypeVar("R")

# Get a logger with context support
_logger = get_logger(__name__)
logger = ContextAdapter(_logger)


# Custom RetryError that doesn't require a Future object
class CustomRetryError(Exception):
    """Custom exception for retry failures that doesn't require a Future object."""

    def __init__(self, message: str, original_exception: Exception | None = None):
        self.message = message
        self.original_exception = original_exception
        super().__init__(message)


@dataclass
class RetryConfig:
    """
    Configuration for retry behavior.

    This class provides a way to configure retry behavior with sensible defaults.
    Under the hood, it uses tenacity for the actual retry implementation.

    Attributes:
        max_attempts: Maximum number of retry attempts
        wait_min: Minimum wait time between retries (in seconds)
        wait_max: Maximum wait time between retries (in seconds)
        wait_multiplier: Multiplier for exponential backoff
        retry_exceptions: Exception types that should trigger a retry
        reraise: Whether to reraise the last exception after all retries fail
    """

    max_attempts: int = 3
    wait_min: float = 1.0
    wait_max: float = 60.0
    wait_multiplier: float = 1.0
    retry_exceptions: tuple[type[Exception], ...] = (Exception,)
    reraise: bool = True

    def get_retry_arguments(self) -> dict[str, Any]:
        """
        Get the arguments to pass to tenacity's Retrying/AsyncRetrying.

        Returns:
            Dictionary of arguments for tenacity.
        """
        return {
            "stop": stop_after_attempt(self.max_attempts),
            "wait": wait_exponential(
                multiplier=self.wait_multiplier,
                min=self.wait_min,
                max=self.wait_max,
            ),
            "retry": retry_if_exception_type(self.retry_exceptions),
            "reraise": self.reraise,
            "before_sleep": lambda retry_state: logger.debug(
                f"Retrying in {retry_state.next_action.sleep} seconds: "
                f"attempt {retry_state.attempt_number}/{self.max_attempts}"
            ),
        }


def with_retry(
    *,  # Force keyword arguments
    config: RetryConfig | None = None,
    **kwargs: Any,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator that applies retry logic to a function.

    Args:
        config: RetryConfig object with retry settings
        **kwargs: Additional retry settings to override the defaults
                  (max_attempts, wait_min, wait_max, wait_multiplier,
                   retry_exceptions, reraise)

    Returns:
        Decorator function that applies retry logic
    """
    # Create a config object if one wasn't provided
    if config is None:
        config = RetryConfig(**kwargs)
    elif kwargs:
        # Update the config with any provided kwargs
        config_dict = asdict(config)
        config_dict.update(kwargs)
        config = RetryConfig(**config_dict)

    return _with_retry_config(config)


def _with_retry_config(
    config: RetryConfig,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Create a retry decorator with the given configuration.

    Args:
        config: Retry configuration

    Returns:
        A decorator function
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        """
        Apply retry logic to a function.

        Args:
            func: The function to decorate

        Returns:
            The decorated function
        """
        if inspect.iscoroutinefunction(func):
            # Async function
            @functools.wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                return await retry_async(func, *args, config=config, **kwargs)

            return cast(Callable[P, R], async_wrapper)
        else:
            # Sync function
            @functools.wraps(func)
            def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                return retry_sync(func, *args, config=config, **kwargs)

            return cast(Callable[P, R], sync_wrapper)

    return decorator


def retry_sync(
    func: Callable[..., R], *args: Any, config: RetryConfig | None = None, **kwargs: Any
) -> R:
    """
    Apply retry logic to a synchronous function call.

    This is useful when you want to apply retry logic to a function call
    without decorating the entire function.

    Args:
        func: The function to call with retry logic
        *args: Positional arguments to pass to the function
        config: Retry configuration (or None to use defaults)
        **kwargs: Keyword arguments to pass to the function

    Returns:
        The result of the function call
    """
    retry_config = config or RetryConfig()
    retry_args = retry_config.get_retry_arguments()
    retrying = Retrying(**retry_args)

    try:
        return retrying(func, *args, **kwargs)
    except RetryError as e:
        logger.error(
            f"All {retry_config.max_attempts} retry attempts failed", exc_info=True
        )
        if retry_config.reraise and e.last_attempt.failed:
            if e.last_attempt.exception() is not None:
                raise e.last_attempt.exception() from e
        raise


async def retry_async(
    func: Callable[..., Any],
    *args: Any,
    config: RetryConfig | None = None,
    **kwargs: Any,
) -> R:
    """
    Apply retry logic to an async function call.

    This is useful when you want to apply retry logic to a function call
    without decorating the entire function.

    Args:
        func: The function to call with retry logic (can be sync or async)
        *args: Positional arguments to pass to the function
        config: Retry configuration (or None to use defaults)
        **kwargs: Keyword arguments to pass to the function

    Returns:
        The result of the function call
    """
    retry_config = config or RetryConfig()

    # Track attempt information for better error reporting
    attempt_number = 1
    last_exception: Exception | None = None

    # Add context to logs for this retry operation
    func_name = getattr(func, "__name__", str(func))
    logger.add_context(function=func_name)
    logger.debug(f"Starting retry operation for {func_name}")

    try:
        while attempt_number <= retry_config.max_attempts:
            try:
                logger.debug(f"Attempt {attempt_number}/{retry_config.max_attempts}")

                # Handle function execution based on its type
                result = await _execute_function(func, *args, **kwargs)

                logger.debug(f"Attempt {attempt_number} succeeded")
                return cast(R, result)

            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt_number} failed: {e!s}", exc_info=True)

                # Check if we should retry based on exception type
                if not _should_retry_exception(e, retry_config.retry_exceptions):
                    logger.debug(
                        f"Exception {type(e).__name__} is not in retry_exceptions, not retrying"
                    )
                    break

                if attempt_number == retry_config.max_attempts:
                    # This was the last attempt, so we're done
                    logger.debug("Maximum retry attempts reached")
                    break

                # Calculate wait time using exponential backoff
                wait_time = _calculate_wait_time(attempt_number, retry_config)
                logger.debug(f"Waiting {wait_time} seconds before next attempt")
                await asyncio.sleep(wait_time)
                attempt_number += 1

        # If we get here, all attempts failed
        _handle_retry_failure(func_name, retry_config, last_exception)
        # This line is never reached as _handle_retry_failure always raises an exception
        # But we need it for type checking
        msg = "This code should never be reached"
        raise RuntimeError(msg)
    finally:
        # Clean up the context
        logger.remove_context("function")


async def _execute_function(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Execute a function that could be sync, async, or a coroutine object."""
    if inspect.iscoroutinefunction(func):
        # Direct coroutine function call
        return await func(*args, **kwargs)
    elif asyncio.iscoroutine(func):
        # Handle case where func is already a coroutine object
        return await func  # type: ignore
    else:
        # Regular function that might return an awaitable
        result = func(*args, **kwargs)
        # If result is awaitable, await it
        if inspect.isawaitable(result):
            return await result
        return result


def _should_retry_exception(
    exception: Exception, retry_exceptions: tuple[type[Exception], ...]
) -> bool:
    """Check if an exception should trigger a retry."""
    for exc_type in retry_exceptions:
        if isinstance(exception, exc_type):
            return True
    return False


def _calculate_wait_time(attempt_number: int, config: RetryConfig) -> float:
    """Calculate the wait time for the next retry attempt."""
    return min(
        config.wait_max,
        config.wait_min * (config.wait_multiplier ** (attempt_number - 1)),
    )


def _handle_retry_failure(
    func_name: str, config: RetryConfig, last_exception: Exception | None
) -> None:
    """Handle the case where all retry attempts have failed."""
    error_msg = f"All {config.max_attempts} retry attempts failed for {func_name}"

    if last_exception is not None:
        logger.error(error_msg, exc_info=last_exception)

        if config.reraise:
            # Add traceback information to the exception for better debugging
            raise last_exception

        error_msg += f": {last_exception!s}"
    else:
        logger.error(error_msg)

    # Use our custom error class instead of tenacity's RetryError
    raise CustomRetryError(error_msg, last_exception)
