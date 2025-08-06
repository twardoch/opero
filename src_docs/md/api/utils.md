# Utilities

Helper functions, debugging tools, and troubleshooting guides for Opero.

## Logging Utilities

### Basic Logging Configuration

Set up logging to monitor Opero's internal operations:

```python
from opero.utils.logging import configure_logging
import logging

# Basic logging setup
logger = configure_logging(level=logging.INFO)

# Available log levels and what they show:
# DEBUG: Detailed internal operations, cache hits/misses, timing
# INFO: Function calls, retry attempts, fallback usage, worker status
# WARNING: Rate limiting actions, cache errors, configuration warnings
# ERROR: Failed attempts, configuration errors, system issues
```

### Structured Logging

For production environments, use structured logging:

```python
import structlog
from opero.utils.logging import setup_structured_logging

# Configure structured logging for production
setup_structured_logging()

# Get structured logger
logger = structlog.get_logger("my_app")

@opero(retries=3, cache=True)
def monitored_function(user_id: str):
    logger.info("Processing user", user_id=user_id)
    
    try:
        result = expensive_operation(user_id)
        logger.info("Operation successful", user_id=user_id, result_size=len(result))
        return result
    except Exception as e:
        logger.error("Operation failed", user_id=user_id, error=str(e))
        raise

# Logs will be in JSON format:
# {"event": "Processing user", "user_id": "123", "timestamp": "2024-01-15T10:30:00Z"}
# {"event": "Operation successful", "user_id": "123", "result_size": 42, "timestamp": "2024-01-15T10:30:01Z"}
```

### Custom Log Formatters

Create custom log formats for specific needs:

```python
from opero.utils.logging import OperoFormatter
import logging

class CustomOperoFormatter(OperoFormatter):
    """Custom formatter for Opero logs."""
    
    def format(self, record):
        # Add custom fields to log records
        if hasattr(record, 'opero_function'):
            record.msg = f"[{record.opero_function}] {record.msg}"
        
        if hasattr(record, 'opero_attempt'):
            record.msg = f"(attempt {record.opero_attempt}) {record.msg}"
        
        return super().format(record)

# Apply custom formatter
handler = logging.StreamHandler()
handler.setFormatter(CustomOperoFormatter())

logger = logging.getLogger("opero")
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

## Debugging Tools

### Function Analysis

Analyze Opero-decorated functions:

```python
from opero.utils.debug import analyze_function, get_execution_trace

@opero(retries=3, cache=True, rate_limit=10.0, arg_fallback="api_key")
def example_function(data: dict, api_key: list[str]):
    """Example function with multiple Opero features."""
    current_key = api_key[0]
    return make_api_call(data, current_key)

# Analyze function configuration
analysis = analyze_function(example_function)
print(analysis)

# Output:
# Function: example_function
# Decorators: @opero
# Configuration:
#   - Retries: 3 attempts with 1.5x exponential backoff
#   - Cache: enabled (memory backend, no TTL limit)
#   - Rate limiting: 10.0 calls per second
#   - Fallback parameter: api_key (list of backup values)
# Resilience layers: cache -> rate_limit -> retry -> fallback -> function
```

### Execution Tracing

Trace function execution to understand behavior:

```python
from opero.utils.debug import trace_execution

@trace_execution
@opero(retries=3, cache=True)
def traced_function(x: int):
    if x < 0:
        raise ValueError("Negative values not allowed")
    return x ** 2

# Execute with tracing
result = traced_function(5)

# Trace output:
# [TRACE] traced_function: Starting execution
# [TRACE] traced_function: Cache miss for key 'opero:traced_function:a1b2c3d4'
# [TRACE] traced_function: Rate limit check passed
# [TRACE] traced_function: Executing original function
# [TRACE] traced_function: Function completed successfully in 0.001s
# [TRACE] traced_function: Storing result in cache
# [TRACE] traced_function: Execution complete, returning result

# Execute again to see cache hit
result2 = traced_function(5)

