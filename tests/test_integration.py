#!/usr/bin/env python3
"""
Integration tests for the opero package.
"""

import asyncio
import time
from unittest.mock import AsyncMock, Mock

import pytest

from opero import AllFailedError, opero, opmap


@pytest.mark.asyncio
async def test_opero_integration_all_features():
    """Test opero decorator with all features enabled."""
    call_count = 0
    
    @opero(
        retries=3,
        backoff_factor=1.1,
        arg_fallback="api_keys",
        cache=True,
        cache_ttl=60,
        rate_limit=10.0
    )
    async def api_call(endpoint: str, api_keys: list = None):
        nonlocal call_count
        call_count += 1
        
        if api_keys is None:
            api_keys = ["key1", "key2", "key3"]
        
        current_key = api_keys[0]
        
        # Simulate key1 failing, key2 succeeding
        if current_key == "key1":
            raise ConnectionError("API unavailable")
        elif current_key == "key2":
            return {"data": f"success with {current_key}", "endpoint": endpoint}
        else:
            raise ValueError("Invalid key")
    
    # First call should use fallback
    result1 = await api_call("users")
    assert result1["data"] == "success with key2"
    assert call_count == 2  # key1 failed, key2 succeeded
    
    # Second call should be cached
    call_count = 0
    result2 = await api_call("users")
    assert result2["data"] == "success with key2"
    assert call_count == 0  # Should be cached


@pytest.mark.asyncio
async def test_opmap_integration_parallel_processing():
    """Test opmap decorator with parallel processing."""
    
    @opmap(
        mode="thread",
        workers=4,
        retries=2,
        cache=True,
        cache_ttl=60,
        progress=False
    )
    def process_item(item_id: int):
        # Simulate processing time
        time.sleep(0.1)
        
        # Simulate failure for even numbers on first try
        if item_id % 2 == 0 and not hasattr(process_item, '_retry_counts'):
            process_item._retry_counts = {}
        
        if item_id % 2 == 0:
            if process_item._retry_counts.get(item_id, 0) == 0:
                process_item._retry_counts[item_id] = 1
                raise ValueError(f"Processing failed for item {item_id}")
        
        return {"item_id": item_id, "status": "processed"}
    
    items = list(range(10))
    results = process_item(items)
    
    # All items should be processed successfully after retries
    assert len(results) == 10
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            pytest.fail(f"Item {i} failed: {result}")
        assert result["item_id"] == i
        assert result["status"] == "processed"


@pytest.mark.asyncio
async def test_opero_error_handling():
    """Test comprehensive error handling in opero."""
    
    @opero(
        retries=2,
        arg_fallback="fallback_values",
        cache=False
    )
    async def failing_function(value: str, fallback_values: list = None):
        if fallback_values is None:
            fallback_values = ["fallback1", "fallback2"]
        
        # All attempts fail
        raise RuntimeError(f"Always fails for {value}")
    
    with pytest.raises(AllFailedError) as exc_info:
        await failing_function("test")
    
    # Check that AllFailedError contains all the individual errors
    assert len(exc_info.value.errors) > 0
    for error in exc_info.value.errors:
        assert isinstance(error, RuntimeError)
        assert "Always fails" in str(error)


@pytest.mark.asyncio
async def test_opmap_error_handling():
    """Test error handling in opmap with mixed success/failure."""
    
    @opmap(
        mode="thread",
        workers=2,
        retries=1,
        cache=False,
        progress=False
    )
    def process_item(item_id: int):
        if item_id == 5:
            raise ValueError(f"Item {item_id} always fails")
        return {"item_id": item_id, "status": "success"}
    
    items = list(range(10))
    results = process_item(items)
    
    # Check that most items succeeded, one failed
    success_count = 0
    error_count = 0
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            error_count += 1
            if i == 5:
                assert isinstance(result, (ValueError, AllFailedError))
        else:
            success_count += 1
            assert result["item_id"] == i
            assert result["status"] == "success"
    
    assert success_count == 9
    assert error_count == 1


