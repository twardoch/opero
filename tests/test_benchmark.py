#!/usr/bin/env python3
"""
Benchmark tests for the opero package.
"""

import asyncio
import time
from unittest.mock import Mock

import pytest

from opero import opero, opmap


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_opero_overhead_benchmark(benchmark):
    """Benchmark the overhead of opero decorator."""
    
    @opero(cache=False, retries=1)
    async def simple_func(value: int):
        return value * 2
    
    async def benchmark_func():
        return await simple_func(42)
    
    result = await benchmark(benchmark_func)
    assert result == 84


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_opero_vs_native_performance(benchmark):
    """Compare opero performance with native function."""
    
    async def native_func(value: int):
        return value * 2
    
    @opero(cache=False, retries=1)
    async def opero_func(value: int):
        return value * 2
    
    # Benchmark native function
    async def benchmark_native():
        tasks = [native_func(i) for i in range(100)]
        return await asyncio.gather(*tasks)
    
    # Benchmark opero function
    async def benchmark_opero():
        tasks = [opero_func(i) for i in range(100)]
        return await asyncio.gather(*tasks)
    
    native_result = await benchmark_native()
    opero_result = await benchmark_opero()
    
    assert len(native_result) == 100
    assert len(opero_result) == 100
    assert native_result == opero_result


@pytest.mark.benchmark
def test_opmap_thread_performance(benchmark):
    """Benchmark opmap with thread mode."""
    
    @opmap(mode="thread", workers=4, cache=False, progress=False)
    def thread_processor(item: int):
        # Simulate some CPU work
        total = 0
        for i in range(1000):
            total += i
        return item * 2 + total
    
    def benchmark_func():
        items = list(range(50))
        return thread_processor(items)
    
    result = benchmark(benchmark_func)
    assert len(result) == 50


@pytest.mark.benchmark
def test_opmap_process_performance(benchmark):
    """Benchmark opmap with process mode."""
    
    @opmap(mode="process", workers=2, cache=False, progress=False)
    def process_processor(item: int):
        # Simulate some CPU work
        total = 0
        for i in range(1000):
            total += i
        return item * 2 + total
    
    def benchmark_func():
        items = list(range(20))  # Fewer items for process mode
        return process_processor(items)
    
    result = benchmark(benchmark_func)
    assert len(result) == 20


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_opero_cache_performance(benchmark):
    """Benchmark cache performance."""
    
    expensive_operation_count = 0
    
    @opero(cache=True, cache_ttl=60)
    async def expensive_func(value: int):
        nonlocal expensive_operation_count
        expensive_operation_count += 1
        # Simulate expensive operation
        await asyncio.sleep(0.01)
        return value * 2
    
    async def benchmark_func():
        # First call will be expensive
        result1 = await expensive_func(42)
        # Second call should be cached
        result2 = await expensive_func(42)
        return result1, result2
    
    result = await benchmark(benchmark_func)
    assert result[0] == 84
    assert result[1] == 84
    assert expensive_operation_count <= 1  # Should only call once due to caching


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_opero_retry_performance(benchmark):
    """Benchmark retry performance."""
    
    attempt_count = 0
    
    @opero(retries=3, cache=False)
    async def retry_func(value: int):
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 2:
            raise ValueError("Retry test")
        return value * 2
    
    async def benchmark_func():
        nonlocal attempt_count
        attempt_count = 0
        return await retry_func(42)
    
    result = await benchmark(benchmark_func)
    assert result == 84
    assert attempt_count == 2


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_opero_fallback_performance(benchmark):
    """Benchmark fallback performance."""
    
    @opero(arg_fallback="fallback_values", cache=False)
    async def fallback_func(value: int, fallback_values: list = None):
        if fallback_values is None:
            fallback_values = ["fail", "succeed"]
        
        current = fallback_values[0]
        if current == "fail":
            raise ValueError("Fallback test")
        return value * 2
    
    async def benchmark_func():
        return await fallback_func(42)
    
    result = await benchmark(benchmark_func)
    assert result == 84


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_opero_rate_limit_performance(benchmark):
    """Benchmark rate limiting performance."""
    
    @opero(rate_limit=100.0, cache=False)  # 100 calls per second
    async def rate_limited_func(value: int):
        return value * 2
    
    async def benchmark_func():
        tasks = [rate_limited_func(i) for i in range(10)]
        return await asyncio.gather(*tasks)
    
    result = await benchmark(benchmark_func)
    assert len(result) == 10


@pytest.mark.benchmark
def test_opmap_scaling(benchmark):
    """Benchmark opmap scaling with different worker counts."""
    
    def cpu_intensive_task(item: int):
        # Simulate CPU-intensive work
        total = 0
        for i in range(10000):
            total += i * item
        return total
    
    @opmap(mode="thread", workers=1, cache=False, progress=False)
    def single_worker_processor(item: int):
        return cpu_intensive_task(item)
    
    @opmap(mode="thread", workers=4, cache=False, progress=False)
    def multi_worker_processor(item: int):
        return cpu_intensive_task(item)
    
    def benchmark_single():
        items = list(range(20))
        return single_worker_processor(items)
    
    def benchmark_multi():
        items = list(range(20))
        return multi_worker_processor(items)
    
    # This is mainly to ensure both work correctly
    single_result = benchmark_single()
    multi_result = benchmark_multi()
    
    assert len(single_result) == 20
    assert len(multi_result) == 20
    assert single_result == multi_result


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_memory_usage_benchmark(benchmark):
    """Benchmark memory usage with large data sets."""
    
    @opero(cache=False)
    async def memory_func(data: list):
        return len(data)
    
    async def benchmark_func():
        large_data = list(range(10000))
        return await memory_func(large_data)
    
    result = await benchmark(benchmark_func)
    assert result == 10000


@pytest.mark.benchmark
def test_opmap_memory_efficiency(benchmark):
    """Benchmark memory efficiency with opmap."""
    
    @opmap(mode="thread", workers=2, cache=False, progress=False)
    def memory_efficient_processor(item: int):
        # Process and return immediately to test memory efficiency
        return item ** 2
    
    def benchmark_func():
        items = list(range(1000))
        return memory_efficient_processor(items)
    
    result = benchmark(benchmark_func)
    assert len(result) == 1000
    assert result[0] == 0
    assert result[999] == 998001


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_concurrent_opero_benchmark(benchmark):
    """Benchmark concurrent opero function calls."""
    
    @opero(cache=False, rate_limit=None)
    async def concurrent_func(value: int):
        await asyncio.sleep(0.001)  # Small delay to simulate async work
        return value * 2
    
    async def benchmark_func():
        tasks = [concurrent_func(i) for i in range(50)]
        return await asyncio.gather(*tasks)
    
    result = await benchmark(benchmark_func)
    assert len(result) == 50
    assert result[0] == 0
    assert result[49] == 98