# Trace output:
# [TRACE] traced_function: Starting execution  
# [TRACE] traced_function: Cache hit for key 'opero:traced_function:a1b2c3d4'
# [TRACE] traced_function: Returning cached result
```

### Performance Profiling

Profile Opero function performance:

```python
from opero.utils.debug import profile_function, PerformanceProfiler

# Quick profiling
@profile_function
@opero(retries=3, cache=True)
def profiled_function(n: int):
    time.sleep(0.1)  # Simulate work
    return sum(range(n))

# Execute multiple times to gather statistics
for i in range(10):
    result = profiled_function(100)

# Get profiling report
profiler = PerformanceProfiler.get_instance()
report = profiler.get_report("profiled_function")
print(report)

# Output:
# Performance Report for 'profiled_function':
# Total calls: 10
# Cache hits: 9 (90.0%)
# Average duration: 0.012s (cached: 0.001s, uncached: 0.101s)
# Success rate: 100.0%
# Retry rate: 0.0%
```

### Memory Usage Analysis

Monitor memory usage during parallel processing:

```python
from opero.utils.debug import MemoryTracker

@opmap(mode="process", workers=4)
def memory_intensive_task(item):
    # Simulate memory-intensive work
    data = [0] * (item * 1000)  # Allocate memory based on item
    return sum(data)

# Track memory usage
with MemoryTracker() as tracker:
    items = list(range(1, 101))  # Process 100 items
    results = memory_intensive_task(items)

# Get memory usage report
memory_report = tracker.get_report()
print(memory_report)

# Output:
# Memory Usage Report:
# Peak memory: 245.6 MB
# Average memory: 123.2 MB
# Memory efficiency: 87.3% (good utilization without excessive peaks)
# Recommendations:
#   - Current worker count (4) is appropriate for available memory
#   - Consider reducing batch size if peak memory exceeds limits
```

## Configuration Helpers

### Configuration Validation

Validate Opero configurations before applying:

```python
from opero.utils.config import validate_config, ConfigValidator

# Validate configuration dictionary
config = {
    "retries": 5,
    "cache": True,
    "cache_ttl": 3600,
    "rate_limit": 10.0,
    "arg_fallback": "api_key"
}

validator = ConfigValidator()
validation_result = validator.validate(config)

if validation_result.is_valid:
    print("Configuration is valid!")
else:
    print("Configuration errors:")
    for error in validation_result.errors:
        print(f"  - {error}")

# Example validation errors:
# Configuration errors:
#   - retries must be non-negative (got -1)
#   - rate_limit must be positive (got 0)
#   - cache_ttl must be positive when cache is enabled (got -300)
```

### Environment-Based Configuration

Load configuration from environment variables:

```python
from opero.utils.config import load_config_from_env

# Set environment variables
os.environ.update({
    "OPERO_RETRIES": "5",
    "OPERO_CACHE": "true", 
    "OPERO_CACHE_TTL": "3600",
    "OPERO_RATE_LIMIT": "20.0",
    "OPERO_BATCH_WORKERS": "8",
    "OPERO_BATCH_MODE": "thread"
})

# Load configuration
api_config = load_config_from_env(prefix="OPERO", config_type="api")
batch_config = load_config_from_env(prefix="OPERO", config_type="batch")

print(f"API config: {api_config}")
print(f"Batch config: {batch_config}")

# Output:
# API config: {'retries': 5, 'cache': True, 'cache_ttl': 3600, 'rate_limit': 20.0}
# Batch config: {'workers': 8, 'mode': 'thread'}

# Use configurations
@opero(**api_config)
def api_function():
    pass

@opmap(**batch_config, **api_config)
def batch_function(item):
    pass
```

### Configuration Templates

Pre-defined configuration templates for common scenarios:

```python
from opero.utils.config import ConfigTemplates

# Get predefined templates
templates = ConfigTemplates()

# API client template
api_config = templates.api_client(
    retries=5,
    cache_duration_minutes=30,
    rate_limit_per_second=15.0
)

# Batch processing template
batch_config = templates.batch_processing(
    workers=8,
    mode="thread",
    timeout_minutes=5
)

