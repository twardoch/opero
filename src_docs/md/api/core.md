# Core Components

Deep dive into Opero's core implementation, internal architecture, and advanced usage patterns.

## Internal Architecture

Opero's decorators work by composing multiple layers of functionality around your functions:

```python
# Conceptual view of how @opero works internally
def opero_decorator(**config):
    def decorator(func):
        # Layer 1: Cache (outermost - checked first)
        cached_func = get_cache_decorator(func, **cache_config)
        
        # Layer 2: Rate limiting
        rate_limited_func = get_rate_limit_decorator(cached_func, **rate_config)
        
        # Layer 3: Retry logic (includes fallbacks)
        retry_func = get_retry_decorator(rate_limited_func, **retry_config)
        
        # Layer 4: Fallback handling (innermost)
        fallback_func = get_fallback_decorator(retry_func, **fallback_config)
        
        return fallback_func
    return decorator
```

## Decorator Implementation Details

### The `@opero` Decorator

Located in `src/opero/decorators/opero.py`, the decorator orchestrates multiple resilience mechanisms:

```python
from opero.decorators.opero import opero
from opero.core.cache import get_cache_decorator
from opero.core.rate_limit import get_rate_limit_decorator
from opero.core.retry import get_retry_decorator
from opero.core.fallback import get_fallback_decorator

def opero(
    retries: int = 3,
    backoff_factor: float = 1.5,
    min_delay: float = 0.1,
    max_delay: float = 30.0,
    cache: bool = False,
    cache_ttl: Optional[int] = None,
    cache_backend: str = "memory",
    cache_key: Optional[Callable] = None,
    cache_namespace: str = "opero",
    rate_limit: Optional[float] = None,
    rate_limit_scope: str = "per_function",
    arg_fallback: Optional[str] = None,
    fallback_delay: float = 0.0,
    retry_on: Union[Exception, Tuple[Exception, ...]] = Exception,
    **kwargs
):
    """
    Add resilience mechanisms to a function.
    
    The decorator applies layers in this order:
    1. Cache check (if enabled)
    2. Rate limiting (if configured)  
    3. Retry logic (with fallbacks inside each retry)
    4. Fallback parameter cycling
    5. Original function execution
    """
    
    def decorator(func: Callable) -> Callable:
        # Validate configuration
        _validate_opero_config(locals())
        
        # Build the resilience stack
        enhanced_func = func
        
        # Apply fallback handling (innermost)
        if arg_fallback:
            enhanced_func = get_fallback_decorator(
                enhanced_func,
                arg_fallback=arg_fallback,
                fallback_delay=fallback_delay
            )
        
        # Apply retry logic
        enhanced_func = get_retry_decorator(
            enhanced_func,
            retries=retries,
            backoff_factor=backoff_factor,
            min_delay=min_delay,
            max_delay=max_delay,
            retry_on=retry_on
        )
        
        # Apply rate limiting
        if rate_limit:
            enhanced_func = get_rate_limit_decorator(
                enhanced_func,
                rate_limit=rate_limit,
                scope=rate_limit_scope
            )
        
        # Apply caching (outermost)
        if cache:
            enhanced_func = get_cache_decorator(
                enhanced_func,
                ttl=cache_ttl,
                backend=cache_backend,
                key_func=cache_key,
                namespace=cache_namespace
            )
        
        return enhanced_func
    
    return decorator
```

### The `@opmap` Decorator

Located in `src/opero/decorators/opmap.py`, combines resilience with parallel processing:

```python
from opero.decorators.opmap import opmap
from opero.concurrency.pool import get_pool_executor

def opmap(
    mode: str = "thread",
    workers: int = 4,
    ordered: bool = True,
    progress: bool = True,
    timeout: Optional[float] = None,
    chunk_size: Optional[int] = None,
    # Include all @opero parameters
    **opero_kwargs
):
    """
    Parallel processing with per-item resilience.
    
    Process:
    1. Apply @opero decorator to the function (per-item resilience)
    2. Create appropriate executor pool based on mode
    3. Distribute items across workers
    4. Collect and return results
    """
    
    def decorator(func: Callable) -> Callable:
        # First, make the function resilient for individual items
        resilient_func = opero(**opero_kwargs)(func)
        
        def parallel_wrapper(items: Iterable) -> List:
            # Get appropriate executor
            executor = get_pool_executor(
                mode=mode,
                workers=workers,
                timeout=timeout
            )
            
            # Process items in parallel
            if mode == "async":
                return _async_parallel_execution(
                    resilient_func, items, executor, ordered, progress
                )
            else:
                return _sync_parallel_execution(
                    resilient_func, items, executor, ordered, progress
                )
        
        return parallel_wrapper
    
    return decorator
```

