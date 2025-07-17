#!/usr/bin/env python3
"""
Test script for the opero package.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: str, cwd: Path = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    print(f"Running: {cmd}")
    if cwd:
        print(f"Working directory: {cwd}")
    
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check
    )
    
    if result.stdout:
        print(f"STDOUT:\n{result.stdout}")
    if result.stderr:
        print(f"STDERR:\n{result.stderr}")
    
    return result


def main():
    """Main test function."""
    repo_root = Path(__file__).parent.parent
    print(f"Repository root: {repo_root}")
    
    # Check hatch is installed
    try:
        run_command("hatch --version")
    except subprocess.CalledProcessError:
        print("❌ Hatch is not installed. Please install it with: pip install hatch")
        sys.exit(1)
    
    # Run tests with coverage
    print("🧪 Running tests with coverage...")
    try:
        run_command("hatch run test:test-cov", cwd=repo_root)
    except subprocess.CalledProcessError as e:
        print(f"❌ Tests failed: {e}")
        sys.exit(1)
    
    # Run benchmarks if available
    print("⚡ Running benchmarks...")
    try:
        run_command("hatch run test:bench", cwd=repo_root, check=False)
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Benchmarks failed or unavailable: {e}")
    
    print("✅ All tests passed!")


if __name__ == "__main__":
    main()