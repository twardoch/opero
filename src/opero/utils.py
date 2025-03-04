#!/usr/bin/env python3
# this_file: src/opero/utils.py
"""
Utility functions for the opero package.

This module provides helper functions used throughout the opero package,
primarily for working with synchronous and asynchronous functions.
"""

import asyncio
import inspect
import logging
import sys
from collections.abc import Callable, Generator, MutableMapping
from contextlib import contextmanager
from typing import Any, TypeVar

# Type variable for function results
T = TypeVar("T")

logger = logging.getLogger(__name__)


async def ensure_async(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """
    Convert a synchronous function to asynchronous or call an async function as is.

    This helper ensures that both sync and async functions can be called in an async context.

    Args:
        func: The function to call (can be sync or async)
        *args: Positional arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function

    Returns:
        The result of the function call
    """
    if inspect.iscoroutinefunction(func):
        # Function is already async, call it directly
        return await func(*args, **kwargs)
    else:
        # Function is sync, run it in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))


def get_logger(
    name: str,
    level: int = logging.INFO,
    format_string: str | None = None,
    add_console_handler: bool = True,
) -> logging.Logger:
    """
    Get a configured logger for the given name.

    Args:
        name: The name for the logger
        level: The logging level (default: INFO)
        format_string: Custom format string for the logger
        add_console_handler: Whether to add a console handler if none exists

    Returns:
        A configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Add a console handler if no handlers are configured and requested
    if add_console_handler and not logger.handlers:
        handler = logging.StreamHandler()
        if format_string is None:
            format_string = (
                "%(asctime)s - %(name)s - %(levelname)s - %(context)s - %(message)s"
            )
        formatter = logging.Formatter(format_string)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


class ContextAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds context information to log messages.

    This adapter allows adding context information to log messages,
    which can be useful for tracking operations across different
    components of the application.
    """

    def __init__(self, logger: logging.Logger, context: dict[str, Any] | None = None):
        """
        Initialize the adapter with a logger and optional context.

        Args:
            logger: The logger to adapt
            context: Initial context dictionary
        """
        # Initialize with empty context
        super().__init__(logger, {"context": ""})
        # Store context separately
        self._context: dict[str, Any] = context or {}
        self._update_context_string()

    def _update_context_string(self) -> None:
        """Update the context string in the extra dict."""
        if self._context:
            context_str = ", ".join(f"{k}={v}" for k, v in self._context.items())
            context_value = f"[{context_str}]"
            # Access the extra dict safely using dict methods
            if isinstance(self.extra, dict):
                self.extra["context"] = context_value

    def process(
        self, msg: str, kwargs: MutableMapping[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        """
        Process the logging message and keyword arguments.

        This method is called by the logging system to process the log record.

        Args:
            msg: The log message
            kwargs: The keyword arguments for the logger

        Returns:
            Tuple of (message, kwargs)
        """
        # Convert kwargs to a dict for easier manipulation
        kwargs_dict = dict(kwargs)

        # Ensure we have an extra dict
        if "extra" not in kwargs_dict:
            kwargs_dict["extra"] = {}
        elif not isinstance(kwargs_dict["extra"], dict):
            kwargs_dict["extra"] = {}

        # Ensure we have a context in the extra dict
        if "context" not in kwargs_dict["extra"]:
            if isinstance(self.extra, dict) and "context" in self.extra:
                # Copy context from our extra dict
                kwargs_dict["extra"]["context"] = self.extra["context"]
            else:
                kwargs_dict["extra"]["context"] = ""

        return msg, kwargs_dict

    def add_context(self, **kwargs: Any) -> None:
        """
        Add context information to the logger.

        Args:
            **kwargs: Key-value pairs to add to the context
        """
        self._context.update(kwargs)
        self._update_context_string()

    def remove_context(self, *keys: str) -> None:
        """
        Remove context keys from the logger.

        Args:
            *keys: Keys to remove from the context
        """
        for key in keys:
            self._context.pop(key, None)
        self._update_context_string()

    def clear_context(self) -> None:
        """Clear all context information."""
        self._context.clear()
        self._update_context_string()


@contextmanager
def log_context(logger: ContextAdapter, **context: Any) -> Generator[None, None, None]:
    """
    Context manager for temporarily adding context to a logger.

    Args:
        logger: The context adapter logger
        **context: Context key-value pairs

    Yields:
        None
    """
    logger.add_context(**context)
    try:
        yield
    finally:
        logger.remove_context(*context.keys())


def configure_root_logger(
    level: int = logging.INFO,
    format_string: str | None = None,
    add_console_handler: bool = True,
) -> logging.Logger:
    """
    Configure the root logger with the given settings.

    Args:
        level: The logging level
        format_string: Custom format string
        add_console_handler: Whether to add a console handler

    Returns:
        The configured root logger
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    if add_console_handler:
        handler = logging.StreamHandler(sys.stdout)
        if format_string is None:
            format_string = (
                "%(asctime)s - %(name)s - %(levelname)s - %(context)s - %(message)s"
            )
        formatter = logging.Formatter(format_string)
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)

    return root_logger
