# API Overview

This section provides comprehensive documentation of Opero's API, including all decorators, functions, classes, and configuration options.

## Core Decorators

Opero provides two main decorators that form the foundation of the library:

### @opero

The primary decorator that adds resilience mechanisms to individual function calls.

```python
from opero import opero

@opero(
    retries=3,
    cache=True,
    rate_limit=10.0,
    arg_fallback="config"
)
def resilient_function(data, config=["primary", "backup"]):
    pass
```

[Full documentation →](core.md#opero-decorator)

### @opmap

Extends `@opero` with parallel processing capabilities for handling multiple items.

```python
from opero import opmap

@opmap(
    mode="thread",
    workers=10,
    retries=2,
    cache=True
)
def process_item(item):
    pass

# Process many items in parallel
results = process_item(items_list)
```

[Full documentation →](core.md#opmap-decorator)

## Core Components

### Resilience Mechanisms

| Component | Description | Key Parameters |
|-----------|-------------|----------------|
| **Retry** | Automatic retry with backoff | `retries`, `backoff_factor`, `retry_on` |
| **Cache** | Result caching | `cache`, `cache_ttl`, `cache_backend` |
| **Rate Limiting** | Request rate control | `rate_limit` |
| **Fallback** | Parameter-based fallbacks | `arg_fallback` |

### Parallel Processing

| Mode | Description | Best For |
|------|-------------|----------|
| `thread` | ThreadPoolExecutor | I/O-bound tasks |
| `process` | ProcessPoolExecutor | CPU-bound tasks |
| `async` | AsyncIO concurrency | Async I/O operations |
| `async_process` | Async in processes | CPU + async I/O |

## Exception Hierarchy

```
OperoError
├── AllFailedError     # All retries and fallbacks exhausted
├── ConfigurationError # Invalid configuration (planned)
└── ConcurrencyError   # Parallel processing issues (planned)
```

## Utility Functions

### Logging Configuration

```python
from opero.utils import configure_logging

logger = configure_logging(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Cache Management

```python
from opero import clear_cache

# Clear all cached results
clear_cache()

# Clear specific namespace
clear_cache(namespace="api_cache")
```

## Type Annotations

Opero is fully type-annotated for better IDE support and type checking:

```python
from typing import TypeVar, Callable, Any
from opero import opero

T = TypeVar('T')

def opero(
    retries: int = 3,
    backoff_factor: float = 1.5,
    cache: bool = False,
    cache_ttl: int | None = None,
    rate_limit: float | None = None,
    arg_fallback: str | None = None,
    **kwargs: Any
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    ...
```

## Configuration Reference

### Common Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `retries` | `int` | `3` | Number of retry attempts |
| `backoff_factor` | `float` | `1.5` | Exponential backoff multiplier |
| `min_delay` | `float` | `0.1` | Minimum retry delay (seconds) |
| `max_delay` | `float` | `30.0` | Maximum retry delay (seconds) |
| `retry_on` | `tuple[Exception, ...]` | `(Exception,)` | Exceptions to retry |
| `cache` | `bool` | `False` | Enable caching |
| `cache_ttl` | `int \| None` | `None` | Cache TTL in seconds |
| `cache_backend` | `str` | `"memory"` | Cache backend type |
| `rate_limit` | `float \| None` | `None` | Max calls per second |
| `arg_fallback` | `str \| None` | `None` | Parameter name for fallbacks |

### @opmap Additional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mode` | `str` | `"process"` | Concurrency mode |
| `workers` | `int` | `4` | Number of workers |
| `ordered` | `bool` | `True` | Preserve input order |
| `progress` | `bool` | `True` | Show progress bar |

## Advanced Features

### Custom Cache Keys

```python
def custom_key(func, *args, **kwargs):
    return f"{func.__name__}:{args[0]}"

@opero(cache=True, cache_key=custom_key)
def cached_function(id: str):
    pass
```

### Event Callbacks

```python
@opero(
    retries=3,
    on_retry=lambda e, attempt: print(f"Retry {attempt}: {e}"),
    on_success=lambda result: print(f"Success: {result}"),
    on_failure=lambda e: print(f"Failed: {e}"),
    on_cache_hit=lambda: print("Cache hit!")
)
def monitored_function():
    pass
```

## Integration Examples

### FastAPI Integration

```python
from fastapi import FastAPI, HTTPException
from opero import opero

app = FastAPI()

@app.get("/users/{user_id}")
@opero(retries=3, cache=True, cache_ttl=300)
async def get_user(user_id: int):
    try:
        return await fetch_user_from_db(user_id)
    except AllFailedError:
        raise HTTPException(status_code=503, detail="Service unavailable")
```

### Celery Integration

```python
from celery import Celery
from opero import opero

app = Celery('tasks')

@app.task
@opero(retries=5, backoff_factor=2.0)
def process_task(data):
    return expensive_operation(data)
```

## Performance Considerations

1. **Decorator Overhead**: ~0.1ms per call without features enabled
2. **Cache Lookup**: O(1) for memory cache, network latency for Redis
3. **Rate Limiting**: Minimal overhead, uses async primitives
4. **Parallel Processing**: Overhead depends on worker pool creation

## Version Compatibility

| Opero Version | Python Version | Key Features |
|---------------|----------------|--------------|
| 0.2.x | 3.10+ | Current stable |
| 0.1.x | 3.8+ | Legacy support |

## Next Steps

- Explore [Core API](core.md) for detailed decorator documentation
- Check [Utilities API](utils.md) for helper functions
- See [Examples](../examples/) for real-world usage patterns