## Core Components Deep Dive

### Cache Implementation

The caching system in `src/opero/core/cache.py` provides a flexible abstraction over multiple backends:

```python
from opero.core.cache import CacheManager, get_cache_decorator

class CacheManager:
    """Manages cache operations across different backends."""
    
    def __init__(self, backend: str = "memory", **backend_config):
        self.backend = self._create_backend(backend, backend_config)
        self.stats = CacheStats()
    
    def _create_backend(self, backend_type: str, config: dict):
        """Factory method for cache backends."""
        if backend_type == "memory":
            from twat_cache import MemoryCache
            return MemoryCache(**config)
        elif backend_type == "disk":
            from twat_cache import DiskCache
            return DiskCache(**config)
        elif backend_type == "redis":
            from twat_cache import RedisCache
            return RedisCache(**config)
        elif backend_type == "sqlite":
            from twat_cache import SQLiteCache
            return SQLiteCache(**config)
        else:
            raise ValueError(f"Unknown cache backend: {backend_type}")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = await self.backend.get(key)
            if value is not None:
                self.stats.record_hit(key)
                return value
            else:
                self.stats.record_miss(key)
                return None
        except Exception as e:
            self.stats.record_error(key, e)
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        try:
            return await self.backend.set(key, value, ttl=ttl)
        except Exception as e:
            self.stats.record_error(key, e)
            return False

def get_cache_decorator(
    func: Callable,
    ttl: Optional[int] = None,
    backend: str = "memory",
    key_func: Optional[Callable] = None,
    namespace: str = "opero",
    **backend_config
) -> Callable:
    """Create cache decorator for a function."""
    
    cache_manager = CacheManager(backend, **backend_config)
    
    def generate_cache_key(*args, **kwargs) -> str:
        """Generate cache key for function call."""
        if key_func:
            return f"{namespace}:{key_func(*args, **kwargs)}"
        else:
            # Default key generation
            import hashlib
            import json
            
            key_data = {
                "func": func.__name__,
                "args": args,
                "kwargs": sorted(kwargs.items())
            }
            key_str = json.dumps(key_data, sort_keys=True, default=str)
            key_hash = hashlib.sha256(key_str.encode()).hexdigest()[:16]
            return f"{namespace}:{func.__name__}:{key_hash}"
    
    @wraps(func)
    async def async_cached_wrapper(*args, **kwargs):
        cache_key = generate_cache_key(*args, **kwargs)
        
        # Try to get from cache
        cached_result = await cache_manager.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Execute function
        if asyncio.iscoroutinefunction(func):
            result = await func(*args, **kwargs)
        else:
            result = func(*args, **kwargs)
        
        # Store in cache
        await cache_manager.set(cache_key, result, ttl=ttl)
        
        return result
    
    @wraps(func)
    def sync_cached_wrapper(*args, **kwargs):
        # Sync wrapper for non-async functions
        return asyncio.run(async_cached_wrapper(*args, **kwargs))
    
    if asyncio.iscoroutinefunction(func):
        return async_cached_wrapper
    else:
        return sync_cached_wrapper
```

### Retry Implementation

The retry system in `src/opero/core/retry.py` uses the `tenacity` library with custom configuration:

```python
from opero.core.retry import get_retry_decorator
from tenacity import (
    Retrying, 
    stop_after_attempt, 
    wait_exponential,
    retry_if_exception_type
)

def get_retry_decorator(
    func: Callable,
    retries: int = 3,
    backoff_factor: float = 1.5,
    min_delay: float = 0.1,
    max_delay: float = 30.0,
    retry_on: Union[Exception, Tuple[Exception, ...]] = Exception
) -> Callable:
    """Create retry decorator with exponential backoff."""
    
    # Configure tenacity retry strategy
    retry_strategy = Retrying(
        stop=stop_after_attempt(retries + 1),  # +1 because initial attempt + retries
        wait=wait_exponential(
            multiplier=min_delay,
            max=max_delay,
            exp_base=backoff_factor
        ),
        retry=retry_if_exception_type(retry_on),
        reraise=True
    )
    
    @wraps(func)
    def retry_wrapper(*args, **kwargs):
        attempt_errors = []
        
        def execute_attempt():
            try:
                return func(*args, **kwargs)
            except Exception as e:
                attempt_errors.append(e)
                raise
        
        try:
            return retry_strategy(execute_attempt)
        except Exception:
            # All retries exhausted, raise AllFailedError
            from opero.exceptions import AllFailedError
            raise AllFailedError(
                f"All {retries + 1} attempts failed for {func.__name__}",
                errors=attempt_errors
            )
    
    return retry_wrapper
```