# Web scraping template
scraping_config = templates.web_scraping(
    max_retries=3,
    rate_limit=2.0,  # Respectful rate limiting
    cache_hours=1,
    user_agent_fallbacks=True
)

# Database operations template
db_config = templates.database_operations(
    connection_retries=3,
    no_cache=True,  # Don't cache database writes
    timeout_seconds=30
)

# Apply templates
@opero(**api_config)
def api_call():
    pass

@opmap(**batch_config)
def process_batch(item):
    pass
```

## Testing Utilities

### Mock Helpers

Utilities for testing Opero-decorated functions:

```python
from opero.utils.testing import OperoTestCase, mock_external_service

class TestMyAPI(OperoTestCase):
    """Test case with Opero-specific utilities."""
    
    def setUp(self):
        super().setUp()
        # Reset Opero state for each test
        self.reset_opero_state()
    
    def test_retry_behavior(self):
        """Test that retry mechanism works correctly."""
        
        # Mock external service with controlled failures
        with mock_external_service(
            fail_attempts=[1, 2],  # Fail first 2 attempts
            success_response={"data": "success"}
        ) as mock_service:
            
            @opero(retries=3)
            def api_call():
                return mock_service.call()
            
            result = api_call()
            
            self.assertEqual(result, {"data": "success"})
            self.assertEqual(mock_service.call_count, 3)
    
    def test_cache_behavior(self):
        """Test caching works correctly."""
        call_count = 0
        
        @opero(cache=True, cache_ttl=1)
        def cached_function(x):
            nonlocal call_count
            call_count += 1
            return f"result_{x}"
        
        # First call - should execute function
        result1 = cached_function("test")
        self.assertEqual(call_count, 1)
        
        # Second call - should use cache
        result2 = cached_function("test")
        self.assertEqual(call_count, 1)
        self.assertEqual(result1, result2)
        
        # Wait for cache expiry
        self.advance_time(1.1)
        
        # Third call - should execute function again
        result3 = cached_function("test")
        self.assertEqual(call_count, 2)
    
    def test_parallel_processing(self):
        """Test parallel processing with controlled timing."""
        
        @opmap(mode="thread", workers=3)
        def parallel_task(item):
            # Simulate work with controlled timing
            time.sleep(0.1)
            return item * 2
        
        items = list(range(10))
        
        with self.measure_time() as timer:
            results = parallel_task(items)
        
        # Should complete faster than sequential
        self.assertLess(timer.elapsed, 0.5)  # Less than 0.5s for parallel
        self.assertEqual(results, [i * 2 for i in items])
```

### Performance Testing

Tools for performance testing and benchmarking:

```python
from opero.utils.testing import BenchmarkSuite, performance_test

class OperoBenchmarks(BenchmarkSuite):
    """Benchmark suite for Opero performance testing."""
    
    def setup(self):
        """Set up test data."""
        self.test_items = list(range(1000))
        self.api_endpoints = [f"endpoint_{i}" for i in range(100)]
    
    @performance_test(iterations=10, warmup=2)
    def benchmark_sequential_processing(self):
        """Benchmark sequential processing."""
        def process_item(item):
            time.sleep(0.001)  # Simulate 1ms work
            return item ** 2
        
        results = [process_item(item) for item in self.test_items[:100]]
        return len(results)
    
    @performance_test(iterations=10, warmup=2)  
    def benchmark_parallel_processing(self):
        """Benchmark parallel processing with Opero."""
        
        @opmap(mode="thread", workers=10)
        def process_item(item):
            time.sleep(0.001)  # Simulate 1ms work
            return item ** 2
        
        results = process_item(self.test_items[:100])
        return len(results)
    
    @performance_test(iterations=20, warmup=5)
    def benchmark_caching_performance(self):
        """Benchmark caching performance."""
        
        @opero(cache=True)
        def expensive_operation(x):
            time.sleep(0.01)  # Simulate 10ms expensive operation
            return x ** 2
        
        # Mix of cached and uncached calls
        results = []
        for i in range(50):
            # This creates cache hits for repeated values
            value = i % 10  # Only 10 unique values, 50 calls
            result = expensive_operation(value)
            results.append(result)
        
        return len(results)

