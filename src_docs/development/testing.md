# Testing Guide

This guide covers testing practices, patterns, and tools used in Opero development.

## Test Organization

### Directory Structure

```
tests/
├── test_decorators.py      # Tests for @opero and @opmap
├── test_core.py           # Tests for core components
├── test_integration.py    # Integration tests
├── test_edge_cases.py     # Edge cases and error conditions
├── test_benchmark.py      # Performance benchmarks
├── test_package.py        # Package-level tests
└── conftest.py           # Shared fixtures and configuration
```

### Test Categories

#### Unit Tests
Test individual components in isolation:

```python
def test_retry_with_backoff():
    """Test retry logic with exponential backoff."""
    delays = []
    
    @opero(retries=3, backoff_factor=2.0)
    def flaky_function():
        if len(delays) < 2:
            delays.append(time.time())
            raise ValueError("Temporary failure")
        return "success"
    
    result = flaky_function()
    assert result == "success"
    assert len(delays) == 2
    # Verify exponential backoff
    assert delays[1] - delays[0] >= 0.2  # 0.1 * 2^1
```

#### Integration Tests
Test component interactions:

```python
@pytest.mark.integration
def test_opero_with_redis_cache(redis_server):
    """Test @opero with Redis cache backend."""
    @opero(
        cache=True,
        cache_backend="redis",
        cache_redis_url=redis_server.url,
        retries=2
    )
    def cached_operation(x):
        return expensive_computation(x)
    
    # First call
    result1 = cached_operation(42)
    
    # Should hit cache
    result2 = cached_operation(42)
    assert result1 == result2
```

#### Benchmark Tests
Measure performance characteristics:

```python
@pytest.mark.benchmark
def test_parallel_processing_performance(benchmark):
    """Benchmark parallel processing overhead."""
    @opmap(mode="thread", workers=4)
    def process_item(x):
        return x * 2
    
    data = list(range(1000))
    result = benchmark(process_item, data)
    assert len(result) == 1000
```

## Testing Patterns

### Mocking External Dependencies

```python
from unittest.mock import Mock, patch

def test_api_fallback():
    """Test fallback to backup API endpoints."""
    primary_api = Mock(side_effect=ConnectionError("Primary down"))
    backup_api = Mock(return_value={"status": "ok"})
    
    @opero(arg_fallback="api_client", retries=1)
    def call_api(data, api_client=[primary_api, backup_api]):
        return api_client[0](data)
    
    result = call_api({"test": "data"})
    assert result == {"status": "ok"}
    assert primary_api.call_count == 1
    assert backup_api.call_count == 1
```

### Testing Async Functions

```python
@pytest.mark.asyncio
async def test_async_rate_limiting():
    """Test rate limiting with async functions."""
    call_times = []
    
    @opero(rate_limit=2.0)  # 2 calls per second
    async def rate_limited_func():
        call_times.append(time.time())
        await asyncio.sleep(0.01)
        return "done"
    
    # Make 4 calls
    tasks = [rate_limited_func() for _ in range(4)]
    await asyncio.gather(*tasks)
    
    # Verify rate limiting
    assert call_times[2] - call_times[0] >= 0.9  # ~1 second
    assert call_times[3] - call_times[1] >= 0.9
```

### Testing Error Conditions

```python
def test_all_fallbacks_exhausted():
    """Test behavior when all fallback options fail."""
    @opero(
        arg_fallback="endpoint",
        retries=1
    )
    def failing_operation(endpoint=["bad1", "bad2", "bad3"]):
        raise ValueError(f"Failed with {endpoint[0]}")
    
    with pytest.raises(AllFailedError) as exc_info:
        failing_operation()
    
    error = exc_info.value
    assert len(error.errors) == 3
    assert all("Failed with" in str(e) for e in error.errors)
```

### Parametrized Tests

```python
@pytest.mark.parametrize("mode,workers,expected_type", [
    ("thread", 4, ThreadPoolExecutor),
    ("process", 2, ProcessPoolExecutor),
    ("async", 8, AsyncExecutor),
])
def test_parallel_modes(mode, workers, expected_type):
    """Test different parallel processing modes."""
    @opmap(mode=mode, workers=workers)
    def process(x):
        return x * 2
    
    result = process([1, 2, 3])
    assert result == [2, 4, 6]
```

## Test Fixtures

### Common Fixtures

```python
# conftest.py
import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_time(monkeypatch):
    """Mock time for deterministic tests."""
    current_time = 0
    
    def mock_time():
        return current_time
    
    def advance(seconds):
        nonlocal current_time
        current_time += seconds
    
    monkeypatch.setattr(time, "time", mock_time)
    return advance

@pytest.fixture
def flaky_function():
    """Function that fails N times before succeeding."""
    def make_flaky(failures=2):
        attempts = 0
        
        def func():
            nonlocal attempts
            attempts += 1
            if attempts <= failures:
                raise ConnectionError(f"Attempt {attempts} failed")
            return f"Success after {attempts} attempts"
        
        return func
    
    return make_flaky
```

