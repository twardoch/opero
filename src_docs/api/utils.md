# Utilities API Reference

This module provides utility functions for logging, async operations, and other helper functionality.

## Logging Utilities

### configure_logging

```python
def configure_logging(
    level: int = logging.INFO,
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers: list[logging.Handler] | None = None
) -> logging.Logger:
    """
    Configure logging for Opero with sensible defaults.
    
    Args:
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
        format: Log message format string.
        handlers: Optional list of logging handlers.
    
    Returns:
        Configured logger instance.
    
    Example:
        ```python
        from opero.utils import configure_logging
        import logging
        
        # Basic configuration
        logger = configure_logging(level=logging.DEBUG)
        
        # Custom format
        logger = configure_logging(
            level=logging.INFO,
            format="%(levelname)s - %(message)s"
        )
        
        # With file handler
        file_handler = logging.FileHandler('opero.log')
        logger = configure_logging(handlers=[file_handler])
        ```
    """
```

### get_logger

```python
def get_logger(name: str | None = None) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name. If None, returns the Opero root logger.
    
    Returns:
        Logger instance.
    
    Example:
        ```python
        from opero.utils import get_logger
        
        # Get module-specific logger
        logger = get_logger(__name__)
        
        # Get Opero root logger
        root_logger = get_logger()
        ```
    """
```

### logger

```python
logger: logging.Logger
"""
Pre-configured logger instance for Opero.

This is the default logger used internally by Opero for all logging operations.

Example:
    ```python
    from opero.utils import logger
    
    logger.info("Starting operation")
    logger.debug("Debug information")
    logger.error("An error occurred", exc_info=True)
    ```
"""
```

## Async Utilities

### is_async_function

```python
def is_async_function(func: Callable) -> bool:
    """
    Check if a function is async (coroutine function).
    
    Args:
        func: Function to check.
    
    Returns:
        True if the function is async, False otherwise.
    
    Example:
        ```python
        async def async_func():
            pass
        
        def sync_func():
            pass
        
        print(is_async_function(async_func))  # True
        print(is_async_function(sync_func))   # False
        ```
    """
```

### ensure_async

```python
def ensure_async(func: Callable[..., T]) -> Callable[..., Awaitable[T]]:
    """
    Convert a sync function to async if needed.
    
    Args:
        func: Function to potentially convert.
    
    Returns:
        Async version of the function.
    
    Example:
        ```python
        def sync_function(x):
            return x * 2
        
        async_version = ensure_async(sync_function)
        
        # Can now await it
        result = await async_version(5)  # Returns 10
        ```
    """
```

### run_async

```python
def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """
    Run an async coroutine in a sync context.
    
    Args:
        coro: Coroutine to run.
    
    Returns:
        Result of the coroutine.
    
    Example:
        ```python
        async def async_operation():
            await asyncio.sleep(1)
            return "Done"
        
        # Run from sync code
        result = run_async(async_operation())
        print(result)  # "Done"
        ```
    
    Note:
        This function handles event loop creation and cleanup properly,
        avoiding common pitfalls with asyncio.run() in nested contexts.
    """
```

## Cache Utilities

### clear_cache

```python
def clear_cache(
    namespace: str | None = None,
    backend: str | None = None
) -> None:
    """
    Clear cached results.
    
    Args:
        namespace: Specific namespace to clear. If None, clears all.
        backend: Specific backend to clear. If None, clears all backends.
    
    Example:
        ```python
        from opero import clear_cache
        
        # Clear all caches
        clear_cache()
        
        # Clear specific namespace
        clear_cache(namespace="api_cache")
        
        # Clear specific backend
        clear_cache(backend="redis")
        ```
    """
```

### get_cache_context

```python
def get_cache_context(
    backend: str = "memory",
    namespace: str = "opero",
    **kwargs: Any
) -> CacheContext:
    """
    Get a cache context for direct cache operations.
    
    Args:
        backend: Cache backend type.
        namespace: Cache namespace.
        **kwargs: Backend-specific options.
    
    Returns:
        Cache context object.
    
    Example:
        ```python
        from opero.utils import get_cache_context
        
        # Get cache context
        cache = get_cache_context(backend="redis", namespace="my_cache")
        
        # Direct cache operations
        cache.set("key", "value", ttl=300)
        value = cache.get("key")
        cache.delete("key")
        ```
    """
```

## Type Utilities

### AsyncOrSync

```python
AsyncOrSync = Union[Callable[..., T], Callable[..., Awaitable[T]]]
"""
Type alias for functions that can be either sync or async.

Used internally by Opero to handle both function types uniformly.
"""
```

