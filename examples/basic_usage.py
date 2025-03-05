#!/usr/bin/env python3
# this_file: examples/basic_usage.py
"""
Basic usage examples for the opero package.

This module demonstrates basic usage of the opero package.
"""

import asyncio
import logging
import time
from typing import List

from opero import (
    opero,
    operomap,
    configure_logging,
)

# Configure logging
logger = configure_logging(level=logging.INFO, verbose=True)


# Example 1: Basic usage of @opero with caching
@opero(cache=True, cache_ttl=60)
def calculate_fibonacci(n: int) -> int:
    """
    Calculate the nth Fibonacci number.

    Args:
        n: The index of the Fibonacci number to calculate

    Returns:
        The nth Fibonacci number
    """
    logger.info(f"Calculating Fibonacci({n})")
    if n <= 1:
        return n
    return calculate_fibonacci(n - 1) + calculate_fibonacci(n - 2)


# Example 2: Using @opero with retries and fallbacks
@opero(retries=3, backoff_factor=2.0, arg_fallback="api_key")
def call_api(data: str, api_key: List[str] = ["primary_key", "backup_key"]) -> str:
    """
    Call an API with retries and fallbacks.

    Args:
        data: Data to send to the API
        api_key: API key to use (with fallbacks)

    Returns:
        API response
    """
    logger.info(f"Calling API with key {api_key}")

    # Simulate API call with potential failures
    if api_key == "primary_key":
        # Simulate primary key failure
        raise ValueError("Primary API key failed")

    # Simulate successful API call with backup key
    return f"API response for {data} using {api_key}"


# Example 3: Using @operomap for parallel processing
@operomap(mode="process", workers=4, cache=True, cache_ttl=300, progress=True)
def process_item(item: int) -> int:
    """
    Process an item in parallel.

    Args:
        item: Item to process

    Returns:
        Processed item
    """
    logger.info(f"Processing item {item}")
    time.sleep(1)  # Simulate processing time
    return item * item


# Example 4: Using @opero with async functions
@opero(
    cache=True,
    retries=2,
    rate_limit=5.0,  # 5 operations per second
)
async def fetch_data(url: str) -> str:
    """
    Fetch data from a URL with caching, retries, and rate limiting.

    Args:
        url: URL to fetch data from

    Returns:
        Fetched data
    """
    logger.info(f"Fetching data from {url}")

    # Simulate async API call
    await asyncio.sleep(0.5)

    # Simulate occasional failures
    if "error" in url:
        raise ValueError(f"Error fetching data from {url}")

    return f"Data from {url}"


# Example 5: Using @operomap with async functions
@operomap(mode="async", workers=8, cache=True, retries=2)
async def fetch_url(url: str) -> str:
    """
    Fetch data from a URL in parallel.

    Args:
        url: URL to fetch data from

    Returns:
        Fetched data
    """
    logger.info(f"Fetching URL {url}")

    # Simulate async API call
    await asyncio.sleep(0.5)

    return f"Data from {url}"


def main():
    """Run the examples."""
    # Example 1: Basic usage of @opero with caching
    print("\n=== Example 1: Basic usage of @opero with caching ===")
    print(f"Fibonacci(10) = {calculate_fibonacci(10)}")
    print("Calling again (should use cache):")
    print(f"Fibonacci(10) = {calculate_fibonacci(10)}")

    # Example 2: Using @opero with retries and fallbacks
    print("\n=== Example 2: Using @opero with retries and fallbacks ===")
    try:
        result = call_api("test data")
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")

    # Example 3: Using @operomap for parallel processing
    print("\n=== Example 3: Using @operomap for parallel processing ===")
    results = process_item(range(10))
    print(f"Results: {results}")

    # Example 4: Using @opero with async functions
    print("\n=== Example 4: Using @opero with async functions ===")

    async def run_async_example():
        urls = [
            "https://example.com/1",
            "https://example.com/2",
            "https://example.com/error",
            "https://example.com/3",
        ]

        for url in urls:
            try:
                result = await fetch_data(url)
                print(f"Result: {result}")
            except Exception as e:
                print(f"Error fetching {url}: {e}")

    asyncio.run(run_async_example())

    # Example 5: Using @operomap with async functions
    print("\n=== Example 5: Using @operomap with async functions ===")

    async def run_async_map_example():
        urls = [
            "https://example.com/1",
            "https://example.com/2",
            "https://example.com/3",
            "https://example.com/4",
            "https://example.com/5",
        ]

        results = await fetch_url(urls)
        print(f"Results: {results}")

    asyncio.run(run_async_map_example())


if __name__ == "__main__":
    main()
