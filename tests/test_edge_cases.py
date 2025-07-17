#!/usr/bin/env python3
"""
Edge case tests for the opero package.
"""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from opero import AllFailedError, opero, opmap
from opero.exceptions import OperoError


@pytest.mark.asyncio
async def test_empty_fallback_list():
    """Test behavior with empty fallback list."""
    
    @opero(arg_fallback="empty_list", cache=False)
    async def func_with_empty_fallback(value: str, empty_list: list = None):
        if empty_list is None:
            empty_list = []
        return f"result_{value}"
    
    # Should work normally when no fallback is needed
    result = await func_with_empty_fallback("test")
    assert result == "result_test"


@pytest.mark.asyncio
async def test_single_item_fallback():
    """Test fallback with single item list."""
    
    @opero(arg_fallback="single_item", cache=False)
    async def func_with_single_fallback(value: str, single_item: list = None):
        if single_item is None:
            single_item = ["only_option"]
        
        current = single_item[0]
        if current == "only_option" and value == "fail":
            raise ValueError("Single option failed")
        return f"result_{current}_{value}"
    
    # Should succeed with normal value
    result = await func_with_single_fallback("success")
    assert result == "result_only_option_success"
    
    # Should fail when single option fails
    with pytest.raises(AllFailedError):
        await func_with_single_fallback("fail")


@pytest.mark.asyncio
async def test_opmap_empty_input():
    """Test opmap with empty input list."""
    
    @opmap(mode="thread", workers=2, cache=False, progress=False)
    def process_empty(item: int):
        return item * 2
    
    results = process_empty([])
    assert results == []


@pytest.mark.asyncio
async def test_opmap_single_item():
    """Test opmap with single item."""
    
    @opmap(mode="thread", workers=2, cache=False, progress=False)
    def process_single(item: int):
        return item * 2
    
    results = process_single([5])
    assert results == [10]


@pytest.mark.asyncio
async def test_zero_retries():
    """Test behavior with zero retries."""
    
    @opero(retries=0, cache=False)
    async def no_retry_func(value: str):
        if value == "fail":
            raise ValueError("Immediate failure")
        return f"success_{value}"
    
    # Should succeed on first try
    result = await no_retry_func("success")
    assert result == "success_success"
    
    # Should fail immediately with no retries
    with pytest.raises(ValueError):
        await no_retry_func("fail")


@pytest.mark.asyncio
async def test_very_high_retry_count():
    """Test with very high retry count."""
    attempt_count = 0
    
    @opero(retries=100, cache=False)
    async def high_retry_func(value: str):
        nonlocal attempt_count
        attempt_count += 1
        
        if attempt_count < 50:
            raise ValueError(f"Attempt {attempt_count} failed")
        return f"success_after_{attempt_count}_attempts"
    
    result = await high_retry_func("test")
    assert result == "success_after_50_attempts"
    assert attempt_count == 50


@pytest.mark.asyncio
async def test_nested_exceptions():
    """Test handling of nested exceptions."""
    
    @opero(retries=2, cache=False)
    async def nested_exception_func(value: str):
        try:
            raise ValueError("Inner exception")
        except ValueError as e:
            raise RuntimeError("Outer exception") from e
    
    with pytest.raises(RuntimeError) as exc_info:
        await nested_exception_func("test")
    
    assert exc_info.value.__cause__ is not None
    assert isinstance(exc_info.value.__cause__, ValueError)


@pytest.mark.asyncio
async def test_opero_with_none_values():
    """Test opero handling None values correctly."""
    
    @opero(cache=False)
    async def func_with_none(value):
        if value is None:
            return "none_handled"
        return f"value_{value}"
    
    result1 = await func_with_none(None)
    assert result1 == "none_handled"
    
    result2 = await func_with_none("test")
    assert result2 == "value_test"


@pytest.mark.asyncio
async def test_opmap_with_none_values():
    """Test opmap handling None values in input."""
    
    @opmap(mode="thread", workers=2, cache=False, progress=False)
    def process_with_none(item):
        if item is None:
            return "none_processed"
        return f"processed_{item}"
    
    results = process_with_none([1, None, 3, None, 5])
    expected = ["processed_1", "none_processed", "processed_3", "none_processed", "processed_5"]
    assert results == expected


