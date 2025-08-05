# Quick Start

Get your first resilient function running in 5 minutes! This guide walks you through the essential Opero patterns you'll use every day.

## Your First Resilient Function

Let's start with a simple function that might fail and make it bulletproof:

```python
import asyncio
from opero import opero

# Before: A fragile function
async def fetch_user_data(user_id: str):
    # This might fail due to network issues, rate limits, etc.
    response = await some_api_call(user_id)
    return response.json()

# After: A resilient function
@opero(
    retries=3,              # Try up to 3 times
    backoff_factor=1.5,     # Wait longer between retries
    cache=True,             # Cache successful results
    cache_ttl=300,          # Cache for 5 minutes
    rate_limit=10.0         # Max 10 calls per second
)
async def fetch_user_data(user_id: str):
    response = await some_api_call(user_id)
    return response.json()

# Usage - same as before, but now resilient!
async def main():
    user_data = await fetch_user_data("user123")
    print(user_data)

asyncio.run(main())
```

**What just happened?**

- ✅ **Automatic retries** if the API call fails
- ✅ **Exponential backoff** to avoid overwhelming the service  
- ✅ **Caching** to avoid repeated API calls
- ✅ **Rate limiting** to respect API limits
- ✅ **Same interface** - no changes to how you call the function

## Adding Smart Fallbacks

Need backup API keys or alternative endpoints? Opero handles fallbacks automatically:

```python
@opero(
    retries=2,
    arg_fallback="api_key",  # Try different API keys on failure
    cache=True
)
async def fetch_data_with_fallback(item_id: str, api_key: list[str]):
    # Opero will try each API key until one works
    current_key = api_key[0]  # Always use the first available key
    
    headers = {"Authorization": f"Bearer {current_key}"}
    response = await http_client.get(f"/api/data/{item_id}", headers=headers)
    return response.json()

# Usage with fallback keys
keys = ["primary_key", "backup_key", "emergency_key"]
data = await fetch_data_with_fallback("item123", api_key=keys)
```

**How it works:**
1. First attempt uses `"primary_key"`
2. If it fails, retry with `"backup_key"`  
3. If that fails, try `"emergency_key"`
4. If all keys fail after retries, raise `AllFailedError`

## Parallel Processing Made Simple

Process thousands of items with a single decorator change:

```python
from opero import opmap
import time

# Single item processor
@opmap(
    mode="thread",          # Use threads (good for I/O)
    workers=10,             # 10 parallel workers
    retries=2,              # Retry failed items
    cache=True,             # Cache results per item
    rate_limit=50.0         # 50 requests per second total
)
def process_item(item_id: str):
    # This function processes ONE item
    # opmap handles the parallelization
    result = expensive_api_call(item_id)
    return {"id": item_id, "result": result}

# Process many items in parallel
items = [f"item_{i}" for i in range(1000)]
results = process_item(items)  # All 1000 items processed in parallel!

print(f"Processed {len(results)} items")
for result in results[:5]:  # Show first 5 results
    print(result)
```

**Performance comparison:**
- **Without Opero**: ~1000 seconds (sequential)
- **With `@opmap`**: ~100 seconds (10x faster with 10 workers)

## Real-World Example: Web Scraping

Here's a complete example that combines everything:

```python
import asyncio
import aiohttp
from opero import opmap, AllFailedError

@opmap(
    mode="async",              # Use asyncio for I/O-bound tasks
    workers=20,                # 20 concurrent requests
    retries=3,                 # Retry failed pages
    cache=True,                # Cache scraped content
    cache_ttl=3600,            # Cache for 1 hour
    rate_limit=10.0,           # Respect rate limits
    arg_fallback="user_agent"  # Try different user agents
)
async def scrape_page(url: str, user_agent: list[str] = None):
    if user_agent is None:
        user_agent = [
            "Mozilla/5.0 (compatible; OperoBot/1.0)",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        ]
    
    headers = {"User-Agent": user_agent[0]}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 403:
                raise aiohttp.ClientError("Forbidden - try different user agent")
            response.raise_for_status()
            return {
                "url": url,
                "status": response.status,
                "content": await response.text(),
                "user_agent": user_agent[0]
            }

async def main():
    urls = [
        "https://example.com/page1",
        "https://example.com/page2", 
        "https://example.com/page3",
        # ... 100 more URLs
    ]
    
    print(f"Scraping {len(urls)} URLs...")
    results = await scrape_page(urls)
    
    # Check results
    successful = [r for r in results if not isinstance(r, Exception)]
    failed = [r for r in results if isinstance(r, Exception)]
    
    print(f"✅ Successfully scraped: {len(successful)} pages")
    print(f"❌ Failed to scrape: {len(failed)} pages")
    
    # Show failed URLs for debugging
    for error in failed[:5]:  # Show first 5 errors
        if isinstance(error, AllFailedError):
            print(f"All attempts failed: {error}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Key Concepts Summary

### Decorators

| Decorator | Purpose | Best For |
|-----------|---------|----------|
| `@opero` | Single function resilience | Individual API calls, database queries |
| `@opmap` | Parallel + resilience | Batch processing, bulk operations |

### Essential Parameters  

| Parameter | Purpose | Example |
|-----------|---------|---------|
| `retries` | How many times to retry | `retries=3` |
| `cache` | Enable result caching | `cache=True` |
| `rate_limit` | Max calls per second | `rate_limit=10.0` |
| `arg_fallback` | Parameter to use for fallbacks | `arg_fallback="api_key"` |
| `mode` | Parallelization mode | `mode="thread"` |
| `workers` | Number of parallel workers | `workers=10` |

### Parallelization Modes

| Mode | Best For | Example Use Case |
|------|----------|------------------|
| `"thread"` | I/O-bound tasks | API calls, file downloads |
| `"process"` | CPU-bound tasks | Data processing, calculations |
| `"async"` | Async I/O tasks | Many concurrent HTTP requests |
| `"async_process"` | Async + CPU | Async functions needing CPU isolation |

## Error Handling

```python
from opero import opero, AllFailedError

@opero(retries=3)
async def might_fail():
    # Your code here
    pass

try:
    result = await might_fail()
except AllFailedError as e:
    print(f"All {len(e.errors)} attempts failed:")
    for i, error in enumerate(e.errors):
        print(f"  Attempt {i+1}: {error}")
```

## Next Steps

🎉 **You've mastered the basics!** 

Now explore:

1. **[Configuration](configuration.md)** - Fine-tune Opero's behavior
2. **[Basic Usage](../guide/basic-usage.md)** - Deep dive into core concepts  
3. **[Advanced Features](../guide/advanced-features.md)** - Custom caching, complex fallbacks
4. **[Best Practices](../guide/best-practices.md)** - Production-ready patterns

## Quick Reference

### Common Patterns

```python
# Simple retry + cache
@opero(retries=3, cache=True)
def api_call(): pass

# With fallbacks
@opero(retries=2, arg_fallback="endpoint") 
def multi_endpoint(data, endpoint: list[str]): pass

# Parallel processing
@opmap(mode="thread", workers=10)
def process_item(item): pass

# High-performance async
@opmap(mode="async", workers=50, rate_limit=100.0)
async def async_task(item): pass
```

### Import Quick Reference

```python
# Essential imports
from opero import opero, opmap, AllFailedError

# Advanced imports  
from opero import configure_logging
from opero.exceptions import OperoError
```

Ready to build resilient applications? Let's go! 🚀