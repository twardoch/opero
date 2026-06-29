#!/usr/bin/env python3
# this_file: tests/test_core.py
"""
Tests for the core functionality of the opero package.
"""

from unittest.mock import AsyncMock

import pytest

from opero.core.fallback import FallbackError, get_fallback_decorator
from opero.core.retry import get_retry_decorator


# Test functions
async def async_success(value):
    return f"Success: {value}"


async def async_fail(value):
    error_msg = f"Failed for value: {value}"
    raise ValueError(error_msg)


async def async_fallback(value):
    return f"Fallback: {value}"


def sync_success(value):
    return f"Sync Success: {value}"


def sync_fail(value):
    error_msg = f"Sync Failed for value: {value}"
    raise ValueError(error_msg)


def sync_fallback(value):
    return f"Sync Fallback: {value}"


# Tests for fallback functionality
@pytest.mark.asyncio
async def test_fallback_success():
    """Test that the first successful function returns the correct result."""
    fallback_decorator = get_fallback_decorator(arg_fallback="fallback_values")

    @fallback_decorator
    async def test_func(value, fallback_values=None):
        return await async_success(value)

    result = await test_func(1)
    assert result == "Success: 1"


@pytest.mark.asyncio
async def test_fallback_with_fallback():
    """Test that the fallback function is called if the first function fails."""
    fallback_decorator = get_fallback_decorator(arg_fallback="fallback_values")

    @fallback_decorator
    async def test_func(value, fallback_values=None):
        # fallback_values is one item from the list provided by the caller
        if fallback_values is None or fallback_values == "fail":
            raise ValueError(f"Failed with key: {fallback_values}")
        return await async_fallback(fallback_values)

    # Pass the list of fallback keys explicitly; decorator tries each in turn
    result = await test_func(1, fallback_values=["fail", "fallback"])
    assert result == "Fallback: fallback"


@pytest.mark.asyncio
async def test_fallback_all_fail():
    """Test that a FallbackError is raised when all functions fail."""
    fallback_decorator = get_fallback_decorator(arg_fallback="fallback_values")

    @fallback_decorator
    async def test_func(value, fallback_values=None):
        raise ValueError(f"Always fails, key={fallback_values}")

    with pytest.raises(FallbackError):
        await test_func(1, fallback_values=["fallback1", "fallback2"])


@pytest.mark.asyncio
async def test_fallback_sync_function():
    """Test that the fallback works with synchronous functions."""
    fallback_decorator = get_fallback_decorator(arg_fallback="fallback_values")

    @fallback_decorator
    def test_func(value, fallback_values=None):
        if fallback_values is None:
            fallback_values = ["fallback"]
        if value != "fallback":
            return sync_fail(value)
        return sync_success(value)

    # The sync wrapper uses ["fallback"] as default and replaces the first arg
    result = test_func(1)
    assert result == "Sync Success: fallback"


# Tests for retry functionality
@pytest.mark.asyncio
async def test_retry_success():
    """Test that a function succeeds on the first try."""
    retry_decorator = get_retry_decorator(retries=2, min_delay=0, max_delay=0)

    @retry_decorator
    async def test_func(value):
        return await async_success(value)

    result = await test_func(1)
    assert result == "Success: 1"


@pytest.mark.asyncio
async def test_retry_with_retry():
    """Test that retries are attempted if the function fails."""
    mock_func = AsyncMock(side_effect=[ValueError("First attempt"), "Success"])
    retry_decorator = get_retry_decorator(retries=2, min_delay=0, max_delay=0)

    @retry_decorator
    async def test_func(value):
        return await mock_func(value)

    result = await test_func(1)
    assert result == "Success"
    assert mock_func.call_count == 2


@pytest.mark.asyncio
async def test_retry_all_fail():
    """Test that an exception is raised when all retries fail."""
    retry_decorator = get_retry_decorator(retries=2, min_delay=0, max_delay=0)

    @retry_decorator
    async def test_func(value):
        return await async_fail(value)

    with pytest.raises(ValueError):
        await test_func(1)


@pytest.mark.asyncio
async def test_retry_sync_function():
    """Test that retry works with synchronous functions."""
    retry_decorator = get_retry_decorator(retries=2, min_delay=0, max_delay=0)

    @retry_decorator
    def test_func(value):
        return sync_success(value)

    # The decorator should handle the sync/async conversion
    result = test_func(1)
    assert result == "Sync Success: 1"
