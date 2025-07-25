# Configuration Guide

This guide covers all configuration options available in Opero's decorators.

## @opero Decorator Configuration

The `@opero` decorator adds resilience mechanisms to individual function calls.

### Basic Parameters

```python
from opero import opero

@opero(
    # Retry configuration
    retries=3,                    # Number of retry attempts (default: 3)
    backoff_factor=1.5,           # Exponential backoff multiplier (default: 1.5)
    min_delay=0.1,                # Minimum retry delay in seconds (default: 0.1)
    max_delay=30.0,               # Maximum retry delay in seconds (default: 30.0)
    retry_on=(Exception,),        # Exceptions that trigger retries
    
    # Fallback configuration
    arg_fallback="config",        # Parameter name containing fallback values
    
    # Caching configuration
    cache=True,                   # Enable caching (default: False)
    cache_ttl=3600,              # Cache TTL in seconds (default: None - no expiry)
    cache_key=None,              # Custom cache key function
    cache_namespace="opero",     # Cache namespace
    
    # Rate limiting
    rate_limit=10.0,             # Max calls per second (default: None - no limit)
)
def my_function(data, config=["primary", "backup"]):
    pass
```

### Advanced Retry Configuration

Control retry behavior with fine-grained settings:

```python
@opero(
    retries=5,
    backoff_factor=2.0,
    min_delay=0.5,
    max_delay=60.0,
    retry_on=(ConnectionError, TimeoutError),  # Only retry network errors
)
def fetch_data(url):
    # Retries with delays: 0.5s, 1s, 2s, 4s, 8s (capped at max_delay)
    pass
```

### Custom Cache Configuration

Configure caching behavior and backends:

```python
def custom_cache_key(func, *args, **kwargs):
    # Create custom cache key based on function arguments
    return f"{func.__name__}:{args[0].id}"

@opero(
    cache=True,
    cache_ttl=1800,              # 30 minutes
    cache_key=custom_cache_key,
    cache_namespace="api_cache",
    cache_backend="memory",      # Options: "memory", "disk", "redis"
)
def get_user_profile(user):
    pass
```

### Parameter Fallbacks

The `arg_fallback` parameter enables automatic failover:

```python
@opero(
    arg_fallback="api_key",  # Must match parameter name
    retries=2,
)
def api_call(endpoint, api_key=["key1", "key2", "key3"]):
    # If call fails with key1, automatically retries with key2, then key3
    current_key = api_key[0]  # Opero manages the iteration
    return f"Called {endpoint} with {current_key}"
```

## @opmap Decorator Configuration

The `@opmap` decorator adds parallel processing on top of all `@opero` features.

### Basic Parallel Configuration

```python
from opero import opmap

@opmap(
    # Parallel processing settings
    mode="thread",               # Concurrency mode: "thread", "process", "async", "async_process"
    workers=4,                   # Number of parallel workers (default: 4)
    ordered=True,                # Preserve input order in results (default: True)
    progress=True,               # Show progress bar if available (default: True)
    
    # All @opero parameters are also supported
    retries=3,
    cache=True,
    rate_limit=5.0,
)
def process_item(item):
    pass
```

### Concurrency Modes Explained

Choose the right mode for your workload:

```python
# I/O-bound tasks (network requests, file operations)
@opmap(mode="thread", workers=10)
def download_file(url):
    pass

# CPU-bound tasks (computation, data processing)
@opmap(mode="process", workers=4)
def compute_hash(data):
    pass

# Async I/O operations
@opmap(mode="async", workers=20)
async def fetch_async(url):
    pass

# CPU-intensive async operations
@opmap(mode="async_process", workers=4)
async def process_async(data):
    pass
```

### Advanced Parallel Configuration

```python
@opmap(
    mode="process",
    workers=8,
    ordered=False,              # Don't preserve order (faster)
    progress=True,
    
    # Resilience for each item
    retries=3,
    arg_fallback="server",
    cache=True,
    cache_ttl=600,
    rate_limit=10.0,
)
def distributed_task(
    task_id: int,
    server: list[str] = ["server1.com", "server2.com"]
):
    # Each task gets resilience features
    pass

# Process many items with automatic load balancing
task_ids = range(1000)
results = distributed_task(task_ids)
```

## Environment Variables

Opero respects these environment variables:

```bash
# Cache configuration
OPERO_CACHE_BACKEND=redis
OPERO_CACHE_REDIS_URL=redis://localhost:6379
OPERO_CACHE_DIR=/tmp/opero_cache

# Logging
OPERO_LOG_LEVEL=INFO
OPERO_LOG_FORMAT=json

# Performance
OPERO_MAX_WORKERS=16
OPERO_DEFAULT_TIMEOUT=30
```

