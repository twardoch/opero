# Configuration

Master Opero's configuration options to fine-tune resilience patterns for your specific needs.

## Core Configuration Principles

Opero follows these configuration principles:

- **Sensible defaults** - Works great out of the box
- **Composable options** - Mix and match features as needed  
- **Environment-aware** - Adapt behavior based on context
- **Type-safe** - Full type hints for better IDE support

## Basic Configuration

### Retry Configuration

Control how Opero retries failed operations:

```python
from opero import opero

@opero(
    retries=5,              # Try up to 5 times (default: 3)
    backoff_factor=2.0,     # Double delay each retry (default: 1.5)
    min_delay=0.5,          # Minimum 0.5s delay (default: 0.1)
    max_delay=60.0,         # Maximum 60s delay (default: 30.0)
    retry_on=(ConnectionError, TimeoutError)  # Only retry these errors
)
async def api_call():
    pass
```

**Backoff calculation:**
```
delay = min(max_delay, min_delay * (backoff_factor ** attempt))

# With backoff_factor=2.0, min_delay=0.5:
# Attempt 1: 0.5s
# Attempt 2: 1.0s  
# Attempt 3: 2.0s
# Attempt 4: 4.0s
# Attempt 5: 8.0s
```

### Cache Configuration

Configure caching behavior:

```python
@opero(
    cache=True,                    # Enable caching
    cache_ttl=3600,               # Cache for 1 hour
    cache_backend="memory",        # Backend type
    cache_namespace="my_app",      # Namespace for keys
    cache_key=lambda *args, **kwargs: f"custom_{args[0]}"  # Custom key function
)
def expensive_operation(item_id: str):
    pass
```

**Available cache backends:**
- `"memory"` - In-memory cache (default, fastest)
- `"disk"` - Persistent disk cache  
- `"redis"` - Redis backend (requires Redis server)
- `"sqlite"` - SQLite-based cache

### Rate Limiting Configuration  

Control function call rates:

```python
@opero(
    rate_limit=10.0,              # 10 calls per second
    rate_limit_scope="global"      # or "per_function", "per_args"
)
def rate_limited_function():
    pass

# Multiple functions sharing rate limit
@opero(rate_limit=5.0, rate_limit_scope="global")
def api_call_1(): pass

@opero(rate_limit=5.0, rate_limit_scope="global")  
def api_call_2(): pass  # Shares the 5/sec limit with api_call_1
```

## Advanced Configuration

### Fallback Configuration

Configure parameter-based fallbacks:

```python
@opero(
    retries=2,
    arg_fallback="endpoint",       # Parameter name to cycle through
    fallback_delay=1.0,           # Delay between fallback attempts
    fallback_exceptions=(ConnectionError, HTTPError)  # Fallback triggers
)
def multi_endpoint_call(data: dict, endpoint: list[str]):
    # Opero tries each endpoint in order
    current_endpoint = endpoint[0]
    return requests.post(current_endpoint, json=data)

# Usage
endpoints = [
    "https://api.primary.com/v1/data",
    "https://api.backup.com/v1/data", 
    "https://api.emergency.com/v1/data"
]
result = multi_endpoint_call({"key": "value"}, endpoint=endpoints)
```

### Parallel Processing Configuration

Configure `@opmap` for optimal performance:

```python
from opero import opmap

@opmap(
    mode="thread",                 # Parallelization mode
    workers=20,                    # Number of workers
    ordered=True,                  # Preserve input order
    progress=True,                 # Show progress bar
    chunk_size=10,                 # Items per worker batch
    timeout=300.0,                 # Maximum time per item
    max_retries_per_item=3         # Retries for each item
)
def process_items(item):
    return expensive_operation(item)
```

**Choosing the right mode:**

