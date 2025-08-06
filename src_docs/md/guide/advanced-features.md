# Advanced Features

Unlock Opero's full potential with advanced patterns, custom implementations, and sophisticated resilience strategies.

## Custom Fallback Strategies

Go beyond simple parameter fallbacks with custom logic.

### Multi-Parameter Fallbacks

Handle complex fallback scenarios involving multiple parameters:

```python
from opero import opero
import itertools

@opero(retries=2)
def complex_api_call(endpoint: str, api_key: str, region: str, timeout: int):
    """API call that might need multiple fallback combinations."""
    response = make_api_request(endpoint, api_key, region, timeout)
    return response.json()

def smart_api_call_with_fallbacks(data: dict):
    """Implement custom fallback logic for multiple parameters."""
    
    # Define fallback options
    endpoints = ["https://api-primary.com", "https://api-backup.com"]
    api_keys = ["key1", "key2", "key3"]
    regions = ["us-east-1", "us-west-2", "eu-west-1"]
    timeouts = [10, 20, 30]
    
    # Try all combinations with priority
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

Implement fallbacks that adapt based on error types:

```python
import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError

@opero(retries=1)  # Minimal retries, we handle fallbacks manually
def adaptive_api_call(url: str, headers: dict = None):
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()

def intelligent_api_call(resource_id: str):
    """API call with context-aware fallbacks."""
    
    # Primary endpoint with authentication
    primary_config = {
        "url": f"https://api.premium.com/v2/{resource_id}",
        "headers": {"Authorization": "Bearer premium_token"}
    }
    
    # Fallback configurations based on error type
    fallback_configs = [
        {
            "url": f"https://api.standard.com/v1/{resource_id}",
            "headers": {"Authorization": "Bearer standard_token"},
            "error_types": (HTTPError,)  # Use for client errors
        },
        {
            "url": f"https://api.public.com/{resource_id}",
            "headers": None,
            "error_types": (ConnectionError, Timeout)  # Use for network errors
        }
    ]
    
    # Try primary endpoint
    try:
        return adaptive_api_call(**primary_config)
    except Exception as primary_error:
        print(f"Primary endpoint failed: {primary_error}")
        
        # Select appropriate fallback based on error type
        for config in fallback_configs:
            if isinstance(primary_error, config["error_types"]):
                try:
                    print(f"Trying fallback: {config['url']}")
                    return adaptive_api_call(config["url"], config["headers"])
                except Exception as fallback_error:
                    print(f"Fallback failed: {fallback_error}")
                    continue
        
        # If all fallbacks fail, raise the original error
        raise primary_error

# Usage
try:
    data = intelligent_api_call("resource123")
except Exception as e:
    print(f"All attempts failed: {e}")
```

## Advanced Caching Patterns

### Multi-Level Caching

Implement hierarchical caching with different TTLs:

```python
from opero import opero
import time

class MultiLevelCache:
    """Custom cache with L1 (fast) and L2 (persistent) levels."""
    
    def __init__(self):
        self.l1_cache = {}  # Fast in-memory cache
        self.l2_cache = {}  # Slower but persistent cache
        self.l1_ttl = 60    # 1 minute for L1
        self.l2_ttl = 3600  # 1 hour for L2
    
    def get(self, key):
        current_time = time.time()
        
        # Try L1 cache first
        if key in self.l1_cache:
            value, timestamp = self.l1_cache[key]
            if current_time - timestamp < self.l1_ttl:
                return value
            else:
                del self.l1_cache[key]
        
        # Try L2 cache
        if key in self.l2_cache:
            value, timestamp = self.l2_cache[key]
            if current_time - timestamp < self.l2_ttl:
                # Promote to L1 cache
                self.l1_cache[key] = (value, current_time)
                return value
            else:
                del self.l2_cache[key]
        
        return None
    
    def set(self, key, value):
        current_time = time.time()
        self.l1_cache[key] = (value, current_time)
        self.l2_cache[key] = (value, current_time)

# Global cache instance
multi_cache = MultiLevelCache()

def multi_level_cache_key(*args, **kwargs):
    return f"ml_cache_{hash(str(args) + str(sorted(kwargs.items())))}"

@opero(
    cache=True,
    cache_key=multi_level_cache_key,
    cache_backend="custom",  # We'll handle caching manually
)
def expensive_computation(data: dict, complexity: int):
    """Computation with multi-level caching."""
    cache_key = multi_level_cache_key(data, complexity=complexity)
    
    # Check our custom cache first
    cached_result = multi_cache.get(cache_key)
    if cached_result is not None:
        print("Multi-level cache hit!")
        return cached_result
    
    # Expensive computation
    print("Computing...")
    time.sleep(complexity)  # Simulate computation time
    result = sum(v for v in data.values()) * complexity
    
    # Store in our custom cache
    multi_cache.set(cache_key, result)
    
    return result

