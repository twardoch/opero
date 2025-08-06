# Basic Usage

Master Opero's core concepts and patterns through practical examples. This guide covers everything you need to know to use Opero effectively in your applications.

## Understanding Opero's Architecture

Opero works by wrapping your functions with layers of resilience mechanisms. Here's how it works:

```mermaid
graph LR
    A[Function Call] --> B[Cache Check]
    B --> C{Cache Hit?}
    C -->|Yes| D[Return Cached Result]
    C -->|No| E[Rate Limiting]
    E --> F[Retry Logic]
    F --> G[Fallback Logic]
    G --> H[Your Function]
    H --> I[Cache Result]
    I --> J[Return Result]
```

Each layer is optional and configurable, giving you precise control over your function's behavior.

## The `@opero` Decorator

The `@opero` decorator is your primary tool for adding resilience to individual functions.

### Basic Syntax

```python
from opero import opero

@opero(parameter=value, ...)
def your_function(args):
    # Your function implementation
    pass
```

### Essential Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `retries` | `int` | `3` | Number of retry attempts |
| `cache` | `bool` | `False` | Enable result caching |
| `rate_limit` | `float` | `None` | Max calls per second |
| `arg_fallback` | `str` | `None` | Parameter name for fallbacks |

### Comprehensive Example

```python
import asyncio
import aiohttp
from opero import opero, AllFailedError

@opero(
    retries=3,                    # Retry up to 3 times
    backoff_factor=1.5,           # Exponential backoff
    min_delay=0.1,                # Minimum delay between retries
    max_delay=30.0,               # Maximum delay between retries
    cache=True,                   # Enable caching
    cache_ttl=300,                # Cache for 5 minutes
    rate_limit=10.0,              # Max 10 calls per second
    arg_fallback="api_key",       # Try different API keys
    retry_on=(aiohttp.ClientError, asyncio.TimeoutError)  # Retry these errors
)
async def fetch_user_profile(user_id: str, api_key: list[str]):
    """Fetch user profile with comprehensive resilience."""
    current_key = api_key[0]  # Opero manages the fallback
    
    headers = {"Authorization": f"Bearer {current_key}"}
    timeout = aiohttp.ClientTimeout(total=10)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        url = f"https://api.example.com/users/{user_id}"
        async with session.get(url, headers=headers) as response:
            response.raise_for_status()
            return await response.json()

# Usage
async def main():
    api_keys = ["primary_key", "backup_key", "emergency_key"]
    
    try:
        profile = await fetch_user_profile("user123", api_key=api_keys)
        print(f"User profile: {profile}")
    except AllFailedError as e:
        print(f"All attempts failed after {len(e.errors)} tries")
        for i, error in enumerate(e.errors, 1):
            print(f"  Attempt {i}: {error}")

asyncio.run(main())
```

## The `@opmap` Decorator

The `@opmap` decorator applies resilience to functions that process single items, then parallelizes them across many items.

### Basic Concept

```python
# Think of it this way:
# 1. Take a function that processes ONE item
# 2. Make it resilient with @opmap
# 3. Pass it MANY items 
# 4. Get back results for ALL items

from opero import opmap

@opmap(mode="thread", workers=5)
def process_single_item(item):
    # This function handles ONE item
    return expensive_operation(item)

# But you call it with MANY items
items = ["item1", "item2", "item3", ..., "item100"]
results = process_single_item(items)  # Processes all 100 in parallel
```

### Parallelization Modes

Choose the right mode for your workload:

```python
# I/O-bound tasks (API calls, file operations)
@opmap(mode="thread", workers=20)
def io_bound_task(item):
    response = requests.get(f"https://api.com/{item}")
    return response.json()

# CPU-bound tasks (calculations, data processing)
@opmap(mode="process", workers=8)  # Usually number of CPU cores
def cpu_bound_task(item):
    return complex_calculation(item)

# Async I/O tasks (concurrent network operations)
@opmap(mode="async", workers=100)
async def async_io_task(item):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.com/{item}") as resp:
            return await resp.json()

# Async tasks needing process isolation
@opmap(mode="async_process", workers=4)
async def async_process_task(item):
    # Async function running in separate process
    return await cpu_intensive_async_operation(item)
```

### Complete Example: Web Scraping

