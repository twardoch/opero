#!/usr/bin/env python3
# this_file: src/opero/exceptions_v2.py
"""
Enhanced exception classes for the opero package with context preservation.

This module defines custom exceptions with enhanced error tracking capabilities.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


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


@dataclass
class ErrorContext:
    """Context information for a failed attempt.
    
    Attributes:
        attempt_number: The attempt number (1-based).
        timestamp: When the attempt was made.
        retry_number: Which retry attempt this was (0 for first try).
        fallback_value: The fallback parameter value used (if any).
        function_name: Name of the function that failed.
        args: Positional arguments used in the call.
        kwargs: Keyword arguments used in the call.
        exception: The exception that was raised.
        duration_ms: How long the attempt took in milliseconds.
        metadata: Additional metadata about the attempt.
    """
    attempt_number: int
    timestamp: datetime
    retry_number: int
    fallback_value: Optional[Any] = None
    function_name: Optional[str] = None
    args: Optional[tuple] = None
    kwargs: Optional[dict] = None
    exception: Optional[Exception] = None
    duration_ms: Optional[float] = None
    metadata: Optional[dict] = None
    
    def __str__(self) -> str:
        """Human-readable representation of the error context."""
        parts = [f"Attempt {self.attempt_number}"]
        
        if self.retry_number > 0:
            parts.append(f"retry {self.retry_number}")
            
        if self.fallback_value is not None:
            parts.append(f"with fallback={self.fallback_value}")
            
        if self.function_name:
            parts.append(f"in {self.function_name}")
            
        if self.duration_ms is not None:
            parts.append(f"took {self.duration_ms:.1f}ms")
            
        parts.append(f"at {self.timestamp.isoformat()}")
        
        if self.exception:
            parts.append(f"failed with {type(self.exception).__name__}: {self.exception}")
            
        return " ".join(parts)


class AllFailedError(OperoError):
    """Raised when all fallback or retry operations have failed.
    
    This enhanced exception provides detailed context about each failed attempt,
    making debugging and monitoring easier.
    
    Attributes:
        errors: List of exceptions from each failed attempt.
        contexts: List of ErrorContext objects with detailed information.
        correlation_id: Optional correlation ID for distributed tracing.
    
    Example:
        @opero(retries=2, arg_fallback="api_key")
        def call_api(data, api_key=["key1", "key2"]):
            # API call implementation
            pass
            
        try:
            result = call_api(data)
        except AllFailedError as e:
            print(f"All attempts failed: {e}")
            for ctx in e.contexts:
                print(f"  {ctx}")
            
            # Access specific details
            first_error = e.contexts[0]
            print(f"First attempt took {first_error.duration_ms}ms")
    """

    def __init__(
        self, 
        message: str = "All operations failed.", 
        errors: list[Exception] | None = None,
        contexts: list[ErrorContext] | None = None,
        correlation_id: str | None = None
    ) -> None:
        """Initialize the exception with detailed context.

        Args:
            message: Human-readable description of the failure.
            errors: List of exceptions from each failed attempt.
            contexts: List of ErrorContext objects with detailed information
                about each attempt.
            correlation_id: Optional ID for correlating errors across systems.
        """
        self.errors = errors or []
        self.contexts = contexts or []
        self.correlation_id = correlation_id
        
        # Build detailed message
        full_message = message
        
        if self.correlation_id:
            full_message = f"[{self.correlation_id}] {full_message}"
            
        if self.contexts:
            full_message += f" ({len(self.contexts)} attempts failed)"
            
        if self.errors and not self.contexts:
            # Backward compatibility
            full_message += f" Underlying errors: {[str(e) for e in self.errors]}"
            
        super().__init__(full_message)
    
    def get_summary(self) -> dict[str, Any]:
        """Get a summary of all failed attempts.
        
        Returns:
            Dictionary with summary statistics about the failures.
        """
        if not self.contexts:
            return {
                "total_attempts": len(self.errors),
                "error_types": list({type(e).__name__ for e in self.errors})
            }
            
        total_duration = sum(ctx.duration_ms for ctx in self.contexts if ctx.duration_ms)
        error_types = {}
        fallback_values = set()
        
        for ctx in self.contexts:
            if ctx.exception:
                error_type = type(ctx.exception).__name__
                error_types[error_type] = error_types.get(error_type, 0) + 1
                
            if ctx.fallback_value is not None:
                fallback_values.add(str(ctx.fallback_value))
                
        return {
            "total_attempts": len(self.contexts),
            "total_duration_ms": total_duration,
            "avg_duration_ms": total_duration / len(self.contexts) if self.contexts else 0,
            "error_types": error_types,
            "fallback_values_tried": list(fallback_values),
            "correlation_id": self.correlation_id,
            "first_attempt": self.contexts[0].timestamp.isoformat() if self.contexts else None,
            "last_attempt": self.contexts[-1].timestamp.isoformat() if self.contexts else None,
        }
    
    def get_errors_by_type(self) -> dict[str, list[ErrorContext]]:
        """Group error contexts by exception type.
        
        Returns:
            Dictionary mapping exception type names to lists of contexts.
        """
        grouped = {}
        for ctx in self.contexts:
            if ctx.exception:
                error_type = type(ctx.exception).__name__
                if error_type not in grouped:
                    grouped[error_type] = []
                grouped[error_type].append(ctx)
        return grouped


class ConfigurationError(OperoError):
    """Raised when decorator configuration is invalid.
    
    Examples:
        - Invalid parameter combinations
        - Missing required parameters
        - Type mismatches in configuration
    """
    
    
class ConcurrencyError(OperoError):
    """Raised when parallel processing encounters issues.
    
    Examples:
        - Worker pool creation failures
        - Task distribution problems
        - Synchronization errors
    """