# Usage
data = {"a": 1, "b": 2, "c": 3}
result1 = expensive_computation(data, complexity=2)  # Computes
result2 = expensive_computation(data, complexity=2)  # L1 cache hit
time.sleep(70)  # Wait for L1 to expire
result3 = expensive_computation(data, complexity=2)  # L2 cache hit, promotes to L1
```

### Conditional Caching

Cache based on result characteristics:

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

@opero(
    cache=True,
    cache_key=conditional_cache_key,
    cache_ttl=300
)
def fetch_with_conditional_caching(query: str):
    """Only cache successful, non-empty results."""
    result = external_api_call(query)
    
    # Don't let Opero cache this result if it's not good
    if not should_cache_result(result):
        # Clear any existing cache entry
        cache_key = conditional_cache_key(query)
        # Custom logic to remove from cache
        # This is a simplified example
        return result
    
    return result
```

### Cache Warming

Pre-populate cache with anticipated data:

```python
from concurrent.futures import ThreadPoolExecutor
from opero import opmap

@opero(cache=True, cache_ttl=3600)
def fetch_user_data(user_id: str):
    """Cached user data fetcher."""
    return api_call(f"/users/{user_id}")

@opmap(mode="thread", workers=10, cache=True)
def warm_user_cache(user_ids: list[str]):
    """Warm the cache for multiple users."""
    results = []
    for user_id in user_ids:
        try:
            result = fetch_user_data(user_id)
            results.append({"user_id": user_id, "status": "cached", "data": result})
        except Exception as e:
            results.append({"user_id": user_id, "status": "failed", "error": str(e)})
    return results

# Cache warming strategy
def warm_cache_for_peak_hours():
    """Pre-warm cache before peak usage."""
    # Get list of frequently accessed users
    frequent_users = get_frequent_users()
    
    print(f"Warming cache for {len(frequent_users)} users...")
    
    # Warm cache in parallel
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

Create specialized worker pools for different workload types:

```python
from opero import opmap
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

class CustomWorkerPool:
    """Custom worker pool with specialized configurations."""
    
    def __init__(self):
        # Different pools for different workload types
        self.io_pool = ThreadPoolExecutor(max_workers=20, thread_name_prefix="io")
        self.cpu_pool = ThreadPoolExecutor(max_workers=8, thread_name_prefix="cpu")
        self.network_semaphore = asyncio.Semaphore(50)  # Limit concurrent connections
    
    @opmap(mode="thread", workers=20, retries=3)
    def io_intensive_task(self, item):
        """I/O intensive tasks use specialized thread pool."""
        # File operations, database queries, etc.
        return self.io_pool.submit(process_io_task, item).result()
    
    @opmap(mode="process", workers=8, retries=1)
    def cpu_intensive_task(self, item):
        """CPU intensive tasks use process pool."""
        # Mathematical computations, data transformations, etc.
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

# Process different workload types with optimized configurations
io_results = worker_pool.io_intensive_task(io_items)
cpu_results = worker_pool.cpu_intensive_task(cpu_items)
network_results = await worker_pool.network_task(network_items)
```

### Dynamic Worker Scaling

Adjust worker count based on system resources and load:

```python
import psutil
import os
from opero import opmap