```python
import asyncio
import aiohttp
from opero import opmap, AllFailedError
from typing import List, Dict, Any

@opmap(
    mode="async",                 # Async for I/O efficiency
    workers=25,                   # 25 concurrent requests
    retries=3,                    # Retry failed pages
    cache=True,                   # Cache scraped content
    cache_ttl=1800,              # Cache for 30 minutes
    rate_limit=15.0,             # 15 requests per second
    arg_fallback="user_agent",   # Try different user agents
    ordered=True,                # Preserve URL order
    progress=True                # Show progress bar
)
async def scrape_url(url: str, user_agent: List[str] = None) -> Dict[str, Any]:
    """Scrape a single URL with fallback user agents."""
    if user_agent is None:
        user_agent = [
            "Mozilla/5.0 (compatible; OperoBot/1.0)",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        ]
    
    headers = {
        "User-Agent": user_agent[0],
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive"
    }
    
    timeout = aiohttp.ClientTimeout(total=30, connect=10)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, headers=headers) as response:
            # Trigger fallback for blocked requests
            if response.status in [403, 429]:
                raise aiohttp.ClientError(f"Blocked with status {response.status}")
            
            response.raise_for_status()
            content = await response.text()
            
            return {
                "url": url,
                "status": response.status,
                "title": extract_title(content),
                "content_length": len(content),
                "user_agent": user_agent[0],
                "headers": dict(response.headers)
            }

def extract_title(html: str) -> str:
    """Extract title from HTML content."""
    import re
    match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else "No title"

async def main():
    urls = [
        "https://httpbin.org/delay/1",
        "https://httpbin.org/delay/2", 
        "https://httpbin.org/status/200",
        "https://httpbin.org/status/404",  # This will fail
        "https://httpbin.org/user-agent",
    ] * 10  # 50 URLs total
    
    print(f"Scraping {len(urls)} URLs...")
    results = await scrape_url(urls)
    
    # Analyze results
    successful = [r for r in results if not isinstance(r, Exception)]
    failed = [r for r in results if isinstance(r, Exception)]
    
    print(f"\n✅ Successfully scraped: {len(successful)} pages")
    print(f"❌ Failed to scrape: {len(failed)} pages")
    
    # Show some successful results
    for result in successful[:3]:
        print(f"  📄 {result['title']} - {result['url']}")
    
    # Show failures
    for error in failed[:3]:
        if isinstance(error, AllFailedError):
            print(f"  ❌ All attempts failed: {error}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Caching Patterns

Opero's caching system is flexible and powerful. Here are common patterns:

### Basic Caching

```python
@opero(cache=True, cache_ttl=300)  # Cache for 5 minutes
def expensive_calculation(n: int) -> int:
    # This expensive calculation only runs once per input
    time.sleep(1)  # Simulate expensive operation
    return sum(i**2 for i in range(n))

# First call: slow (runs calculation)
result1 = expensive_calculation(1000)  # Takes ~1 second

# Second call: fast (uses cache)
result2 = expensive_calculation(1000)  # Returns instantly
assert result1 == result2
```

### Custom Cache Keys

Control what gets cached:

```python
def cache_key_func(*args, **kwargs):
    """Custom cache key that ignores timestamp parameter."""
    # Only cache based on data, ignore timestamp
    return f"process_data_{kwargs['data']['id']}"

@opero(
    cache=True,
    cache_key=cache_key_func,
    cache_ttl=3600
)
def process_data(data: dict, timestamp: float = None):
    # timestamp changes don't affect cache
    return expensive_operation(data)

# These calls use the same cache entry
result1 = process_data({"id": "123", "value": "test"}, timestamp=1000)
result2 = process_data({"id": "123", "value": "test"}, timestamp=2000)
```

### Cache Backends

Choose the right cache backend:

```python
# Memory cache (default, fastest)
@opero(cache=True, cache_backend="memory")
def memory_cached(): pass

# Disk cache (persistent across runs)
@opero(cache=True, cache_backend="disk", cache_ttl=86400)
def disk_cached(): pass

# Redis cache (shared across instances)
@opero(
    cache=True, 
    cache_backend="redis",
    cache_backend_config={"host": "localhost", "port": 6379, "db": 0}
)
def redis_cached(): pass
```

## Error Handling Patterns

### Understanding AllFailedError

```python
from opero import opero, AllFailedError

@opero(retries=3, arg_fallback="endpoint")
def api_call(data: dict, endpoint: list[str]):
    current_endpoint = endpoint[0]
    response = requests.post(current_endpoint, json=data)
    response.raise_for_status()
    return response.json()

try:
    result = api_call(
        {"key": "value"}, 
        endpoint=["https://api1.com", "https://api2.com", "https://api3.com"]
    )
except AllFailedError as e:
    print(f"All {len(e.errors)} attempts failed:")
    
    # e.errors contains all the failed attempts
    for i, error in enumerate(e.errors, 1):
        print(f"  Attempt {i}: {type(error).__name__}: {error}")
    
    # Get the last error for more details
    last_error = e.errors[-1]
    print(f"Last error was: {last_error}")
```

### Selective Error Handling

Only retry specific errors:

```python
import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError

@opero(
    retries=3,
    retry_on=(ConnectionError, Timeout),  # Only retry these
    # HTTPError will not be retried
)
def selective_retry(url: str):
    response = requests.get(url, timeout=10)
    
    if response.status_code >= 500:
        # Server errors trigger retry
        raise ConnectionError(f"Server error: {response.status_code}")
    elif response.status_code == 404:
        # Client errors don't trigger retry
        raise HTTPError(f"Not found: {url}")
    
    return response.json()

