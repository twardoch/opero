#!/usr/bin/env python3
# this_file: src/opero/utils/correlation.py
"""
Correlation ID utilities for distributed tracing.

This module provides utilities for generating and managing correlation IDs
to track operations across distributed systems.
"""

import contextvars
import uuid
from typing import Optional


# Context variable to store correlation ID for the current execution context
_correlation_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    'opero_correlation_id', 
    default=None
)


def generate_correlation_id(prefix: str = "opero") -> str:
    """Generate a new correlation ID.
    
    The ID format is: {prefix}-{uuid4}
    
    Args:
        prefix: Prefix for the correlation ID. Defaults to "opero".
        
    Returns:
        A unique correlation ID string.
        
    Example:
        >>> correlation_id = generate_correlation_id()
        >>> print(correlation_id)
        opero-550e8400-e29b-41d4-a716-446655440000
        
        >>> custom_id = generate_correlation_id(prefix="api")
        >>> print(custom_id)
        api-6ba7b810-9dad-11d1-80b4-00c04fd430c8
    """
    return f"{prefix}-{uuid.uuid4()}"


def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID from context.
    
    Returns:
        The current correlation ID if set, None otherwise.
        
    Example:
        >>> set_correlation_id("opero-123")
        >>> print(get_correlation_id())
        opero-123
    """
    return _correlation_id_var.get()


def set_correlation_id(correlation_id: Optional[str]) -> None:
    """Set the correlation ID for the current context.
    
    Args:
        correlation_id: The correlation ID to set, or None to clear.
        
    Example:
        >>> set_correlation_id("opero-123")
        >>> # All operations in this context will use this ID
        >>> clear_correlation_id()  # Or set_correlation_id(None)
    """
    _correlation_id_var.set(correlation_id)


def clear_correlation_id() -> None:
    """Clear the current correlation ID.
    
    This is equivalent to set_correlation_id(None).
    """
    _correlation_id_var.set(None)


class CorrelationContext:
    """Context manager for correlation IDs.
    
    This ensures correlation IDs are properly scoped and cleaned up.
    
    Example:
        # Automatic ID generation
        with CorrelationContext() as correlation_id:
            print(f"Processing with ID: {correlation_id}")
            # All operations here will have this correlation ID
            
        # Using existing ID
        with CorrelationContext("existing-id-123"):
            # Operations with existing ID
            pass
            
        # Nested contexts
        with CorrelationContext() as outer_id:
            print(f"Outer: {get_correlation_id()}")  # outer_id
            
            with CorrelationContext() as inner_id:
                print(f"Inner: {get_correlation_id()}")  # inner_id
                
            print(f"Back to outer: {get_correlation_id()}")  # outer_id
    """
    
    def __init__(self, correlation_id: Optional[str] = None, prefix: str = "opero"):
        """Initialize the context.
        
        Args:
            correlation_id: Existing correlation ID to use, or None to generate.
            prefix: Prefix for generated IDs if correlation_id is None.
        """
        self.correlation_id = correlation_id or generate_correlation_id(prefix)
        self._token = None
        
    def __enter__(self) -> str:
        """Enter the context and set the correlation ID.
        
        Returns:
            The correlation ID being used.
        """
        self._token = _correlation_id_var.set(self.correlation_id)
        return self.correlation_id
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context and restore previous correlation ID."""
        if self._token:
            _correlation_id_var.reset(self._token)


def with_correlation_id(func):
    """Decorator to add correlation ID to a function.
    
    If no correlation ID is in context, generates a new one.
    
    Example:
        @with_correlation_id
        def process_request(data):
            correlation_id = get_correlation_id()
            logger.info(f"[{correlation_id}] Processing request")
            return result
            
        # Will generate ID if none exists
        result = process_request(data)
        
        # Or use existing ID
        with CorrelationContext("request-123"):
            result = process_request(data)  # Uses "request-123"
    """
    def wrapper(*args, **kwargs):
        if get_correlation_id() is None:
            with CorrelationContext():
                return func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    
    async def async_wrapper(*args, **kwargs):
        if get_correlation_id() is None:
            with CorrelationContext():
                return await func(*args, **kwargs)
        else:
            return await func(*args, **kwargs)
    
    if asyncio.iscoroutinefunction(func):
        return functools.wraps(func)(async_wrapper)
    else:
        return functools.wraps(func)(wrapper)


# Example integration with logging
def get_correlation_log_extra() -> dict:
    """Get logging extra dict with correlation ID.
    
    Returns:
        Dictionary with correlation_id key if set.
        
    Example:
        logger.info("Processing", extra=get_correlation_log_extra())
        # Logs: "Processing" with correlation_id in structured logs
    """
    correlation_id = get_correlation_id()
    return {"correlation_id": correlation_id} if correlation_id else {}


import asyncio
import functools