### Rate Limiting Implementation

The rate limiting system in `src/opero/core/rate_limit.py` uses `asynciolimiter` for precise rate control:

```python
from opero.core.rate_limit import RateLimitManager, get_rate_limit_decorator
from asynciolimiter import Limiter
import asyncio

class RateLimitManager:
    """Manages rate limiters with different scopes."""
    
    def __init__(self):
        self._limiters = {}
        self._lock = asyncio.Lock()
    
    async def get_limiter(self, scope: str, rate: float) -> Limiter:
        """Get or create rate limiter for scope."""
        async with self._lock:
            if scope not in self._limiters:
                self._limiters[scope] = Limiter(max_rate=rate, time_period=1.0)
            return self._limiters[scope]
    
    def generate_scope_key(
        self,
        scope_type: str,
        func_name: str,
        args: tuple,
        kwargs: dict
    ) -> str:
        """Generate scope key based on scope type."""
        if scope_type == "global":
            return "global"
        elif scope_type == "per_function":
            return f"func:{func_name}"
        elif scope_type == "per_args":
            import hashlib
            args_str = str(args) + str(sorted(kwargs.items()))
            args_hash = hashlib.md5(args_str.encode()).hexdigest()[:8]
            return f"args:{func_name}:{args_hash}"
        else:
            raise ValueError(f"Unknown rate limit scope: {scope_type}")

# Global rate limit manager
_rate_limit_manager = RateLimitManager()

def get_rate_limit_decorator(
    func: Callable,
    rate_limit: float,
    scope: str = "per_function"
) -> Callable:
    """Create rate limiting decorator."""
    
    @wraps(func)
    async def async_rate_limited_wrapper(*args, **kwargs):
        scope_key = _rate_limit_manager.generate_scope_key(
            scope, func.__name__, args, kwargs
        )
        limiter = await _rate_limit_manager.get_limiter(scope_key, rate_limit)
        
        # Wait for rate limit allowance
        async with limiter:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
    
    @wraps(func)
    def sync_rate_limited_wrapper(*args, **kwargs):
        return asyncio.run(async_rate_limited_wrapper(*args, **kwargs))
    
    if asyncio.iscoroutinefunction(func):
        return async_rate_limited_wrapper
    else:
        return sync_rate_limited_wrapper
```

### Fallback Implementation

The fallback system in `src/opero/core/fallback.py` manages parameter-based fallback strategies:

```python
from opero.core.fallback import get_fallback_decorator
import inspect
import time

def get_fallback_decorator(
    func: Callable,
    arg_fallback: str,
    fallback_delay: float = 0.0
) -> Callable:
    """Create parameter fallback decorator."""
    
    # Validate that the fallback parameter exists
    sig = inspect.signature(func)
    if arg_fallback not in sig.parameters:
        raise ValueError(
            f"Fallback parameter '{arg_fallback}' not found in function signature"
        )
    
    @wraps(func)
    def fallback_wrapper(*args, **kwargs):
        # Get the fallback parameter value
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        
        fallback_values = bound_args.arguments[arg_fallback]
        
        if not isinstance(fallback_values, (list, tuple)):
            # No fallback values, just execute normally
            return func(*args, **kwargs)
        
        if len(fallback_values) == 0:
            raise ValueError(f"Empty fallback list for parameter '{arg_fallback}'")
        
        last_exception = None
        
        for i, fallback_value in enumerate(fallback_values):
            try:
                # Update the parameter with current fallback value
                bound_args.arguments[arg_fallback] = [fallback_value]
                
                # Add delay between fallback attempts (except first)
                if i > 0 and fallback_delay > 0:
                    time.sleep(fallback_delay)
                
                # Execute with current fallback value
                return func(*bound_args.args, **bound_args.kwargs)
                
            except Exception as e:
                last_exception = e
                logger.debug(
                    f"Fallback attempt {i+1}/{len(fallback_values)} failed "
                    f"for {func.__name__} with {arg_fallback}={fallback_value}: {e}"
                )
                continue
        
        # All fallback values failed
        raise last_exception or Exception("All fallback attempts failed")
    
    return fallback_wrapper
```

