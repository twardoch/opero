# Core API Reference

## Decorators

### @opero Decorator

The main decorator that adds resilience mechanisms to functions.

```python
def opero(
    retries: int = 3,
    backoff_factor: float = 1.5,
    min_delay: float = 0.1,
    max_delay: float = 30.0,
    retry_on: tuple[type[Exception], ...] = (Exception,),
    arg_fallback: str | None = None,
    cache: bool = False,
    cache_ttl: int | None = None,
    cache_key: Callable | None = None,
    cache_namespace: str = "opero",
    cache_backend: str = "memory",
    rate_limit: float | None = None,
    **kwargs: Any
) -> Callable[[F], F]:
    """
    Decorator that adds resilience mechanisms to a function.
    
    Args:
        retries: Number of retry attempts for failed operations.
        backoff_factor: Multiplier for exponential backoff between retries.
        min_delay: Minimum delay between retries in seconds.
        max_delay: Maximum delay between retries in seconds.
        retry_on: Tuple of exception types that should trigger a retry.
        arg_fallback: Name of parameter containing fallback values list.
        cache: Whether to cache function results.
        cache_ttl: Time-to-live for cached results in seconds.
        cache_key: Custom function to generate cache keys.
        cache_namespace: Namespace for cache entries.
        cache_backend: Cache backend to use ('memory', 'disk', 'redis').
        rate_limit: Maximum number of calls per second.
        **kwargs: Additional arguments passed to underlying implementations.
    
    Returns:
        Decorated function with resilience mechanisms.
    
    Examples:
        Basic retry with caching:
        ```python
        @opero(retries=3, cache=True, cache_ttl=300)
        def fetch_data(id: str):
            return api.get(f"/data/{id}")
        ```
        
        With fallback parameters:
        ```python
        @opero(arg_fallback="endpoint", retries=2)
        def call_api(data, endpoint=["primary.com", "backup.com"]):
            return requests.post(endpoint[0], json=data)
        ```
    """
```

### @opmap Decorator

Decorator that combines resilience mechanisms with parallel processing.

```python
def opmap(
    mode: Literal["thread", "process", "async", "async_process"] = "process",
    workers: int = 4,
    ordered: bool = True,
    progress: bool = True,
    retries: int = 3,
    backoff_factor: float = 1.5,
    min_delay: float = 0.1,
    max_delay: float = 30.0,
    retry_on: tuple[type[Exception], ...] = (Exception,),
    arg_fallback: str | None = None,
    cache: bool = False,
    cache_ttl: int | None = None,
    cache_namespace: str = "opero_opmap_item",
    rate_limit: float | None = None,
    **kwargs: Any
) -> Callable[[F], Callable[[Iterable], list]]:
    """
    Decorator for parallel processing with resilience mechanisms.
    
    Args:
        mode: Concurrency mode for parallel execution.
            - 'thread': Use ThreadPoolExecutor (good for I/O-bound tasks)
            - 'process': Use ProcessPoolExecutor (good for CPU-bound tasks)
            - 'async': Use asyncio for concurrent execution
            - 'async_process': Use aiomultiprocess for async functions in processes
        workers: Number of parallel workers.
        ordered: Whether to preserve input order in results.
        progress: Whether to show progress bar (if supported).
        retries: Number of retry attempts per item.
        backoff_factor: Multiplier for exponential backoff.
        min_delay: Minimum retry delay in seconds.
        max_delay: Maximum retry delay in seconds.
        retry_on: Exceptions that trigger retries.
        arg_fallback: Parameter name for fallback values.
        cache: Whether to cache individual item results.
        cache_ttl: Cache time-to-live in seconds.
        cache_namespace: Cache namespace for items.
        rate_limit: Rate limit per worker.
        **kwargs: Additional arguments.
    
    Returns:
        Decorator that returns a function accepting an iterable and returning results list.
    
    Examples:
        I/O-bound parallel processing:
        ```python
        @opmap(mode="thread", workers=10, cache=True)
        def download_file(url: str):
            return requests.get(url).content
        
        # Download multiple files in parallel
        contents = download_file(urls)
        ```
        
        CPU-bound processing with retries:
        ```python
        @opmap(mode="process", workers=4, retries=2)
        def process_image(image_path: str):
            return compute_intensive_operation(image_path)
        
        results = process_image(image_paths)
        ```
    """
```

## Core Functions

### get_cache_decorator

```python
def get_cache_decorator(
    cache: bool = True,
    cache_ttl: int | None = None,
    cache_key: Callable | None = None,
    cache_namespace: str = "opero",
    cache_backend: str = "memory",
    **kwargs: Any
) -> Callable:
    """
    Create a caching decorator.
    
    Args:
        cache: Enable caching.
        cache_ttl: Time-to-live in seconds.
        cache_key: Custom key generation function.
        cache_namespace: Cache namespace.
        cache_backend: Backend type ('memory', 'disk', 'redis').
        **kwargs: Backend-specific options.
    
    Returns:
        Caching decorator.
    """
```

### get_retry_decorator

