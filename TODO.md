---
this_file: TODO.md
---


# TODO

Tip: Periodically run `python ./cleanup.py status` to see results of lints and tests. Use `uv pip ...` not `pip ...`

## 1. Plan for Rewriting `opero`

### 1.1. Restructure API into Two Primary Decorators

#### 1.1.1. `@opero` Decorator
- Focus on providing resilience mechanisms for single functions
- Support both sync and async functions
- Integrate the following capabilities in a logical order:
  1. Caching (via twat-cache)
    - Support multiple cache backends (memory, disk, redis)
    - Configurable TTL and namespace
    - Custom key generation
  2. Retry mechanisms
  3. Parameter-based fallbacks with `arg_fallback`
  4. Rate limiting
- Allow simple configuration of each capability
- Support parameter-based fallbacks with `arg_fallback`

#### 1.1.2. `@operomap` Decorator
- Inspired by `twat-mp`'s map functions (`pmap`, `imap`, `amap`, `apmap`)
- Support parallel execution of functions over multiple inputs
- Integrate the following capabilities in a logical order:
  1. Caching (via twat-cache)
    - Shared cache configuration with `@opero`
    - Efficient caching for parallel operations
  2. Retry mechanisms
  3. Parameter-based fallbacks with `arg_fallback`
  4. Rate limiting
  5. Parallel execution (via twat-mp)
    - Process-based parallelism (pmap)
    - Thread-based parallelism (tmap)
    - Async-based parallelism (amap)
    - Process-pool async parallelism (apmap)
- Support various concurrency modes (process, thread, async)
- Support parameter-based fallbacks with `arg_fallback`

### 1.2. Simplify Configuration

- Remove the complex nested configuration classes
- Use simple function parameters with sensible defaults
- Make the API more intuitive with clear parameter names
- Focus exclusively on parameter-based fallbacks (trying the same function with different parameter values)
- Provide a logical order of operations for all resilience mechanisms

### 1.3. Implementation Plan

1. **Dependencies Integration**
   - Add `twat-mp>=1.0.0` as a dependency for parallel execution
     - Support for process, thread, and async-based parallelism
     - Efficient worker pool management
     - Progress tracking and cancellation support
   - Add `twat-cache>=2.3.0` as a dependency for caching functionality
     - Multiple backend support (memory, disk, redis)
     - Async-compatible caching
     - Flexible key generation and namespacing
   - Ensure compatibility between these libraries and opero

2. **Core Module Refactoring**
   - Identify and preserve the essential resilience mechanisms
   - Simplify the internal implementation
   - Remove unnecessary abstraction layers
   - Implement parameter-based fallback mechanism

3. **New Decorator API**
   - Implement the `@opero` decorator for single function resilience
   - Implement the `@operomap` decorator for parallel operations
   - DROP backward compatibility with the existing API, it's not important
   - Support parameter-based fallbacks exclusively

4. **Logical Processing Order**
   - Establish a clear order of operations for resilience mechanisms:
     1. Caching (check cache first before any execution)
     2. Retry mechanism (attempt execution multiple times)
     3. Parameter-based fallbacks (try alternative parameters)
     4. Rate limiting (control execution frequency)
     5. Concurrency (for operomap only)

5. **Function Signatures**
   ```python
   # @opero decorator with caching, retry, parameter-based fallbacks, and rate limiting
   @opero(
       # Caching options (via twat-cache)
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
       retry_on=(Exception,),          # Exception types to retry on
       
       # Fallback options
       arg_fallback="model",           # Parameter name containing fallback values
       
       # Rate limiting options
       rate_limit=None,                # Operations per second (if needed)
   )
   def call_llm(prompt: str, model: list[str] = ["gpt-4", "gpt-3.5"]):
       # Will try with model="gpt-4" first, then model="gpt-3.5" if it fails
       pass

   # @operomap decorator with caching, retry, parameter-based fallbacks, rate limiting, and concurrency
   @operomap(
       # Caching options (via twat-cache)
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
       retry_on=(Exception,),          # Exception types to retry on
       
       # Fallback options
       arg_fallback="model",           # Parameter name containing fallback values
       
       # Rate limiting options
       rate_limit=None,                # Operations per second (if needed)
       
       # Concurrency options (via twat-mp)
       mode="process",                 # "process", "thread", or "async"
       workers=4,                      # Number of workers
       ordered=True,                   # Whether to preserve input order in results
       progress=True                   # Enable progress tracking
   )
   def process_item(item, model: list[str] = ["gpt-4", "gpt-3.5"]):
       # Process a single item
       return result
   
   # Usage
   results = process_item([item1, item2, item3])
   ```

### 1.4. Testing Strategy

1. Create unit tests for both decorators
2. Test each resilience mechanism individually:
   - Caching functionality with different backends
   - Retry mechanisms with various backoff strategies
   - Parameter-based fallbacks
   - Rate limiting
   - Concurrency modes
3. Test the integration of multiple resilience mechanisms
4. Test edge cases and error scenarios
5. Ensure performance is comparable to or better than the previous implementation

### 1.5. Documentation Updates

1. Rewrite README.md with the new API
2. Create clear, concise examples for both decorators
3. Provide migration guide for users of the old API
4. Document all parameters and their behavior
5. Include examples of each resilience mechanism
6. Document the logical order of operations

### 1.6. Code Cleanup

1. Remove deprecated functionality
2. Simplify internal implementation
3. Use modern Python features (match statements, type hints)
4. Minimize dependencies (except for twat-mp and twat-cache)

### 1.7. Release Plan