# Run benchmarks
benchmarks = OperoBenchmarks()
report = benchmarks.run_all()
print(report)

# Output:
# Benchmark Report:
# 
# benchmark_sequential_processing:
#   Mean: 105.2ms ± 2.1ms
#   Min: 102.1ms, Max: 108.7ms
#   
# benchmark_parallel_processing:  
#   Mean: 23.4ms ± 1.8ms
#   Min: 21.2ms, Max: 26.1ms
#   Speedup: 4.5x over sequential
#   
# benchmark_caching_performance:
#   Mean: 12.3ms ± 0.8ms  
#   Min: 11.1ms, Max: 13.9ms
#   Cache hit rate: 80% (40/50 calls)
```

## Async Utilities

### Async/Sync Interop

Utilities for working with both sync and async functions:

```python
from opero.utils.async_utils import ensure_async, run_sync, bridge_sync_async

# Convert sync function to async
def sync_function(x):
    time.sleep(0.1)
    return x * 2

async_version = ensure_async(sync_function)
result = await async_version(5)  # Works in async context

# Run async function in sync context
async def async_function(x):
    await asyncio.sleep(0.1)
    return x * 2

sync_result = run_sync(async_function(5))  # Works in sync context

# Bridge sync and async execution
@bridge_sync_async
def flexible_function(x):
    """Function that works in both sync and async contexts."""
    if asyncio.iscoroutinefunction(expensive_operation):
        return expensive_operation(x)  # Will be awaited if needed
    else:
        return expensive_operation(x)

# Works in both contexts:
sync_result = flexible_function(5)          # Sync context
async_result = await flexible_function(5)   # Async context
```

### Async Context Management

Manage async resources properly:

```python
from opero.utils.async_utils import AsyncResourceManager

class DatabaseConnectionPool(AsyncResourceManager):
    """Async context manager for database connections."""
    
    async def __aenter__(self):
        self.pool = await create_connection_pool()
        return self.pool
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.pool.close()

# Use with Opero
@opero(retries=3)
async def database_operation(query: str):
    async with DatabaseConnectionPool() as pool:
        async with pool.acquire() as conn:
            return await conn.execute(query)
```

## Troubleshooting Tools

### Common Issues Diagnostic

Diagnostic tools for common Opero issues:

```python
from opero.utils.troubleshooting import diagnose_issues, OperoDoctor

# Diagnose common issues
@opero(retries=3, cache=True, rate_limit=10.0)
def problematic_function():
    pass

doctor = OperoDoctor()
diagnosis = doctor.diagnose(problematic_function)

print(diagnosis.report)

# Example output:
# Opero Health Check for 'problematic_function':
# 
# ✓ Configuration: Valid
# ✓ Dependencies: All required packages installed
# ✓ Cache Backend: Memory cache accessible
# ✓ Rate Limiter: Configured correctly
# 
# Recommendations:
# - Consider using disk cache for persistence across restarts
# - Rate limit seems conservative, could increase for better throughput
# - Function has no fallback strategy, consider adding arg_fallback
```

### Performance Issues

Identify and resolve performance bottlenecks:

```python
from opero.utils.troubleshooting import PerformanceDiagnostic

@opmap(mode="thread", workers=20)
def slow_function(item):
    time.sleep(1)  # Simulated slow operation
    return item

# Diagnose performance issues
diagnostic = PerformanceDiagnostic()

with diagnostic.monitor("slow_function"):
    items = list(range(10))
    results = slow_function(items)

issues = diagnostic.get_issues()
for issue in issues:
    print(f"Issue: {issue.description}")
    print(f"Suggestion: {issue.suggestion}")

# Example output:
# Issue: High worker contention detected
# Suggestion: Reduce worker count from 20 to 8 for better resource utilization
# 
# Issue: Tasks completing much slower than expected
# Suggestion: Consider using process mode for CPU-bound tasks
# 
# Issue: Memory usage growing during execution  
# Suggestion: Implement memory-efficient processing with smaller batch sizes
```

### Error Analysis

Analyze error patterns and suggest improvements:

```python
from opero.utils.troubleshooting import ErrorAnalyzer