```python
def get_retry_decorator(
    retries: int = 3,
    backoff_factor: float = 1.5,
    min_delay: float = 0.1,
    max_delay: float = 30.0,
    retry_on: tuple[type[Exception], ...] = (Exception,),
    **kwargs: Any
) -> Callable:
    """
    Create a retry decorator using tenacity.
    
    Args:
        retries: Maximum retry attempts.
        backoff_factor: Exponential backoff multiplier.
        min_delay: Minimum delay between retries.
        max_delay: Maximum delay between retries.
        retry_on: Exception types to retry.
        **kwargs: Additional tenacity options.
    
    Returns:
        Retry decorator.
    """
```

### get_rate_limit_decorator

```python
def get_rate_limit_decorator(
    rate_limit: float,
    **kwargs: Any
) -> Callable:
    """
    Create a rate limiting decorator.
    
    Args:
        rate_limit: Maximum calls per second.
        **kwargs: Additional options.
    
    Returns:
        Rate limiting decorator.
    """
```

### get_fallback_decorator

```python
def get_fallback_decorator(
    arg_fallback: str,
    **kwargs: Any
) -> Callable:
    """
    Create a parameter fallback decorator.
    
    Args:
        arg_fallback: Parameter name containing fallback values.
        **kwargs: Additional options.
    
    Returns:
        Fallback decorator.
    
    Raises:
        ValueError: If arg_fallback parameter not found or not a sequence.
    """
```

## Classes

### RateLimiter

```python
class RateLimiter:
    """
    Rate limiter implementation using asynciolimiter.
    
    Attributes:
        rate_limit: Maximum calls per second.
        limiter: Internal Limiter instance.
    
    Methods:
        acquire(): Acquire rate limit permit (async).
        __aenter__/__aexit__: Async context manager support.
    """
    
    def __init__(self, rate_limit: float):
        """Initialize rate limiter with specified rate."""
        
    async def acquire(self) -> None:
        """Wait until rate limit allows next call."""
```

## Exceptions

### OperoError

```python
class OperoError(RuntimeError):
    """
    Base exception for all Opero errors.
    
    All Opero-specific exceptions inherit from this class.
    """
```

### AllFailedError

```python
class AllFailedError(OperoError):
    """
    Raised when all retry attempts and fallbacks are exhausted.
    
    Attributes:
        message: Error description.
        errors: List of exceptions from each failed attempt.
    
    Example:
        ```python
        try:
            result = unreliable_function()
        except AllFailedError as e:
            print(f"All attempts failed: {e}")
            for i, error in enumerate(e.errors):
                print(f"  Attempt {i+1}: {error}")
        ```
    """
    
    def __init__(self, message: str, errors: list[Exception] | None = None):
        """
        Initialize with message and list of errors.
        
        Args:
            message: Description of the failure.
            errors: List of exceptions from failed attempts.
        """
```

## Type Definitions

```python
from typing import TypeVar, Callable, Any, Iterable

# Type variable for decorated functions
F = TypeVar('F', bound=Callable[..., Any])

# Type variable for return values
T = TypeVar('T')

# Parallel processing modes
ParallelMode = Literal["thread", "process", "async", "async_process"]

# Cache backends
CacheBackend = Literal["memory", "disk", "redis"]
```

## Configuration Objects

### CacheConfig

```python
@dataclass
class CacheConfig:
    """Configuration for caching behavior."""
    enabled: bool = False
    ttl: int | None = None
    backend: str = "memory"
    namespace: str = "opero"
    key_function: Callable | None = None
    backend_options: dict[str, Any] = field(default_factory=dict)
```

### RetryConfig

```python
@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    attempts: int = 3
    backoff_factor: float = 1.5
    min_delay: float = 0.1
    max_delay: float = 30.0
    retry_on: tuple[type[Exception], ...] = (Exception,)
```

### RateLimitConfig

```python
@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    rate: float | None = None
    burst: int = 1
```

## Usage Examples

### Combined Resilience Features

```python
from opero import opero, AllFailedError

@opero(
    retries=3,
    backoff_factor=2.0,
    cache=True,
    cache_ttl=600,
    rate_limit=5.0,
    arg_fallback="api_key"
)
def resilient_api_call(
    endpoint: str,
    api_key: list[str] = ["primary_key", "backup_key"]
):
    """
    Make API call with full resilience stack.
    
    - Checks cache first
    - Respects rate limit
    - Retries with exponential backoff
    - Falls back to backup API key
    """
    headers = {"Authorization": f"Bearer {api_key[0]}"}
    response = requests.get(endpoint, headers=headers)
    response.raise_for_status()
    return response.json()
```

### Parallel Processing with Resilience

```python
from opero import opmap

@opmap(
    mode="thread",
    workers=10,
    retries=2,
    cache=True,
    cache_ttl=3600,
    rate_limit=2.0,
    ordered=True
)
def scrape_product(product_id: int) -> dict:
    """Scrape product with rate limiting and caching."""
    url = f"https://api.example.com/products/{product_id}"
    response = requests.get(url)
    return response.json()

# Scrape 100 products in parallel with all protections
product_ids = range(1, 101)
results = scrape_product(product_ids)

# Handle results
successful = [r for r in results if not isinstance(r, Exception)]
failed = [r for r in results if isinstance(r, Exception)]
```

## See Also

- [Utilities API](utils.md) for helper functions
- [Configuration Guide](../getting-started/configuration.md) for detailed setup
- [Best Practices](../guide/best-practices.md) for production usage