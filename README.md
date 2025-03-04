---
this_file: README.md
---

# Opero

[![PyPI version](https://img.shields.io/pypi/v/opero.svg)](https://pypi.org/project/opero/)
[![Python versions](https://img.shields.io/pypi/pyversions/opero.svg)](https://pypi.org/project/opero/)
[![License](https://img.shields.io/github/license/twardoch/opero.svg)](https://github.com/twardoch/opero/blob/main/LICENSE)

**Opero** is a Python package that provides a clean, Pythonic interface for orchestrating resilient, parallelized operations with fallback mechanisms, retry logic, rate limiting, and multiprocessing support. The name "Opero" comes from the Latin word for "to work" or "to operate."

## Key Features

- **Fallback Chains**: Automatically try alternative functions when primary operations fail
- **Automatic Retries**: Robust retry mechanism with configurable backoff strategies
- **Rate Limiting**: Control operation frequency to prevent resource exhaustion
- **Parallel Processing**: Execute operations concurrently with configurable limits
- **Async First**: Built for modern async workflows while fully supporting sync functions
- **Unified Interface**: Both class-based (`Orchestrator`) and decorator-based (`@orchestrate`) APIs
- **Composable**: Layer different resilience mechanisms as needed
- **Type Safety**: Comprehensive type hints for better IDE integration and error detection
- **Comprehensive Logging**: Structured logging with context for better debugging and monitoring
- **Error Resilience**: Robust error handling with proper propagation and recovery

## Recent Improvements

- **Enhanced Logging**: Added comprehensive logging throughout the codebase with configurable log levels
- **Improved Error Handling**: Better handling of errors in async/sync conversions and fallback scenarios
- **Optimized Core Functions**: Reduced complexity in key functions for better maintainability
- **Fixed Process Method**: Modified to apply functions to each item individually for more intuitive behavior
- **Code Quality**: Fixed various linter errors and improved type annotations

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

### Basic Usage with Fallbacks

```python
import asyncio
from opero import Orchestrator, OrchestratorConfig

async def primary_function(value):
    if value % 2 == 0:
        raise ValueError(f"Failed for value: {value}")
    return f"Primary: {value}"

async def fallback_function(value):
    return f"Fallback: {value}"

async def main():
    # Create an orchestrator with a fallback
    orchestrator = Orchestrator(
        config=OrchestratorConfig(
            fallbacks=[fallback_function]
        )
    )

    # Execute a single operation
    result = await orchestrator.execute(primary_function, 2)
    print(result)  # "Fallback: 2"

    # Process multiple items
    results = await orchestrator.process([primary_function], 1, 2, 3, 4)
    print(results)  # ["Primary: 1", "Fallback: 2", "Primary: 3", "Fallback: 4"]

asyncio.run(main())
```

### Using the Decorator with Retry

```python
import asyncio
from opero import orchestrate, RetryConfig, OrchestratorConfig

@orchestrate(
    config=OrchestratorConfig(
        retry_config=RetryConfig(
            max_attempts=3,
            wait_min=1.0,
            wait_max=5.0,
            wait_multiplier=1.5
        )
    )
)
async def unreliable_function(value):
    # This function will be retried up to 3 times if it fails
    if value % 3 == 0:
        raise ValueError(f"Failed for value: {value}")
    return f"Success: {value}"

async def main():
    # The function will be retried automatically if it fails
    result = await unreliable_function(3)  # Will retry but eventually use fallback
    print(result)

asyncio.run(main())
```

### Rate Limiting and Concurrency

```python
import asyncio
from opero import Orchestrator, OrchestratorConfig, RateLimitConfig, ConcurrencyConfig

async def api_call(item):
    # Simulate an API call
    await asyncio.sleep(0.1)
    return f"Result: {item}"

async def main():
    # Create an orchestrator with rate limiting and concurrency control
    orchestrator = Orchestrator(
        config=OrchestratorConfig(
            rate_limit_config=RateLimitConfig(rate=5),  # 5 operations per second
            concurrency_config=ConcurrencyConfig(limit=3)  # Max 3 concurrent operations
        )
    )

    # Process multiple items with controlled concurrency and rate
    items = list(range(10))
    results = await orchestrator.process([api_call], *items)
    print(results)

asyncio.run(main())
```

### Using Structured Logging

```python
import asyncio
import logging
from opero import Orchestrator, OrchestratorConfig, get_logger, ContextAdapter, log_context

# Create a logger with context support
logger = ContextAdapter(get_logger("my_app", level=logging.DEBUG))

async def api_call(item):
    # Log with context
    logger.debug(f"Processing item {item}")
    await asyncio.sleep(0.1)
    return f"Result: {item}"

async def main():
    # Add global context
    logger.add_context(service="api_service", version="1.0.0")
    
    orchestrator = Orchestrator(
        config=OrchestratorConfig()
    )
    
    # Use context manager for temporary context
    with log_context(logger, operation="batch_process", batch_id="123"):
        logger.info("Starting batch processing")
        results = await orchestrator.process([api_call], *range(5))
        logger.info(f"Completed batch processing with {len(results)} results")
    
    # Context from the context manager is removed here
    logger.info("Continuing with other operations")

asyncio.run(main())
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
  results = await orchestrator.process([my_function], *items, **kwargs)
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

## Advanced Usage

### Mixing Sync and Async Functions

Opero seamlessly handles both synchronous and asynchronous functions. You can mix and match sync and async functions in fallback chains.

```python
from opero import Orchestrator, OrchestratorConfig

# Synchronous function
def sync_function(value):
    if value % 2 == 0:
        raise ValueError("Sync function failed")
    return f"Sync: {value}"

# Asynchronous function
async def async_function(value):
    return f"Async: {value}"

# Mix them in a fallback chain
orchestrator = Orchestrator(
    config=OrchestratorConfig(
        fallbacks=[async_function]
    )
)

# Works with both sync and async primary functions
result1 = await orchestrator.execute(sync_function, 2)   # "Async: 2"
result2 = await orchestrator.execute(async_function, 1)  # "Async: 1"
```

### Custom Retry Logic

Fine-tune retry behavior for specific exception types. You can configure which exceptions trigger retries and how the retries are performed.

```python
from opero import RetryConfig, orchestrate, OrchestratorConfig

# Only retry on specific exceptions
retry_config = RetryConfig(
    max_attempts=5,
    retry_exceptions=(ConnectionError, TimeoutError),
    wait_min=0.5,
    wait_max=10.0,
    wait_multiplier=2.0
)

@orchestrate(
    config=OrchestratorConfig(
        retry_config=retry_config
    )
)
async def network_operation(url):
    # Implementation...
    pass
```

### Multiprocessing for CPU-Bound Tasks

Use multiprocessing for CPU-intensive operations. This can significantly improve performance for CPU-bound tasks.

```python
from opero import Orchestrator, OrchestratorConfig, MultiprocessConfig

def cpu_intensive_task(data):
    # Heavy computation...
    return result

orchestrator = Orchestrator(
    config=OrchestratorConfig(
        multiprocess_config=MultiprocessConfig(
            max_workers=4,
            backend="pathos"  # More flexible serialization
        )
    )
)

# Process items in parallel using multiple processes
results = await orchestrator.process([cpu_intensive_task], *large_data_items)
```

### Using FallbackChain Directly

You can use the `FallbackChain` class directly for more control over fallback behavior. This is useful when you need to customize how fallbacks are executed.

```python
from opero import FallbackChain

async def primary_function(value):
    if value < 0:
        raise ValueError("Value must be non-negative")
    return f"Primary: {value}"

async def fallback1(value):
    if value == 0:
        raise ValueError("Value must be non-zero")
    return f"Fallback1: {value}"

async def fallback2(value):
    return f"Fallback2: {value}"

# Create a fallback chain with multiple fallbacks
chain = FallbackChain(primary_function, [fallback1, fallback2])

# Execute the chain with different values
result1 = await chain.execute(5)    # "Primary: 5"
result2 = await chain.execute(-5)   # "Fallback1: -5"
result3 = await chain.execute(0)    # "Fallback2: 0"
```

### Combining Multiple Resilience Mechanisms

Combine multiple resilience mechanisms for robust operations. This is useful for operations that need to be both resilient and performant.

```python
from opero import Orchestrator, OrchestratorConfig, RetryConfig, RateLimitConfig, ConcurrencyConfig

# Create an orchestrator with multiple resilience mechanisms
orchestrator = Orchestrator(
    config=OrchestratorConfig(
        retry_config=RetryConfig(max_attempts=3),
        rate_limit_config=RateLimitConfig(rate=10),
        concurrency_config=ConcurrencyConfig(limit=5),
        fallbacks=[backup_function]
    )
)

# Execute a function with all the configured resilience mechanisms
result = await orchestrator.execute(my_function, *args, **kwargs)
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