def get_optimal_worker_count(task_type: str, item_count: int):
    """Calculate optimal worker count based on system resources."""
    cpu_count = os.cpu_count()
    memory_gb = psutil.virtual_memory().total / (1024**3)
    load_avg = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
    
    if task_type == "cpu_bound":
        # CPU-bound: use fewer workers if system is busy
        base_workers = max(1, cpu_count - 1)
        if load_avg > cpu_count * 0.8:
            return max(1, base_workers // 2)
        return base_workers
    
    elif task_type == "io_bound":
        # I/O-bound: can use more workers, limited by memory
        max_workers = min(100, int(memory_gb * 10))  # 10 workers per GB
        return min(max_workers, max(10, item_count // 10))
    
    elif task_type == "network":
        # Network: balance between concurrency and rate limits
        return min(50, max(10, item_count // 20))
    
    return 10  # Default

class AdaptiveProcessor:
    """Processor that adapts to system conditions."""
    
    def process_batch(self, items: list, task_type: str):
        """Process batch with dynamic worker scaling."""
        
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

# System automatically adapts worker count
cpu_results = processor.process_batch(cpu_items, "cpu_bound")
io_results = processor.process_batch(io_items, "io_bound")
network_results = await processor.process_batch(network_items, "network")
```

## Circuit Breaker Pattern

Implement circuit breaker logic to prevent cascading failures:

```python
import time
from enum import Enum
from typing import Callable, Any
from opero import opero

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreaker:
    """Circuit breaker implementation for resilience."""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        
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
        """Handle successful call."""
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            print("Circuit breaker: Transitioning to CLOSED")
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            print("Circuit breaker: Transitioning to OPEN")

# Global circuit breaker instances
api_circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=30)

def with_circuit_breaker(circuit_breaker: CircuitBreaker):
    """Decorator to add circuit breaker to any function."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            return circuit_breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator

@with_circuit_breaker(api_circuit_breaker)
@opero(retries=2, cache=True, rate_limit=10.0)
def protected_api_call(endpoint: str):
    """API call protected by circuit breaker and Opero resilience."""
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
    # Circuit breaker tracks failures and can reject future calls
```

## Advanced Error Recovery

### Retry with Exponential Backoff + Jitter

Implement sophisticated retry strategies:

```python
import random
import time
from opero import opero

def jittered_backoff(attempt: int, base_delay: float = 0.1, max_delay: float = 30.0, jitter: bool = True):
    """Calculate delay with exponential backoff and jitter."""
    delay = min(max_delay, base_delay * (2 ** attempt))
    
    if jitter:
        # Add random jitter to avoid thundering herd
        delay = delay * (0.5 + random.random() * 0.5)
    
    return delay

class AdvancedRetryStrategy:
    """Advanced retry strategy with custom logic."""
    
    def __init__(self, max_retries: int = 5, base_delay: float = 0.1):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.attempt_count = 0
    
    def should_retry(self, exception: Exception) -> bool:
        """Determine if we should retry based on exception type and attempt count."""
        if self.attempt_count >= self.max_retries:
            return False
        
        # Different retry logic for different error types
        if isinstance(exception, (ConnectionError, TimeoutError)):
            return True  # Always retry network errors
        elif isinstance(exception, requests.HTTPError):
            # Retry server errors, not client errors
            if hasattr(exception, 'response') and exception.response:
                return 500 <= exception.response.status_code < 600
        elif "rate limit" in str(exception).lower():
            return True  # Retry rate limit errors
        
        return False
    
    def get_delay(self) -> float:
        """Get delay for current attempt."""
        return jittered_backoff(self.attempt_count, self.base_delay)
    
    def execute_with_retry(self, func, *args, **kwargs):
        """Execute function with advanced retry strategy."""
        self.attempt_count = 0
        last_exception = None
        
        while self.attempt_count <= self.max_retries:
            try:
                if self.attempt_count > 0:
                    delay = self.get_delay()
                    print(f"Retrying in {delay:.2f}s (attempt {self.attempt_count + 1})")
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

# Usage with custom retry strategy
retry_strategy = AdvancedRetryStrategy(max_retries=5, base_delay=0.2)

def resilient_operation(data):
    """Operation with advanced retry strategy."""
    return retry_strategy.execute_with_retry(risky_operation, data)

# Can also combine with Opero decorators
@opero(cache=True, rate_limit=5.0)
def cached_resilient_operation(data):
    return resilient_operation(data)
```

## Monitoring and Observability

### Comprehensive Metrics Collection

Implement detailed metrics for your resilient functions:

```python
import time
from collections import defaultdict, Counter
from functools import wraps
from opero import opero

class OperationMetrics:
    """Collect and track metrics for resilient operations."""
    
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
        """Get metrics summary for a function or all functions."""
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
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            summary[func] = {
                "calls": calls,
                "success_rate": successes / calls if calls > 0 else 0,
                "failure_rate": failures / calls if calls > 0 else 0,
                "retry_rate": retries / calls if calls > 0 else 0,
                "cache_hit_rate": cache_hits / (cache_hits + cache_misses) if (cache_hits + cache_misses) > 0 else 0,
                "avg_response_time": avg_response_time,
                "total_retries": retries
            }
        
        return summary

# Global metrics instance
metrics = OperationMetrics()

def with_metrics(func):
    """Decorator to add metrics collection to any function."""
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

# Usage with metrics
@with_metrics
@opero(retries=3, cache=True, rate_limit=10.0)
def monitored_api_call(endpoint: str):
    """API call with comprehensive metrics collection."""
    response = requests.get(f"https://api.com/{endpoint}")
    response.raise_for_status()
    return response.json()

# Monitor metrics periodically
def print_metrics_report():
    """Print comprehensive metrics report."""
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

# Schedule periodic reporting
import threading
def periodic_metrics_report():
    while True:
        time.sleep(300)  # Report every 5 minutes
        print_metrics_report()

metrics_thread = threading.Thread(target=periodic_metrics_report, daemon=True)
metrics_thread.start()
```

## Next Steps

You've now mastered Opero's advanced features! Continue with:

1. **[Best Practices](best-practices.md)** - Production-ready patterns and strategies
2. **[API Reference](../api/overview.md)** - Complete technical documentation
3. **[Core Components](../api/core.md)** - Deep dive into implementation details

## Advanced Patterns Quick Reference

```python
# Multi-parameter fallbacks
def complex_fallback_strategy(primary_config, fallback_configs): pass

# Multi-level caching
@opero(cache=True, cache_key=custom_key_func)
def multi_level_cached(): pass

# Circuit breaker pattern
@with_circuit_breaker(circuit_breaker)
@opero(retries=3)
def protected_function(): pass

# Advanced retry strategies
retry_strategy = AdvancedRetryStrategy(max_retries=5)
def custom_retry_function(): pass

# Comprehensive metrics
@with_metrics
@opero(retries=3, cache=True)
def monitored_function(): pass

# Dynamic worker scaling
worker_count = get_optimal_worker_count("cpu_bound", len(items))
@opmap(mode="process", workers=worker_count)
def adaptive_processor(): pass
```