@pytest.mark.asyncio
async def test_opero_rate_limiting():
    """Test rate limiting functionality."""
    
    @opero(
        rate_limit=5.0,  # 5 calls per second
        cache=False
    )
    async def rate_limited_func(value: int):
        return f"processed_{value}"
    
    # Make multiple calls and measure time
    start_time = time.time()
    tasks = [rate_limited_func(i) for i in range(10)]
    results = await asyncio.gather(*tasks)
    end_time = time.time()
    
    # Should take at least 2 seconds for 10 calls at 5/sec
    assert end_time - start_time >= 1.8
    assert len(results) == 10
    for i, result in enumerate(results):
        assert result == f"processed_{i}"


@pytest.mark.asyncio
async def test_opero_caching():
    """Test caching functionality."""
    call_count = 0
    
    @opero(
        cache=True,
        cache_ttl=60,
        retries=1
    )
    async def cached_func(value: str):
        nonlocal call_count
        call_count += 1
        return f"result_{value}_{call_count}"
    
    # First call
    result1 = await cached_func("test")
    assert call_count == 1
    assert result1 == "result_test_1"
    
    # Second call should be cached
    result2 = await cached_func("test")
    assert call_count == 1  # Should not increment
    assert result2 == "result_test_1"  # Same result
    
    # Different argument should not be cached
    result3 = await cached_func("different")
    assert call_count == 2
    assert result3 == "result_different_2"


@pytest.mark.asyncio
async def test_mixed_sync_async_operations():
    """Test mixing synchronous and asynchronous operations."""
    
    @opero(cache=False, retries=2)
    def sync_func(value: int):
        if value == 42:
            raise ValueError("Special number not allowed")
        return f"sync_result_{value}"
    
    @opero(cache=False, retries=2)
    async def async_func(value: int):
        if value == 42:
            raise ValueError("Special number not allowed")
        return f"async_result_{value}"
    
    # Test sync function
    sync_result = sync_func(10)
    assert sync_result == "sync_result_10"
    
    # Test async function
    async_result = await async_func(10)
    assert async_result == "async_result_10"
    
    # Test error handling
    with pytest.raises(ValueError):
        sync_func(42)
    
    with pytest.raises(ValueError):
        await async_func(42)


@pytest.mark.asyncio
async def test_opmap_different_modes():
    """Test opmap with different execution modes."""
    
    def simple_processor(item: int):
        return item * 2
    
    async def async_processor(item: int):
        await asyncio.sleep(0.01)
        return item * 3
    
    # Test thread mode
    @opmap(mode="thread", workers=2, cache=False, progress=False)
    def thread_processor(item: int):
        return simple_processor(item)
    
    # Test async mode
    @opmap(mode="async", workers=2, cache=False, progress=False)
    async def async_mode_processor(item: int):
        return await async_processor(item)
    
    items = [1, 2, 3, 4, 5]
    
    # Thread mode results
    thread_results = thread_processor(items)
    assert thread_results == [2, 4, 6, 8, 10]
    
    # Async mode results
    async_results = async_mode_processor(items)
    assert async_results == [3, 6, 9, 12, 15]


@pytest.mark.asyncio
async def test_performance_baseline():
    """Basic performance test to ensure decorators don't add excessive overhead."""
    
    @opero(cache=False)
    async def simple_func(value: int):
        return value * 2
    
    # Warm up
    await simple_func(1)
    
    # Time multiple calls
    start_time = time.time()
    tasks = [simple_func(i) for i in range(100)]
    results = await asyncio.gather(*tasks)
    end_time = time.time()
    
    # Should complete reasonably quickly (less than 1 second for 100 calls)
    assert end_time - start_time < 1.0
    assert len(results) == 100
    assert results[0] == 0
    assert results[99] == 198