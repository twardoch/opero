# Opero: Resilient, Parallel Task Orchestration for Python

<div align="center">

[![PyPI version](https://img.shields.io/pypi/v/opero.svg)](https://pypi.org/project/opero/)
[![Python versions](https://img.shields.io/pypi/pyversions/opero.svg)](https://pypi.org/project/opero/)
[![License](https://img.shields.io/github/license/twardoch/opero.svg)](https://github.com/twardoch/opero/blob/main/LICENSE)
[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue)](https://twardoch.github.io/opero/)

</div>

## What is Opero?

Opero (Latin for "to work" or "to operate") is a Python library that makes your functions more robust and efficient through simple decorators. It provides automatic retries, fallbacks, rate limiting, caching, and parallel processing - all with minimal code changes.

## :material-flash: TLDR - Quick Start

```python
from opero import opero, opmap

# Make any function resilient with @opero
@opero(retries=3, cache=True, rate_limit=10.0)
async def fetch_data(item_id: str):
    # Your code here - now with automatic retries, caching, and rate limiting
    return await api_call(item_id)

# Process thousands of items in parallel with @opmap
@opmap(mode="thread", workers=10, retries=2)
def process_item(item):
    # Process one item - opmap handles the parallelization
    return expensive_operation(item)

# Use it
results = process_item(list_of_1000_items)  # Processes all items in parallel
```

## :material-book-open: Documentation Contents

This documentation is organized into 9 comprehensive chapters to help you master Opero:

### :material-rocket-launch: Getting Started
Learn the basics and get up and running quickly.

- **[Installation](getting-started/installation.md)** - Install Opero and its optional dependencies
- **[Quick Start](getting-started/quickstart.md)** - Your first resilient function in 5 minutes
- **[Configuration](getting-started/configuration.md)** - Essential configuration options

### :material-book: User Guide
Master Opero's features and best practices.

- **[Basic Usage](guide/basic-usage.md)** - Core concepts and simple examples
- **[Advanced Features](guide/advanced-features.md)** - Fallbacks, custom caching, and complex scenarios
- **[Best Practices](guide/best-practices.md)** - Patterns, performance tips, and common pitfalls

### :material-api: API Reference
Complete technical reference.

- **[Overview](api/overview.md)** - High-level API overview and design principles
- **[Core Components](api/core.md)** - Detailed decorator and component documentation
- **[Utilities](api/utils.md)** - Helper functions and advanced utilities

## :material-heart: Key Features

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

## :material-lightning-bolt: Why Choose Opero?

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
    return expensive_operation(item)

# Process all items in parallel with automatic resilience
results = process_item(list_of_1000_items)
```

## :material-compass: Navigation Guide

### :material-account-school: New to Opero?

1. Start with **[Installation](getting-started/installation.md)** to get set up
2. Follow the **[Quick Start](getting-started/quickstart.md)** guide for your first function
3. Read **[Basic Usage](guide/basic-usage.md)** to understand core concepts

### :material-account-wrench: Ready to Go Deeper?

1. Explore **[Advanced Features](guide/advanced-features.md)** for complex scenarios
2. Review **[Best Practices](guide/best-practices.md)** for production-ready code
3. Reference the **[API Documentation](api/overview.md)** for complete details

### :material-account-cog: Contributing or Troubleshooting?

1. Check the **[API Reference](api/core.md)** for implementation details
2. Browse **[Utilities](api/utils.md)** for helper functions
3. See development guides in the **Development** section

## :material-rocket: Quick Installation

```bash
# Basic installation
pip install opero

# With enhanced multiprocessing
pip install opero[pathos]

# With async multiprocessing  
pip install opero[aiomultiprocess]

# All features
pip install opero[all]
```

## :material-github: Community & Support

- **Issues**: [GitHub Issues](https://github.com/twardoch/opero/issues)
- **Discussions**: [GitHub Discussions](https://github.com/twardoch/opero/discussions)  
- **Source Code**: [GitHub Repository](https://github.com/twardoch/opero)
- **Package**: [PyPI](https://pypi.org/project/opero/)

## :material-scale-balance: License

Opero is licensed under the MIT License. See [LICENSE](https://github.com/twardoch/opero/blob/main/LICENSE) for details.

---

<div align="center">
<strong>Ready to make your Python functions more resilient?</strong><br>
<a href="getting-started/installation.md" class="md-button md-button--primary">Get Started Now</a>
</div>