```python
# I/O-bound tasks (API calls, file I/O)
@opmap(mode="thread", workers=50)
def io_task(item): pass

# CPU-bound tasks (calculations, data processing)
@opmap(mode="process", workers=8)  # Usually = CPU cores
def cpu_task(item): pass

# Async I/O tasks (many concurrent connections)
@opmap(mode="async", workers=100)
async def async_io_task(item): pass

# Async + CPU isolation
@opmap(mode="async_process", workers=4)
async def async_cpu_task(item): pass
```

## Environment-Based Configuration

### Configuration Profiles

Create reusable configuration profiles:

```python
from opero import opero

# Development profile
DEV_CONFIG = {
    "retries": 1,
    "cache": False,
    "rate_limit": None,
    "backoff_factor": 1.0
}

# Production profile  
PROD_CONFIG = {
    "retries": 5, 
    "cache": True,
    "cache_ttl": 3600,
    "rate_limit": 10.0,
    "backoff_factor": 2.0
}

# Use based on environment
import os
config = PROD_CONFIG if os.getenv("ENV") == "production" else DEV_CONFIG

@opero(**config)
def api_call():
    pass
```

### Environment Variables

Configure Opero via environment variables:

```python
import os

@opero(
    retries=int(os.getenv("OPERO_RETRIES", "3")),
    cache_ttl=int(os.getenv("OPERO_CACHE_TTL", "300")),
    rate_limit=float(os.getenv("OPERO_RATE_LIMIT", "10.0")),
)
def configurable_function():
    pass
```

### Configuration Files

Load configuration from files:

```python
import json
import yaml
from pathlib import Path

def load_opero_config(config_file: str = "opero.yaml"):
    """Load Opero configuration from file."""
    config_path = Path(config_file)
    
    if config_path.suffix == ".yaml":
        with open(config_path) as f:
            return yaml.safe_load(f)
    elif config_path.suffix == ".json":
        with open(config_path) as f:
            return json.load(f)
    else:
        raise ValueError(f"Unsupported config format: {config_path.suffix}")

# opero.yaml
"""
default:
  retries: 3
  cache: true
  cache_ttl: 300
  
api_calls:
  retries: 5
  rate_limit: 10.0
  arg_fallback: "endpoint"
  
batch_processing:
  mode: "thread" 
  workers: 20
  retries: 2
"""

# Usage
config = load_opero_config()

@opero(**config["api_calls"])
def api_function():
    pass
```

## Dynamic Configuration

### Runtime Configuration Changes

Update configuration based on runtime conditions:

```python
import time
from opero import opero

def adaptive_config():
    """Adjust configuration based on current load."""
    current_hour = time.gmtime().tm_hour
    
    if 9 <= current_hour <= 17:  # Business hours
        return {
            "rate_limit": 20.0,    # Higher rate limit
            "retries": 5,          # More retries
            "backoff_factor": 1.2  # Shorter backoff
        }
    else:  # Off hours
        return {
            "rate_limit": 5.0,     # Lower rate limit  
            "retries": 3,          # Fewer retries
            "backoff_factor": 2.0  # Longer backoff
        }

@opero(**adaptive_config())
def time_sensitive_api():
    pass
```

### Context-Aware Configuration

Configure based on function arguments:

```python
def priority_config(priority: str):
    """Configuration based on task priority."""
    configs = {
        "high": {
            "retries": 10,
            "backoff_factor": 1.1,
            "cache_ttl": 60
        },
        "normal": {
            "retries": 3,
            "backoff_factor": 1.5, 
            "cache_ttl": 300
        },
        "low": {
            "retries": 1,
            "backoff_factor": 2.0,
            "cache_ttl": 3600
        }
    }
    return configs.get(priority, configs["normal"])

# Apply configuration dynamically
def create_prioritized_function(priority: str):
    @opero(**priority_config(priority))
    def process_task(task_data):
        return expensive_operation(task_data)
    return process_task

# Usage
high_priority_processor = create_prioritized_function("high")
low_priority_processor = create_prioritized_function("low")
```

## Performance Tuning

### Memory-Optimized Configuration

For memory-constrained environments:

