# Advanced Features

Opero's advanced features let you build resilient systems that adapt to failures and scale with demand.

## Custom Fallback Strategies

### Multi-Parameter Fallbacks

Handle complex fallback scenarios with multiple parameters:

```python
from opero import opero
import itertools


@opero(retries=2)
def complex_api_call(endpoint: str, api_key: str, region: str, timeout: int):
    """API call that might need multiple fallback combinations."""
    response = make_api_request(endpoint, api_key, region, timeout)
    return response.json()


def smart_api_call_with_fallbacks(data: dict):
    """Try all parameter combinations until one works."""

    endpoints = ["https://api-primary.com", "https://api-backup.com"]
    api_keys = ["key1", "key2", "key3"]
    regions = ["us-east-1", "us-west-2", "eu-west-1"]
    timeouts = [10, 20, 30]

    combinations = itertools.product(endpoints, api_keys, regions, timeouts)

    for endpoint, api_key, region, timeout in combinations:
        try:
            return complex_api_call(endpoint, api_key, region, timeout)
        except Exception as e:
            print(f"Failed with {endpoint}, {api_key}, {region}, {timeout}: {e}")
            continue

    raise Exception("All fallback combinations exhausted")


# Usage
result = smart_api_call_with_fallbacks({"key": "value"})
```

### Context-Aware Fallbacks

Choose fallbacks based on error type:

```python
import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError


@opero(retries=1)
def adaptive_api_call(url: str, headers: dict = None):
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()


def intelligent_api_call(resource_id: str):
    """Use different fallbacks for different error types."""

    primary_config = {
        "url": f"https://api.premium.com/v2/{resource_id}",
        "headers": {"Authorization": "Bearer premium_token"},
    }

    fallback_configs = [
        {
            "url": f"https://api.standard.com/v1/{resource_id}",
            "headers": {"Authorization": "Bearer standard_token"},
            "error_types": (HTTPError,),
        },
        {
            "url": f"https://api.public.com/{resource_id}",
            "headers": None,
            "error_types": (ConnectionError, Timeout),
        },
    ]

    # Try primary endpoint
    try:
        return adaptive_api_call(**primary_config)
    except Exception as primary_error:
        print(f"Primary endpoint failed: {primary_error}")

        # Try appropriate fallback
        for config in fallback_configs:
            if isinstance(primary_error, config["error_types"]):
                try:
                    print(f"Trying fallback: {config['url']}")
                    return adaptive_api_call(config["url"], config["headers"])
                except Exception as fallback_error:
                    print(f"Fallback failed: {fallback_error}")
                    continue

        raise primary_error


# Usage
try:
    data = intelligent_api_call("resource123")
except Exception as e:
    print(f"All attempts failed: {e}")
```

## Advanced Caching Patterns

### Multi-Level Caching

Cache with different TTLs for different layers:

```python
from opero import opero
import time


class MultiLevelCache:
    """L1 (fast) and L2 (persistent) cache with different TTLs."""

    def __init__(self):
        self.l1_cache = {}
        self.l2_cache = {}
        self.l1_ttl = 60
        self.l2_ttl = 3600

    def get(self, key):
        current_time = time.time()

        # Check L1 cache
        if key in self.l1_cache:
            value, timestamp = self.l1_cache[key]
            if current_time - timestamp < self.l1_ttl:
                return value
            else:
                del self.l1_cache[key]

        # Check L2 cache
        if key in self.l2_cache:
            value, timestamp = self.l2_cache[key]
            if current_time - timestamp < self.l2_ttl:
                self.l1_cache[key] = (value, current_time)
                return value
            else:
                del self.l2_cache[key]

        return None

    def set(self, key, value):
        current_time = time.time()
        self.l1_cache[key] = (value, current_time)
        self.l2_cache[key] = (value, current_time)


multi_cache = MultiLevelCache()


def multi_level_cache_key(*args, **kwargs):
    return f"ml_cache_{hash(str(args) + str(sorted(kwargs.items())))}"


@opero(cache=True, cache_key=multi_level_cache_key, cache_backend="custom")
def expensive_computation(data: dict, complexity: int):
    """Computation with multi-level caching."""
    cache_key = multi_level_cache_key(data, complexity=complexity)

    cached_result = multi_cache.get(cache_key)
    if cached_result is not None:
        print("Multi-level cache hit!")
        return cached_result

    print("Computing...")
    time.sleep(complexity)
    result = sum(v for v in data.values()) * complexity

    multi_cache.set(cache_key, result)
    return result


# Usage
data = {"a": 1, "b": 2, "c": 3}
result1 = expensive_computation(data, complexity=2)  # Computes
result2 = expensive_computation(data, complexity=2)  # L1 cache hit
time.sleep(70)
result3 = expensive_computation(data, complexity=2)  # L2 cache hit, promotes to L1
```

