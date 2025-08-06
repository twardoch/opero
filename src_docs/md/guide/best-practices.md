# Best Practices

Production-ready patterns, performance optimization strategies, and proven approaches for building resilient applications with Opero.

## Architecture Patterns

### Layered Resilience Architecture

Structure your application with multiple resilience layers:

```python
from opero import opero, opmap
import logging
from functools import wraps

# Layer 1: Application-level resilience patterns
class ResilientAPIClient:
    """Base class for resilient API clients."""
    
    def __init__(self, base_url: str, api_keys: list[str], timeout: int = 30):
        self.base_url = base_url
        self.api_keys = api_keys
        self.timeout = timeout
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @opero(
        retries=3,
        backoff_factor=2.0,
        cache=True,
        cache_ttl=300,
        rate_limit=10.0,
        arg_fallback="api_key"
    )
    async def _base_request(self, endpoint: str, api_key: list[str], **kwargs):
        """Base request method with resilience."""
        current_key = api_key[0]
        headers = {"Authorization": f"Bearer {current_key}"}
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(self.timeout)) as session:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            async with session.get(url, headers=headers, **kwargs) as response:
                response.raise_for_status()
                return await response.json()
    
    async def get(self, endpoint: str, **kwargs):
        """Public GET method."""
        return await self._base_request(endpoint, api_key=self.api_keys, **kwargs)

# Layer 2: Service-level resilience
class UserService:
    """User service with service-level resilience patterns."""
    
    def __init__(self):
        self.api_client = ResilientAPIClient(
            base_url="https://api.users.com",
            api_keys=["primary_key", "backup_key"]
        )
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @opero(cache=True, cache_ttl=600)  # Cache user data for 10 minutes
    async def get_user(self, user_id: str):
        """Get single user with caching."""
        try:
            return await self.api_client.get(f"users/{user_id}")
        except Exception as e:
            self.logger.error(f"Failed to fetch user {user_id}: {e}")
            # Return default user data for graceful degradation
            return {"id": user_id, "name": "Unknown User", "email": None}
    
    @opmap(
        mode="async",
        workers=20,
        retries=2,
        ordered=True,
        progress=True
    )
    async def get_users_batch(self, user_ids: list[str]):
        """Batch user fetching with parallelization."""
        results = []
        for user_id in user_ids:
            try:
                user_data = await self.get_user(user_id)
                results.append(user_data)
            except Exception as e:
                self.logger.warning(f"Failed to fetch user {user_id} in batch: {e}")
                results.append(None)
        return results

# Layer 3: Application-level coordination
class ApplicationController:
    """Application controller coordinating multiple services."""
    
    def __init__(self):
        self.user_service = UserService()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def get_user_dashboard(self, user_id: str):
        """Get complete user dashboard data."""
        try:
            # Each service handles its own resilience
            user_data = await self.user_service.get_user(user_id)
            
            # Combine data from multiple services
            dashboard_data = {
                "user": user_data,
                "timestamp": time.time(),
                "status": "success"
            }
            
            return dashboard_data
            
        except Exception as e:
            self.logger.error(f"Dashboard generation failed for user {user_id}: {e}")
            # Graceful degradation at application level
            return {
                "user": {"id": user_id, "name": "Unknown User"},
                "timestamp": time.time(),
                "status": "degraded",
                "error": str(e)
            }
```

### Configuration Management

Centralize and standardize your Opero configurations:

```python
from dataclasses import dataclass
from typing import Optional, Dict, Any
import os

@dataclass
class OperoConfig:
    """Centralized Opero configuration."""
    
    # Retry settings
    retries: int = 3
    backoff_factor: float = 1.5
    min_delay: float = 0.1
    max_delay: float = 30.0
    
    # Cache settings
    cache: bool = True
    cache_ttl: Optional[int] = 300
    cache_backend: str = "memory"
    
    # Rate limiting
    rate_limit: Optional[float] = None
    
    # Parallel processing
    workers: int = 10
    mode: str = "thread"
    
    @classmethod
    def for_environment(cls, env: str = None) -> 'OperoConfig':
        """Get configuration for specific environment."""
        env = env or os.getenv("ENVIRONMENT", "development")
        
        if env == "production":
            return cls(
                retries=5,
                backoff_factor=2.0,
                cache_ttl=3600,
                rate_limit=20.0,
                workers=20
            )
        elif env == "staging":
            return cls(
                retries=3,
                backoff_factor=1.5,
                cache_ttl=600,
                rate_limit=15.0,
                workers=15
            )
        else:  # development
            return cls(
                retries=1,
                backoff_factor=1.0,
                cache_ttl=60,
                rate_limit=5.0,
                workers=5
            )
    
    def as_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for use with Opero decorators."""
        return {k: v for k, v in self.__dict__.items() if v is not None}

# Usage
config = OperoConfig.for_environment()

@opero(**config.as_dict())
def configured_function():
    pass

# Environment-specific configurations
API_CONFIG = OperoConfig(
    retries=5,
    cache=True,
    cache_ttl=1800,
    rate_limit=10.0
).as_dict()

BATCH_CONFIG = OperoConfig(
    mode="thread",
    workers=15,
    retries=2,
    cache=False
).as_dict()

DB_CONFIG = OperoConfig(
    retries=3,
    backoff_factor=2.0,
    cache=False,  # Don't cache database writes
    rate_limit=50.0
).as_dict()
```

## Performance Optimization

### Choosing the Right Parallelization Mode

Select optimal modes based on workload characteristics:

```python
import psutil
import asyncio
from opero import opmap

class PerformanceOptimizer:
    """Automatically optimize Opero configurations for performance."""
    
    @staticmethod
    def analyze_workload(sample_items: list, func, sample_size: int = 10):
        """Analyze workload characteristics to suggest optimal configuration."""
        import time
        import concurrent.futures
        
        sample = sample_items[:sample_size]
        
        # Test sequential execution
        start_time = time.time()
        for item in sample:
            func(item)
        sequential_time = time.time() - start_time
        
        # Test threaded execution
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            list(executor.map(func, sample))
        threaded_time = time.time() - start_time
        
        # Calculate characteristics
        avg_item_time = sequential_time / len(sample)
        threading_benefit = sequential_time / threaded_time if threaded_time > 0 else 1
        
        # Determine workload type
        if threading_benefit < 1.2:
            workload_type = "cpu_bound"
        elif avg_item_time > 0.1:  # More than 100ms per item
            workload_type = "io_bound"
        else:
            workload_type = "mixed"
        
        return {
            "workload_type": workload_type,
            "avg_item_time": avg_item_time,
            "threading_benefit": threading_benefit,
            "recommended_mode": PerformanceOptimizer.get_recommended_mode(workload_type),
            "recommended_workers": PerformanceOptimizer.get_recommended_workers(workload_type)
        }
    
    @staticmethod
    def get_recommended_mode(workload_type: str) -> str:
        """Get recommended parallelization mode."""
        recommendations = {
            "cpu_bound": "process",
            "io_bound": "thread",
            "mixed": "thread"
        }
        return recommendations.get(workload_type, "thread")
    
    @staticmethod
    def get_recommended_workers(workload_type: str) -> int:
        """Get recommended worker count."""
        cpu_count = psutil.cpu_count()
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        if workload_type == "cpu_bound":
            return max(1, cpu_count - 1)  # Leave one CPU for system
        elif workload_type == "io_bound":
            return min(50, max(10, int(memory_gb * 5)))  # 5 workers per GB
        else:  # mixed
            return max(5, cpu_count)

# Usage
def sample_task(item):
    # Your actual task implementation
    return process_item(item)

# Analyze and optimize
optimizer = PerformanceOptimizer()
analysis = optimizer.analyze_workload(sample_items, sample_task)

print(f"Workload analysis: {analysis}")

# Apply recommendations
@opmap(
    mode=analysis["recommended_mode"],
    workers=analysis["recommended_workers"],
    retries=2,
    progress=True
)
def optimized_processor(item):
    return sample_task(item)

# Process with optimized configuration
results = optimized_processor(all_items)
```