```python
@opero(
    cache="disk",              # Use disk instead of memory
    cache_ttl=300,            # Shorter cache duration
    max_cache_size=100        # Limit cache entries
)
def memory_efficient_function():
    pass

@opmap(
    mode="process",           # Isolate memory per worker
    workers=2,                # Fewer workers
    chunk_size=5              # Smaller batches
)
def memory_efficient_batch(items):
    pass
```

### High-Throughput Configuration

For maximum performance:

```python
@opero(
    cache="memory",           # Fastest cache
    cache_ttl=60,            # Short cache for fresh data
    rate_limit=None,         # No rate limiting
    retries=1,               # Fast failure
    backoff_factor=1.0       # No backoff delay
)
def high_performance_function():
    pass

@opmap(
    mode="async",            # Maximum concurrency
    workers=200,             # Many workers
    ordered=False,           # Skip ordering overhead
    progress=False           # Skip progress overhead
)
async def high_throughput_batch(items):
    pass
```

## Configuration Validation

### Type-Safe Configuration

Use type hints for configuration validation:

```python
from typing import Optional, List, Union
from dataclasses import dataclass

@dataclass
class OperoConfig:
    retries: int = 3
    cache: bool = True
    cache_ttl: Optional[int] = None
    rate_limit: Optional[float] = None
    arg_fallback: Optional[str] = None
    retry_on: tuple = (Exception,)
    
    def __post_init__(self):
        if self.retries < 0:
            raise ValueError("retries must be non-negative")
        if self.rate_limit is not None and self.rate_limit <= 0:
            raise ValueError("rate_limit must be positive")

# Usage
config = OperoConfig(retries=5, rate_limit=10.0)

@opero(**config.__dict__)
def validated_function():
    pass
```

### Configuration Testing

Test your configuration:

```python
import pytest
from unittest.mock import Mock

def test_retry_configuration():
    """Test retry behavior with specific configuration."""
    mock_func = Mock(side_effect=[ConnectionError(), ConnectionError(), "success"])
    
    @opero(retries=3, backoff_factor=1.0, min_delay=0.01)
    def test_func():
        return mock_func()
    
    result = test_func()
    assert result == "success"
    assert mock_func.call_count == 3

def test_cache_configuration():
    """Test cache behavior."""
    call_count = 0
    
    @opero(cache=True, cache_ttl=1)
    def test_func(x):
        nonlocal call_count
        call_count += 1
        return f"result_{x}"
    
    # First call
    result1 = test_func("test")
    assert call_count == 1
    
    # Second call (should be cached)
    result2 = test_func("test")
    assert call_count == 1
    assert result1 == result2
```

## Best Practices

### Configuration Guidelines

1. **Start simple** - Use defaults first, then customize
2. **Profile performance** - Measure before optimizing
3. **Environment-specific** - Different configs for dev/prod
4. **Document choices** - Explain why you chose specific values
5. **Test configurations** - Verify behavior with unit tests

### Common Patterns

```python
# API client configuration
API_CONFIG = {
    "retries": 3,
    "cache": True,
    "cache_ttl": 300,
    "rate_limit": 10.0,
    "arg_fallback": "api_key"
}

# Batch processing configuration  
BATCH_CONFIG = {
    "mode": "thread",
    "workers": 10,
    "retries": 2,
    "ordered": True,
    "progress": True
}

# Database operation configuration
DB_CONFIG = {
    "retries": 5,
    "backoff_factor": 2.0,
    "retry_on": (ConnectionError, TimeoutError),
    "cache": False  # Don't cache database writes
}
```

## Next Steps

Now that you understand configuration:

1. **[Basic Usage](../guide/basic-usage.md)** - Apply configurations in real scenarios
2. **[Advanced Features](../guide/advanced-features.md)** - Complex configuration patterns  
3. **[Best Practices](../guide/best-practices.md)** - Production configuration strategies
4. **[API Reference](../api/core.md)** - Complete parameter documentation