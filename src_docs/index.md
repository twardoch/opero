# Opero: Resilient, Parallel Task Orchestration for Python

<div align="center">

[![PyPI version](https://img.shields.io/pypi/v/opero.svg)](https://pypi.org/project/opero/)
[![Python versions](https://img.shields.io/pypi/pyversions/opero.svg)](https://pypi.org/project/opero/)
[![License](https://img.shields.io/github/license/twardoch/opero.svg)](https://github.com/twardoch/opero/blob/main/LICENSE)
[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue)](https://twardoch.github.io/opero/)

</div>

## What is Opero?

Opero (Latin for "to work" or "to operate") is a Python library that makes your functions more robust and efficient through simple decorators. It provides automatic retries, fallbacks, rate limiting, caching, and parallel processing - all with minimal code changes.

## Key Features

<div class="grid cards" markdown>

-   :material-refresh: **Automatic Retries**  
    Handle transient failures gracefully with configurable retry strategies and exponential backoff.

-   :material-swap-horizontal: **Smart Fallbacks**  
    Define alternative parameters (like backup API keys) that activate automatically on failure.

-   :material-memory: **Intelligent Caching**  
    Speed up repeated operations with flexible caching backends and TTL support.

-   :material-speedometer: **Rate Limiting**  
    Protect external services from overload with built-in rate limiting.

-   :material-call-split: **Parallel Processing**  
    Process data in parallel across threads, processes, or async tasks with a single decorator.

-   :material-language-python: **Type-Safe & Async-First**  
    Full type hints and native support for both sync and async functions.

</div>

## Quick Example

```python
from opero import opero

@opero(
    retries=3,                    # Retry up to 3 times
    backoff_factor=1.5,           # Exponential backoff
    cache=True,                   # Cache results
    rate_limit=10.0,              # Max 10 calls per second
    arg_fallback="api_key"        # Try backup keys on failure
)
async def fetch_data(item_id: str, api_key: list[str] = ["key1", "key2"]):
    # Your function implementation
    # Opero will automatically handle retries, caching, and fallbacks
    pass
```

## Installation

```bash
pip install opero
```

For enhanced features:

```bash
# For advanced multiprocessing (supports more object types)
pip install opero[pathos]

# For async multiprocessing
pip install opero[aiomultiprocess]

# All optional dependencies
pip install opero[all]
```

## Why Opero?

### Simple Yet Powerful

Add enterprise-grade resilience with just a decorator:

```python
# Before: Fragile code
def process_data(item):
    response = api.call(item)  # Might fail!
    return response.data

# After: Resilient code
@opero(retries=3, cache=True)
def process_data(item):
    response = api.call(item)  # Now handles failures gracefully
    return response.data
```

### Built for Real-World Challenges

- **API Integration**: Handle rate limits, timeouts, and service failures
- **Data Processing**: Parallelize CPU-intensive or I/O-bound operations
- **Web Scraping**: Manage retries, rate limits, and fallback strategies
- **Microservices**: Add resilience patterns with minimal overhead

### Performance at Scale

Process thousands of items efficiently:

```python
from opero import opmap

@opmap(
    mode="thread",      # Use threads for I/O-bound tasks
    workers=10,         # 10 parallel workers
    retries=2,          # Retry failed items
    cache=True          # Cache results
)
def process_item(item):
    # Process individual item
    return expensive_operation(item)

# Process all items in parallel with automatic resilience
results = process_item(list_of_1000_items)
```

## Next Steps

<div class="grid cards" markdown>

-   :material-rocket-launch: **[Getting Started](getting-started/installation.md)**  
    Install Opero and run your first resilient function

-   :material-book-open-variant: **[User Guide](guide/basic-usage.md)**  
    Learn core concepts and best practices

-   :material-api: **[API Reference](api/overview.md)**  
    Detailed documentation of all features

-   :material-github: **[GitHub Repository](https://github.com/twardoch/opero)**  
    View source code and contribute

</div>

## Features Overview

### Resilience Mechanisms

| Feature | Description |
|---------|------------|
| **Retries** | Automatic retries with exponential backoff |
| **Fallbacks** | Try alternative parameters on failure |
| **Rate Limiting** | Prevent API overload and respect limits |
| **Caching** | Reduce redundant operations |
| **Circuit Breaker** | Stop cascading failures (coming soon) |

### Parallel Processing Modes

| Mode | Best For | Description |
|------|----------|-------------|
| `thread` | I/O-bound tasks | ThreadPool for network/disk operations |
| `process` | CPU-bound tasks | ProcessPool for computation |
| `async` | Async I/O | Native asyncio concurrency |
| `async_process` | Async + CPU | Async functions in separate processes |

## Community

- **Issues**: [GitHub Issues](https://github.com/twardoch/opero/issues)
- **Discussions**: [GitHub Discussions](https://github.com/twardoch/opero/discussions)
- **Contributing**: See our [Contributing Guide](development/contributing.md)

## License

Opero is licensed under the MIT License. See [LICENSE](https://github.com/twardoch/opero/blob/main/LICENSE) for details.