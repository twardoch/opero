---
this_file: README.md
---

# Opero: Resilient, Parallel Task Orchestration for Python

[![PyPI version](https://img.shields.io/pypi/v/opero.svg)](https://pypi.org/project/opero/)
[![Python versions](https://img.shields.io/pypi/pyversions/opero.svg)](https://pypi.org/project/opero/)
[![License](https://img.shields.io/github/license/twardoch/opero.svg)](https://github.com/twardoch/opero/blob/main/LICENSE)

Opero (Latin for "to work" or "to operate") is a Python library designed to make your functions more robust and efficient. It provides a simple yet powerful way to add resilience mechanisms like automatic retries, fallbacks to alternative parameters, rate limiting, and caching, all through easy-to-use decorators. Additionally, Opero can effortlessly parallelize operations, helping you process large amounts of data or perform many tasks concurrently.

## What does Opero do?

Opero enhances your Python functions by adding layers of resilience and parallelism with minimal code changes. By simply adding a decorator to your function, you can:

*   **Automatically retry** operations that fail due to temporary issues (e.g., network glitches).
*   Define **fallback parameters** (like a backup API key or a different server) to use if an operation fails.
*   **Cache results** of expensive operations to speed up repeated calls.
*   **Limit the rate** at which functions are called to avoid overwhelming external services or APIs.
*   **Run your function in parallel** across multiple items, significantly speeding up batch processing tasks.

## Who is Opero for?

Opero is for Python developers who want to:

*   Build more reliable applications that can gracefully handle transient errors.
*   Improve the performance of I/O-bound or computationally intensive tasks.
*   Interact with external APIs or services that may be unreliable or have rate limits.
*   Simplify the implementation of complex error handling and concurrency patterns.
*   Focus on their core application logic without getting bogged down in boilerplate code for resilience and parallelism.

Whether you're working on web scraping, data processing pipelines, interacting with third-party APIs, or any task that involves potentially unreliable operations or could benefit from parallelism, Opero can help.

## Why is Opero useful?

*   **Simplicity:** Add powerful features with clean, Pythonic decorators (`@opero` and `@opmap`).
*   **Increased Reliability:** Automatically handles retries and fallbacks, making your applications more fault-tolerant.
*   **Improved Performance:** Caching reduces redundant computations, and parallel processing speeds up batch tasks.
*   **Resource Protection:** Rate limiting prevents your application from overwhelming external services.
*   **Modern Python:** Built with async-first principles while fully supporting synchronous code.
*   **Type Safety:** Includes comprehensive type hints for better editor integration and code quality.

## Installation

You can install Opero using pip:

```bash
pip install opero
```

Opero uses `twat-mp` for parallel processing, which has optional dependencies for enhanced capabilities:

*   For enhanced multiprocessing support using `pathos` (allows pickling of more complex objects):
    ```bash
    pip install opero[pathos]
    ```
*   For asynchronous multiprocessing:
    ```bash
    pip install opero[aiomultiprocess]
    ```
*   To install all optional dependencies:
    ```bash
    pip install opero[all]
    ```

## How to Use Opero

Opero is a library and is used programmatically by decorating your Python functions. It does not provide a command-line interface (CLI).

### Basic Usage with `@opero`

The `@opero` decorator adds resilience mechanisms to a single function call.

```python
import asyncio
from opero import opero, AllFailedError

# Example: Calling an external API that might fail or need different keys
@opero(
    retries=3,                # Try up to 3 times
    backoff_factor=1.5,       # Exponential backoff for retries
    arg_fallback="api_key",   # If it fails, try the next key in the 'api_key' list
    cache=True,               # Cache successful results
    cache_ttl=3600,           # Cache results for 1 hour
    rate_limit=5.0            # Don't call this function more than 5 times per second
)
async def fetch_data_from_service(item_id: str, api_key: list[str] = ["key1", "key2", "key3"]):
    """
    Fetches data for a given item_id using an API key.
    Tries key1, then key2, then key3 if failures occur.
    """
    current_key = api_key[0] # The decorator handles trying other keys from the list
    print(f"Attempting to fetch data for {item_id} using API key: {current_key}")

    # Simulate an API call that might fail
    # In a real scenario, this would be an HTTP request or similar
    if current_key == "key1" and item_id == "special": # Simulate key1 failing for "special" item
        raise ConnectionError("Service unavailable with key1 for special item")
    if current_key == "key2": # Simulate key2 always failing
        raise ValueError("Invalid API key: key2")

    # Simulate a successful call
    await asyncio.sleep(0.1)
    return {"item_id": item_id, "data": f"Data fetched with {current_key}", "key_used": current_key}

async def main_opero_example(): # Renamed to avoid conflict
    try:
        # This call might try key1, then key2, then key3 due to arg_fallback
        result1 = await fetch_data_from_service("special")
        print(f"Result 1: {result1}")

        # This call should succeed with key1 (or key3 if key1 somehow fails for "normal")
        result2 = await fetch_data_from_service("normal", api_key=["key1", "key3"]) # Provide specific keys
        print(f"Result 2: {result2}")

        # This will be cached if called again within 1 hour for "normal"
        result3 = await fetch_data_from_service("normal", api_key=["key1", "key3"])
        print(f"Result 3 (cached): {result3}")

    except AllFailedError as e:
        print(f"All attempts failed for an operation: {e}")
        for i, error in enumerate(e.errors):
            print(f"  Attempt {i+1} failed with: {error}")

if __name__ == "__main__":
    # This block is for example purposes.
    # To run this specific example:
    # 1. Save this code snippet as a Python file (e.g., example_opero.py).
    # 2. Ensure Opero is installed (`pip install opero`).
    # 3. Run from your terminal: `python example_opero.py`
    asyncio.run(main_opero_example())
```

### Parallel Processing with `@opmap`

The `@opmap` decorator applies resilience mechanisms to a function that processes a single item, and then runs this function in parallel over an iterable of items.

```python
import time
from opero import opmap, AllFailedError # AllFailedError might be relevant for individual task failures

# Example: Processing a batch of items, where each item's processing might fail
@opmap(
    mode="thread",            # Use threads for parallelism (good for I/O-bound tasks)
    workers=4,                # Use 4 worker threads
    retries=2,                # Retry processing each item up to 2 times
    arg_fallback="config_profile", # Try different config profiles if an item fails
    cache=True,               # Cache results for each item
    cache_ttl=600             # Cache for 10 minutes
)
def process_data_item(item_id: int, config_profile: list[str] = ["default", "backup_config"]):
    """
    Processes a single data item using a configuration profile.
    """
    current_config = config_profile[0]
    print(f"Processing item {item_id} with config: {current_config}")
    
    # Simulate work and potential failure
    time.sleep(0.2)
    if item_id % 5 == 0 and current_config == "default": # Simulate 'default' config failing for every 5th item
        raise RuntimeError(f"Processing failed for item {item_id} with {current_config}")
    if item_id % 3 == 0 and current_config == "backup_config": # Simulate 'backup_config' also failing for some
         raise ValueError(f"Backup config also failed for item {item_id}")
    
    return {"item_id": item_id, "status": "processed", "config_used": current_config}

def run_batch_processing():
    items_to_process = list(range(10)) # Process items 0 through 9

    print("Starting batch processing...")
    # opmap expects an iterable of items as the first argument.
    # The decorated function `process_data_item` is designed to handle one item.
    # `opmap` takes care of distributing `items_to_process` to `process_data_item` workers.
    # Results will be a list. If a task failed permanently (AllFailedError),
    # twat-mp typically places the exception object in the results list.
    results = process_data_item(items_to_process)
    
    print("\\nBatch processing complete. Results:")
    for res in results:
        if isinstance(res, Exception):
            print(f"Error processing an item: {res}")
            if isinstance(res, AllFailedError): # Check if it's the specific error from Opero's core logic
                print(f"  Underlying errors for AllFailedError:")
                for i, err_detail in enumerate(res.errors): # Access the .errors attribute
                    print(f"    Attempt {i+1}: {err_detail}")
        else:
            print(res)

if __name__ == "__main__":
    # This block is for example purposes.
    # To run this specific example:
    # 1. Save this code snippet as a Python file (e.g., example_opmap.py).
    # 2. Ensure Opero is installed (`pip install opero`).
    # 3. Run from your terminal: `python example_opmap.py`
    run_batch_processing()
    # Example of processing again, results for non-failing items should be cached
    print("\\nRunning batch again (expecting cache hits for some):")
    run_batch_processing()
```

## Technical Deep Dive

This section provides a more detailed look into Opero's architecture, components, and development practices.

### How Opero Works

Opero's core functionality is delivered through two main decorators: `@opero` and `@opmap`. These decorators wrap your functions and apply a chain of resilience and concurrency behaviors.

#### Core Decorators

1.  **`@opero`**:
    *   Applies to functions that operate on a single set of inputs at a time.
    *   Orchestrates caching, rate limiting, retries, and parameter-based fallbacks for the decorated function.
    *   The order of execution for these mechanisms is crucial:
        1.  **Caching (`get_cache_decorator`)**: Checks if a valid cached result exists. If so, returns it immediately.
        2.  **Rate Limiting (`get_rate_limit_decorator`)**: If not cached, ensures the function call respects the defined rate limits before proceeding.
        3.  **Retry (`get_retry_decorator`)**: Wraps the core execution logic (including fallbacks) to retry it multiple times if specified exceptions occur.
        4.  **Parameter-Based Fallbacks (`get_fallback_decorator`)**: If the function call fails (inside a retry attempt), this mechanism tries alternative values for a specified parameter.

2.  **`@opmap`**:
    *   Designed for functions that process a single item, but you want to apply this processing to many items in parallel.
    *   It first wraps the user-provided single-item processing function with the same resilience mechanisms as `@opero` (Caching, Rate Limiting, Retry, Fallback).
    *   Then, it uses a parallel execution engine (powered by `twat-mp`) to map this now-resilient single-item function over an iterable of input items.
    *   Each item's processing journey (including its own retries and fallbacks) is independent within its worker process/thread.

#### Resilience Mechanisms

*   **Caching**:
    *   **Implementation**: Leverages `twat-cache`.
    *   **Configuration**:
        *   `cache=True`: Enables caching.
        *   `cache_ttl` (int, optional): Time-to-live for cache entries in seconds.
        *   `cache_backend` (str): Backend to use (e.g., "memory", "disk", "redis"). Refer to `twat-cache` documentation for available backends and their specific configurations.
        *   `cache_key` (Callable, optional): Custom function to generate cache keys.
        *   `cache_namespace` (str): Namespace for cache entries (default: "opero" for `@opero`, "opero_opmap_item" for items in `@opmap`).
    *   **Behavior**: Checks cache before any other operation. If a fresh result is found, it's returned immediately.

*   **Rate Limiting**:
    *   **Implementation**: Uses `asynciolimiter.Limiter`.
    *   **Configuration**:
        *   `rate_limit` (float, optional): Maximum number of operations per second.
    *   **Behavior**: Ensures that the decorated function (or each parallel task in `@opmap` before execution by a worker) does not exceed the specified call rate.

*   **Retry Mechanism**:
    *   **Implementation**: Built upon the `tenacity` library.
    *   **Configuration**:
        *   `retries` (int): Number of retry attempts (default: 3).
        *   `backoff_factor` (float): Multiplier for exponential backoff (default: 1.5).
        *   `min_delay` (float): Minimum delay between retries in seconds (default: 0.1).
        *   `max_delay` (float): Maximum delay between retries in seconds (default: 30.0).
        *   `retry_on` (Exception or tuple of Exceptions): Specific exceptions that should trigger a retry (default: `Exception`).
    *   **Behavior**: If the wrapped function (including any fallback attempts for a given main attempt) raises one of the `retry_on` exceptions, it will be retried according to the backoff strategy.

*   **Parameter-Based Fallbacks**:
    *   **Implementation**: Managed by `opero.core.fallback.get_fallback_decorator`.
    *   **Configuration**:
        *   `arg_fallback` (str, optional): The *name* of a function parameter. This parameter in your decorated function must be a list (or sequence) of values.
    *   **Behavior**:
        *   When the decorated function is called, Opero initially calls it with the first value from the list provided to the `arg_fallback` parameter.
        *   If this call results in an exception, Opero will then re-invoke the function using the *next* value from the `arg_fallback` list for that specific parameter, keeping other arguments the same.
        *   This process continues until the function succeeds or all values in the `arg_fallback` list have been attempted.
        *   Each attempt with a new fallback value is considered part of the *same overall attempt* from the perspective of the Retry mechanism. If all fallbacks are exhausted and the operation still fails, this entire sequence is what gets retried.

#### Parallel Processing (`@opmap`)

*   **Implementation**: Uses `twat-mp` for managing parallel execution.
*   **Configuration**:
    *   `mode` (str): Concurrency mode:
        *   `"process"`: Uses a pool of processes (good for CPU-bound tasks, default).
        *   `"thread"`: Uses a pool of threads (good for I/O-bound tasks).
        *   `"async"`: Uses asyncio for concurrent execution of async functions (good for many async I/O tasks).
        *   `"async_process"`: Uses `aiomultiprocess` for running async functions in separate processes. Requires `opero[aiomultiprocess]`.
    *   `workers` (int): Number of parallel worker processes or threads (default: 4).
    *   `ordered` (bool): If `True`, results are returned in the same order as the input items (default: `True`). May have a slight performance overhead.
    *   `progress` (bool): If `True`, displays a progress bar (if supported by the underlying `twat-mp` mode and environment, typically uses `tqdm`). Default: `True`.
*   **Behavior**: The `@opmap` decorator takes your single-item processing function, makes it resilient using the mechanisms described above, and then uses the chosen `twat-mp` backend to apply this resilient function to each item in the input iterable concurrently.

#### Async Support

Opero is designed with asynchronous operations in mind.
*   Decorators correctly handle both `async def` and regular `def` functions.
*   Internal components like rate limiting and retries use their respective async-compatible versions when decorating async functions.
*   Utilities like `ensure_async` and `run_async` (from `opero.utils.async_utils`) are used internally where needed to bridge sync/async contexts, but users typically don't interact with these directly.

#### Error Handling

*   **`AllFailedError`**: If all retry attempts and all parameter-based fallbacks for a given operation are exhausted (relevant for `@opero`, or for a single item inside `@opmap` before `twat-mp` collects it), Opero will raise an `opero.exceptions.AllFailedError`.
*   This custom exception class (subclass of `OperoError`, which is a `RuntimeError`) contains an `errors` attribute. This attribute is a list that stores the exceptions captured from each significant failed attempt (e.g., after exhausting fallbacks for a particular retry cycle). This allows for detailed inspection of what went wrong.
*   **`@opmap` Error Handling**: When using `@opmap`, if an individual item's processing ultimately fails (i.e., its resiliently-wrapped function would raise `AllFailedError` or another exception that exhausts retries/fallbacks), the underlying `twat-mp` library typically collects this exception. The list of results returned by the `@opmap`-decorated function will contain the exception object at the position corresponding to the failed item. Your code should check for and handle these exception objects in the results list. The example for `@opmap` demonstrates this.

#### Logging

*   Opero includes internal logging for important events like retries, fallbacks, cache hits/misses, and rate limit actions.
*   **`configure_logging`**: You can use `from opero.utils import configure_logging` to set up a basic logger with a specific level and format.
    ```python
    import logging
    from opero import configure_logging
    logger = configure_logging(level=logging.INFO) # Or logging.DEBUG for more detail
    ```
*   The library uses standard Python `logging`, so its output can be integrated into your application's existing logging setup.

### Contributing to Opero

Contributions are highly welcome! Here's how to get started:

#### Development Environment

Opero uses [Hatch](https://hatch.pypa.io/) for project management and development workflows.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/twardoch/opero.git
    cd opero
    ```
2.  **Install Hatch:**
    ```bash
    pip install hatch
    ```
3.  **Activate the development environment:**
    ```bash
    hatch shell
    ```
    This will create a virtual environment, install dependencies (including development tools), and make the `opero` package available in an editable mode.

#### Running Tests

Tests are written using `pytest`.

*   **Run all tests:**
    ```bash
    hatch run test
    ```
    This command (defined in `pyproject.toml`) executes `python -m pytest -n auto tests`. The `-n auto` flag enables parallel test execution using `pytest-xdist`.
*   **Run tests with coverage report:**
    ```bash
    hatch run test-cov
    ```
    This generates a coverage report to the console and an XML report (`coverage.xml`). Coverage settings are in `pyproject.toml` under `[tool.coverage.run]`.

#### Code Style, Linting, and Formatting

Opero uses `Ruff` for linting and formatting, and `mypy` for static type checking.

*   **Linting & Formatting (Ruff):**
    *   To check for linting issues: `hatch run lint:style` (runs `ruff check .`)
    *   To automatically fix linting issues and format code: `hatch run lint:fmt` (runs `ruff format .` then `ruff check --fix .`)
    *   Configuration for Ruff is in `pyproject.toml` under `[tool.ruff]`. Key settings include a line length of 88 characters.
*   **Static Type Checking (Mypy):**
    *   To run type checking: `hatch run lint:typing` (runs `mypy src/opero tests`)
    *   Mypy configuration is in `pyproject.toml` under `[tool.mypy]`.
*   **All Checks:**
    *   To run all linting, formatting, and type checks: `hatch run lint:all`

#### Pre-Commit Hooks

The repository is configured with pre-commit hooks (see `.pre-commit-config.yaml`) that run `Ruff` and other checks automatically before each commit. This helps ensure code quality and consistency.

*   **Install pre-commit hooks:**
    ```bash
    pre-commit install
    ```

#### Continuous Integration / Continuous Deployment (CI/CD)

*   **GitHub Actions:** Opero uses GitHub Actions for:
    *   **Build & Test (`.github/workflows/push.yml`):** On pushes to `main` or pull requests, this workflow runs code quality checks (Ruff) and tests (pytest) across multiple Python versions and operating systems. It also builds distribution files.
    *   **Release (`.github/workflows/release.yml`):** When a tag matching `v*` is pushed, this workflow builds the distribution files and publishes the package to PyPI. It also creates a GitHub Release.

#### Versioning

*   Versioning is managed by `hatch-vcs`. The version is derived from Git tags and written to `src/opero/__version__.py`.
*   To release a new version:
    1.  Ensure `CHANGELOG.md` is updated.
    2.  Commit all changes.
    3.  Tag the commit (e.g., `git tag v0.2.0`).
    4.  Push the tags to GitHub (`git push --tags`). This will trigger the release workflow.

#### Submitting Pull Requests

1.  Fork the repository on GitHub.
2.  Create a new branch for your feature or bug fix.
3.  Make your changes, ensuring you add tests for new functionality and that all tests and linters pass.
4.  Update `CHANGELOG.md` with a description of your changes under the `[Unreleased]` section.
5.  Push your branch to your fork and submit a pull request to the `main` branch of `twardoch/opero`.

#### License

Opero is licensed under the MIT License. See the `LICENSE` file for details. By contributing, you agree that your contributions will be licensed under its MIT License.