## Parallel Processing Engine

### Pool Management

The concurrency system in `src/opero/concurrency/pool.py` manages different types of worker pools:

```python
from opero.concurrency.pool import PoolManager, get_pool_executor
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import asyncio

class PoolManager:
    """Manages worker pools for different execution modes."""
    
    def __init__(self):
        self._pools = {}
        self._lock = threading.Lock()
    
    def get_or_create_pool(
        self,
        mode: str,
        workers: int,
        timeout: Optional[float] = None
    ):
        """Get or create worker pool for specified mode."""
        pool_key = f"{mode}:{workers}:{timeout}"
        
        with self._lock:
            if pool_key not in self._pools:
                self._pools[pool_key] = self._create_pool(mode, workers, timeout)
            return self._pools[pool_key]
    
    def _create_pool(self, mode: str, workers: int, timeout: Optional[float]):
        """Factory method for different pool types."""
        if mode == "thread":
            return ThreadPoolExecutor(
                max_workers=workers,
                thread_name_prefix="opero-thread"
            )
        elif mode == "process":
            return ProcessPoolExecutor(
                max_workers=workers,
                mp_context=multiprocessing.get_context("spawn")
            )
        elif mode == "async":
            return AsyncPool(max_workers=workers)
        elif mode == "async_process":
            try:
                import aiomultiprocess
                return aiomultiprocess.Pool(processes=workers)
            except ImportError:
                raise ImportError(
                    "async_process mode requires 'opero[aiomultiprocess]' "
                    "installation"
                )
        else:
            raise ValueError(f"Unknown execution mode: {mode}")

class AsyncPool:
    """Custom async pool for handling concurrent async operations."""
    
    def __init__(self, max_workers: int = 100):
        self.semaphore = asyncio.Semaphore(max_workers)
        self.max_workers = max_workers
    
    async def map(self, func: Callable, items: Iterable, ordered: bool = True):
        """Execute async function across multiple items."""
        
        async def worker(item):
            async with self.semaphore:
                return await func(item)
        
        if ordered:
            # Maintain order by using asyncio.gather
            tasks = [worker(item) for item in items]
            return await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # Don't maintain order, process as completed
            tasks = [worker(item) for item in items]
            results = []
            for coro in asyncio.as_completed(tasks):
                result = await coro
                results.append(result)
            return results

# Global pool manager
_pool_manager = PoolManager()

def get_pool_executor(mode: str, workers: int, timeout: Optional[float] = None):
    """Get appropriate executor for the specified mode."""
    return _pool_manager.get_or_create_pool(mode, workers, timeout)
```

### Result Collection and Ordering

The result collection system handles different execution modes and maintains ordering when requested:

```python
def collect_results(
    executor,
    func: Callable,
    items: List,
    mode: str,
    ordered: bool = True,
    progress: bool = True
) -> List:
    """Collect results from parallel execution."""
    
    if mode == "async":
        return asyncio.run(_collect_async_results(
            executor, func, items, ordered, progress
        ))
    else:
        return _collect_sync_results(
            executor, func, items, ordered, progress
        )

def _collect_sync_results(executor, func, items, ordered, progress):
    """Collect results from sync executors (thread/process)."""
    
    if progress:
        from tqdm import tqdm
        items = tqdm(items, desc="Processing")
    
    if ordered:
        # Use executor.map to maintain order
        results = list(executor.map(func, items))
    else:
        # Use as_completed for better performance
        from concurrent.futures import as_completed
        
        # Submit all tasks
        future_to_item = {
            executor.submit(func, item): item 
            for item in items
        }
        
        results = []
        for future in as_completed(future_to_item):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append(e)
    
    return results

async def _collect_async_results(executor, func, items, ordered, progress):
    """Collect results from async executor."""
    
    if progress:
        from tqdm.asyncio import tqdm
        items = tqdm(items, desc="Processing")
    
    return await executor.map(func, items, ordered=ordered)
```

## Exception Handling

### Exception Hierarchy

