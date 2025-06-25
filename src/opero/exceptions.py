#!/usr/bin/env python3
# this_file: src/opero/exceptions.py
"""
Exception classes for the opero package.

This module defines custom exceptions used throughout the opero package.
"""


class OperoError(Exception):
    """Base class for all custom exceptions in opero."""


class AllFailedError(OperoError):
    """Raised when all fallback or retry operations have failed."""

    def __init__(self, message: str = "All operations failed.", errors: list[Exception] | None = None) -> None:
        """
        Initialize the exception.

        Args:
            message: Error message.
            errors: Optional list of exceptions from underlying attempts.
        """
        self.errors = errors or []
        full_message = message
        if self.errors:
            full_message += f" Underlying errors: {[str(e) for e in self.errors]}"
        super().__init__(full_message)

    def __str__(self) -> str:
        return super().__str__()
