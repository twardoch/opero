# Advanced Features

This guide covers advanced Opero features for complex use cases and production scenarios.

## Advanced Parallel Processing

### Dynamic Worker Allocation

Adjust worker count based on system resources:

```python
import os
from opero import opmap

def get_optimal_workers(mode: str) -> int:
    """Calculate optimal worker count based on mode and system."""
    cpu_count = os.cpu_count() or 4
    
    if mode == "thread":
        # I/O-bound: can use more workers than CPUs
        return min(cpu_count * 4, 32)
    elif mode == "process":
        # CPU-bound: match CPU count
        return cpu_count
    else:
        return 4

@opmap(
    mode="thread",
    workers=get_optimal_workers("thread"),
    retries=3,
    cache=True
)
def parallel_io_task(item):
    # Your I/O-bound operation
    pass
```

### Custom Task Distribution

Implement custom logic for task distribution:

```python
from typing import List, Any
import numpy as np

def distribute_tasks_by_size(items: List[Any], workers: int) -> List[List[Any]]:
    """Distribute tasks to balance workload across workers."""
    # Sort items by expected processing time
    sorted_items = sorted(items, key=lambda x: estimate_processing_time(x))
    
    # Round-robin distribution for balanced load
    chunks = [[] for _ in range(workers)]
    for i, item in enumerate(sorted_items):
        chunks[i % workers].append(item)
    
    return chunks

@opmap(
    mode="process",
    workers=4,
    ordered=False  # Don't need order preservation
)
def process_with_load_balancing(chunk):
    # Process a balanced chunk of items
    return [process_single_item(item) for item in chunk]

# Usage
all_items = get_large_dataset()
distributed = distribute_tasks_by_size(all_items, 4)
results = process_with_load_balancing(distributed)
```

### Async Process Pool

Use async functions with process pools:

```python
@opmap(
    mode="async_process",  # Requires opero[aiomultiprocess]
    workers=4,
    retries=2
)
async def cpu_intensive_async_task(data):
    """CPU-intensive task that also does async I/O."""
    # Perform CPU-intensive computation
    result = compute_heavy_operation(data)
    
    # Also perform async I/O
    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.example.com/results", 
                               json=result) as response:
            return await response.json()
```

## Advanced Caching Strategies

### Custom Cache Keys

Implement sophisticated cache key generation:

```python
import hashlib
import json
from typing import Any

def create_stable_cache_key(func, *args, **kwargs) -> str:
    """Create cache key that's stable across runs."""
    # Normalize arguments
    key_data = {
        "function": func.__qualname__,
        "args": args,
        "kwargs": dict(sorted(kwargs.items()))
    }
    
    # Create stable hash
    key_json = json.dumps(key_data, sort_keys=True, default=str)
    key_hash = hashlib.md5(key_json.encode()).hexdigest()
    
    return f"{func.__module__}:{func.__name__}:{key_hash}"

@opero(
    cache=True,
    cache_key=create_stable_cache_key,
    cache_ttl=3600
)
def complex_cached_function(user_id: int, filters: dict, options: dict = None):
    # Complex function with multiple parameters
    pass
```

### Cache Warming

Pre-populate cache for better performance:

```python
from concurrent.futures import ThreadPoolExecutor

@opero(cache=True, cache_ttl=3600)
def get_product_details(product_id: int):
    # Expensive operation
    return fetch_from_database(product_id)

def warm_cache(product_ids: List[int]):
    """Pre-populate cache with frequently accessed items."""
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Trigger cache population
        list(executor.map(get_product_details, product_ids))

# Warm cache on startup
popular_products = get_popular_product_ids()
warm_cache(popular_products)
```

### Hierarchical Caching

Implement multi-level caching:

```python
@opero(
    cache=True,
    cache_backend="memory",  # L1 cache
    cache_ttl=60,           # Short TTL
    cache_max_size=100
)
@opero(
    cache=True,
    cache_backend="redis",   # L2 cache
    cache_ttl=3600,         # Longer TTL
    cache_namespace="l2"
)
def hierarchical_cached_function(key: str):
    # Will check memory cache first, then Redis, then execute
    return expensive_operation(key)
```

## Advanced Retry Strategies

### Conditional Retries

Retry based on response content:

```python
def should_retry(exception, response=None):
    """Determine if operation should be retried."""
    if isinstance(exception, requests.HTTPError):
        if exception.response.status_code == 429:  # Rate limited
            return True
        elif exception.response.status_code >= 500:  # Server error
            return True
    elif response and response.get("status") == "pending":
        return True
    return False

@opero(
    retries=5,
    retry_on=Exception,  # Catch all exceptions
    retry_predicate=should_retry  # Custom logic
)
def smart_retry_operation(data):
    response = make_api_call(data)
    if response["status"] == "pending":
        raise Exception("Operation still pending")
    return response
```

### Retry with Exponential Backoff and Jitter

Prevent thundering herd with jittered backoff:

```python
import random

def jittered_backoff(attempt: int, base_delay: float = 1.0) -> float:
    """Calculate delay with exponential backoff and jitter."""
    # Exponential backoff: 1s, 2s, 4s, 8s...
    delay = base_delay * (2 ** attempt)
    
    # Add jitter: ±25% randomization
    jitter = delay * 0.25 * (2 * random.random() - 1)
    
    return max(0.1, delay + jitter)

@opero(
    retries=4,
    backoff_function=jittered_backoff
)
def distributed_operation(item):
    # Operation that many instances might retry simultaneously
    pass
```

## Advanced Fallback Patterns

### Cascading Fallbacks

Implement multiple levels of fallbacks:

```python
@opero(
    arg_fallback="endpoint",
    retries=2
)
def primary_service_call(data, endpoint=["https://primary.api.com", 
                                         "https://backup.api.com"]):
    return call_api(endpoint[0], data)

@opero(
    cache=True,
    cache_ttl=86400  # 24 hour cache
)
def cached_service_call(data):
    # Cached backup service
    return call_backup_service(data)

def resilient_service_call(data):
    """Multi-level fallback strategy."""
    try:
        # Try primary and backup endpoints
        return primary_service_call(data)
    except AllFailedError:
        try:
            # Try cached backup service
            return cached_service_call(data)
        except Exception:
            # Final fallback: return degraded response
            return {"data": data, "status": "degraded", "source": "fallback"}
```

### Smart Fallback Selection

Choose fallbacks based on context:

```python
class FallbackSelector:
    def __init__(self):
        self.endpoint_stats = defaultdict(lambda: {"success": 0, "failure": 0})
    
    def get_ordered_endpoints(self, endpoints: List[str]) -> List[str]:
        """Order endpoints by success rate."""
        def success_rate(endpoint):
            stats = self.endpoint_stats[endpoint]
            total = stats["success"] + stats["failure"]
            return stats["success"] / total if total > 0 else 0.5
        
        return sorted(endpoints, key=success_rate, reverse=True)
    
    def record_result(self, endpoint: str, success: bool):
        if success:
            self.endpoint_stats[endpoint]["success"] += 1
        else:
            self.endpoint_stats[endpoint]["failure"] += 1

selector = FallbackSelector()

@opero(
    arg_fallback="endpoint",
    retries=3
)
def adaptive_fallback_call(query, endpoint=None):
    if endpoint is None:
        endpoint = selector.get_ordered_endpoints([
            "https://fast.api.com",
            "https://reliable.api.com",
            "https://backup.api.com"
        ])
    
    current = endpoint[0]
    try:
        result = call_api(current, query)
        selector.record_result(current, True)
        return result
    except Exception as e:
        selector.record_result(current, False)
        raise
```

## Production Patterns

### Circuit Breaker Pattern

Prevent cascading failures:

```python
from datetime import datetime, timedelta
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self):
        return (self.last_failure_time and 
                datetime.now() - self.last_failure_time > 
                timedelta(seconds=self.recovery_timeout))
    
    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

# Usage with Opero
breaker = CircuitBreaker()

@opero(retries=1)  # Minimal retries when using circuit breaker
def protected_operation(data):
    return breaker.call(external_service_call, data)
```

### Request Deduplication

Prevent duplicate concurrent requests:

```python
from threading import Lock
from collections import defaultdict

class RequestDeduplicator:
    def __init__(self):
        self.in_flight = {}
        self.lock = Lock()
    
    def deduplicated_call(self, key, func, *args, **kwargs):
        with self.lock:
            if key in self.in_flight:
                # Return existing future
                return self.in_flight[key]
            
            # Create new future
            future = concurrent.futures.Future()
            self.in_flight[key] = future
        
        try:
            result = func(*args, **kwargs)
            future.set_result(result)
            return result
        except Exception as e:
            future.set_exception(e)
            raise
        finally:
            with self.lock:
                del self.in_flight[key]

deduplicator = RequestDeduplicator()

@opero(cache=True, cache_ttl=60)
def deduplicated_api_call(resource_id: str):
    return deduplicator.deduplicated_call(
        f"api:{resource_id}",
        fetch_resource,
        resource_id
    )
```

### Graceful Degradation

Implement feature flags for degradation:

```python
class FeatureFlags:
    def __init__(self):
        self.flags = {
            "use_cache_only": False,
            "disable_expensive_features": False,
            "reduced_rate_limit": False
        }
    
    def is_enabled(self, flag: str) -> bool:
        return self.flags.get(flag, False)
    
    def enable_degraded_mode(self):
        self.flags["use_cache_only"] = True
        self.flags["disable_expensive_features"] = True
        self.flags["reduced_rate_limit"] = True

flags = FeatureFlags()

@opero(
    cache=True,
    cache_ttl=3600,
    rate_limit=lambda: 2.0 if flags.is_enabled("reduced_rate_limit") else 10.0
)
def adaptive_operation(data):
    if flags.is_enabled("use_cache_only"):
        # Try cache first
        try:
            return adaptive_operation.cache_get(data)
        except KeyError:
            pass
    
    if flags.is_enabled("disable_expensive_features"):
        return simple_operation(data)
    else:
        return expensive_operation(data)
```

## Monitoring and Observability

### Custom Metrics Collection

```python
from dataclasses import dataclass
from datetime import datetime
import prometheus_client as prom

# Define metrics
retry_counter = prom.Counter('opero_retries_total', 
                           'Total number of retries',
                           ['function', 'exception'])
cache_hit_counter = prom.Counter('opero_cache_hits_total',
                               'Total number of cache hits',
                               ['function'])
latency_histogram = prom.Histogram('opero_latency_seconds',
                                 'Function execution latency',
                                 ['function'])

@dataclass
class MetricsCollector:
    def record_retry(self, function_name: str, exception: Exception):
        retry_counter.labels(
            function=function_name,
            exception=type(exception).__name__
        ).inc()
    
    def record_cache_hit(self, function_name: str):
        cache_hit_counter.labels(function=function_name).inc()
    
    def record_latency(self, function_name: str, duration: float):
        latency_histogram.labels(function=function_name).observe(duration)

collector = MetricsCollector()

# Integrate with Opero
@opero(
    retries=3,
    cache=True,
    on_retry=lambda e: collector.record_retry("my_function", e),
    on_cache_hit=lambda: collector.record_cache_hit("my_function")
)
def monitored_function(data):
    start = datetime.now()
    try:
        result = process_data(data)
        return result
    finally:
        duration = (datetime.now() - start).total_seconds()
        collector.record_latency("my_function", duration)
```

## Next Steps

- Review [Best Practices](best-practices.md) for production deployment
- Explore the [API Reference](../api/overview.md) for complete details
- Check [Development Guide](../development/contributing.md) to contribute