```python
# src/opero/exceptions.py

class OperoError(RuntimeError):
    """Base exception for all Opero-related errors."""
    pass

class AllFailedError(OperoError):
    """Raised when all retry attempts and fallbacks fail."""
    
    def __init__(self, message: str, errors: List[Exception]):
        super().__init__(message)
        self.errors = errors
        self.attempt_count = len(errors)
    
    def __str__(self) -> str:
        base_msg = super().__str__()
        error_summary = []
        
        for i, error in enumerate(self.errors[:3], 1):  # Show first 3 errors
            error_summary.append(f"  {i}. {type(error).__name__}: {error}")
        
        if len(self.errors) > 3:
            error_summary.append(f"  ... and {len(self.errors) - 3} more errors")
        
        return f"{base_msg}\nAttempt details:\n" + "\n".join(error_summary)

class ConfigurationError(OperoError):
    """Raised when Opero is misconfigured."""
    pass

class CacheError(OperoError):
    """Raised when cache operations fail."""
    pass

class RateLimitError(OperoError):
    """Raised when rate limiting fails."""
    pass
```

### Error Context and Tracing

```python
from opero.utils.correlation import CorrelationContext

class ErrorContext:
    """Provides context for error tracking and debugging."""
    
    def __init__(self, func_name: str, correlation_id: str = None):
        self.func_name = func_name
        self.correlation_id = correlation_id or CorrelationContext.get_id()
        self.start_time = time.time()
        self.attempts = []
    
    def record_attempt(self, attempt_num: int, error: Optional[Exception] = None):
        """Record an attempt (success or failure)."""
        attempt_info = {
            "attempt": attempt_num,
            "timestamp": time.time(),
            "duration": time.time() - self.start_time,
            "error": error,
            "correlation_id": self.correlation_id
        }
        self.attempts.append(attempt_info)
    
    def to_dict(self) -> dict:
        """Convert context to dictionary for logging."""
        return {
            "function": self.func_name,
            "correlation_id": self.correlation_id,
            "total_duration": time.time() - self.start_time,
            "total_attempts": len(self.attempts),
            "attempts": self.attempts
        }
```

## Performance Optimizations

### Memory Management

```python
from opero.utils.memory import MemoryMonitor, memory_efficient

class MemoryMonitor:
    """Monitor memory usage during parallel processing."""
    
    def __init__(self, max_memory_mb: int = 1000):
        self.max_memory_mb = max_memory_mb
        self.peak_memory = 0
    
    def check_memory(self) -> float:
        """Check current memory usage in MB."""
        import psutil
        current_memory = psutil.Process().memory_info().rss / 1024 / 1024
        self.peak_memory = max(self.peak_memory, current_memory)
        return current_memory
    
    def should_throttle(self) -> bool:
        """Check if we should throttle processing to save memory."""
        return self.check_memory() > self.max_memory_mb * 0.8

def memory_efficient(max_memory_mb: int = 1000):
    """Decorator to make functions memory-efficient."""
    def decorator(func):
        monitor = MemoryMonitor(max_memory_mb)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            if monitor.should_throttle():
                import gc
                gc.collect()  # Force garbage collection
                
                if monitor.should_throttle():
                    import time
                    time.sleep(0.1)  # Brief pause to allow memory cleanup
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator
```

### Adaptive Configuration

```python
from opero.utils.adaptive import AdaptiveConfig

class AdaptiveConfig:
    """Dynamically adjust Opero configuration based on performance."""
    
    def __init__(self):
        self.performance_history = {}
        self.config_adjustments = {}
    
    def record_performance(
        self,
        func_name: str,
        config: dict,
        duration: float,
        success: bool
    ):
        """Record performance data for a function."""
        if func_name not in self.performance_history:
            self.performance_history[func_name] = []
        
        self.performance_history[func_name].append({
            "config": config.copy(),
            "duration": duration,
            "success": success,
            "timestamp": time.time()
        })
        
        # Keep only recent history
        if len(self.performance_history[func_name]) > 100:
            self.performance_history[func_name] = \
                self.performance_history[func_name][-50:]
    
    def suggest_config(self, func_name: str, current_config: dict) -> dict:
        """Suggest optimized configuration based on performance history."""
        if func_name not in self.performance_history:
            return current_config
        
        history = self.performance_history[func_name]
        recent_history = [h for h in history if time.time() - h["timestamp"] < 3600]
        
        if len(recent_history) < 10:
            return current_config
        
        # Analyze success rates by configuration
        config_performance = {}
        for record in recent_history:
            config_key = str(sorted(record["config"].items()))
            if config_key not in config_performance:
                config_performance[config_key] = {"successes": 0, "total": 0, "avg_duration": 0}
            
            config_performance[config_key]["total"] += 1
            if record["success"]:
                config_performance[config_key]["successes"] += 1
                config_performance[config_key]["avg_duration"] += record["duration"]
        
        # Find best performing configuration
        best_config = None
        best_score = 0
        
        for config_key, perf in config_performance.items():
            if perf["total"] < 5:  # Need minimum samples
                continue
            
            success_rate = perf["successes"] / perf["total"]
            avg_duration = perf["avg_duration"] / perf["successes"] if perf["successes"] > 0 else float('inf')
            
            # Score based on success rate and speed (lower duration is better)
            score = success_rate * 100 - avg_duration
            
            if score > best_score:
                best_score = score
                best_config = eval(config_key)  # Convert back to dict
        
        return dict(best_config) if best_config else current_config

# Global adaptive config manager
_adaptive_config = AdaptiveConfig()
```