### Conditional Caching

Cache only good results:

```python
def conditional_cache_key(*args, **kwargs):
    return f"conditional_{hash(str(args) + str(kwargs))}"


def should_cache_result(result):
    """Only cache successful, non-empty results."""
    if not result:
        return False
    if isinstance(result, dict) and result.get("error"):
        return False
    if isinstance(result, list) and len(result) == 0:
        return False
    return True


@opero(cache=True, cache_key=conditional_cache_key, cache_ttl=300)
def fetch_with_conditional_caching(query: str):
    """Cache only good results."""
    result = external_api_call(query)

    if not should_cache_result(result):
        return result

    return result
```

### Cache Warming

Pre-populate cache before peak usage:

```python
from concurrent.futures import ThreadPoolExecutor
from opero import opmap


@opero(cache=True, cache_ttl=3600)
def fetch_user_data(user_id: str):
    """Cached user data fetcher."""
    return api_call(f"/users/{user_id}")


@opmap(mode="thread", workers=10, cache=True)
def warm_user_cache(user_ids: list[str]):
    """Warm cache for multiple users."""
    results = []
    for user_id in user_ids:
        try:
            result = fetch_user_data(user_id)
            results.append({"user_id": user_id, "status": "cached", "data": result})
        except Exception as e:
            results.append({"user_id": user_id, "status": "failed", "error": str(e)})
    return results


def warm_cache_for_peak_hours():
    """Warm cache before peak usage."""
    frequent_users = get_frequent_users()
    print(f"Warming cache for {len(frequent_users)} users...")

    warming_results = warm_user_cache(frequent_users)

    successful = sum(1 for r in warming_results if r["status"] == "cached")
    failed = len(warming_results) - successful

    print(f"Cache warming complete: {successful} cached, {failed} failed")


# Schedule cache warming
import schedule

schedule.every().day.at("08:00").do(warm_cache_for_peak_hours)
```

## Advanced Parallel Processing

### Custom Worker Pools

Use different pools for different workloads:

```python
from opero import opmap
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor


class CustomWorkerPool:
    """Specialized worker pools for different task types."""

    def __init__(self):
        self.io_pool = ThreadPoolExecutor(max_workers=20, thread_name_prefix="io")
        self.cpu_pool = ThreadPoolExecutor(max_workers=8, thread_name_prefix="cpu")
        self.network_semaphore = asyncio.Semaphore(50)

    @opmap(mode="thread", workers=20, retries=3)
    def io_intensive_task(self, item):
        """I/O intensive tasks."""
        return self.io_pool.submit(process_io_task, item).result()

    @opmap(mode="process", workers=8, retries=1)
    def cpu_intensive_task(self, item):
        """CPU intensive tasks."""
        return complex_calculation(item)

    @opmap(mode="async", workers=50, retries=3, rate_limit=100.0)
    async def network_task(self, item):
        """Network tasks with connection limiting."""
        async with self.network_semaphore:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://api.com/{item}") as response:
                    return await response.json()


# Usage
worker_pool = CustomWorkerPool()

io_results = worker_pool.io_intensive_task(io_items)
cpu_results = worker_pool.cpu_intensive_task(cpu_items)
network_results = await worker_pool.network_task(network_items)
```

### Dynamic Worker Scaling

Adjust workers based on system load:

```python
import psutil
import os
from opero import opmap


def get_optimal_worker_count(task_type: str, item_count: int):
    """Calculate workers based on system resources."""
    cpu_count = os.cpu_count()
    memory_gb = psutil.virtual_memory().total / (1024**3)
    load_avg = psutil.getloadavg()[0] if hasattr(psutil, "getloadavg") else 0

    if task_type == "cpu_bound":
        base_workers = max(1, cpu_count - 1)
        if load_avg > cpu_count * 0.8:
            return max(1, base_workers // 2)
        return base_workers

    elif task_type == "io_bound":
        max_workers = min(100, int(memory_gb * 10))
        return min(max_workers, max(10, item_count // 10))

    elif task_type == "network":
        return min(50, max(10, item_count // 20))

    return 10


class AdaptiveProcessor:
    """Processor that adapts to system conditions."""

    def process_batch(self, items: list, task_type: str):
        """Process with dynamic worker scaling."""

        worker_count = get_optimal_worker_count(task_type, len(items))
        print(f"Using {worker_count} workers for {len(items)} {task_type} tasks")

        if task_type == "cpu_bound":
            return self._process_cpu_bound(items, worker_count)
        elif task_type == "io_bound":
            return self._process_io_bound(items, worker_count)
        elif task_type == "network":
            return self._process_network(items, worker_count)

    def _process_cpu_bound(self, items: list, workers: int):
        @opmap(mode="process", workers=workers, retries=1)
        def cpu_task(item):
            return cpu_intensive_operation(item)

        return cpu_task(items)

    def _process_io_bound(self, items: list, workers: int):
        @opmap(mode="thread", workers=workers, retries=3)
        def io_task(item):
            return io_operation(item)

        return io_task(items)

    async def _process_network(self, items: list, workers: int):
        @opmap(mode="async", workers=workers, retries=3, rate_limit=50.0)
        async def network_task(item):
            return await network_operation(item)

        return await network_task(items)


# Usage
processor = AdaptiveProcessor()

cpu_results = processor.process_batch(cpu_items, "cpu_bound")
io_results = processor.process_batch(io_items, "io_bound")
network_results = await processor.process_batch(network_items, "network")
```