### F

```python
F = TypeVar('F', bound=Callable[..., Any])
"""
Type variable for generic callable types.

Used in decorator signatures to preserve function types.
"""
```

## Internal Utilities

### compose_decorators

```python
def compose_decorators(*decorators: Callable) -> Callable:
    """
    Compose multiple decorators into a single decorator.
    
    Args:
        *decorators: Decorators to compose, applied in order.
    
    Returns:
        Composed decorator.
    
    Example:
        ```python
        # Instead of:
        @decorator1
        @decorator2
        @decorator3
        def func():
            pass
        
        # Can use:
        combined = compose_decorators(decorator1, decorator2, decorator3)
        
        @combined
        def func():
            pass
        ```
    
    Note:
        This is primarily used internally by Opero to combine
        cache, retry, rate limit, and fallback decorators.
    """
```

### normalize_exceptions

```python
def normalize_exceptions(
    exceptions: Exception | type[Exception] | tuple[type[Exception], ...]
) -> tuple[type[Exception], ...]:
    """
    Normalize exception specifications to a tuple of exception types.
    
    Args:
        exceptions: Single exception, type, or tuple of types.
    
    Returns:
        Normalized tuple of exception types.
    
    Example:
        ```python
        # All of these return (ValueError, TypeError)
        normalize_exceptions(ValueError)
        normalize_exceptions((ValueError, TypeError))
        normalize_exceptions(ValueError())  # instance
        ```
    """
```

## Environment Utilities

### get_env_bool

```python
def get_env_bool(key: str, default: bool = False) -> bool:
    """
    Get boolean value from environment variable.
    
    Args:
        key: Environment variable name.
        default: Default value if not set.
    
    Returns:
        Boolean value.
    
    Example:
        ```python
        # OPERO_DEBUG=true
        debug = get_env_bool("OPERO_DEBUG")  # True
        
        # OPERO_CACHE=false
        cache = get_env_bool("OPERO_CACHE", default=True)  # False
        ```
    
    Note:
        Recognizes: true/false, yes/no, 1/0, on/off (case-insensitive)
    """
```

### get_env_int

```python
def get_env_int(key: str, default: int = 0) -> int:
    """
    Get integer value from environment variable.
    
    Args:
        key: Environment variable name.
        default: Default value if not set or invalid.
    
    Returns:
        Integer value.
    
    Example:
        ```python
        # OPERO_WORKERS=8
        workers = get_env_int("OPERO_WORKERS", default=4)  # 8
        
        # OPERO_TIMEOUT not set
        timeout = get_env_int("OPERO_TIMEOUT", default=30)  # 30
        ```
    """
```

## Usage Examples

### Custom Logging Setup

```python
import logging
from opero.utils import configure_logging, get_logger

# Configure with custom handlers
file_handler = logging.FileHandler('app.log')
console_handler = logging.StreamHandler()

logger = configure_logging(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[file_handler, console_handler]
)

# Get logger for specific module
module_logger = get_logger('myapp.module')
module_logger.info("Module initialized")
```

### Async/Sync Compatibility

```python
from opero.utils import ensure_async, is_async_function, run_async

# Make any function awaitable
def sync_operation(x):
    return x * 2

async def async_operation(x):
    await asyncio.sleep(0.1)
    return x * 3

# Convert sync to async
async_sync_op = ensure_async(sync_operation)

# Use in async context
async def process():
    # Both can be awaited now
    result1 = await async_sync_op(5)  # 10
    result2 = await async_operation(5)  # 15
    
    # Check function types
    print(is_async_function(sync_operation))   # False
    print(is_async_function(async_operation))  # True
    
    return result1 + result2

# Run async from sync code
total = run_async(process())  # 25
```

### Direct Cache Operations

```python
from opero.utils import get_cache_context, clear_cache

# Get cache context for direct operations
cache = get_cache_context(
    backend="redis",
    namespace="user_data",
    redis_url="redis://localhost:6379"
)

# Set with TTL
cache.set("user:123", {"name": "John", "age": 30}, ttl=3600)

# Get value
user_data = cache.get("user:123")

# Check existence
if cache.exists("user:123"):
    print("User data cached")

# Delete specific key
cache.delete("user:123")

# Clear entire namespace
clear_cache(namespace="user_data")
```

## See Also

- [Core API](core.md) for main decorators and functions
- [Configuration Guide](../getting-started/configuration.md) for setup options
- [Advanced Features](../guide/advanced-features.md) for complex scenarios