1. Implement core functionality first
2. Release an alpha version for feedback
3. Refine based on user feedback
4. Complete documentation
5. Release beta version
6. Final release

### 1.8. Example Usage After Refactoring

```python
from opero import opero, operomap

# Using caching and parameter-based fallbacks
@opero(cache=True, cache_ttl=3600, arg_fallback="model")
async def call_llm(prompt: str, model: list[str] = ["gpt-4", "gpt-3.5"]):
    # Will try with model="gpt-4" first, then model="gpt-3.5" if it fails
    # Results will be cached for 1 hour
    response = await api_call(prompt=prompt, model=model)
    return response

# Simple retry with no fallbacks or caching
@opero(retries=3, cache=False)
async def fetch_data(item_id):
    # Implementation that might fail
    ...

# Parallel processing with caching, resilience, and rate limiting
@operomap(mode="process", workers=4, retries=2, rate_limit=10, cache=True)
def process_item(item):
    # Process a single item
    return result

# Parameter-based fallbacks with parallel processing and caching
@operomap(
    mode="thread",
    workers=4,
    arg_fallback="api_key",
    cache=True,
    cache_ttl=1800,
    progress=True
)
def call_api(item, api_key: list[str] = ["primary_key", "backup_key", "emergency_key"]):
    # Will try each API key in order if previous ones fail
    # Results will be cached for 30 minutes
    return make_request(item, api_key=api_key)

# Usage examples
data = await call_llm("Tell me about Python")  # Will try with gpt-4, fallback to gpt-3.5, and cache results
results = call_api([item1, item2, item3])      # Process items in parallel with key fallbacks and caching
```

### 1.9. Timeline

1. Core refactoring: 1-2 weeks
2. New decorator implementation: 1 week
3. Testing and bug fixes: 1 week
4. Documentation: 2-3 days
5. Release process: 1 week

Total estimated time: ~4 weeks

### 1.10. Implementation Details for Parameter-Based Fallbacks

To implement parameter-based fallbacks, the decorator will:

1. Parse and validate the decorated function's signature
2. Check if the specified `arg_fallback` parameter exists and has a sequence type
3. When the function is called:
   - Store the original parameter value (list of fallback options)
   - Try executing the function with the first value in the list
   - If an exception occurs, retry with the next value in the list
   - Continue until success or all values are exhausted
   
This implementation must handle:
- Proper type annotation preservation
- Documentation generation
- Graceful failure if the parameter isn't a sequence
- Integration with other resilience mechanisms (caching, retries, rate limiting)

## 2. Detailed Implementation Steps

### 2.1. Create New File Structure

1. Create new core modules:
   ```
   src/opero/
   ├── __init__.py            # Re-exports public API
   ├── _version.py            # Version information
   ├── decorators/            # New directory for decorators
   │   ├── __init__.py        # Re-exports decorators
   │   ├── opero.py           # @opero decorator implementation
   │   └── operomap.py        # @operomap decorator implementation
   ├── core/                  # Core functionality
   │   ├── __init__.py
   │   ├── cache.py           # Integration with twat-cache
   │   ├── retry.py           # Retry mechanisms
   │   ├── fallback.py        # Parameter-based fallback implementation
   │   └── rate_limit.py      # Rate limiting mechanisms
   ├── concurrency/           # Concurrency implementations (using twat-mp)
   │   ├── __init__.py
   │   └── pool.py            # Integration with twat-mp
   └── utils/                 # Utility functions
       ├── __init__.py
       ├── async_utils.py     # Async utilities
       └── logging.py         # Logging utilities
   ```

2. Rename existing modules to avoid conflicts during development:
   - `core.py` → `_old_core.py`
   - `decorators.py` → `_old_decorators.py`
   - etc.

### 2.2. Implement Cache Integration with twat-cache

1. Create `core/cache.py` with key features:
   ```python
   from typing import Any, Callable, TypeVar, ParamSpec, Optional, Union, Dict
   import functools
   import inspect
   
   # Import from twat-cache
   from twat_cache import ucache, CacheContext
   
   P = ParamSpec('P')
   R = TypeVar('R')
   
   def get_cache_decorator(
       cache: bool = True,
       cache_ttl: Optional[int] = None,
       cache_backend: str = "memory",
       cache_key: Optional[Callable] = None,
       cache_namespace: str = "opero",
       **kwargs
   ) -> Callable[[Callable[P, R]], Callable[P, R]]:
       """
       Get a cache decorator from twat-cache based on the provided configuration.
       
       Args:
           cache: Whether to enable caching
           cache_ttl: Time-to-live for cache entries in seconds
           cache_backend: Cache backend to use ("memory", "disk", "redis", etc.)
           cache_key: Custom function to generate cache keys
           cache_namespace: Namespace for cache entries
           **kwargs: Additional arguments to pass to the cache decorator
           
       Returns:
           A cache decorator function
       """
       if not cache:
           # Return a no-op decorator if caching is disabled
           return lambda func: func
       
       # Configure the cache decorator
       cache_config = {
           "ttl": cache_ttl,
           "preferred_engine": cache_backend,
           "namespace": cache_namespace,
       }
       
       if cache_key:
           cache_config["key_builder"] = cache_key
           
       # Add any additional kwargs
       cache_config.update(kwargs)
       
       # Return the configured cache decorator
       return lambda func: ucache(**cache_config)(func)
   
   def get_cache_context(
       cache_backend: str = "memory",
       cache_namespace: str = "opero",
       **kwargs
   ) -> CacheContext:
       """
       Get a cache context for manual cache operations.