### Memory Management

Optimize memory usage for large-scale processing:

```python
from opero import opmap
import gc
import sys

class MemoryEfficientProcessor:
    """Memory-efficient processing patterns."""
    
    def __init__(self, max_memory_mb: int = 1000):
        self.max_memory_mb = max_memory_mb
    
    def get_current_memory_mb(self) -> float:
        """Get current memory usage in MB."""
        return psutil.Process().memory_info().rss / 1024 / 1024
    
    def process_in_chunks(self, items: list, chunk_size: int = None):
        """Process large datasets in memory-efficient chunks."""
        
        if chunk_size is None:
            # Calculate optimal chunk size based on available memory
            available_memory = self.max_memory_mb - self.get_current_memory_mb()
            estimated_item_size = sys.getsizeof(items[0]) / 1024 / 1024  # MB per item
            chunk_size = max(10, int(available_memory / (estimated_item_size * 10)))
        
        print(f"Processing {len(items)} items in chunks of {chunk_size}")
        
        all_results = []
        for i in range(0, len(items), chunk_size):
            chunk = items[i:i + chunk_size]
            print(f"Processing chunk {i//chunk_size + 1} ({len(chunk)} items)")
            
            # Process chunk
            chunk_results = self._process_chunk(chunk)
            all_results.extend(chunk_results)
            
            # Force garbage collection between chunks
            gc.collect()
            
            # Check memory usage
            current_memory = self.get_current_memory_mb()
            if current_memory > self.max_memory_mb * 0.8:
                print(f"Warning: High memory usage ({current_memory:.1f}MB)")
        
        return all_results
    
    @opmap(
        mode="process",  # Isolate memory per worker
        workers=4,       # Fewer workers to limit memory
        retries=1,
        progress=False   # Reduce memory overhead
    )
    def _process_chunk(self, items: list):
        """Process individual chunk with memory isolation."""
        results = []
        for item in items:
            try:
                result = self._process_single_item(item)
                results.append(result)
                
                # Clear item reference immediately
                del item
                
            except Exception as e:
                results.append(f"Error: {e}")
        
        return results
    
    def _process_single_item(self, item):
        """Process single item - override in subclass."""
        return f"processed_{item}"

# Usage for large datasets
processor = MemoryEfficientProcessor(max_memory_mb=2000)
large_dataset = list(range(100000))  # 100K items

results = processor.process_in_chunks(large_dataset, chunk_size=1000)
```

### Caching Strategies

Implement intelligent caching for optimal performance:

```python
from opero import opero
import time
import hashlib
import json

class SmartCacheManager:
    """Intelligent cache management with multiple strategies."""
    
    def __init__(self):
        self.cache_stats = {}
        self.access_patterns = {}
    
    def adaptive_cache_key(self, func_name: str, *args, **kwargs):
        """Generate cache keys based on access patterns."""
        
        # Track access patterns
        if func_name not in self.access_patterns:
            self.access_patterns[func_name] = {"calls": 0, "unique_args": set()}
        
        self.access_patterns[func_name]["calls"] += 1
        
        # Create deterministic key
        key_data = {
            "func": func_name,
            "args": args,
            "kwargs": sorted(kwargs.items())
        }
        
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        
        self.access_patterns[func_name]["unique_args"].add(key_hash)
        
        return f"{func_name}:{key_hash}"
    
    def adaptive_cache_ttl(self, func_name: str) -> int:
        """Calculate adaptive TTL based on access patterns."""
        
        if func_name not in self.access_patterns:
            return 300  # Default 5 minutes
        
        patterns = self.access_patterns[func_name]
        calls = patterns["calls"]
        unique_args = len(patterns["unique_args"])
        
        # High frequency, low uniqueness = longer cache
        if calls > 100 and unique_args < 20:
            return 3600  # 1 hour
        # Medium frequency = medium cache
        elif calls > 20:
            return 900   # 15 minutes
        # Low frequency = short cache
        else:
            return 300   # 5 minutes

# Global cache manager
cache_manager = SmartCacheManager()

# Smart caching decorator factory
def smart_cached(func_name: str = None):
    def decorator(func):
        name = func_name or func.__name__
        
        @opero(
            cache=True,
            cache_key=lambda *args, **kwargs: cache_manager.adaptive_cache_key(name, *args, **kwargs),
            cache_ttl=lambda: cache_manager.adaptive_cache_ttl(name)
        )
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

# Usage
@smart_cached("user_profile")
def get_user_profile(user_id: str):
    """User profile with adaptive caching."""
    return fetch_user_data(user_id)

@smart_cached("product_catalog")
def get_product_info(product_id: str, category: str = None):
    """Product info with smart caching."""
    return fetch_product_data(product_id, category)
```

