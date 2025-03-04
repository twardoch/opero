#!/usr/bin/env python3
# this_file: src/opero/core.py
"""
Core functionality for the opero package.

This module provides the main orchestration classes for the opero package,
including the Orchestrator and FallbackChain classes.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar, cast
import time

from opero.concurrency import ConcurrencyConfig, MultiprocessConfig
from opero.exceptions import AllFailedError
from opero.rate_limit import RateLimitConfig
from opero.retry import RetryConfig, retry_async, retry_sync
from opero.utils import ensure_async

# Type variables
T = TypeVar("T")  # Input type
R = TypeVar("R")  # Return type

logger = logging.getLogger(__name__)


@dataclass
class OrchestratorConfig:
    """
    Configuration for the Orchestrator.

    This class provides a way to configure the Orchestrator with sensible defaults.

    Attributes:
        retry_config: Configuration for retry behavior
        rate_limit_config: Configuration for rate limiting
        multiprocess_config: Configuration for multiprocessing
        concurrency_config: Configuration for concurrency
        fallbacks: List of fallback functions
        logger: Logger to use
    """

    retry_config: RetryConfig | None = None
    rate_limit_config: RateLimitConfig | None = None
    multiprocess_config: MultiprocessConfig | None = None
    concurrency_config: ConcurrencyConfig | None = None
    fallbacks: list[Callable[..., Any]] = field(default_factory=list)
    logger: logging.Logger | None = None


class FallbackChain:
    """
    Chain of fallback functions to try in sequence.

    This class provides a way to chain multiple fallback functions together.
    If the primary function fails, the fallbacks will be tried in sequence.
    """

    def __init__(
        self,
        primary: Callable[..., Any],
        fallbacks: Callable[..., Any] | list[Callable[..., Any]] | None = None,
    ) -> None:
        """
        Initialize a fallback chain.

        Args:
            primary: The primary function to try first
            fallbacks: Fallback function or list of fallback functions to try in sequence
        """
        self.primary = primary

        # Handle both single function and list of functions
        if fallbacks is None:
            self.fallbacks = []
        elif callable(fallbacks) and not isinstance(fallbacks, list):
            self.fallbacks = [fallbacks]
        else:
            self.fallbacks = fallbacks

        self.logger = logger

    def has_fallbacks(self) -> bool:
        """
        Check if this chain has any fallback functions.

        Returns:
            True if there are fallback functions, False otherwise
        """
        return len(self.fallbacks) > 0

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """
        Call the fallback chain.

        This method makes the FallbackChain callable, delegating to the execute method.

        Args:
            *args: Positional arguments to pass to the functions
            **kwargs: Keyword arguments to pass to the functions

        Returns:
            The result of the first successful function call

        Raises:
            Exception: If all functions fail
        """
        return await self.execute(*args, **kwargs)

    async def execute(self, *args: Any, **kwargs: Any) -> Any:
        """
        Execute the primary function with fallbacks.

        Args:
            *args: Positional arguments to pass to the functions
            **kwargs: Keyword arguments to pass to the functions

        Returns:
            The result of the first successful function call

        Raises:
            AllFailedError: If all functions fail
        """
        # Try the primary function first
        try:
            self.logger.debug("Trying primary function")
            result = await ensure_async(self.primary, *args, **kwargs)
            self.logger.debug("Primary function succeeded")
            return result
        except Exception as e:
            self.logger.warning(f"Primary function failed: {e}")
            if not self.fallbacks:
                self.logger.error("No fallbacks available")
                raise

        # Try each fallback in order
        last_exception = None
        for i, fallback in enumerate(self.fallbacks):
            try:
                self.logger.debug(f"Trying fallback {i + 1}/{len(self.fallbacks)}")
                result = await ensure_async(fallback, *args, **kwargs)
                self.logger.debug(f"Fallback {i + 1} succeeded")
                return result
            except Exception as e:
                self.logger.warning(f"Fallback {i + 1} failed: {e}")
                last_exception = e

        # If we get here, all fallbacks failed
        self.logger.error("All fallbacks failed")
        if last_exception:
            msg = "All functions in the fallback chain failed"
            raise AllFailedError(msg) from last_exception
        msg = "All functions in the fallback chain failed but no exception was captured"
        raise AllFailedError(msg)


class Orchestrator:
    """
    Main orchestration class for executing functions with resilience patterns.

    The Orchestrator provides a unified interface for executing functions with
    various resilience patterns such as retries, fallbacks, rate limiting, and
    concurrency control. It can be used to execute a single function or process
    multiple items with the same function.

    Attributes:
        config: Configuration for the orchestrator
        logger: Logger to use for logging

    Example:
        ```python
        # Create an orchestrator with fallbacks and retry
        orchestrator = Orchestrator(
            config=OrchestratorConfig(
                fallbacks=[fallback_function],
                retry_config=RetryConfig(max_attempts=3)
            )
        )

        # Execute a function with the orchestrator
        result = await orchestrator.execute(my_function, arg1, arg2, keyword_arg=value)
        ```
    """

    def __init__(self, *, config: OrchestratorConfig | None = None):
        """
        Initialize the Orchestrator with the given configuration.

        Args:
            config: Configuration for the orchestrator. If None, default configuration is used.
        """
        self.config = config or OrchestratorConfig()
        self.logger = self.config.logger or logger

    def _wrap_fallback_with_retry(
        self, fallback_func: Callable[..., Any]
    ) -> Callable[..., Any]:
        """
        Wrap a fallback function with retry logic if retry is configured.

        Args:
            fallback_func: The fallback function to wrap

        Returns:
            The wrapped fallback function
        """
        if self.config.retry_config:
            # Create a wrapper that applies retry logic to the fallback
            async def wrapped_fallback(*args: Any, **kwargs: Any) -> Any:
                return await self._execute_with_retry(fallback_func, *args, **kwargs)

            return wrapped_fallback
        else:
            # No retry, return the original fallback
            return fallback_func

    def _create_fallback_chain(self, primary: Callable[..., Any]) -> FallbackChain:
        """
        Create a fallback chain with the given primary function.

        Args:
            primary: The primary function to use

        Returns:
            A FallbackChain instance
        """
        # Get fallbacks from config
        fallbacks = list(self.config.fallbacks or [])

        # Wrap fallbacks with retry if needed
        if self.config.retry_config:
            fallbacks = [self._wrap_fallback_with_retry(f) for f in fallbacks]

        # Create and return the fallback chain
        return FallbackChain(primary=primary, fallbacks=fallbacks)

    async def _execute_with_retry(
        self, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Any:
        """
        Execute a function with retry logic and fallbacks.

        This internal method applies retry logic to the function execution
        and falls back to the fallback chain if all retry attempts fail.

        Args:
            func: The function to execute
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            The result of the function execution

        Raises:
            AllFailedError: If all execution attempts (including fallbacks) fail
        """
        # Ensure we have a valid retry config
        retry_config = self.config.retry_config or RetryConfig()

        if asyncio.iscoroutinefunction(func):
            # Async function
            try:
                result = await retry_async(func, retry_config, *args, **kwargs)
                return result
            except Exception as e:
                self.logger.warning(f"Retry failed: {e}")
                raise
        else:
            # Sync function
            try:
                result = retry_sync(func, retry_config, *args, **kwargs)
                return result
            except Exception as e:
                self.logger.warning(f"Retry failed: {e}")
                raise

    async def execute(self, func: Callable[..., R], *args: Any, **kwargs: Any) -> R:
        """
        Execute a function with resilience patterns.

        This method applies the configured resilience patterns (retries, fallbacks,
        rate limiting) to the execution of the given function.

        Args:
            func: The function to execute
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            The result of the function execution

        Raises:
            AllFailedError: If all execution attempts (including fallbacks) fail
            Exception: Any exception raised by the function if no fallbacks are configured

        Example:
            ```python
            result = await orchestrator.execute(fetch_data, "https://example.com/api")
            ```
        """
        # Create a fallback chain if needed
        chain = self._create_fallback_chain(func)

        # Apply rate limiting if configured
        if self.config.rate_limit_config:
            await self._apply_rate_limit()

        # Execute with or without retry
        if self.config.retry_config:
            if chain.has_fallbacks():
                # Execute the fallback chain with retry for the primary function
                result = await self._execute_with_retry(chain.execute, *args, **kwargs)
            else:
                # No fallbacks, just execute the function with retry
                result = await self._execute_with_retry(func, *args, **kwargs)
        # Execute without retry
        elif chain.has_fallbacks():
            result = await chain.execute(*args, **kwargs)
        else:
            result = await ensure_async(func, *args, **kwargs)

        return cast(R, result)

    async def process(
        self, funcs: list[Callable[..., R]], *args: Any, **kwargs: Any
    ) -> list[R]:
        """
        Process multiple items with the given functions.

        This method applies the configured resilience patterns to each item
        and returns a list of results. If concurrency is configured, the items
        will be processed concurrently.

        Args:
            funcs: List of functions to execute for each item
            *args: Items to process
            **kwargs: Additional keyword arguments to pass to each function

        Returns:
            List of results, one for each processed item

        Example:
            ```python
            # Process multiple URLs with the same function
            results = await orchestrator.process([fetch_data], "https://example.com/1",
                                                "https://example.com/2", "https://example.com/3")

            # Process multiple items with different functions
            results = await orchestrator.process([func1, func2, func3], item)
            ```
        """
        results = []
        for func in funcs:
            # Process each argument individually
            for arg in args:
                result = await self.execute(func, arg, **kwargs)
                results.append(result)
        return results

    async def _apply_rate_limit(self) -> None:
        """
        Apply rate limiting if configured.

        This internal method enforces the configured rate limit by
        waiting if necessary before allowing the next operation.
        """
        if self.config.rate_limit_config and self.config.rate_limit_config.rate > 0:
            # Calculate time since last request
            now = time.time()
            if hasattr(self, "_last_request_time"):
                elapsed = now - self._last_request_time
                min_interval = 1.0 / self.config.rate_limit_config.rate
                if elapsed < min_interval:
                    # Wait to enforce rate limit
                    wait_time = min_interval - elapsed
                    self.logger.debug(f"Rate limiting: waiting {wait_time:.4f} seconds")
                    await asyncio.sleep(wait_time)
            # Update last request time
            self._last_request_time = time.time()