@pytest.mark.asyncio
async def test_opero_large_fallback_list():
    """Test with large fallback list."""
    
    @opero(arg_fallback="large_list", cache=False)
    async def func_with_large_fallback(value: str, large_list: list = None):
        if large_list is None:
            large_list = [f"option_{i}" for i in range(100)]
        
        current = large_list[0]
        # Only the 50th option works
        if current != "option_49":
            raise ValueError(f"Option {current} failed")
        return f"success_with_{current}"
    
    result = await func_with_large_fallback("test")
    assert result == "success_with_option_49"


@pytest.mark.asyncio
async def test_opmap_many_workers():
    """Test opmap with many workers."""
    
    @opmap(mode="thread", workers=20, cache=False, progress=False)
    def process_with_many_workers(item: int):
        return item ** 2
    
    items = list(range(50))
    results = process_with_many_workers(items)
    
    expected = [i ** 2 for i in range(50)]
    assert results == expected


@pytest.mark.asyncio
async def test_opero_with_keyword_only_args():
    """Test opero with keyword-only arguments."""
    
    @opero(cache=False)
    async def func_with_kwonly(value: str, *, multiplier: int = 2):
        return value * multiplier
    
    result = await func_with_kwonly("test", multiplier=3)
    assert result == "testtesttest"


@pytest.mark.asyncio
async def test_opmap_with_complex_data_types():
    """Test opmap with complex data types."""
    
    @opmap(mode="thread", workers=2, cache=False, progress=False)
    def process_complex(item: dict):
        return {
            "id": item["id"],
            "result": item["value"] * 2,
            "processed": True
        }
    
    items = [
        {"id": 1, "value": 10},
        {"id": 2, "value": 20},
        {"id": 3, "value": 30}
    ]
    
    results = process_complex(items)
    
    assert len(results) == 3
    assert results[0]["result"] == 20
    assert results[1]["result"] == 40
    assert results[2]["result"] == 60
    assert all(r["processed"] for r in results)


@pytest.mark.asyncio
async def test_opero_exception_preservation():
    """Test that original exception types are preserved."""
    
    @opero(retries=1, cache=False)
    async def func_with_specific_exception(value: str):
        if value == "custom":
            raise FileNotFoundError("Custom file not found")
        elif value == "value":
            raise ValueError("Value error occurred")
        return f"success_{value}"
    
    with pytest.raises(FileNotFoundError):
        await func_with_specific_exception("custom")
    
    with pytest.raises(ValueError):
        await func_with_specific_exception("value")


@pytest.mark.asyncio
async def test_opero_with_generators():
    """Test opero behavior with generator functions."""
    
    @opero(cache=False)
    def generator_func(count: int):
        for i in range(count):
            yield i * 2
    
    result = generator_func(5)
    values = list(result)
    assert values == [0, 2, 4, 6, 8]


@pytest.mark.asyncio
async def test_opmap_ordered_vs_unordered():
    """Test ordered vs unordered results in opmap."""
    
    @opmap(mode="thread", workers=3, cache=False, progress=False, ordered=True)
    def ordered_processor(item: int):
        import time
        # Add variable delay to test ordering
        time.sleep(0.01 * (5 - item))
        return item * 2
    
    items = [1, 2, 3, 4, 5]
    results = ordered_processor(items)
    
    # Results should be in original order despite varying processing times
    assert results == [2, 4, 6, 8, 10]


@pytest.mark.asyncio
async def test_opero_with_very_long_strings():
    """Test with very long strings to check memory handling."""
    
    @opero(cache=False)
    async def process_long_string(value: str):
        return f"processed_{len(value)}_chars"
    
    long_string = "x" * 10000
    result = await process_long_string(long_string)
    assert result == "processed_10000_chars"


@pytest.mark.asyncio
async def test_concurrent_opero_calls():
    """Test concurrent calls to the same opero function."""
    
    call_count = 0
    
    @opero(cache=False, rate_limit=None)
    async def concurrent_func(value: int):
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.01)
        return f"result_{value}"
    
    # Make concurrent calls
    tasks = [concurrent_func(i) for i in range(10)]
    results = await asyncio.gather(*tasks)
    
    assert len(results) == 10
    assert call_count == 10
    for i, result in enumerate(results):
        assert result == f"result_{i}"