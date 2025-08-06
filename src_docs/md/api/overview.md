# API Overview

Complete reference for Opero's API, including all decorators, functions, exceptions, and utilities.

## Architecture Overview

Opero is built on a modular architecture that provides resilience through composable decorators:

```mermaid
graph TB
    A[User Function] --> B[@opero Decorator]
    A --> C[@opmap Decorator]
    
    B --> D[Cache Layer]
    B --> E[Rate Limit Layer] 
    B --> F[Retry Layer]
    B --> G[Fallback Layer]
    
    C --> H[Parallel Engine]
    C --> I[Per-Item Resilience]
    
    D --> J[Cache Backends]
    E --> K[Rate Limiters]
    F --> L[Retry Strategies]
    G --> M[Fallback Logic]
    
    H --> N[Thread Pool]
    H --> O[Process Pool]
    H --> P[Async Pool]
```

## Core Decorators

### `@opero` - Single Function Resilience

The primary decorator for adding resilience to individual functions.

```python
from opero import opero

@opero(
    retries: int = 3,
    backoff_factor: float = 1.5,
    min_delay: float = 0.1,
    max_delay: float = 30.0,
    cache: bool = False,
    cache_ttl: Optional[int] = None,
    cache_backend: str = "memory",
    cache_key: Optional[Callable] = None,
    cache_namespace: str = "opero",
    rate_limit: Optional[float] = None,
    arg_fallback: Optional[str] = None,
    retry_on: Union[Exception, Tuple[Exception, ...]] = Exception
)
def your_function():
    pass
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `retries` | `int` | `3` | Number of retry attempts |
| `backoff_factor` | `float` | `1.5` | Exponential backoff multiplier |
| `min_delay` | `float` | `0.1` | Minimum delay between retries (seconds) |
| `max_delay` | `float` | `30.0` | Maximum delay between retries (seconds) |
| `cache` | `bool` | `False` | Enable result caching |
| `cache_ttl` | `Optional[int]` | `None` | Cache time-to-live (seconds) |
| `cache_backend` | `str` | `"memory"` | Cache backend type |
| `cache_key` | `Optional[Callable]` | `None` | Custom cache key function |
| `cache_namespace` | `str` | `"opero"` | Cache namespace |
| `rate_limit` | `Optional[float]` | `None` | Maximum calls per second |
| `arg_fallback` | `Optional[str]` | `None` | Parameter name for fallback values |
| `retry_on` | `Union[Exception, Tuple[Exception, ...]]` | `Exception` | Exceptions that trigger retries |

### `@opmap` - Parallel Processing with Resilience

Decorator for parallel processing of multiple items with per-item resilience.

```python
from opero import opmap

@opmap(
    mode: str = "thread",
    workers: int = 4,
    ordered: bool = True,
    progress: bool = True,
    timeout: Optional[float] = None,
    chunk_size: Optional[int] = None,
    # All @opero parameters are also available
    retries: int = 3,
    cache: bool = False,
    rate_limit: Optional[float] = None,
    # ... etc
)
def process_single_item(item):
    pass

# Call with multiple items
results = process_single_item([item1, item2, item3, ...])
```

**Additional Parameters (beyond @opero):**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mode` | `str` | `"thread"` | Parallelization mode: `"thread"`, `"process"`, `"async"`, `"async_process"` |
| `workers` | `int` | `4` | Number of parallel workers |
| `ordered` | `bool` | `True` | Preserve input order in results |
| `progress` | `bool` | `True` | Show progress bar |
| `timeout` | `Optional[float]` | `None` | Timeout per item (seconds) |
| `chunk_size` | `Optional[int]` | `None` | Items per worker batch |

## Exception Classes

### `OperoError`

Base exception class for all Opero-related errors.

```python
from opero.exceptions import OperoError

class OperoError(RuntimeError):
    """Base exception for Opero-related errors."""
    pass
```

### `AllFailedError`

Raised when all retry attempts and fallbacks have been exhausted.