## Debugging and Introspection

### Function Introspection

```python
from opero.utils.introspection import get_opero_info, analyze_function

def get_opero_info(func: Callable) -> dict:
    """Get information about Opero decorators applied to a function."""
    
    info = {
        "function_name": func.__name__,
        "is_opero_decorated": False,
        "is_opmap_decorated": False,
        "configuration": {},
        "layers": []
    }
    
    # Check for Opero attributes (added by decorators)
    if hasattr(func, '_opero_config'):
        info["is_opero_decorated"] = True
        info["configuration"] = func._opero_config
    
    if hasattr(func, '_opmap_config'):
        info["is_opmap_decorated"] = True
        info["configuration"].update(func._opmap_config)
    
    # Analyze wrapper layers
    current_func = func
    while hasattr(current_func, '__wrapped__'):
        wrapper_name = getattr(current_func, '_opero_layer', 'unknown')
        info["layers"].append(wrapper_name)
        current_func = current_func.__wrapped__
    
    return info

def analyze_function(func: Callable) -> str:
    """Generate human-readable analysis of function's Opero configuration."""
    
    info = get_opero_info(func)
    
    if not info["is_opero_decorated"] and not info["is_opmap_decorated"]:
        return f"Function '{info['function_name']}' is not decorated with Opero."
    
    analysis = [f"Analysis of '{info['function_name']}':"]
    
    config = info["configuration"]
    
    if info["is_opero_decorated"]:
        analysis.append("  ✓ @opero decorator applied")
        
        if config.get("retries", 0) > 0:
            analysis.append(f"    - Retries: {config['retries']} attempts")
            analysis.append(f"    - Backoff: {config.get('backoff_factor', 1.5)}x exponential")
        
        if config.get("cache", False):
            ttl = config.get("cache_ttl", "no limit")
            backend = config.get("cache_backend", "memory")
            analysis.append(f"    - Caching: {backend} backend, TTL: {ttl}")
        
        if config.get("rate_limit"):
            analysis.append(f"    - Rate limit: {config['rate_limit']}/sec")
        
        if config.get("arg_fallback"):
            analysis.append(f"    - Fallback parameter: {config['arg_fallback']}")
    
    if info["is_opmap_decorated"]:
        analysis.append("  ✓ @opmap decorator applied")
        analysis.append(f"    - Mode: {config.get('mode', 'thread')}")
        analysis.append(f"    - Workers: {config.get('workers', 4)}")
        analysis.append(f"    - Ordered: {config.get('ordered', True)}")
    
    if info["layers"]:
        analysis.append("  Resilience layers (outer to inner):")
        for layer in info["layers"]:
            analysis.append(f"    - {layer}")
    
    return "\n".join(analysis)

# Usage
@opero(retries=3, cache=True, rate_limit=10.0)
def example_function():
    pass

print(analyze_function(example_function))
```

## Next Steps

You've now explored Opero's core implementation details. Continue with:

1. **[Utilities](utils.md)** - Helper functions and troubleshooting tools
2. **[Best Practices](../guide/best-practices.md)** - Production patterns and optimization strategies

## Core Architecture Summary

Opero's power comes from its layered architecture:

1. **Configuration Validation** - Ensures valid parameters
2. **Decorator Composition** - Stacks resilience mechanisms
3. **Execution Flow** - Cache → Rate Limit → Retry → Fallback → Function
4. **Error Handling** - Comprehensive error tracking and context
5. **Parallel Processing** - Efficient distribution across workers
6. **Performance Optimization** - Adaptive configuration and memory management

This modular design allows you to pick and choose exactly the resilience mechanisms you need while maintaining high performance and reliability.