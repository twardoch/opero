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
T = TypeVar("T")  # Additional type variable for _execute_function

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
    Decorator that adds retry capability to a function.

    This decorator can be applied to both synchronous and asynchronous functions.
    It will automatically detect the function type and apply the appropriate retry logic.

    Args:
        config: Configuration for retry behavior. If None, default RetryConfig is used.
        **kwargs: Additional keyword arguments to override specific RetryConfig attributes.
            These will take precedence over the values in the config object.

    Returns:
        A decorator function that adds retry capability to the decorated function.

    Example:
        ```python
        @with_retry(max_attempts=5, wait_min=2.0)
        async def fetch_data(url):
            # This function will be retried up to 5 times with a minimum wait of 2 seconds
            response = await aiohttp.get(url)
            return await response.json()
        ```
    """
    # Create or update the retry configuration
    retry_config = config or RetryConfig()
    if kwargs:
        # Update the config with any provided kwargs
        retry_config = RetryConfig(**{**asdict(retry_config), **kwargs})

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        """
        Inner decorator function that wraps the target function with retry logic.

        Args:
            func: The function to add retry capability to.

        Returns:
            A wrapped function with retry capability.
        """
        if inspect.iscoroutinefunction(func):
            # Async function
            @functools.wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                """
                Async wrapper that adds retry capability to an async function.

                Args:
                    *args: Positional arguments to pass to the wrapped function.
                    **kwargs: Keyword arguments to pass to the wrapped function.

                Returns:
                    The result of the wrapped function.

                Raises:
                    CustomRetryError: If all retry attempts fail and reraise is False.
                    Original exception: If all retry attempts fail and reraise is True.
                """
                return await retry_async(func, retry_config, *args, **kwargs)

            return cast(Callable[P, R], async_wrapper)
        else:
            # Sync function
            @functools.wraps(func)
            def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                """
                Sync wrapper that adds retry capability to a sync function.

                Args:
                    *args: Positional arguments to pass to the wrapped function.
                    **kwargs: Keyword arguments to pass to the wrapped function.

                Returns:
                    The result of the wrapped function.

                Raises:
                    CustomRetryError: If all retry attempts fail and reraise is False.
                    Original exception: If all retry attempts fail and reraise is True.
                """
                return retry_sync(func, retry_config, *args, **kwargs)

            return cast(Callable[P, R], sync_wrapper)

    return decorator


def retry_sync(
    func: Callable[..., R],
    config: RetryConfig,
    *args: Any,
    **kwargs: Any,
) -> R:
    """
    Apply retry logic to a synchronous function.

    This function executes the provided sync function with retry logic according to the
    provided configuration. If all retry attempts fail, it will either reraise the last
    exception or raise a CustomRetryError, depending on the config.

    Args:
        func: The sync function to retry.
        config: Configuration for retry behavior.
        *args: Positional arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.

    Returns:
        The result of the function call if successful.

    Raises:
        CustomRetryError: If all retry attempts fail and reraise is False.
        Original exception: If all retry attempts fail and reraise is True.
    """
    retry_args = config.get_retry_arguments()
    retrying = Retrying(**retry_args)

    try:
        return retrying(func, *args, **kwargs)
    except RetryError as e:
        logger.error(f"All {config.max_attempts} retry attempts failed", exc_info=True)
        if config.reraise and e.last_attempt.failed:
            if e.last_attempt.exception() is not None:
                raise e.last_attempt.exception() from e
        raise


async def retry_async(
    func: Callable[..., R],
    config: RetryConfig,
    *args: Any,
    **kwargs: Any,
) -> R:
    """
    Apply retry logic to an asynchronous function.

    This function executes the provided async function with retry logic according to the
    provided configuration. If all retry attempts fail, it will either reraise the last
    exception or raise a CustomRetryError, depending on the config.

    Args:
        func: The async function to retry.
        config: Configuration for retry behavior.
        *args: Positional arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.

    Returns:
        The result of the function call if successful.

    Raises:
        CustomRetryError: If all retry attempts fail and reraise is False.
        Original exception: If all retry attempts fail and reraise is True.
    """
    # Track attempt information for better error reporting
    attempt_number = 1
    last_exception: Exception | None = None

    # Add context to logs for this retry operation
    func_name = getattr(func, "__name__", str(func))
    logger.add_context(function=func_name)
    logger.debug(f"Starting retry operation for {func_name}")

    try:
        while attempt_number <= config.max_attempts:
            try:
                logger.debug(f"Attempt {attempt_number}/{config.max_attempts}")

                # Handle function execution based on its type
                result = await _execute_function(func, *args, **kwargs)

                logger.debug(f"Attempt {attempt_number} succeeded")
                return cast(R, result)

            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt_number} failed: {e!s}", exc_info=True)

                # Check if we should retry based on exception type
                if not _should_retry_exception(e, config.retry_exceptions):
                    logger.debug(
                        f"Exception {type(e).__name__} is not in retry_exceptions, not retrying"
                    )
                    break

                if attempt_number == config.max_attempts:
                    # This was the last attempt, so we're done
                    logger.debug("Maximum retry attempts reached")
                    break

                # Calculate wait time using exponential backoff
                wait_time = _calculate_wait_time(attempt_number, config)
                logger.debug(f"Waiting {wait_time} seconds before next attempt")
                await asyncio.sleep(wait_time)
                attempt_number += 1

        # If we get here, all attempts failed
        _handle_retry_failure(func_name, config, last_exception)
        # This line is never reached as _handle_retry_failure always raises an exception
        # But we need it for type checking
        msg = "This code should never be reached"
        raise RuntimeError(msg)
    finally:
        # Clean up the context
        logger.remove_context("function")


async def _execute_function(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """
    Execute a function, handling both sync and async functions.

    This is a helper function used by retry_async to execute the target function.
    It detects whether the function is synchronous or asynchronous and executes it accordingly.

    Args:
        func: The function to execute (can be sync or async).
        *args: Positional arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.

    Returns:
        The result of the function call.
    """
    if inspect.iscoroutinefunction(func):
        # Direct coroutine function call
        return await func(*args, **kwargs)
    elif asyncio.iscoroutine(func):
        # Already a coroutine object
        return await func
    else:
        # Synchronous function, run in executor
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))


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
