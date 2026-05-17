# Opero: resilience and parallelism for Python functions

[![PyPI version](https://img.shields.io/pypi/v/opero.svg)](https://pypi.org/project/opero/)
[![Python versions](https://img.shields.io/pypi/pyversions/opero.svg)](https://pypi.org/project/opero/)
[![License](https://img.shields.io/github/license/twardoch/opero.svg)](https://github.com/twardoch/opero/blob/main/LICENSE)

Two decorators — `@opero` and `@opmap` — add automatic retries, parameter fallbacks, caching, rate limiting, and parallel execution to any Python function with minimal code changes.

## Install

```bash
pip install opero

# Optional extras
pip install opero[pathos]        # multiprocessing with complex objects
pip install opero[aiomultiprocess]  # async multiprocessing
pip install opero[all]           # everything
```

## Quick example

```python
from opero import opero, opmap, AllFailedError

# Single-call resilience: cache results, retry up to 3 times,
# fall back through a list of API keys on failure.
@opero(cache=True, cache_ttl=3600, retries=3, arg_fallback="api_key", rate_limit=5.0)
async def fetch(item_id: str, api_key: list[str] = ["key1", "key2", "key3"]):
    return await call_api(item_id, api_key[0])

# Batch resilience: same protections, applied in parallel across many items.
@opmap(mode="thread", workers=8, retries=2, arg_fallback="config")
def process(item: dict, config: list[str] = ["primary", "backup"]):
    return transform(item, config[0])

results = process(list_of_items)   # returns list; failed items are exceptions
```

## What each mechanism does

### Retries (`retries`, `backoff_factor`, `min_delay`, `max_delay`, `retry_on`)

Re-runs the function on failure using exponential backoff with jitter (via `tenacity`). Set `retry_on` to restrict which exception types trigger a retry.

### Parameter fallbacks (`arg_fallback`)

Names a parameter whose value is a list of alternatives. On each failure the next value from the list is tried. Useful for rotating API keys, backup endpoints, or config profiles. Raises `AllFailedError` when the list is exhausted.

### Caching (`cache`, `cache_ttl`, `cache_backend`, `cache_namespace`, `cache_key`)

Skips the function body on repeated calls with the same arguments (via `twat-cache`). Backends: `"memory"` (default), `"disk"`, `"redis"`.

### Rate limiting (`rate_limit`)

Caps calls-per-second using `asynciolimiter`. Protects downstream APIs from being hammered.

### Parallel execution (`mode`, `workers`, `ordered`, `progress`) — `@opmap` only

Maps the decorated function across a list of inputs using `twat-mp`. Modes:

| Mode | Best for |
|------|---------|
| `"thread"` | I/O-bound work (HTTP, DB, file) |
| `"process"` | CPU-bound work |
| `"async"` | Async I/O functions |
| `"async_process"` | Async functions in separate processes |

Failed items are returned as exception objects in the results list rather than stopping the batch.

## Execution order

Each call goes through: **cache check → rate limiter → retry loop → fallback cycle**.

## Error handling

```python
from opero import AllFailedError

try:
    result = await fetch("item-42")
except AllFailedError as e:
    for i, err in enumerate(e.errors):
        print(f"attempt {i+1}: {err}")
```

## Async support

Both sync and async functions work. Opero detects async functions automatically and uses async-compatible retry and rate-limit implementations.

## Logging

```python
from opero import configure_logging
import logging
configure_logging(level=logging.DEBUG)   # see retries, cache hits, fallbacks
```

## Package structure

| Module | Purpose |
|--------|---------|
| `decorators/opero.py` | `@opero` — single-call resilience decorator |
| `decorators/opmap.py` | `@opmap` — batch parallel resilience decorator |
| `core/retry.py` | Exponential backoff retry via `tenacity` |
| `core/fallback.py` | Parameter-list fallback cycling |
| `core/cache.py` | Cache integration via `twat-cache` |
| `core/rate_limit.py` | Rate limiting via `asynciolimiter` |
| `concurrency/pool.py` | Parallel executor via `twat-mp` |
| `exceptions.py` | `OperoError`, `AllFailedError` |

## Development

```bash
git clone https://github.com/twardoch/opero && cd opero
pip install hatch
hatch shell
hatch run test          # run tests
hatch run lint:all      # ruff + mypy
```

## License

MIT.