```python
from opero.exceptions import AllFailedError

class AllFailedError(OperoError):
    """Raised when all retry attempts and fallbacks fail."""
    
    def __init__(self, message: str, errors: List[Exception]):
        super().__init__(message)
        self.errors = errors  # List of all failed attempts
```

**Usage:**

```python
from opero import opero, AllFailedError

@opero(retries=3)
def might_fail():
    raise ConnectionError("Connection failed")

try:
    result = might_fail()
except AllFailedError as e:
    print(f"All {len(e.errors)} attempts failed:")
    for i, error in enumerate(e.errors, 1):
        print(f"  Attempt {i}: {error}")
```

## Cache Backends

### Built-in Cache Backends

Opero supports multiple cache backends through the `twat-cache` library:

| Backend | Description | Use Case |
|---------|-------------|----------|
| `"memory"` | In-memory cache (default) | Fast access, single process |
| `"disk"` | Disk-based cache | Persistent across restarts |
| `"redis"` | Redis backend | Shared across processes/instances |
| `"sqlite"` | SQLite-based cache | Persistent, embedded database |

### Cache Configuration

```python
# Memory cache (default)
@opero(cache=True, cache_backend="memory")
def memory_cached_function():
    pass

# Disk cache with custom path
@opero(
    cache=True, 
    cache_backend="disk",
    cache_backend_config={"cache_dir": "/tmp/opero_cache"}
)
def disk_cached_function():
    pass

# Redis cache
@opero(
    cache=True,
    cache_backend="redis", 
    cache_backend_config={
        "host": "localhost",
        "port": 6379,
        "db": 0,
        "password": "optional_password"
    }
)
def redis_cached_function():
    pass
```

### Custom Cache Keys

Define custom cache key generation:

```python
def custom_cache_key(*args, **kwargs):
    """Generate custom cache key."""
    # Only include specific arguments in cache key
    return f"my_func_{args[0]}_{kwargs.get('important_param', 'default')}"

@opero(
    cache=True,
    cache_key=custom_cache_key,
    cache_namespace="my_app"
)
def function_with_custom_key(arg1, arg2, important_param=None, ignore_this=None):
    # ignore_this parameter won't affect caching
    return f"result for {arg1}, {important_param}"
```

## Parallelization Modes

### Thread Mode (`mode="thread"`)

Best for I/O-bound tasks like API calls, file operations, database queries.

```python
@opmap(mode="thread", workers=20)
def io_bound_task(item):
    # Network request, file I/O, etc.
    response = requests.get(f"https://api.com/{item}")
    return response.json()
```

**Characteristics:**
- Shared memory space
- Good for I/O-bound operations
- Limited by GIL for CPU-bound tasks
- Fast startup time
- Efficient for many concurrent operations

### Process Mode (`mode="process"`)

Best for CPU-bound tasks like calculations, data processing, image manipulation.

```python
@opmap(mode="process", workers=8)  # Usually = CPU cores
def cpu_bound_task(item):
    # CPU-intensive computation
    return complex_calculation(item)
```

**Characteristics:**
- Separate memory spaces
- No GIL limitations
- Good for CPU-bound operations
- Higher startup overhead
- Objects must be picklable

### Async Mode (`mode="async"`)

Best for async I/O operations with high concurrency needs.

```python
@opmap(mode="async", workers=100)
async def async_io_task(item):
    # Async network operations
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.com/{item}") as response:
            return await response.json()
```

**Characteristics:**
- Single-threaded, event-driven
- Very high concurrency
- Excellent for I/O-bound async operations
- Low memory overhead
- Requires async functions

### Async Process Mode (`mode="async_process"`)

Combines async and multiprocessing for async functions needing CPU isolation.

```python
@opmap(mode="async_process", workers=4)
async def async_cpu_task(item):
    # Async function that also needs CPU isolation
    await asyncio.sleep(0.1)  # Async I/O
    return cpu_intensive_operation(item)  # CPU work
```