### Cache Testing Fixtures

```python
@pytest.fixture
def temp_cache_dir(tmp_path):
    """Temporary directory for disk cache."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    yield str(cache_dir)
    # Cleanup happens automatically

@pytest.fixture
def redis_mock():
    """Mock Redis client for testing."""
    client = Mock()
    storage = {}
    
    client.get.side_effect = lambda k: storage.get(k)
    client.set.side_effect = lambda k, v, **kw: storage.update({k: v})
    client.delete.side_effect = lambda k: storage.pop(k, None)
    
    return client
```

## Testing Best Practices

### 1. Test Isolation

Ensure tests don't affect each other:

```python
def test_cache_isolation():
    """Ensure cache doesn't leak between tests."""
    @opero(cache=True, cache_namespace="test_isolation")
    def cached_func(x):
        return x * 2
    
    try:
        result = cached_func(5)
        assert result == 10
    finally:
        # Clean up
        clear_cache(namespace="test_isolation")
```

### 2. Deterministic Tests

Make tests predictable:

```python
def test_retry_timing(mock_time):
    """Test retry delays are deterministic."""
    attempts = []
    
    @opero(retries=3, backoff_factor=2.0)
    def timed_function():
        attempts.append(mock_time())
        if len(attempts) < 3:
            mock_time.advance(0.1)  # Simulate delay
            raise ValueError("Retry me")
        return "success"
    
    result = timed_function()
    assert attempts == [0, 0.2, 0.6]  # 0.1 * 2^n delays
```

### 3. Resource Cleanup

Always clean up resources:

```python
class TestWithResources:
    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Ensure cleanup after each test."""
        yield
        # Cleanup code here
        clear_cache()
        reset_rate_limiters()
```

### 4. Testing Concurrency

Test thread/process safety:

```python
def test_thread_safety():
    """Test concurrent access to shared resources."""
    counter = 0
    lock = threading.Lock()
    
    @opmap(mode="thread", workers=10)
    def increment(x):
        nonlocal counter
        with lock:
            counter += 1
        return x
    
    results = increment(range(100))
    assert counter == 100
    assert len(results) == 100
```

## Performance Testing

### Benchmark Structure

```python
import pytest

@pytest.mark.benchmark(group="decorators")
def test_opero_overhead(benchmark):
    """Measure @opero decorator overhead."""
    def simple_function(x):
        return x * 2
    
    @opero()  # Minimal configuration
    def decorated_function(x):
        return x * 2
    
    # Benchmark the overhead
    result = benchmark.pedantic(
        decorated_function,
        args=(42,),
        iterations=1000,
        rounds=100
    )
    
    assert result == 84
```

### Memory Profiling

```python
import tracemalloc

def test_memory_usage():
    """Test memory usage doesn't grow unbounded."""
    tracemalloc.start()
    
    @opmap(mode="thread", workers=4)
    def process(x):
        return [0] * 1000  # Allocate some memory
    
    # Process many items
    for _ in range(10):
        results = process(range(100))
        del results  # Explicit cleanup
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    # Memory should be reasonable
    assert peak < 100 * 1024 * 1024  # Less than 100MB
```

## Continuous Integration

### Test Matrix

Tests run on:
- Python versions: 3.10, 3.11, 3.12
- Operating systems: Ubuntu, macOS, Windows
- Optional dependencies: with/without pathos, aiomultiprocess

### Running Tests Locally

```bash
# Full test suite
hatch run test

# With coverage
hatch run test-cov

# Specific markers
hatch run pytest -m "not slow"
hatch run pytest -m benchmark

# Parallel execution
hatch run pytest -n auto

# Verbose output
hatch run pytest -vvs
```

## Debugging Tests

### Using pdb

```python
def test_complex_scenario():
    """Debug a complex test."""
    import pdb; pdb.set_trace()  # Breakpoint
    
    @opero(retries=2, cache=True)
    def complex_function(x):
        # Test logic here
        pass
```

### Detailed Logging

```python
def test_with_logging(caplog):
    """Test with detailed logging."""
    import logging
    caplog.set_level(logging.DEBUG)
    
    @opero(retries=2)
    def logged_function():
        logger.info("Function called")
        raise ValueError("Test error")
    
    with pytest.raises(AllFailedError):
        logged_function()
    
    # Verify logs
    assert "Retry attempt 1" in caplog.text
    assert "Retry attempt 2" in caplog.text
```

## Test Coverage

### Coverage Goals

- Overall: 90%+ coverage
- Core modules: 95%+ coverage
- Critical paths: 100% coverage

### Coverage Reports

```bash
# Generate HTML report
hatch run test-cov
open htmlcov/index.html

# Generate XML for CI
hatch run pytest --cov-report=xml

# Check specific module
hatch run pytest --cov=opero.decorators tests/test_decorators.py
```

## See Also

- [Contributing Guide](contributing.md) for development setup
- [GitHub Actions](.github/workflows/) for CI configuration
- [pytest documentation](https://docs.pytest.org/) for testing framework details