## Error Handling and Monitoring

### Comprehensive Error Handling

Implement robust error handling patterns:

```python
from opero import opero, AllFailedError
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

class ErrorTracker:
    """Track and analyze error patterns."""
    
    def __init__(self):
        self.error_history = []
        self.error_counts = {}
        self.recovery_times = {}
    
    def record_error(self, func_name: str, error: Exception, context: Dict[str, Any] = None):
        """Record error occurrence."""
        error_info = {
            "timestamp": datetime.now(),
            "function": func_name,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }
        
        self.error_history.append(error_info)
        
        # Track error counts
        error_key = f"{func_name}:{type(error).__name__}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
    
    def record_recovery(self, func_name: str, attempts: int, total_time: float):
        """Record successful recovery."""
        self.recovery_times[func_name] = {
            "attempts": attempts,
            "total_time": total_time,
            "timestamp": datetime.now()
        }
    
    def get_error_rate(self, func_name: str, time_window: timedelta = timedelta(hours=1)) -> float:
        """Calculate error rate for a function in given time window."""
        cutoff_time = datetime.now() - time_window
        
        total_errors = sum(1 for error in self.error_history 
                          if error["function"] == func_name and error["timestamp"] > cutoff_time)
        
        # This is simplified - in practice, you'd track total calls too
        return total_errors
    
    def should_circuit_break(self, func_name: str, threshold: int = 10) -> bool:
        """Determine if function should be circuit-broken."""
        recent_error_rate = self.get_error_rate(func_name, timedelta(minutes=5))
        return recent_error_rate > threshold

# Global error tracker
error_tracker = ErrorTracker()

def with_error_handling(func):
    """Comprehensive error handling decorator."""
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        start_time = time.time()
        attempts = 0
        
        try:
            # Check if function should be circuit-broken
            if error_tracker.should_circuit_break(func_name):
                raise Exception(f"Circuit breaker active for {func_name}")
            
            result = func(*args, **kwargs)
            
            # Record successful recovery if there were previous attempts
            if attempts > 0:
                total_time = time.time() - start_time
                error_tracker.record_recovery(func_name, attempts, total_time)
            
            return result
            
        except AllFailedError as e:
            # Handle Opero's AllFailedError specially
            error_tracker.record_error(func_name, e, {
                "total_attempts": len(e.errors),
                "error_types": [type(err).__name__ for err in e.errors],
                "args": str(args)[:100],  # Truncate for logging
                "kwargs": str(kwargs)[:100]
            })
            
            # Log detailed error information
            logging.error(f"All resilience mechanisms failed for {func_name}")
            for i, error in enumerate(e.errors, 1):
                logging.error(f"  Attempt {i}: {type(error).__name__}: {error}")
            
            raise
            
        except Exception as e:
            # Handle other exceptions
            error_tracker.record_error(func_name, e, {
                "args": str(args)[:100],
                "kwargs": str(kwargs)[:100]
            })
            
            logging.error(f"Unexpected error in {func_name}: {type(e).__name__}: {e}")
            raise
    
    return wrapper

# Usage
@with_error_handling
@opero(retries=3, cache=True, rate_limit=10.0)
def robust_api_call(endpoint: str, data: dict = None):
    """API call with comprehensive error handling."""
    response = requests.post(f"https://api.com/{endpoint}", json=data)
    response.raise_for_status()
    return response.json()
```