@opero(retries=3, arg_fallback="api_key")
def flaky_api_call(data, api_key: list[str]):
    import random
    if random.random() < 0.7:  # 70% failure rate
        raise ConnectionError("Service unavailable")
    return {"status": "success", "data": data}

# Collect error data
analyzer = ErrorAnalyzer()

for i in range(100):
    try:
        result = flaky_api_call({"id": i}, api_key=["key1", "key2", "key3"])
    except Exception as e:
        analyzer.record_error("flaky_api_call", e, {"attempt": i})

# Analyze error patterns
analysis = analyzer.analyze("flaky_api_call")
print(analysis.summary)

# Example output:
# Error Analysis for 'flaky_api_call':
# 
# Total errors: 72 out of 100 calls (72% error rate)
# 
# Error breakdown:
# - ConnectionError: 65 occurrences (90.3%)
# - TimeoutError: 7 occurrences (9.7%)
# 
# Patterns identified:
# - High error rate suggests external service instability
# - Errors cluster in time periods, suggesting service outages
# - Fallback mechanism activated in 23% of failed calls
# 
# Recommendations:
# - Increase retry count from 3 to 5
# - Add exponential backoff with jitter
# - Consider circuit breaker pattern for this service
# - Monitor external service health independently
```

## Integration Helpers

### Framework Integration

Helpers for integrating Opero with popular frameworks:

```python
from opero.utils.integration import FastAPIIntegration, DjangoIntegration

# FastAPI integration
class FastAPIOpero(FastAPIIntegration):
    """FastAPI-specific Opero integration."""
    
    def resilient_endpoint(self, **opero_config):
        """Decorator for resilient FastAPI endpoints."""
        def decorator(func):
            # Apply Opero with FastAPI-specific error handling
            opero_func = opero(**opero_config)(func)
            
            @wraps(opero_func)
            async def wrapper(*args, **kwargs):
                try:
                    return await opero_func(*args, **kwargs)
                except AllFailedError as e:
                    # Convert to FastAPI HTTPException
                    from fastapi import HTTPException
                    raise HTTPException(
                        status_code=503,
                        detail=f"Service temporarily unavailable: {e}"
                    )
            
            return wrapper
        return decorator

# Usage with FastAPI
from fastapi import FastAPI

app = FastAPI()
fastapi_opero = FastAPIOpero()

@app.get("/users/{user_id}")
@fastapi_opero.resilient_endpoint(retries=3, cache=True, cache_ttl=300)
async def get_user(user_id: str):
    return await fetch_user_data(user_id)
```

### Database Integration

Database-specific integration helpers:

```python
from opero.utils.integration import DatabaseIntegration

class SQLAlchemyIntegration(DatabaseIntegration):
    """SQLAlchemy-specific Opero integration."""
    
    def resilient_query(self, **opero_config):
        """Decorator for resilient database queries."""
        
        # Database-specific error types
        database_errors = (
            sqlalchemy.exc.DisconnectionError,
            sqlalchemy.exc.TimeoutError,
            sqlalchemy.exc.OperationalError
        )
        
        # Default configuration for database operations
        default_config = {
            "retries": 3,
            "backoff_factor": 2.0,
            "retry_on": database_errors,
            "cache": False  # Don't cache database writes by default
        }
        
        # Merge with user config
        config = {**default_config, **opero_config}
        
        return opero(**config)

# Usage
db_integration = SQLAlchemyIntegration()

@db_integration.resilient_query(retries=5)
def get_user_from_db(session, user_id):
    return session.query(User).filter(User.id == user_id).first()

@db_integration.resilient_query(cache=False, retries=2)
def update_user_in_db(session, user_id, data):
    user = session.query(User).filter(User.id == user_id).first()
    for key, value in data.items():
        setattr(user, key, value)
    session.commit()
    return user
```

## Monitoring and Metrics

### Metrics Collection

Collect detailed metrics about Opero operations:

```python
from opero.utils.metrics import MetricsCollector, get_metrics