**Characteristics:**
- Async functions in separate processes
- Good for mixed I/O + CPU workloads
- Requires `opero[aiomultiprocess]`
- Higher complexity and overhead

## Retry Mechanisms

### Retry Strategies

Opero uses exponential backoff with jitter for retry delays:

```python
delay = min(max_delay, min_delay * (backoff_factor ** attempt_number))
```

### Retry Configuration Examples

```python
# Conservative retry strategy
@opero(
    retries=2,
    backoff_factor=1.2,
    min_delay=0.5,
    max_delay=10.0
)
def conservative_function():
    pass

# Aggressive retry strategy
@opero(
    retries=10,
    backoff_factor=2.0,
    min_delay=0.1,
    max_delay=60.0
)
def aggressive_function():
    pass

# Selective retry - only retry specific errors
@opero(
    retries=5,
    retry_on=(ConnectionError, TimeoutError, requests.HTTPError)
)
def selective_retry_function():
    pass
```

### Retry Decision Logic

The retry mechanism considers:
1. Number of attempts remaining
2. Exception type (must match `retry_on`)
3. Backoff delay calculation
4. Maximum delay limits

## Rate Limiting

### Rate Limiting Scopes

Control how rate limits are applied:

```python
# Per-function rate limiting (default)
@opero(rate_limit=10.0, rate_limit_scope="per_function")
def function1():
    pass

@opero(rate_limit=5.0, rate_limit_scope="per_function") 
def function2():
    pass  # Independent 5/sec limit

# Global rate limiting - shared across functions
@opero(rate_limit=10.0, rate_limit_scope="global")
def function3():
    pass

@opero(rate_limit=10.0, rate_limit_scope="global")
def function4():
    pass  # Shares the 10/sec limit with function3

# Per-argument rate limiting
@opero(rate_limit=5.0, rate_limit_scope="per_args")
def function5(api_endpoint):
    pass  # 5/sec limit per unique api_endpoint value
```

## Fallback Mechanisms

### Parameter-Based Fallbacks

Automatically try alternative parameter values on failure:

```python
@opero(
    retries=2,
    arg_fallback="api_key",  # Parameter name to cycle through
    fallback_delay=0.5       # Optional delay between fallback attempts
)
def api_call_with_fallback(data: dict, api_key: list[str]):
    # Opero automatically uses api_key[0], then api_key[1], etc.
    current_key = api_key[0]
    headers = {"Authorization": f"Bearer {current_key}"}
    response = requests.post("https://api.com/data", json=data, headers=headers)
    response.raise_for_status()
    return response.json()

# Usage
result = api_call_with_fallback(
    {"key": "value"},
    api_key=["primary_key", "backup_key", "emergency_key"]
)
```

### Fallback Execution Order

1. Try with first value in fallback parameter list
2. If fails, try with second value (for same retry attempt)
3. Continue through all fallback values
4. If all fallback values fail, that counts as one retry attempt
5. Repeat the entire process for subsequent retry attempts

## Utility Functions

### Logging Configuration

```python
from opero.utils import configure_logging
import logging

# Configure Opero's internal logging
logger = configure_logging(level=logging.INFO)

# Available log levels and their typical output:
# DEBUG: Detailed internal operations, cache operations
# INFO: Function calls, retry attempts, fallback usage
# WARNING: Rate limiting actions, cache misses
# ERROR: Failed attempts, configuration issues
```

### Async Utilities

```python
from opero.utils.async_utils import ensure_async, run_async

# Convert sync function to async
async_func = ensure_async(sync_function)
result = await async_func(args)

# Run async function in sync context
result = run_async(async_function(args))
```

## Type Hints and Generics

Opero includes comprehensive type hints for better IDE support:

```python
from typing import TypeVar, Awaitable, Union, List, Callable
from opero import opero, opmap

T = TypeVar('T')
R = TypeVar('R')

# Function type annotations
@opero(retries=3)
def typed_function(input_data: T) -> R:
    return process_data(input_data)

# Async function type annotations  
@opero(retries=3)
async def async_typed_function(input_data: T) -> R:
    return await async_process_data(input_data)

# Parallel processing type annotations
@opmap(mode="thread", workers=10)
def parallel_typed_function(item: T) -> R:
    return process_single_item(item)

# Usage with type checking
items: List[str] = ["item1", "item2", "item3"]
results: List[str] = parallel_typed_function(items)
```

## Configuration Validation

Opero validates configuration parameters and provides helpful error messages:

```python
# Invalid configuration examples that will raise errors:

@opero(retries=-1)  # Error: retries must be non-negative
def invalid_retries():
    pass

@opero(rate_limit=0)  # Error: rate_limit must be positive
def invalid_rate_limit():
    pass

@opero(arg_fallback="nonexistent_param")  # Error: parameter not found
def invalid_fallback(existing_param: str):
    pass

@opmap(mode="invalid_mode")  # Error: unknown parallelization mode
def invalid_mode():
    pass
```

## Performance Considerations

### Memory Usage

- **Memory cache**: Stores results in memory, fast but limited by RAM
- **Process mode**: Each worker process has separate memory space
- **Thread mode**: Shared memory space, more memory efficient
- **Async mode**: Single process, lowest memory usage

### CPU Usage

- **Process mode**: Can utilize multiple CPU cores effectively
- **Thread mode**: Limited by Python's GIL for CPU-bound tasks
- **Async mode**: Single-threaded, good for I/O-bound tasks

### Network/I/O

- **Rate limiting**: Prevents overwhelming external services
- **Connection pooling**: Reuse connections when possible
- **Timeout handling**: Set appropriate timeouts for network operations

## Integration Points

### Framework Integration

Opero works seamlessly with popular Python frameworks:

```python
# FastAPI integration
from fastapi import FastAPI
from opero import opero

app = FastAPI()

@app.get("/users/{user_id}")
@opero(retries=3, cache=True, cache_ttl=300)
async def get_user(user_id: str):
    return await fetch_user_data(user_id)

# Django integration
from django.http import JsonResponse
from opero import opero

@opero(retries=3, cache=True)
def django_view(request):
    data = expensive_operation(request.GET.get('param'))
    return JsonResponse(data)

# Flask integration
from flask import Flask, jsonify
from opero import opero

app = Flask(__name__)

@app.route('/api/data')
@opero(retries=3, cache=True)
def flask_endpoint():
    return jsonify(fetch_data())
```

### Database Integration

```python
# SQLAlchemy integration
from sqlalchemy.orm import Session
from opero import opero

@opero(
    retries=3,
    retry_on=(sqlalchemy.exc.DisconnectionError, sqlalchemy.exc.TimeoutError),
    cache=False  # Don't cache database writes
)
def database_operation(session: Session, data: dict):
    return session.execute(query, data)

# Redis integration
import redis
from opero import opero

@opero(
    retries=5,
    retry_on=(redis.ConnectionError, redis.TimeoutError),
    backoff_factor=2.0
)
def redis_operation(r: redis.Redis, key: str, value: str):
    return r.set(key, value)
```

## Next Steps

Now that you understand Opero's API:

1. **[Core Components](core.md)** - Detailed implementation documentation
2. **[Utilities](utils.md)** - Helper functions and troubleshooting
3. **[Best Practices](../guide/best-practices.md)** - Production patterns and strategies

## API Quick Reference

### Essential Imports

```python
# Core functionality
from opero import opero, opmap

# Exceptions
from opero import AllFailedError, OperoError

# Utilities
from opero import configure_logging
```

### Common Patterns

```python
# Basic resilience
@opero(retries=3, cache=True)
def basic_function(): pass

# API integration
@opero(retries=3, rate_limit=10.0, arg_fallback="api_key")
def api_function(data, api_key: list[str]): pass

# Batch processing
@opmap(mode="thread", workers=10, retries=2)
def batch_processor(item): pass

# High-performance async
@opmap(mode="async", workers=50, ordered=False)
async def async_processor(item): pass
```