### Health Checks and Monitoring

Implement health monitoring for your resilient services:

```python
from dataclasses import dataclass
from typing import List, Dict
import asyncio
import aiohttp

@dataclass
class HealthStatus:
    """Health status for a service component."""
    name: str
    status: str  # "healthy", "degraded", "unhealthy"
    response_time: float
    error_rate: float
    last_error: Optional[str] = None
    uptime: float = 0.0

class HealthMonitor:
    """Monitor health of resilient services."""
    
    def __init__(self):
        self.health_checks = {}
        self.status_history = {}
    
    def register_health_check(self, name: str, check_func):
        """Register a health check function."""
        self.health_checks[name] = check_func
        self.status_history[name] = []
    
    async def run_health_check(self, name: str) -> HealthStatus:
        """Run a single health check."""
        if name not in self.health_checks:
            raise ValueError(f"No health check registered for {name}")
        
        start_time = time.time()
        
        try:
            result = await self.health_checks[name]()
            response_time = time.time() - start_time
            
            status = HealthStatus(
                name=name,
                status="healthy",
                response_time=response_time,
                error_rate=0.0
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            
            status = HealthStatus(
                name=name,
                status="unhealthy",
                response_time=response_time,
                error_rate=1.0,
                last_error=str(e)
            )
        
        # Store in history
        self.status_history[name].append(status)
        
        # Keep only last 100 entries
        if len(self.status_history[name]) > 100:
            self.status_history[name] = self.status_history[name][-100:]
        
        return status
    
    async def run_all_health_checks(self) -> Dict[str, HealthStatus]:
        """Run all registered health checks concurrently."""
        tasks = [
            self.run_health_check(name) 
            for name in self.health_checks.keys()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            name: result if isinstance(result, HealthStatus) else HealthStatus(
                name=name,
                status="unhealthy", 
                response_time=0.0,
                error_rate=1.0,
                last_error=str(result)
            )
            for name, result in zip(self.health_checks.keys(), results)
        }
    
    def get_overall_health(self) -> str:
        """Get overall system health status."""
        if not self.status_history:
            return "unknown"
        
        latest_statuses = []
        for name in self.health_checks.keys():
            if name in self.status_history and self.status_history[name]:
                latest_statuses.append(self.status_history[name][-1].status)
        
        if not latest_statuses:
            return "unknown"
        
        if all(status == "healthy" for status in latest_statuses):
            return "healthy"
        elif any(status == "unhealthy" for status in latest_statuses):
            return "degraded"
        else:
            return "healthy"

# Global health monitor
health_monitor = HealthMonitor()

# Health check implementations
@opero(retries=1, timeout=5.0)
async def api_health_check():
    """Health check for external API."""
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.com/health") as response:
            response.raise_for_status()
            return await response.json()

@opero(retries=1, timeout=2.0)
async def database_health_check():
    """Health check for database."""
    # Simplified database ping
    await asyncio.sleep(0.1)  # Simulate DB query
    return {"status": "ok"}

@opero(retries=1, timeout=1.0)
async def cache_health_check():
    """Health check for cache."""
    # Simplified cache check
    return {"status": "ok"}

# Register health checks
health_monitor.register_health_check("api", api_health_check)
health_monitor.register_health_check("database", database_health_check)
health_monitor.register_health_check("cache", cache_health_check)

# Health monitoring endpoint
async def health_endpoint():
    """Health endpoint for load balancers."""
    health_results = await health_monitor.run_all_health_checks()
    overall_health = health_monitor.get_overall_health()
    
    return {
        "status": overall_health,
        "timestamp": datetime.now().isoformat(),
        "checks": {
            name: {
                "status": result.status,
                "response_time": result.response_time,
                "error_rate": result.error_rate,
                "last_error": result.last_error
            }
            for name, result in health_results.items()
        }
    }
```