# Global metrics collector
metrics = MetricsCollector()

@metrics.instrument
@opero(retries=3, cache=True, rate_limit=10.0)
def instrumented_function(x):
    time.sleep(0.1)
    return x * 2

# Execute function multiple times
for i in range(100):
    try:
        result = instrumented_function(i % 10)  # Creates cache hits
    except Exception:
        pass

# Get metrics report
report = metrics.get_report("instrumented_function")
print(report)

# Example output:
# Metrics Report for 'instrumented_function':
# 
# Call Statistics:
# - Total calls: 100
# - Successful calls: 100 (100.0%)
# - Failed calls: 0 (0.0%)
# 
# Performance:
# - Average response time: 0.012s
# - 95th percentile: 0.098s
# - 99th percentile: 0.102s
# 
# Cache Statistics:
# - Cache hit rate: 90.0% (90/100)
# - Cache miss rate: 10.0% (10/100)
# - Average cache response time: 0.001s
# 
# Retry Statistics:
# - Functions requiring retries: 0
# - Average retries per failed call: 0
# 
# Rate Limiting:
# - Rate limit violations: 0
# - Average wait time for rate limit: 0.005s
```

### Health Monitoring

Monitor the health of Opero-decorated functions:

```python
from opero.utils.monitoring import HealthMonitor

health_monitor = HealthMonitor()

@health_monitor.monitor
@opero(retries=3, cache=True)
def monitored_service():
    # Simulate occasional failures
    import random
    if random.random() < 0.1:  # 10% failure rate
        raise ConnectionError("Service temporarily unavailable")
    return {"status": "healthy"}

# Health monitor automatically tracks success/failure rates
# and can alert when thresholds are exceeded

# Get current health status
health_status = health_monitor.get_health("monitored_service")
print(f"Service health: {health_status.status}")
print(f"Success rate: {health_status.success_rate:.1%}")
print(f"Average response time: {health_status.avg_response_time:.3f}s")

# Configure alerting
health_monitor.configure_alerts(
    success_rate_threshold=0.95,  # Alert if success rate < 95%
    response_time_threshold=1.0,  # Alert if avg response time > 1s
    alert_callback=lambda service, issue: print(f"ALERT: {service} - {issue}")
)
```

## Summary

Opero's utilities provide comprehensive support for:

- **Debugging**: Function analysis, execution tracing, performance profiling
- **Configuration**: Validation, environment loading, templates
- **Testing**: Mock helpers, performance testing, benchmarking
- **Troubleshooting**: Issue diagnosis, performance analysis, error patterns
- **Integration**: Framework-specific helpers, database integration
- **Monitoring**: Metrics collection, health monitoring, alerting

These utilities help you get the most out of Opero in development, testing, and production environments.

## Next Steps

You've now mastered Opero's complete API and utilities! Consider:

1. **[Best Practices](../guide/best-practices.md)** - Production patterns and optimization strategies
2. **[Advanced Features](../guide/advanced-features.md)** - Complex patterns and custom implementations
3. **Contributing** - Help improve Opero by contributing to the project

## Utility Quick Reference

### Essential Imports

```python
# Logging
from opero.utils.logging import configure_logging

# Debugging  
from opero.utils.debug import analyze_function, trace_execution

# Configuration
from opero.utils.config import validate_config, load_config_from_env

# Testing
from opero.utils.testing import OperoTestCase, mock_external_service

# Async utilities
from opero.utils.async_utils import ensure_async, run_sync

# Troubleshooting
from opero.utils.troubleshooting import OperoDoctor, diagnose_issues

# Metrics
from opero.utils.metrics import MetricsCollector, get_metrics
```

### Common Utility Patterns

```python
# Basic logging setup
logger = configure_logging(level=logging.INFO)

# Function analysis
analysis = analyze_function(my_function)

# Configuration validation
validator = ConfigValidator()
result = validator.validate(config)

# Performance testing
@performance_test(iterations=10)
def benchmark_function(): pass

# Health monitoring
@health_monitor.monitor
@opero(retries=3)
def monitored_function(): pass
```