## Circuit Breaker Pattern

Stop cascading failures:

```python
import time
from enum import Enum
from typing import Callable, Any
from opero import opero


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Prevent cascading failures."""

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute with circuit breaker protection."""

        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.timeout:
                self.state = CircuitState.HALF_OPEN
                print("Circuit breaker: Transitioning to HALF_OPEN")
            else:
                raise Exception("Circuit breaker is OPEN - calls rejected")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            print("Circuit breaker: Transitioning to CLOSED")

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            print("Circuit breaker: Transitioning to OPEN")


api_circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=30)


def with_circuit_breaker(circuit_breaker: CircuitBreaker):
    """Add circuit breaker to any function."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            return circuit_breaker.call(func, *args, **kwargs)

        return wrapper

    return decorator


@with_circuit_breaker(api_circuit_breaker)
@opero(retries=2, cache=True, rate_limit=10.0)
def protected_api_call(endpoint: str):
    """API call with circuit breaker."""
    response = requests.get(f"https://api.com/{endpoint}")

    if response.status_code >= 500:
        raise requests.RequestException(f"Server error: {response.status_code}")

    response.raise_for_status()
    return response.json()


# Usage
try:
    result = protected_api_call("users/123")
except Exception as e:
    print(f"Call failed: {e}")
```

## Advanced Error Recovery

### Retry with Exponential Backoff + Jitter

Smart retries that avoid overwhelming services:

```python
import random
import time
from opero import opero


def jittered_backoff(attempt: int, base_delay: float = 0.1, max_delay: float = 30.0):
    """Exponential backoff with jitter."""
    delay = min(max_delay, base_delay * (2**attempt))
    delay = delay * (0.5 + random.random() * 0.5)
    return delay


class AdvancedRetryStrategy:
    """Retry based on error type."""

    def __init__(self, max_retries: int = 5, base_delay: float = 0.1):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.attempt_count = 0

    def should_retry(self, exception: Exception) -> bool:
        if self.attempt_count >= self.max_retries:
            return False

        if isinstance(exception, (ConnectionError, TimeoutError)):
            return True
        elif isinstance(exception, requests.HTTPError):
            if hasattr(exception, "response") and exception.response:
                return 500 <= exception.response.status_code < 600
        elif "rate limit" in str(exception).lower():
            return True

        return False

    def get_delay(self) -> float:
        return jittered_backoff(self.attempt_count, self.base_delay)

    def execute_with_retry(self, func, *args, **kwargs):
        self.attempt_count = 0
        last_exception = None

        while self.attempt_count <= self.max_retries:
            try:
                if self.attempt_count > 0:
                    delay = self.get_delay()
                    print(
                        f"Retrying in {delay:.2f}s (attempt {self.attempt_count + 1})"
                    )
                    time.sleep(delay)

                return func(*args, **kwargs)

            except Exception as e:
                last_exception = e
                self.attempt_count += 1

                if not self.should_retry(e):
                    print(f"Not retrying {type(e).__name__}: {e}")
                    break

                print(f"Attempt {self.attempt_count} failed: {e}")

        raise last_exception


# Usage
retry_strategy = AdvancedRetryStrategy(max_retries=5, base_delay=0.2)


def resilient_operation(data):
    return retry_strategy.execute_with_retry(risky_operation, data)


@opero(cache=True, rate_limit=5.0)
def cached_resilient_operation(data):
    return resilient_operation(data)
```

## Monitoring and Observability

### Comprehensive Metrics Collection

Track what your functions actually do:

```python
import time
from collections import defaultdict, Counter
from functools import wraps
from opero import opero


class OperationMetrics:
    """Track function performance and reliability."""

    def __init__(self):
        self.call_counts = Counter()
        self.success_counts = Counter()
        self.failure_counts = Counter()
        self.retry_counts = Counter()
        self.cache_hits = Counter()
        self.cache_misses = Counter()
        self.response_times = defaultdict(list)
        self.error_types = Counter()

    def record_call(self, func_name: str):
        self.call_counts[func_name] += 1

    def record_success(self, func_name: str, duration: float):
        self.success_counts[func_name] += 1
        self.response_times[func_name].append(duration)

    def record_failure(self, func_name: str, error: Exception, duration: float):
        self.failure_counts[func_name] += 1
        self.error_types[f"{func_name}:{type(error).__name__}"] += 1
        self.response_times[func_name].append(duration)

    def record_retry(self, func_name: str):
        self.retry_counts[func_name] += 1

    def record_cache_hit(self, func_name: str):
        self.cache_hits[func_name] += 1

    def record_cache_miss(self, func_name: str):
        self.cache_misses[func_name] += 1

    def get_summary(self, func_name: str = None):
        """Get metrics summary."""
        if func_name:
            funcs = [func_name]
        else:
            funcs = set(self.call_counts.keys())

        summary = {}
        for func in funcs:
            calls = self.call_counts[func]
            successes = self.success_counts[func]
            failures = self.failure_counts[func]
            retries = self.retry_counts[func]
            cache_hits = self.cache_hits[func]
            cache_misses = self.cache_misses[func]

            response_times = self.response_times[func]
            avg_response_time = (
                sum(response_times) / len(response_times) if response_times else 0
            )

            summary[func] = {
                "calls": calls,
                "success_rate": successes / calls if calls > 0 else 0,
                "failure_rate": failures / calls if calls > 0 else 0,
                "retry_rate": retries / calls if calls > 0 else 0,
                "cache_hit_rate": cache_hits / (cache_hits + cache_misses)
                if (cache_hits + cache_misses) > 0
                else 0,
                "avg_response_time": avg_response_time,
                "total_retries": retries,
            }

        return summary


metrics = OperationMetrics()


def with_metrics(func):
    """Add metrics to any function."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        start_time = time.time()

        metrics.record_call(func_name)

        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            metrics.record_success(func_name, duration)
            return result
        except Exception as e:
            duration = time.time() - start_time
            metrics.record_failure(func_name, e, duration)
            raise

    return wrapper


@with_metrics
@opero(retries=3, cache=True, rate_limit=10.0)
def monitored_api_call(endpoint: str):
    """API call with metrics."""
    response = requests.get(f"https://api.com/{endpoint}")
    response.raise_for_status()
    return response.json()


def print_metrics_report():
    """Print metrics report."""
    summary = metrics.get_summary()

    print("\n=== OPERO METRICS REPORT ===")
    for func_name, stats in summary.items():
        print(f"\nFunction: {func_name}")
        print(f"  Total calls: {stats['calls']}")
        print(f"  Success rate: {stats['success_rate']:.2%}")
        print(f"  Failure rate: {stats['failure_rate']:.2%}")
        print(f"  Retry rate: {stats['retry_rate']:.2%}")
        print(f"  Cache hit rate: {stats['cache_hit_rate']:.2%}")
        print(f"  Avg response time: {stats['avg_response_time']:.3f}s")
        print(f"  Total retries: {stats['total_retries']}")


# Schedule reporting
import threading


def periodic_metrics_report():
    while True:
        time.sleep(300)
        print_metrics_report()


metrics_thread = threading.Thread(target=periodic_metrics_report, daemon=True)
metrics_thread.start()
```

## Next Steps

You've now mastered Opero's advanced features. Continue with:

1. **[Best Practices](best-practices.md)** - Production-ready patterns
2. **[API Reference](../api/overview.md)** - Technical documentation
3. **[Core Components](../api/core.md)** - Implementation details

## Advanced Patterns Quick Reference

```python
# Multi-parameter fallbacks
def complex_fallback_strategy(primary_config, fallback_configs):
    pass


# Multi-level caching
@opero(cache=True, cache_key=custom_key_func)
def multi_level_cached():
    pass


# Circuit breaker pattern
@with_circuit_breaker(circuit_breaker)
@opero(retries=3)
def protected_function():
    pass


# Advanced retry strategies
retry_strategy = AdvancedRetryStrategy(max_retries=5)


def custom_retry_function():
    pass


# Comprehensive metrics
@with_metrics
@opero(retries=3, cache=True)
def monitored_function():
    pass


# Dynamic worker scaling
worker_count = get_optimal_worker_count("cpu_bound", len(items))


@opmap(mode="process", workers=worker_count)
def adaptive_processor():
    pass
```