## Production Deployment

### Configuration for Production

Production-ready configuration patterns:

```python
import os
from typing import Dict, Any

class ProductionConfig:
    """Production-optimized Opero configuration."""
    
    @staticmethod
    def get_api_config() -> Dict[str, Any]:
        """Configuration for API calls in production."""
        return {
            "retries": int(os.getenv("OPERO_API_RETRIES", "5")),
            "backoff_factor": float(os.getenv("OPERO_API_BACKOFF", "2.0")),
            "cache": True,
            "cache_ttl": int(os.getenv("OPERO_API_CACHE_TTL", "1800")),  # 30 minutes
            "rate_limit": float(os.getenv("OPERO_API_RATE_LIMIT", "50.0")),
            "retry_on": (ConnectionError, TimeoutError, requests.HTTPError)
        }
    
    @staticmethod
    def get_batch_config() -> Dict[str, Any]:
        """Configuration for batch processing in production."""
        cpu_count = os.cpu_count() or 4
        
        return {
            "mode": os.getenv("OPERO_BATCH_MODE", "process"),
            "workers": int(os.getenv("OPERO_BATCH_WORKERS", str(max(1, cpu_count - 1)))),
            "retries": int(os.getenv("OPERO_BATCH_RETRIES", "3")),
            "ordered": os.getenv("OPERO_BATCH_ORDERED", "true").lower() == "true",
            "progress": os.getenv("OPERO_BATCH_PROGRESS", "false").lower() == "true",
            "timeout": float(os.getenv("OPERO_BATCH_TIMEOUT", "300.0"))
        }
    
    @staticmethod
    def get_database_config() -> Dict[str, Any]:
        """Configuration for database operations in production."""
        return {
            "retries": int(os.getenv("OPERO_DB_RETRIES", "3")),
            "backoff_factor": float(os.getenv("OPERO_DB_BACKOFF", "1.5")),
            "cache": False,  # Don't cache database writes
            "rate_limit": float(os.getenv("OPERO_DB_RATE_LIMIT", "100.0")),
            "retry_on": (ConnectionError, TimeoutError)  # Don't retry data errors
        }

# Environment-based configuration loading
def load_opero_config():
    """Load configuration based on environment."""
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        return ProductionConfig()
    elif env == "staging":
        # Staging uses production config with reduced limits
        config = ProductionConfig()
        # Override specific settings for staging
        return config
    else:
        # Development configuration
        return DevelopmentConfig()

# Usage in production
prod_config = load_opero_config()

@opero(**prod_config.get_api_config())
def production_api_call(endpoint: str, data: dict = None):
    """Production API call with optimized configuration."""
    pass

@opmap(**prod_config.get_batch_config())
def production_batch_processor(item):
    """Production batch processing with optimized configuration."""
    pass
```

### Logging and Observability

Production logging and monitoring setup:

```python
import structlog
import logging
from pythonjsonlogger import jsonlogger
from opero import configure_logging

def setup_production_logging():
    """Set up structured logging for production."""
    
    # Configure Opero's internal logging
    configure_logging(level=logging.INFO)
    
    # Configure structured logging
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure JSON logging for structured logs
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter()
    logHandler.setFormatter(formatter)
    
    logger = logging.getLogger()
    logger.addHandler(logHandler)
    logger.setLevel(logging.INFO)

# Metrics collection for production
class ProductionMetrics:
    """Production metrics collection."""
    
    def __init__(self):
        self.metrics = {}
        self.logger = structlog.get_logger("opero.metrics")
    
    def record_function_call(self, func_name: str, duration: float, status: str, **kwargs):
        """Record function call metrics."""
        self.logger.info(
            "function_call",
            function=func_name,
            duration=duration,
            status=status,
            **kwargs
        )
    
    def record_error(self, func_name: str, error_type: str, error_message: str, **kwargs):
        """Record error metrics."""
        self.logger.error(
            "function_error",
            function=func_name,
            error_type=error_type,
            error_message=error_message,
            **kwargs
        )

# Production deployment decorator
def production_resilient(config_type: str = "api"):
    """Production-ready resilient decorator."""
    
    def decorator(func):
        config = getattr(ProductionConfig(), f"get_{config_type}_config")()
        
        @opero(**config)
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            func_name = func.__name__
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                metrics.record_function_call(
                    func_name=func_name,
                    duration=duration,
                    status="success",
                    config_type=config_type
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                metrics.record_function_call(
                    func_name=func_name,
                    duration=duration,
                    status="error",
                    config_type=config_type
                )
                
                metrics.record_error(
                    func_name=func_name,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    config_type=config_type
                )
                
                raise
        
        return wrapper
    return decorator

# Setup for production
setup_production_logging()
metrics = ProductionMetrics()

# Usage
@production_resilient("api")
def production_api_function(endpoint: str):
    """Production API function with full observability."""
    return make_api_call(endpoint)

@production_resilient("batch")
def production_batch_function(items: list):
    """Production batch function with full observability."""
    return process_items(items)
```

## Testing Strategies

### Testing Resilient Functions

Comprehensive testing patterns for Opero-decorated functions:

```python
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from opero import opero, opmap, AllFailedError

class TestResilientFunctions:
    """Test suite for resilient functions."""
    
    def test_retry_behavior(self):
        """Test retry mechanism works correctly."""
        mock_func = Mock(side_effect=[
            ConnectionError("Connection failed"),
            ConnectionError("Connection failed"), 
            "success"
        ])
        
        @opero(retries=3, backoff_factor=1.0, min_delay=0.01)
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        assert mock_func.call_count == 3
    
    def test_cache_behavior(self):
        """Test caching works correctly."""
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
        
        # Wait for cache to expire
        time.sleep(1.1)
        
        # Third call (cache expired)
        result3 = test_func("test")
        assert call_count == 2
    
    def test_fallback_behavior(self):
        """Test fallback mechanism."""
        def failing_func(endpoint, api_key):
            current_key = api_key[0]
            if current_key == "bad_key":
                raise ConnectionError("Bad key")
            return f"success_with_{current_key}"
        
        @opero(retries=1, arg_fallback="api_key")
        def test_func(endpoint, api_key):
            return failing_func(endpoint, api_key)
        
        result = test_func("test_endpoint", api_key=["bad_key", "good_key"])
        assert result == "success_with_good_key"
    
    def test_rate_limiting(self):
        """Test rate limiting works."""
        call_times = []
        
        @opero(rate_limit=10.0)  # 10 calls per second
        def test_func():
            call_times.append(time.time())
            return "success"
        
        # Make multiple rapid calls
        for _ in range(5):
            test_func()
        
        # Check that calls were rate limited
        if len(call_times) > 1:
            time_diff = call_times[-1] - call_times[0]
            assert time_diff >= 0.4  # Should take at least 0.4 seconds for 5 calls at 10/sec
    
    def test_all_failed_error(self):
        """Test AllFailedError is raised when all attempts fail."""
        @opero(retries=2, arg_fallback="key")
        def always_fails(key):
            raise ConnectionError(f"Failed with {key[0]}")
        
        with pytest.raises(AllFailedError) as exc_info:
            always_fails(key=["key1", "key2"])
        
        # Check that all attempts are recorded
        assert len(exc_info.value.errors) > 0
    
    @pytest.mark.asyncio
    async def test_parallel_processing(self):
        """Test parallel processing with opmap."""
        items = list(range(10))
        
        @opmap(mode="thread", workers=3, retries=1)
        def process_item(item):
            time.sleep(0.1)  # Simulate work
            return item * 2
        
        start_time = time.time()
        results = process_item(items)
        end_time = time.time()
        
        # Should complete faster than sequential processing
        assert end_time - start_time < 1.0  # Less than 1 second for parallel
        assert results == [i * 2 for i in items]

# Integration tests
class TestIntegration:
    """Integration tests for complex scenarios."""
    
    @pytest.mark.asyncio
    async def test_api_client_integration(self):
        """Test full API client with all resilience features."""
        
        class MockAPIClient:
            def __init__(self):
                self.call_count = 0
            
            @opero(
                retries=3,
                cache=True,
                cache_ttl=60,
                rate_limit=5.0,
                arg_fallback="api_key"
            )
            async def fetch_data(self, endpoint, api_key):
                self.call_count += 1
                current_key = api_key[0]
                
                if self.call_count <= 2 and current_key == "bad_key":
                    raise ConnectionError("Bad key")
                
                return {"data": f"result_for_{endpoint}", "key": current_key}
        
        client = MockAPIClient()
        
        # Test with fallback
        result = await client.fetch_data(
            "test_endpoint", 
            api_key=["bad_key", "good_key"]
        )
        
        assert result["data"] == "result_for_test_endpoint"
        assert result["key"] == "good_key"

# Performance tests
class TestPerformance:
    """Performance tests for Opero features."""
    
    def test_cache_performance(self):
        """Test that caching significantly improves performance."""
        
        @opero(cache=True)
        def expensive_operation(x):
            time.sleep(0.1)  # Simulate expensive operation
            return x ** 2
        
        # First call (no cache)
        start_time = time.time()
        result1 = expensive_operation(5)
        first_call_time = time.time() - start_time
        
        # Second call (cached)
        start_time = time.time()
        result2 = expensive_operation(5)
        second_call_time = time.time() - start_time
        
        assert result1 == result2
        assert second_call_time < first_call_time / 10  # Cached call should be much faster

# Mock external dependencies for testing
@pytest.fixture
def mock_external_api():
    """Mock external API for testing."""
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {"test": "data"}
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        yield mock_get

def test_with_mocked_api(mock_external_api):
    """Test function with mocked external API."""
    
    @opero(retries=2, cache=True)
    def api_function():
        response = requests.get("https://api.example.com/data")
        response.raise_for_status()
        return response.json()
    
    result = api_function()
    assert result == {"test": "data"}
    assert mock_external_api.call_count == 1
```