## Cache Backend Configuration

### Memory Cache (Default)

```python
@opero(
    cache=True,
    cache_backend="memory",
    cache_max_size=1000,  # Maximum items in cache
)
def cached_function():
    pass
```

### Disk Cache

```python
@opero(
    cache=True,
    cache_backend="disk",
    cache_dir="/tmp/opero_cache",
    cache_ttl=86400,  # 24 hours
)
def expensive_computation():
    pass
```

### Redis Cache

```python
@opero(
    cache=True,
    cache_backend="redis",
    cache_redis_url="redis://localhost:6379",
    cache_redis_db=0,
    cache_ttl=3600,
)
def distributed_function():
    pass
```

## Logging Configuration

Enable detailed logging to debug issues:

```python
import logging
from opero.utils import configure_logging

# Basic configuration
logger = configure_logging(level=logging.INFO)

# Custom configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('opero.log'),
        logging.StreamHandler()
    ]
)

# Now Opero will log detailed information about:
# - Retry attempts
# - Cache hits/misses
# - Rate limiting delays
# - Fallback attempts
# - Worker pool status
```

## Configuration Best Practices

### 1. Start Simple

Begin with basic configuration and add features as needed:

```python
# Start here
@opero(retries=3, cache=True)
def my_function():
    pass

# Add more as requirements grow
@opero(
    retries=3,
    cache=True,
    cache_ttl=300,
    rate_limit=10.0,
    arg_fallback="endpoint"
)
def my_enhanced_function(endpoint=["primary", "backup"]):
    pass
```

### 2. Choose Appropriate Timeouts

Balance reliability with responsiveness:

```python
@opero(
    retries=3,
    min_delay=0.1,      # Quick first retry
    max_delay=10.0,     # Don't wait too long
    backoff_factor=2.0,  # Reasonable progression
)
def time_sensitive_operation():
    pass
```

### 3. Use Specific Exception Types

Only retry exceptions you expect to be transient:

```python
@opero(
    retry_on=(
        ConnectionError,
        requests.Timeout,
        requests.HTTPError,
    ),
    # Don't retry on ValueError, TypeError, etc.
)
def network_operation():
    pass
```

### 4. Configure Cache Wisely

Match cache TTL to your data freshness requirements:

```python
# Frequently changing data
@opero(cache=True, cache_ttl=60)  # 1 minute
def get_stock_price(symbol):
    pass

# Stable data
@opero(cache=True, cache_ttl=86400)  # 24 hours
def get_company_info(company_id):
    pass

# Immutable data
@opero(cache=True)  # No TTL
def calculate_hash(data):
    pass
```

### 5. Scale Workers Appropriately

```python
import os

# Scale based on workload type
@opmap(
    mode="thread",
    workers=20,  # High for I/O-bound
)
def io_task(item):
    pass

@opmap(
    mode="process",
    workers=os.cpu_count(),  # Match CPU cores
)
def cpu_task(item):
    pass
```

## Configuration Examples

### Web Scraping Configuration

```python
@opmap(
    mode="thread",
    workers=10,
    ordered=False,
    retries=3,
    backoff_factor=2.0,
    rate_limit=2.0,  # Respect robots.txt
    cache=True,
    cache_ttl=3600,
    arg_fallback="user_agent",
)
def scrape_page(
    url: str,
    user_agent: list[str] = [
        "Mozilla/5.0 (Bot 1.0)",
        "Mozilla/5.0 (Bot 2.0)",
    ]
):
    pass
```

### API Integration Configuration

```python
@opero(
    retries=5,
    retry_on=(requests.HTTPError,),
    backoff_factor=2.0,
    max_delay=60.0,
    rate_limit=100.0,  # API rate limit
    cache=True,
    cache_ttl=300,
    arg_fallback="api_key",
)
def call_external_api(
    endpoint: str,
    api_key: list[str] = ["primary_key", "secondary_key"]
):
    pass
```

### Data Processing Configuration

```python
@opmap(
    mode="process",
    workers=8,
    ordered=True,
    retries=2,
    cache=True,
    cache_backend="disk",  # Persist results
    cache_dir="./processing_cache",
)
def process_data_chunk(chunk):
    pass
```

## Next Steps

- Learn about [Basic Usage](../guide/basic-usage.md) patterns
- Explore [Advanced Features](../guide/advanced-features.md)
- Read [Best Practices](../guide/best-practices.md) for production use