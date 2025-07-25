#!/usr/bin/env python3
# this_file: src/opero/utils/logging.py
"""
Logging utility functions for the opero package.

This module provides utility functions for logging in the opero package.
"""

import logging
import sys
from typing import TextIO

# Default logger
logger = logging.getLogger("opero")


def configure_logging(
    level: int | str = logging.INFO,
    format_string: str | None = None,
    stream: TextIO | None = None,
    verbose: bool = False,
) -> logging.Logger:
    """Configure logging for the opero package with sensible defaults.

    This function sets up the Opero logger with the specified configuration.
    It's useful for debugging and monitoring Opero's internal operations.

    Args:
        level: Logging level, either as an int (e.g., logging.INFO) or 
            string (e.g., "INFO", "DEBUG"). Defaults to INFO.
        format_string: Custom format string for log messages. If None,
            uses a simple format for normal mode or detailed format for
            verbose mode.
        stream: Output stream for log messages. Defaults to sys.stderr.
        verbose: If True, uses a more detailed log format including
            timestamps and module names.

    Returns:
        The configured opero logger instance.

    Example:
        # Basic setup
        logger = configure_logging(level=logging.DEBUG)
        
        # Verbose mode with custom format
        logger = configure_logging(
            level="DEBUG",
            verbose=True,
            format_string="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        
        # Log to a file
        with open("opero.log", "w") as f:
            logger = configure_logging(stream=f)
    
    Note:
        This configures the root "opero" logger. Child loggers (e.g.,
        "opero.core.retry") will inherit these settings.
    """
    # Set the logging level
    if isinstance(level, str):
        level = getattr(logging, level.upper())

    # Set the format string
    if format_string is None:
        if verbose:
            format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        else:
            format_string = "%(levelname)s: %(message)s"

    # Configure the logger
    handler = logging.StreamHandler(stream or sys.stderr)
    handler.setFormatter(logging.Formatter(format_string))

    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Get a logger instance for the opero package.

    This function returns a logger that follows Opero's naming hierarchy.
    All Opero loggers are children of the main "opero" logger.

    Args:
        name: Optional name for a child logger. If None, returns the
            root "opero" logger. If provided, returns a logger named
            "opero.{name}".

    Returns:
        A logger instance with the appropriate name.

    Example:
        # Get the main opero logger
        main_logger = get_logger()
        main_logger.info("Opero initialized")
        
        # Get a module-specific logger
        retry_logger = get_logger("retry")
        retry_logger.debug("Retry attempt 1 failed")
        
        # In a module, use __name__
        module_logger = get_logger(__name__.split(".")[-1])
    """
    if name is None:
        return logger

    return logging.getLogger(f"opero.{name}")
