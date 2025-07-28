#!/usr/bin/env python3
# this_file: src/opero/exceptions.py
"""
Exception classes for the opero package.

This module defines custom exceptions used throughout the opero package.
"""


class OperoError(Exception):
    """Base class for all custom exceptions in opero.
    
    All Opero-specific exceptions inherit from this class, making it easy
    to catch any Opero-related error with a single except clause.
    
    Example:
        try:
            result = some_opero_function()
        except OperoError as e:
            # Handle any Opero-specific error
            logger.error(f"Opero operation failed: {e}")
    """


class AllFailedError(OperoError):
    """Raised when all fallback or retry operations have failed.
    
    This exception is raised when all retry attempts and all parameter-based
    fallback values have been exhausted without success. It contains a list
    of all the exceptions that occurred during the attempts.
    
    Attributes:
        errors: List of exceptions from each failed attempt.
    
    Example:
        @opero(retries=2, arg_fallback="api_key")
        def call_api(data, api_key=["key1", "key2"]):
            # API call implementation
            pass
            
        try:
            result = call_api(data)
        except AllFailedError as e:
            print(f"All attempts failed: {e}")
            for i, error in enumerate(e.errors):
                print(f"  Attempt {i+1}: {error}")
    """

    def __init__(self, message: str = "All operations failed.", errors: list[Exception] | None = None) -> None:
        """Initialize the exception with a message and list of underlying errors.

        Args:
            message: Human-readable description of the failure.
            errors: List of exceptions from each failed attempt. The order
                corresponds to the order of attempts (retries and fallbacks).
        """
        self.errors = errors or []
        full_message = message
        if self.errors:
            full_message += f" Underlying errors: {[str(e) for e in self.errors]}"
        super().__init__(full_message)

    def __str__(self) -> str:
        return super().__str__()
