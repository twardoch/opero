# Best Practices

This guide provides recommendations for using Opero effectively in production environments.

## Design Principles

### 1. Start Simple, Evolve Gradually

Begin with minimal configuration and add features as needed:

```python
# Phase 1: Basic retry
@opero(retries=3)
def my_function():
    pass

# Phase 2: Add caching when you notice repeated calls
@opero(retries=3, cache=True, cache_ttl=300)
def my_function():
    pass

# Phase 3: Add rate limiting when hitting API limits
@opero(retries=3, cache=True, cache_ttl=300, rate_limit=10.0)
def my_function():
    pass
```

### 2. Be Explicit About Failure Modes

Specify which exceptions should trigger retries:

```python
# Good: Specific exceptions
@opero(
    retries=3,
    retry_on=(ConnectionError, TimeoutError, requests.HTTPError)
)
def network_operation():
    pass

# Bad: Catching all exceptions
@opero(
    retries=3,
    retry_on=Exception  # May retry on programming errors!
)
def risky_operation():
    pass
```

### 3. Design for Idempotency

Ensure operations can be safely retried:

```python
# Good: Idempotent operation
@opero(retries=3)
def update_user_status(user_id: int, status: str):
    # PUT is idempotent
    return api.put(f"/users/{user_id}", {"status": status})

# Bad: Non-idempotent operation
@opero(retries=3)
def increment_counter(counter_id: int):
    # POST might increment multiple times!
    return api.post(f"/counters/{counter_id}/increment")

# Better: Make it idempotent with request ID
@opero(retries=3)
def increment_counter_safe(counter_id: int, request_id: str):
    return api.post(
        f"/counters/{counter_id}/increment",
        {"request_id": request_id}  # Server deduplicates
    )
```

## Configuration Guidelines

### Cache Configuration

Match cache TTL to data characteristics:

```python
# Static data: Long or no TTL
@opero(cache=True)  # No TTL for immutable data
def get_country_codes():
    return fetch_country_codes()

# Frequently updated data: Short TTL
@opero(cache=True, cache_ttl=60)  # 1 minute
def get_stock_price(symbol: str):
    return fetch_stock_price(symbol)

# User-specific data: Medium TTL with smart keys
def user_cache_key(func, user_id, *args, **kwargs):
    return f"user:{user_id}:{func.__name__}"

@opero(
    cache=True,
    cache_ttl=900,  # 15 minutes
    cache_key=user_cache_key
)
def get_user_preferences(user_id: int):
    return fetch_user_preferences(user_id)
```

### Retry Configuration

Balance reliability with responsiveness:

```python
# Fast failures for user-facing operations
@opero(
    retries=2,
    backoff_factor=1.5,
    max_delay=3.0  # Cap at 3 seconds
)
def user_facing_api_call():
    pass

# More aggressive for background jobs
@opero(
    retries=5,
    backoff_factor=2.0,
    max_delay=60.0  # Can wait longer
)
def background_sync_operation():
    pass

# Critical operations with fallbacks
@opero(
    retries=3,
    arg_fallback="provider",
    cache=True
)
def critical_payment_operation(
    amount: float,
    provider: list[str] = ["primary_gateway", "backup_gateway"]
):
    pass
```

### Parallel Processing

Choose the right concurrency mode:

```python
# I/O-bound: Use threads
@opmap(
    mode="thread",
    workers=20,  # Can exceed CPU count for I/O
    rate_limit=5.0  # Respect external service limits
)
def fetch_web_pages(url: str):
    return requests.get(url).text

# CPU-bound: Use processes
@opmap(
    mode="process",
    workers=os.cpu_count(),  # Match CPU cores
    cache=True  # Cache expensive computations
)
def process_image(image_path: str):
    return apply_filters(load_image(image_path))

# Async I/O: Use async mode
@opmap(
    mode="async",
    workers=100,  # High concurrency for async
    ordered=True
)
async def fetch_async_data(item_id: int):
    async with aiohttp.ClientSession() as session:
        return await fetch_item(session, item_id)
```

## Error Handling Patterns

### Graceful Degradation

Always have a fallback plan:

```python
from opero import opero, AllFailedError
import logging

logger = logging.getLogger(__name__)

def get_product_info(product_id: int):
    """Get product info with multiple fallback levels."""
    
    # Level 1: Try primary service with retries
    try:
        return get_product_from_api(product_id)
    except AllFailedError as e:
        logger.warning(f"API failed for product {product_id}: {e}")
    
    # Level 2: Try cache
    try:
        cached = get_product_from_cache(product_id)
        if cached:
            logger.info(f"Serving cached data for product {product_id}")
            return cached
    except Exception as e:
        logger.error(f"Cache lookup failed: {e}")
    
    # Level 3: Return degraded response
    logger.error(f"All sources failed for product {product_id}")
    return {
        "id": product_id,
        "name": "Product information temporarily unavailable",
        "status": "degraded"
    }

@opero(retries=3, cache=True, cache_ttl=300)
def get_product_from_api(product_id: int):
    return api.get(f"/products/{product_id}")

@opero(cache=True, cache_ttl=3600)
def get_product_from_cache(product_id: int):
    return cache.get(f"product:{product_id}")
```

### Structured Error Logging

Log errors with context for debugging:

```python
import structlog

logger = structlog.get_logger()

@opero(
    retries=3,
    on_retry=lambda e, attempt: logger.warning(
        "retry_attempt",
        exception=str(e),
        attempt=attempt,
        max_attempts=3
    )
)
def operation_with_structured_logging(request_id: str, data: dict):
    logger.info("operation_started", request_id=request_id)
    
    try:
        result = process_data(data)
        logger.info("operation_completed", request_id=request_id)
        return result
    except Exception as e:
        logger.error(
            "operation_failed",
            request_id=request_id,
            error=str(e),
            data_size=len(data)
        )
        raise
```

## Performance Optimization

### Minimize Decorator Overhead

Consolidate decorators when possible:

```python
# Less efficient: Multiple decorator layers
@cache_decorator()
@retry_decorator()
@rate_limit_decorator()
def my_function():
    pass

# More efficient: Single Opero decorator
@opero(cache=True, retries=3, rate_limit=10.0)
def my_function():
    pass
```

### Optimize Cache Keys

Use efficient cache key generation:

```python
# Inefficient: Large objects in cache key
@opero(cache=True)
def process_large_object(huge_dict: dict):
    pass  # Entire dict gets serialized for key

# Efficient: Use identifying attributes
def efficient_cache_key(func, data_id: str, version: int, **kwargs):
    return f"{func.__name__}:{data_id}:v{version}"

@opero(cache=True, cache_key=efficient_cache_key)
def process_by_id(data_id: str, version: int, large_data: dict = None):
    # Only ID and version in cache key
    pass
```

### Batch Operations

Process items in batches for efficiency:

```python
from typing import List

def batch_items(items: List, batch_size: int):
    """Split items into batches."""
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]

@opmap(
    mode="thread",
    workers=5,
    cache=True
)
def process_batch(batch: List[dict]):
    """Process a batch of items together."""
    # More efficient than processing individually
    return api.post("/batch-process", {"items": batch})

# Usage
all_items = get_items()  # 1000 items
batches = list(batch_items(all_items, batch_size=50))  # 20 batches
results = process_batch(batches)
```

## Production Deployment

### Health Checks

Implement health check endpoints:

```python
from datetime import datetime, timedelta

class HealthChecker:
    def __init__(self):
        self.last_success = {}
        self.failure_counts = {}
    
    def record_success(self, component: str):
        self.last_success[component] = datetime.now()
        self.failure_counts[component] = 0
    
    def record_failure(self, component: str):
        self.failure_counts[component] = self.failure_counts.get(component, 0) + 1
    
    def is_healthy(self, component: str, max_age_minutes: int = 5) -> bool:
        if component not in self.last_success:
            return False
        
        age = datetime.now() - self.last_success[component]
        recent = age < timedelta(minutes=max_age_minutes)
        not_failing = self.failure_counts.get(component, 0) < 3
        
        return recent and not_failing

health = HealthChecker()

@opero(
    retries=2,
    on_success=lambda: health.record_success("api"),
    on_failure=lambda e: health.record_failure("api")
)
def monitored_api_call():
    return api.get("/health")

# Health check endpoint
def health_check():
    return {
        "status": "healthy" if health.is_healthy("api") else "unhealthy",
        "components": {
            "api": health.is_healthy("api"),
            "cache": health.is_healthy("cache"),
            "database": health.is_healthy("database")
        }
    }
```

