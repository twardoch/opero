# Basic Usage

This guide covers the fundamental patterns and use cases for Opero.

## Core Concepts

### The @opero Decorator

The `@opero` decorator is the foundation of Opero. It wraps your functions with resilience mechanisms:

```python
from opero import opero

@opero()  # Even with no parameters, adds basic error handling
def simple_function():
    return "Hello, Opero!"
```

### Resilience Layers

Opero applies resilience mechanisms in a specific order:

1. **Cache Check** - Returns cached result if available
2. **Rate Limiting** - Ensures rate limits are respected
3. **Retry Logic** - Attempts the operation with retries
4. **Fallback Logic** - Tries alternative parameters on failure

Understanding this order helps you design effective resilient functions.

## Common Patterns

### Pattern 1: Unreliable Network Operations

Handle network failures gracefully:

```python
import requests
from opero import opero

@opero(
    retries=3,
    backoff_factor=2.0,
    retry_on=(requests.RequestException,)
)
def fetch_api_data(endpoint: str):
    response = requests.get(f"https://api.example.com/{endpoint}")
    response.raise_for_status()
    return response.json()

# Usage
try:
    data = fetch_api_data("users/123")
except Exception as e:
    print(f"Failed after all retries: {e}")
```

### Pattern 2: Multiple API Keys

Rotate through API keys automatically:

```python
@opero(
    arg_fallback="api_key",
    retries=2  # Try each key up to 2 times
)
def call_paid_api(query: str, api_key: list[str] = ["key1", "key2", "key3"]):
    headers = {"Authorization": f"Bearer {api_key[0]}"}
    response = requests.post(
        "https://api.service.com/query",
        json={"query": query},
        headers=headers
    )
    
    if response.status_code == 429:  # Rate limited
        raise Exception("Rate limited")
    elif response.status_code == 401:  # Invalid key
        raise Exception("Invalid API key")
    
    return response.json()
```

### Pattern 3: Caching Expensive Operations

Reduce redundant computations:

```python
import time
import hashlib

@opero(
    cache=True,
    cache_ttl=3600  # Cache for 1 hour
)
def expensive_calculation(data: str):
    print(f"Computing hash for: {data}")
    time.sleep(2)  # Simulate expensive operation
    
    return {
        "input": data,
        "hash": hashlib.sha256(data.encode()).hexdigest(),
        "timestamp": time.time()
    }

# First call takes 2 seconds
result1 = expensive_calculation("hello")

# Subsequent calls return instantly
result2 = expensive_calculation("hello")
assert result1 == result2
```

### Pattern 4: Rate-Limited Operations

Respect external service limits:

```python
import asyncio
from datetime import datetime

@opero(
    rate_limit=1.0  # 1 call per second
)
async def rate_limited_api_call(item_id: int):
    timestamp = datetime.now().isoformat()
    print(f"[{timestamp}] Processing item {item_id}")
    
    # Simulate API call
    await asyncio.sleep(0.1)
    return f"Result for item {item_id}"

async def process_many_items():
    # These will be automatically spaced out
    tasks = [rate_limited_api_call(i) for i in range(5)]
    results = await asyncio.gather(*tasks)
    return results
```

## Working with Different Data Types

### Functions Returning Complex Objects

Opero works with any Python object:

```python
from dataclasses import dataclass
from typing import List

@dataclass
class User:
    id: int
    name: str
    email: str

@opero(
    retries=3,
    cache=True,
    cache_ttl=300
)
def get_user_details(user_id: int) -> User:
    # Simulate database query
    return User(
        id=user_id,
        name=f"User {user_id}",
        email=f"user{user_id}@example.com"
    )

@opero(
    retries=2,
    cache=True
)
def get_user_list(department: str) -> List[User]:
    # Return list of users
    return [get_user_details(i) for i in range(1, 6)]
```

### Generator Functions

Opero supports generator functions:

```python
@opero(
    retries=2,
    cache=False  # Generators shouldn't be cached
)
def read_large_file(filename: str):
    """Read file line by line with retry capability."""
    with open(filename, 'r') as f:
        for line in f:
            yield line.strip()

# Usage
for line in read_large_file("data.txt"):
    process_line(line)
```

## Error Handling Strategies

### Handling Specific Errors

```python
from opero import opero, AllFailedError

@opero(
    retries=3,
    retry_on=(ConnectionError, TimeoutError),
    arg_fallback="timeout"
)
def unstable_connection(url: str, timeout: list[float] = [1.0, 3.0, 10.0]):
    response = requests.get(url, timeout=timeout[0])
    return response.text

try:
    content = unstable_connection("https://slow-server.com")
except AllFailedError as e:
    print("Failed with all timeouts:")
    for i, error in enumerate(e.errors):
        print(f"  Timeout {i+1}: {error}")
    # Implement fallback logic
    content = get_cached_content()
```

### Graceful Degradation

```python
@opero(
    retries=2,
    cache=True,
    cache_ttl=3600
)
def get_weather_data(city: str):
    # Primary data source
    return fetch_from_weather_api(city)

def get_weather_with_fallback(city: str):
    try:
        # Try to get fresh data
        return get_weather_data(city)
    except AllFailedError:
        # Fall back to cached data if available
        try:
            return get_weather_data.cache_get(city)
        except KeyError:
            # Final fallback
            return {"city": city, "status": "unavailable"}
```

## Async Functions

Opero fully supports async/await:

```python
import aiohttp

@opero(
    retries=3,
    backoff_factor=1.5,
    cache=True,
    rate_limit=10.0
)
async def fetch_async(session: aiohttp.ClientSession, url: str):
    async with session.get(url) as response:
        return await response.json()

async def fetch_multiple_urls(urls: list[str]):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_async(session, url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle results
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                print(f"Failed to fetch {url}: {result}")
            else:
                print(f"Success: {url}")
```

## Monitoring and Debugging

### Enable Logging

```python
import logging
from opero.utils import configure_logging

# Enable INFO level logging
logger = configure_logging(level=logging.INFO)

@opero(retries=3, cache=True)
def monitored_function(x):
    logger.info(f"Processing: {x}")
    return x * 2

# You'll see logs for:
# - Cache hits/misses
# - Retry attempts
# - Rate limiting delays
```

### Custom Logging

```python
import logging

logger = logging.getLogger(__name__)

@opero(
    retries=3,
    cache=True
)
def function_with_custom_logging(data):
    logger.info(f"Starting processing for: {data}")
    
    try:
        result = process_data(data)
        logger.info(f"Successfully processed: {data}")
        return result
    except Exception as e:
        logger.error(f"Error processing {data}: {e}")
        raise
```

## Best Practices Summary

1. **Start Simple**: Begin with basic retry and caching, add features as needed
2. **Be Specific**: Use specific exception types in `retry_on`
3. **Cache Wisely**: Set appropriate TTLs based on data freshness needs
4. **Monitor**: Enable logging during development and debugging
5. **Test Failures**: Test your fallback and error handling paths
6. **Document**: Document which parameters can be used for fallbacks

## Next Steps

- Explore [Advanced Features](advanced-features.md) for complex scenarios
- Learn about [Best Practices](best-practices.md) for production use
- Check the [API Reference](../api/overview.md) for detailed documentation