try:
    result = selective_retry("https://api.example.com/data")
except HTTPError:
    print("Resource not found - not retried")
except AllFailedError:
    print("Network issues - retried but failed")
```

### Graceful Degradation

Provide fallbacks for failed operations:

```python
@opero(retries=2, cache=True)
def fetch_user_preferences(user_id: str) -> dict:
    # Try to fetch from API
    response = requests.get(f"https://api.com/users/{user_id}/preferences")
    response.raise_for_status()
    return response.json()

def get_user_preferences(user_id: str) -> dict:
    """Get user preferences with graceful fallback."""
    try:
        return fetch_user_preferences(user_id)
    except AllFailedError:
        # Fall back to default preferences
        print(f"Using default preferences for user {user_id}")
        return {
            "theme": "light",
            "language": "en",
            "notifications": True
        }

# Usage always succeeds
preferences = get_user_preferences("user123")
```

## Rate Limiting Patterns

### API Rate Limiting

Respect API rate limits:

```python
@opero(rate_limit=10.0)  # 10 calls per second
def api_call(endpoint: str):
    return requests.get(f"https://api.com/{endpoint}").json()

# These calls will be automatically spaced out
results = []
for i in range(50):
    result = api_call(f"data/{i}")  # Automatically rate-limited
    results.append(result)
```

### Shared Rate Limits

Multiple functions sharing the same rate limit:

```python
# Both functions share the same 5/sec rate limit
@opero(rate_limit=5.0, rate_limit_scope="api_group")
def get_data(item_id: str): pass

@opero(rate_limit=5.0, rate_limit_scope="api_group")  
def post_data(item_data: dict): pass

# Combined calls respect the shared limit
get_data("123")  # Uses 1/5 of rate limit
post_data({"key": "value"})  # Uses 2/5 of rate limit
```

### Dynamic Rate Limiting

Adjust rate limits based on conditions:

```python
def get_rate_limit():
    """Adjust rate limit based on time of day."""
    import time
    hour = time.gmtime().tm_hour
    
    if 9 <= hour <= 17:  # Business hours
        return 20.0  # Higher rate limit
    else:
        return 5.0   # Lower rate limit

@opero(rate_limit=get_rate_limit())
def time_aware_api():
    pass
```

## Monitoring and Debugging

### Logging Integration

Enable logging to monitor Opero's behavior:

```python
import logging
from opero import configure_logging

# Configure Opero logging
logger = configure_logging(level=logging.INFO)

@opero(retries=3, cache=True, rate_limit=5.0)
def monitored_function(x):
    return x * 2

# Logs will show:
# - Cache hits/misses
# - Retry attempts
# - Rate limiting actions
# - Fallback attempts
result = monitored_function(42)
```

### Custom Monitoring

Add custom metrics:

```python
import time
from functools import wraps

def add_timing_metrics(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            print(f"{func.__name__} succeeded in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            print(f"{func.__name__} failed after {duration:.2f}s: {e}")
            raise
    return wrapper

@add_timing_metrics
@opero(retries=3, cache=True)
def timed_function(x):
    return expensive_operation(x)
```

## Best Practices Summary

### Configuration Best Practices

1. **Start conservative** - Low retries and short cache TTLs initially
2. **Profile first** - Measure performance before optimizing
3. **Environment-specific** - Different configs for dev/staging/prod
4. **Document decisions** - Explain your configuration choices

### Code Organization

```python
# Good: Centralized configuration
API_CONFIG = {
    "retries": 3,
    "cache": True,
    "cache_ttl": 300,
    "rate_limit": 10.0
}

@opero(**API_CONFIG)
def api_function_1(): pass

@opero(**API_CONFIG)  
def api_function_2(): pass

# Good: Specific configurations for different use cases
BATCH_CONFIG = {"mode": "thread", "workers": 10, "retries": 2}
REALTIME_CONFIG = {"retries": 1, "cache": False, "rate_limit": 50.0}
```

### Error Handling Best Practices

```python
# Good: Specific error handling
try:
    result = resilient_function()
except AllFailedError as e:
    # Handle the specific case where all retries/fallbacks failed
    logger.error(f"Resilience mechanisms exhausted: {e}")
    # Provide graceful degradation
    result = default_value
except SpecificError as e:
    # Handle other specific errors
    logger.warning(f"Specific error occurred: {e}")
    raise

# Good: Logging for debugging
logger.info(f"Function succeeded after resilience mechanisms")
```

## Next Steps

Now that you understand basic usage:

1. **[Advanced Features](advanced-features.md)** - Complex patterns and custom implementations
2. **[Best Practices](best-practices.md)** - Production-ready code and patterns
3. **[API Reference](../api/overview.md)** - Complete technical documentation

## Common Patterns Quick Reference

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