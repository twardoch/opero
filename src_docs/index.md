# Opero: Resilient, Parallel Task Orchestration for Python

<div align="center">

[![PyPI version](https://img.shields.io/pypi/v/opero.svg)](https://pypi.org/project/opero/)
[![Python versions](https://img.shields.io/pypi/pyversions/opero.svg)](https://pypi.org/project/opero/)
[![License](https://img.shields.io/github/license/twardoch/opero.svg)](https://github.com/twardoch/opero/blob/main/LICENSE)
[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue)](https://twardoch.github.io/opero/)

</div>

## What is Opero?

Opero (Latin for "to work" or "to operate") is a Python library that adds resilience and parallelism to your functions with decorators. It handles retries, fallbacks, rate limiting, caching, and concurrent execution automatically.

## Key Features

<div class="grid cards" markdown>

-   :material-refresh: **Automatic Retries**  
    Configurable retry strategies with exponential backoff.

-   :material-swap-horizontal: **Smart Fallbacks**  
    Automatically switch to backup parameters on failure.

-   :material-memory: **Intelligent Caching**  
    Cache results with TTL support and multiple backend options.

-   :material-speedometer: **Rate Limiting**  
    Enforce call frequency limits to protect external services.

-   :material-call-split: **Parallel Processing**  
    Run tasks across threads, processes, or async workers with one decorator.

-   :material-language-python: **Type-Safe & Async-First**  
    Full type hints. Works with both sync and async functions.

</div>

## Quick Example

```python
from opero import opero

@opero(
    retries=3,
    backoff_factor=1.5,
    cache=True,
    rate_limit=10.0,
    arg_fallback="api_key"
)
async def fetch_data(item_id: str, api_key: list[str] = ["key1", "key2"]):
    # Your function implementation
    # Opero handles retries, caching, and fallbacks automatically
    pass
```

## Installation

```bash
pip install opero
```

Optional dependencies:

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

Upgrade fragile code to enterprise-grade resilience with a single decorator:

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

Process large datasets efficiently:

```python
from opero import opmap

@opmap(
    mode="thread",
    workers=10,
    retries=2,
    cache=True
)
def process_item(item):
    return expensive_operation(item)

# Process all items in parallel with automatic resilience
results = process_item(list_of_1000_items)
```

## Next Steps

<div class="grid cards" markdown>

-   :material-rocket-launch: **[Getting Started](getting-started/installation.md)**  
    Install Opero and run your first resilient function

-   :material-book-open-variant: **[User Guide](guide/basic-usage.md)**  
    Core concepts and best practices

-   :material-api: **[API Reference](api/overview.md)**  
    Complete feature documentation

-   :material-github: **[GitHub Repository](https://github.com/twardoch/opero)**  
    Source code and contributions

</div>

## Features Overview

### Resilience Mechanisms

| Feature | Description |
|---------|------------|
| **Retries** | Automatic retries with exponential backoff |
| **Fallbacks** | Switch to alternative parameters on failure |
| **Rate Limiting** | Prevent API overload |
| **Caching** | Avoid redundant operations |
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