## Summary of Best Practices

### Quick Reference Checklist

**Configuration:**
- ✅ Use environment-specific configurations
- ✅ Centralize Opero settings in configuration classes
- ✅ Document configuration choices and rationale
- ✅ Test configurations in staging environment

**Performance:**
- ✅ Profile workloads before choosing parallelization mode
- ✅ Use appropriate worker counts based on resource constraints  
- ✅ Implement memory-efficient processing for large datasets
- ✅ Use adaptive caching strategies based on access patterns

**Error Handling:**
- ✅ Implement comprehensive error tracking and monitoring
- ✅ Use circuit breaker patterns for external dependencies
- ✅ Provide graceful degradation for non-critical failures
- ✅ Log detailed error information for debugging

**Monitoring:**
- ✅ Implement health checks for all resilience components
- ✅ Use structured logging for production observability
- ✅ Track key metrics (success rate, retry rate, cache hit rate)
- ✅ Set up alerting for critical failure patterns

**Testing:**
- ✅ Test retry mechanisms with controlled failures
- ✅ Verify cache behavior and TTL functionality
- ✅ Test fallback scenarios with mock data
- ✅ Performance test parallel processing configurations

**Production:**
- ✅ Use production-optimized configurations
- ✅ Implement comprehensive logging and metrics
- ✅ Set up health monitoring and alerting
- ✅ Plan for graceful degradation scenarios

## Next Steps

You're now equipped with production-ready Opero patterns! Continue with:

1. **[API Reference](../api/overview.md)** - Complete technical documentation
2. **[Core Components](../api/core.md)** - Implementation details and advanced usage
3. **[Utilities](../api/utils.md)** - Helper functions and troubleshooting guides

Remember: Start simple, measure performance, and gradually add complexity as needed. Opero's power comes from thoughtful application of resilience patterns, not from using every feature at once.