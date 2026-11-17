# Quick Start

Get started with Opero in minutes.

## Your First Resilient Function

Here's a minimal example that shows Opero's core behavior:

```python
from opero import opero


@opero(retries=3, backoff_factor=2.0, cache=True, cache_ttl=300)
def fetch_user_data(user_id: int):
    """Fetch user data from an API (simulated)."""
    import random
    import time

    time.sleep(0.1)

    if random.random() < 0.3:
        raise ConnectionError("API temporarily unavailable")

    return {"id": user_id, "name": f"User {user_id}"}


# First call may retry on failure
user = fetch_user_data(123)
print(f"Fetched: {user}")

# Second call returns instantly from cache
user_cached = fetch_user_data(123)
print(f"From cache: {user_cached}")
```

## Handling Multiple Fallback Options

When one service fails, Opero can automatically try others:

```python
from opero import opero, AllFailedError


@opero(retries=2, arg_fallback="api_endpoint", cache=True)
def fetch_weather(
    city: str,
    api_endpoint: list[str] = [
        "https://api.primary.com",
        "https://api.backup.com",
        "https://api.emergency.com",
    ],
):
    """Fetch weather with automatic failover to backup APIs."""
    import requests

    current_endpoint = api_endpoint[0]
    print(f"Trying {current_endpoint}...")

    response = requests.get(f"{current_endpoint}/weather/{city}", timeout=5)
    response.raise_for_status()

    return response.json()


try:
    weather = fetch_weather("London")
    print(f"Weather data: {weather}")
except AllFailedError as e:
    print(f"All endpoints failed: {e.errors}")
```

## Parallel Processing with @opmap

Run multiple operations at once with built-in error handling:

```python
from opero import opmap
import time


@opmap(mode="thread", workers=5, retries=2, cache=True, ordered=True)
def download_image(url: str):
    """Download a single image."""
    import requests

    print(f"Downloading {url}...")
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    return {
        "url": url,
        "size": len(response.content),
        "content_type": response.headers.get("content-type"),
    }


# Process multiple URLs in parallel
urls = [
    "https://httpbin.org/image/jpeg",
    "https://httpbin.org/image/png",
    "https://httpbin.org/image/webp",
]

results = download_image(urls)
for result in results:
    if isinstance(result, Exception):
        print(f"Failed: {result}")
    else:
        print(f"Downloaded: {result['url']} ({result['size']} bytes)")
```

## Rate Limiting for API Protection

Prevent overwhelming external services:

```python
from opero import opero
import asyncio
from datetime import datetime


@opero(rate_limit=2.0, retries=3, cache=True)
async def call_api(endpoint: str):
    """Make rate-limited API calls."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] Calling {endpoint}")

    await asyncio.sleep(0.1)
    return f"Response from {endpoint}"


async def main():
    endpoints = [f"/api/v1/resource/{i}" for i in range(6)]

    tasks = [call_api(endpoint) for endpoint in endpoints]
    results = await asyncio.gather(*tasks)

    for result in results:
        print(result)


asyncio.run(main())
```

## Combining Features

A practical example using several Opero features together:

```python
from opero import opmap
import time


@opmap(
    mode="thread",
    workers=3,
    retries=3,
    backoff_factor=1.5,
    arg_fallback="headers",
    rate_limit=5.0,
    cache=True,
    cache_ttl=3600,
)
def scrape_product(
    product_id: int,
    headers: list[dict] = [
        {"User-Agent": "Bot 1.0"},
        {"User-Agent": "Bot 2.0"},
    ],
):
    """Scrape product data with multiple fallback headers."""
    import requests

    current_headers = headers[0]
    url = f"https://api.example.com/products/{product_id}"

    response = requests.get(url, headers=current_headers, timeout=10)
    response.raise_for_status()

    return {
        "id": product_id,
        "data": response.json(),
        "headers_used": current_headers["User-Agent"],
    }


# Scrape multiple products in parallel
product_ids = list(range(1, 21))
results = scrape_product(product_ids)

successful = [r for r in results if not isinstance(r, Exception)]
failed = [r for r in results if isinstance(r, Exception)]

print(f"Successfully scraped: {len(successful)} products")
print(f"Failed: {len(failed)} products")
```

## Error Handling Best Practices

Control exactly what gets retried and when:

```python
from opero import opero, AllFailedError
import logging

logging.basicConfig(level=logging.INFO)


@opero(
    retries=3,
    retry_on=(ConnectionError, TimeoutError),
    arg_fallback="timeout",
    cache=True,
)
def unreliable_operation(data: str, timeout: list[float] = [1.0, 2.0, 5.0]):
    """Operation with increasing timeout fallbacks."""
    import requests

    current_timeout = timeout[0]
    print(f"Attempting with timeout={current_timeout}s")

    try:
        response = requests.post(
            "https://httpbin.org/delay/3", json={"data": data}, timeout=current_timeout
        )
        return response.json()
    except requests.Timeout:
        raise TimeoutError(f"Request timed out after {current_timeout}s")


try:
    result = unreliable_operation("important data")
    print(f"Success: {result}")
except AllFailedError as e:
    print(f"Operation failed after all attempts:")
    for i, error in enumerate(e.errors):
        print(f"  Attempt {i + 1}: {error}")
```

## Next Steps

- **[Configuration Guide](configuration.md)** - All decorator options
- **[User Guide](../guide/basic-usage.md)** - Detailed examples
- **[API Reference](../api/overview.md)** - Complete documentation
- **[Best Practices](../guide/best-practices.md)** - Production tips

## Quick Reference

### Common Decorator Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `retries` | int | Number of retry attempts |
| `backoff_factor` | float | Multiplier for exponential backoff |
| `retry_on` | Exception | Exceptions that trigger retries |
| `arg_fallback` | str | Parameter name containing fallback values |
| `cache` | bool | Enable caching |
| `cache_ttl` | int | Cache time-to-live in seconds |
| `rate_limit` | float | Maximum calls per second |

### Parallel Processing Modes

| Mode | Use Case |
|------|----------|
| `thread` | I/O-bound tasks (API calls, file I/O) |
| `process` | CPU-bound tasks (computation, data processing) |
| `async` | Async I/O operations |
| `async_process` | CPU-intensive async operations |