### Graceful Shutdown

Handle shutdown signals properly:

```python
import signal
import sys
from concurrent.futures import ThreadPoolExecutor

class GracefulShutdown:
    def __init__(self):
        self.shutdown = False
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)
    
    def _handle_signal(self, signum, frame):
        logger.info(f"Received signal {signum}, initiating shutdown")
        self.shutdown = True

shutdown_handler = GracefulShutdown()

@opmap(
    mode="thread",
    workers=10,
    should_process=lambda: not shutdown_handler.shutdown
)
def long_running_task(item):
    if shutdown_handler.shutdown:
        raise SystemExit("Shutdown requested")
    
    return process_item(item)
```

### Resource Management

Properly manage resources:

```python
from contextlib import contextmanager

@contextmanager
def managed_resource():
    """Ensure resources are cleaned up."""
    resource = acquire_resource()
    try:
        yield resource
    finally:
        release_resource(resource)

@opero(retries=3, cache=True)
def operation_with_resources(data):
    with managed_resource() as resource:
        return resource.process(data)
```

## Security Considerations

### Input Validation

Always validate inputs:

```python
from pydantic import BaseModel, validator

class APIRequest(BaseModel):
    user_id: int
    action: str
    
    @validator('action')
    def action_must_be_valid(cls, v):
        allowed = ['read', 'write', 'delete']
        if v not in allowed:
            raise ValueError(f'Action must be one of {allowed}')
        return v

@opero(retries=2, cache=True)
def secure_api_operation(request: APIRequest):
    # Input is validated by Pydantic
    return process_request(request)
```

### Sensitive Data

Handle sensitive data carefully:

```python
def redact_sensitive_data(data: dict) -> dict:
    """Redact sensitive fields for logging."""
    sensitive_fields = ['password', 'api_key', 'token']
    redacted = data.copy()
    
    for field in sensitive_fields:
        if field in redacted:
            redacted[field] = '***REDACTED***'
    
    return redacted

@opero(
    retries=3,
    on_retry=lambda e, attempt: logger.warning(
        "Retry attempt",
        attempt=attempt,
        error=str(e)
        # Do NOT log sensitive data!
    )
)
def handle_sensitive_operation(user_data: dict):
    logger.info("Processing user", user_id=user_data.get('id'))
    # Never log full user_data
    return process_user(user_data)
```

## Testing Strategies

### Test Resilience Mechanisms

```python
import pytest
from unittest.mock import Mock, patch

def test_retry_behavior():
    mock_func = Mock(side_effect=[
        ConnectionError("First attempt"),
        ConnectionError("Second attempt"),
        {"success": True}  # Third attempt succeeds
    ])
    
    @opero(retries=3)
    def test_function():
        return mock_func()
    
    result = test_function()
    assert result == {"success": True}
    assert mock_func.call_count == 3

def test_fallback_behavior():
    @opero(arg_fallback="endpoint", retries=1)
    def test_api_call(endpoint=["primary", "backup"]):
        if endpoint[0] == "primary":
            raise ConnectionError("Primary failed")
        return f"Success with {endpoint[0]}"
    
    result = test_api_call()
    assert result == "Success with backup"
```

## Summary

Key takeaways for production use:

1. **Start simple** and add features incrementally
2. **Be explicit** about failure modes and exceptions
3. **Design for idempotency** to enable safe retries
4. **Monitor everything** with structured logging and metrics
5. **Plan for degradation** with multiple fallback levels
6. **Test resilience** mechanisms thoroughly
7. **Manage resources** properly with cleanup
8. **Validate inputs** and handle sensitive data carefully

Following these practices will help you build robust, scalable applications with Opero.