---
this_file: README.md
---

# Opero: Resilient, Parallel Task Orchestration for Python

[![PyPI version](https://img.shields.io/pypi/v/opero.svg)](https://pypi.org/project/opero/)
[![Python versions](https://img.shields.io/pypi/pyversions/opero.svg)](https://pypi.org/project/opero/)
[![License](https://img.shields.io/github/license/twardoch/opero.svg)](https://github.com/twardoch/opero/blob/main/LICENSE)

Opero provides a clean, Pythonic interface for orchestrating resilient, parallelized operations with parameter-based fallbacks, retry logic, rate limiting, and multiprocessing support.

## Key Features

- **Simple, focused decorators**: `@opero` and `@operomap` for resilient operations
- **Parameter-based fallbacks**: Try the same function with different parameter values
- **Integrated caching**: Efficient caching with multiple backends via `twat-cache`
- **Retry mechanisms**: Exponential backoff, jitter, and customizable retry conditions
- **Rate limiting**: Control execution frequency to avoid overwhelming resources
- **Parallel execution**: Process, thread, and async-based parallelism via `twat-mp`
- **Async support**: Full support for async/await functions
- **Logical processing order**: Clear order of operations for all resilience mechanisms

## Recent Improvements

- **Enhanced Logging**: Added comprehensive logging throughout the codebase with configurable log levels and context support
- **Improved Error Handling**: Better handling of errors in async/sync conversions and fallback scenarios
- **Optimized Core Functions**: Reduced complexity in key functions for better maintainability
- **Fixed Process Method**: Modified to apply functions to each item individually for more intuitive behavior
- **Fixed Retry Functionality**: Corrected parameter order in retry function calls and added fallback for None configurations
- **Enhanced Documentation**: Added detailed docstrings, usage examples, and best practices sections
- **Type Safety**: Improved type annotations and fixed type incompatibility issues
- **Code Quality**: Fixed various linter errors and improved overall code structure

## Installation

```bash
pip install opero
```

For optional dependencies:

```bash
# For enhanced multiprocessing support
pip install opero[pathos]

# For async multiprocessing
pip install opero[aiomultiprocess]

# Install all optional dependencies
pip install opero[all]
```

## Quick Start

### Basic Usage with `@opero`

```python
from opero import opero

# Add caching, retries, and parameter-based fallbacks to a function
@opero(
    # Caching options
    cache=True,
    cache_ttl=3600,  # Cache for 1 hour
    
    # Retry options
    retries=3,
    backoff_factor=1.5,
    
    # Fallback options
    arg_fallback="model"
)
async def call_llm(prompt: str, model: list[str] = ["gpt-4", "gpt-3.5"]):
    # Will try with model="gpt-4" first, then model="gpt-3.5" if it fails
    # Results will be cached for 1 hour
    response = await api_call(prompt=prompt, model=model)
    return response
```

### Parallel Processing with `@operomap`

```python
from opero import operomap

# Process items in parallel with resilience mechanisms
@operomap(
    # Concurrency options
    mode="process",  # Use process-based parallelism
    workers=4,       # Use 4 worker processes
    
    # Caching options
    cache=True,
    cache_ttl=1800,  # Cache for 30 minutes
    
    # Fallback options
    arg_fallback="api_key"
)
def call_api(item, api_key: list[str] = ["primary_key", "backup_key"]):
    # Will try each API key in order if previous ones fail
    # Results will be cached for 30 minutes
    return make_request(item, api_key=api_key)

# Usage
results = call_api([item1, item2, item3])
```

## Decorator Options

### `@opero` Decorator

```python
@opero(
    # Caching options
    cache=True,                     # Enable caching
    cache_ttl=3600,                 # Cache time-to-live in seconds
    cache_backend="memory",         # Cache backend: "memory", "disk", "redis", etc.
    cache_key=None,                 # Custom cache key function
    cache_namespace="opero",        # Cache namespace
    
    # Retry options
    retries=3,                      # Number of retry attempts
    backoff_factor=1.5,             # Backoff multiplier between retries
    min_delay=0.1,                  # Minimum delay between retries (seconds)
    max_delay=30,                   # Maximum delay between retries (seconds)
    retry_on=Exception,             # Exception types to retry on
    
    # Fallback options
    arg_fallback="model",           # Parameter name containing fallback values
    
    # Rate limiting options
    rate_limit=None,                # Operations per second (if needed)
)
def my_function(arg1, arg2, model=["option1", "option2"]):
    # Function implementation
    pass
```

### `@operomap` Decorator

```python
@operomap(
    # Caching options
    cache=True,                     # Enable caching
    cache_ttl=3600,                 # Cache time-to-live in seconds
    cache_backend="memory",         # Cache backend: "memory", "disk", "redis", etc.
    cache_key=None,                 # Custom cache key function
    cache_namespace="opero",        # Cache namespace
    
    # Retry options
    retries=3,                      # Number of retry attempts
    backoff_factor=1.5,             # Backoff multiplier between retries
    min_delay=0.1,                  # Minimum delay between retries (seconds)
    max_delay=30,                   # Maximum delay between retries (seconds)
    retry_on=Exception,             # Exception types to retry on
    
    # Fallback options
    arg_fallback="model",           # Parameter name containing fallback values
    
    # Rate limiting options
    rate_limit=None,                # Operations per second (if needed)
    
    # Concurrency options
    mode="process",                 # "process", "thread", "async", or "async_process"
    workers=4,                      # Number of workers
    ordered=True,                   # Whether to preserve input order in results
    progress=True                   # Enable progress tracking
)
def process_item(item, model=["option1", "option2"]):
    # Process a single item
    return result

# Usage
results = process_item([item1, item2, item3])
```

## Advanced Usage

### Async Functions

Both decorators fully support async functions:

```python
@opero(cache=True, retries=3)
async def fetch_data(url):
    # Async implementation
    response = await aiohttp.get(url)
    return await response.json()

# Usage
data = await fetch_data("https://api.example.com/data")
```

### Parameter-Based Fallbacks

The `arg_fallback` parameter allows you to specify a parameter that contains fallback values:

```python
@opero(arg_fallback="api_key")
def call_api(data, api_key=["primary", "secondary", "tertiary"]):
    # Will try with each API key in sequence until one succeeds
    return make_request(data, api_key=api_key)
```

### Caching with Different Backends

```python
@opero(
    cache=True,
    cache_backend="redis",
    cache_namespace="my_app",
    cache_ttl=3600
)
def expensive_calculation(x):
    # Results will be cached in Redis
    return x * x
```

## Best Practices

### Error Handling

Opero provides several mechanisms for handling errors gracefully. Here are some best practices:

1. **Use Fallbacks for Critical Operations**: Always provide fallback functions for critical operations that must succeed.

```python
from opero import Orchestrator, OrchestratorConfig

# Primary function that might fail
async def fetch_from_primary_api(item_id):
    # Implementation that might fail
    ...

# Fallback function that uses a different approach
async def fetch_from_backup_api(item_id):
    # More reliable but possibly slower implementation
    ...

# Last resort fallback that returns cached data
async def fetch_from_cache(item_id):
    # Return cached data
    ...

# Create an orchestrator with multiple fallbacks in order of preference
orchestrator = Orchestrator(
    config=OrchestratorConfig(
        fallbacks=[fetch_from_backup_api, fetch_from_cache]
    )
)

# Execute with fallbacks
result = await orchestrator.execute(fetch_from_primary_api, "item123")
```

2. **Configure Retries Appropriately**: Adjust retry parameters based on the operation's characteristics.

```python
from opero import RetryConfig, orchestrate

# For quick operations that might fail due to temporary issues
@orchestrate(
    config=OrchestratorConfig(
        retry_config=RetryConfig(
            max_attempts=5,
            wait_min=0.1,
            wait_max=1.0,
            wait_multiplier=1.2
        )
    )
)
async def quick_operation():
    # Implementation
    ...

# For operations that might take longer to recover
@orchestrate(
    config=OrchestratorConfig(
        retry_config=RetryConfig(
            max_attempts=3,
            wait_min=2.0,
            wait_max=30.0,
            wait_multiplier=2.0,
            # Only retry specific exceptions
            retry_exceptions=(ConnectionError, TimeoutError)
        )
    )
)
async def slow_operation():
    # Implementation
    ...
```

3. **Handle Specific Exceptions**: Configure retries to only trigger for specific exceptions.

```python
from opero import RetryConfig, orchestrate

@orchestrate(
    config=OrchestratorConfig(
        retry_config=RetryConfig(
            max_attempts=3,
            # Only retry these specific exceptions
            retry_exceptions=(ConnectionError, TimeoutError, ValueError)
        )
    )
)
async def network_operation():
    # Implementation
    ...
```

### Performance Optimization

1. **Use Concurrency for I/O-Bound Operations**: Limit concurrency based on your application's needs and the target system's capacity.

```python
from opero import Orchestrator, OrchestratorConfig, ConcurrencyConfig

# Create an orchestrator with concurrency control
orchestrator = Orchestrator(
    config=OrchestratorConfig(
        concurrency_config=ConcurrencyConfig(
            limit=10  # Limit to 10 concurrent operations
        )
    )
)

# Process many items efficiently
urls = [f"https://example.com/api/{i}" for i in range(100)]
results = await orchestrator.process([fetch_url], *urls)
```

2. **Use Rate Limiting for API Calls**: Respect API rate limits to avoid being throttled.

```python
from opero import Orchestrator, OrchestratorConfig, RateLimitConfig

# Create an orchestrator with rate limiting
orchestrator = Orchestrator(
    config=OrchestratorConfig(
        rate_limit_config=RateLimitConfig(
            rate=5  # Limit to 5 requests per second
        )
    )
)

# Process API calls without exceeding rate limits
api_ids = list(range(100))
results = await orchestrator.process([api_call], *api_ids)
```

3. **Combine Multiple Resilience Patterns**: For complex scenarios, combine multiple patterns.

```python
from opero import (
    Orchestrator, OrchestratorConfig, 
    RetryConfig, RateLimitConfig, ConcurrencyConfig
)

# Create an orchestrator with multiple resilience patterns
orchestrator = Orchestrator(
    config=OrchestratorConfig(
        retry_config=RetryConfig(max_attempts=3),
        rate_limit_config=RateLimitConfig(rate=10),
        concurrency_config=ConcurrencyConfig(limit=5),
        fallbacks=[fallback_function]
    )
)

# Process items with full resilience
results = await orchestrator.process([primary_function], *items)
```

### Logging Best Practices

1. **Configure Comprehensive Logging**: Set up logging to capture important events and errors.

```python
import logging
from opero import Orchestrator, OrchestratorConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("my_app")

# Pass the logger to the orchestrator
orchestrator = Orchestrator(
    config=OrchestratorConfig(
        logger=logger
    )
)
```

2. **Log Context Information**: Include relevant context in your function logs.

```python
import logging
from opero import orchestrate, OrchestratorConfig

logger = logging.getLogger("my_app")

@orchestrate(
    config=OrchestratorConfig(
        logger=logger
    )
)
async def process_item(item_id, context=None):
    context = context or {}
    logger.info(f"Processing item {item_id}", extra={"context": context})
    # Implementation
    ...
```

### Advanced Patterns

1. **Chaining Operations**: Chain multiple orchestrated operations together.

```python
from opero import orchestrate, OrchestratorConfig, RetryConfig

@orchestrate(
    config=OrchestratorConfig(
        retry_config=RetryConfig(max_attempts=3)
    )
)
async def fetch_data(item_id):
    # Fetch data implementation
    ...

@orchestrate(
    config=OrchestratorConfig(
        retry_config=RetryConfig(max_attempts=2)
    )
)
async def process_data(data):
    # Process data implementation
    ...

@orchestrate(
    config=OrchestratorConfig(
        retry_config=RetryConfig(max_attempts=2)
    )
)
async def save_result(processed_data):
    # Save result implementation
    ...

async def pipeline(item_id):
    # Chain operations together
    data = await fetch_data(item_id)
    processed = await process_data(data)
    result = await save_result(processed)
    return result
```

2. **Dynamic Configuration**: Adjust configuration based on runtime conditions.

```python
from opero import Orchestrator, OrchestratorConfig, RetryConfig

async def get_config_for_item(item):
    # Determine appropriate configuration based on item characteristics
    if item.priority == "high":
        return OrchestratorConfig(
            retry_config=RetryConfig(max_attempts=5),
            fallbacks=[high_priority_fallback]
        )
    else:
        return OrchestratorConfig(
            retry_config=RetryConfig(max_attempts=2),
            fallbacks=[standard_fallback]
        )

async def process_items(items):
    results = []
    for item in items:
        # Create orchestrator with dynamic configuration
        config = await get_config_for_item(item)
        orchestrator = Orchestrator(config=config)
        
        # Process item with appropriate resilience
        result = await orchestrator.execute(process_item, item)
        results.append(result)
    return results
```

## Core Components

### Orchestrator

The central class for managing resilient operations. The `Orchestrator` class provides a unified interface for applying various resilience mechanisms to function calls.

```python
from opero import Orchestrator, OrchestratorConfig, RetryConfig

# Create an orchestrator with various configurations
orchestrator = Orchestrator(
    config=OrchestratorConfig(
        retry_config=RetryConfig(max_attempts=3),
        fallbacks=[backup_function1, backup_function2],
        # Other configurations...
    )
)

# Execute a function with the configured resilience mechanisms
result = await orchestrator.execute(my_function, *args, **kwargs)

# Process multiple items with the same function
results = await orchestrator.process([my_function], *items)
```

#### Key Methods

- **execute**: Executes a single function with the configured resilience mechanisms.
  ```python
  result = await orchestrator.execute(my_function, *args, **kwargs)
  ```

- **process**: Processes multiple items with the same function or functions. Each item is processed individually.
  ```python
  results = await orchestrator.process([my_function], *items)
  ```

### FallbackChain

Manages sequential execution of fallback functions. The `FallbackChain` class provides a way to try multiple functions in sequence until one succeeds.

```python
from opero import FallbackChain

# Create a fallback chain with a primary function and fallbacks
# You can provide a single fallback function
chain1 = FallbackChain(primary_function, fallback_function)

# Or a list of fallback functions
chain2 = FallbackChain(primary_function, [fallback1, fallback2])

# Or no fallbacks at all
chain3 = FallbackChain(primary_function)

# Execute the chain - will try each function in order until one succeeds
result = await chain.execute(*args, **kwargs)
```

#### Key Methods

- **execute**: Executes the primary function and falls back to the fallback functions if the primary fails.
  ```python
  result = await chain.execute(*args, **kwargs)
  ```

- **has_fallbacks**: Checks if the chain has any fallback functions.
  ```python
  if chain.has_fallbacks():
      # Do something
  ```

### Configuration Classes

#### OrchestratorConfig

Unified configuration for the Orchestrator. This class brings together all the different configuration options for the Orchestrator.
```python
from opero import OrchestratorConfig, RetryConfig, RateLimitConfig

config = OrchestratorConfig(
    retry_config=RetryConfig(max_attempts=3),
    rate_limit_config=RateLimitConfig(rate=10),
    fallbacks=[backup_function],
    # Other configurations...
)
```

#### RetryConfig

Configure retry behavior. This class provides a way to configure how functions are retried when they fail.

```python
from opero import RetryConfig

retry_config = RetryConfig(
    max_attempts=3,                          # Maximum number of retry attempts
    wait_min=1.0,                            # Minimum wait time between retries (seconds)
    wait_max=60.0,                           # Maximum wait time between retries (seconds)
    wait_multiplier=1.0,                     # Multiplier for exponential backoff
    retry_exceptions=(ValueError, KeyError), # Exception types that trigger a retry
    reraise=True                             # Whether to reraise the last exception
)
```

#### RateLimitConfig

Configure rate limiting. This class provides a way to limit how frequently functions are called.

```python
from opero import RateLimitConfig

# Limit operations to 10 per second
rate_limit_config = RateLimitConfig(rate=10.0)
```

#### ConcurrencyConfig

Configure concurrency limits. This class provides a way to limit how many operations can be executed concurrently.

```python
from opero import ConcurrencyConfig

# Limit to 5 concurrent operations
concurrency_config = ConcurrencyConfig(limit=5)
```

#### MultiprocessConfig

Configure multiprocessing. This class provides a way to configure how operations are executed across multiple processes.

```python
from opero import MultiprocessConfig

# Use 4 worker processes with the pathos backend
multiprocess_config = MultiprocessConfig(max_workers=4, backend="pathos")
```

### @orchestrate Decorator

Apply orchestration to functions. The `@orchestrate` decorator provides a way to apply orchestration to functions without having to create an Orchestrator instance.

```python
from opero import orchestrate, OrchestratorConfig, RetryConfig

@orchestrate(
    config=OrchestratorConfig(
        retry_config=RetryConfig(max_attempts=3),
        fallbacks=[backup_function]
    )
)
async def my_function(arg):
    # Function implementation
    pass

# The function now has retry and fallback capabilities
result = await my_function(some_arg)

# For processing multiple items
results = await my_function.process(item1, item2, item3)
```

### Logging Utilities

Opero provides several utilities for structured logging with context.

#### get_logger

Create a logger with a specific name and level.

```python
from opero import get_logger
import logging

# Create a logger with DEBUG level
logger = get_logger("my_app", level=logging.DEBUG)
```

#### ContextAdapter

Enhance a logger with context information.

```python
from opero import get_logger, ContextAdapter
import logging

# Create a logger with context support
logger = ContextAdapter(get_logger("my_app", level=logging.DEBUG))

# Add context information
logger.add_context(service="api_service", version="1.0.0")

# Log with context
logger.info("Starting service")  # Will include service and version in the log
```

#### log_context

A context manager for temporary logging context.

```python
from opero import log_context

# Use context manager for temporary context
with log_context(logger, operation="batch_process", batch_id="123"):
    logger.info("Starting batch processing")  # Will include operation and batch_id
    # Do something
    logger.info("Completed batch processing")  # Will include operation and batch_id

# Context from the context manager is removed here
logger.info("Continuing with other operations")  # Will not include operation and batch_id
```

## Development

This project uses [Hatch](https://hatch.pypa.io/) for development workflow management.

### Setup Development Environment

```bash
# Install hatch if you haven't already
pip install hatch

# Create and activate development environment
hatch shell

# Run tests
hatch run test

# Run tests with coverage
hatch run test-cov

# Run linting
hatch run lint

# Format code
hatch run format
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
