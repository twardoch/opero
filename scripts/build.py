#!/usr/bin/env python3
"""
Build script for the opero package.
"""

import os
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
    """Main build function."""
    repo_root = Path(__file__).parent.parent
    print(f"Repository root: {repo_root}")
    
    # Clean previous builds
    print("🧹 Cleaning previous builds...")
    dist_dir = repo_root / "dist"
    if dist_dir.exists():
        import shutil
        shutil.rmtree(dist_dir)
    
    build_dir = repo_root / "build"
    if build_dir.exists():
        import shutil
        shutil.rmtree(build_dir)
    
    # Check hatch is installed
    try:
        run_command("hatch --version")
    except subprocess.CalledProcessError:
        print("❌ Hatch is not installed. Please install it with: pip install hatch")
        sys.exit(1)
    
    # Run linting and formatting
    print("🔍 Running linting and formatting...")
    try:
        run_command("hatch run lint:style", cwd=repo_root)
    except subprocess.CalledProcessError as e:
        print(f"❌ Linting failed: {e}")
        sys.exit(1)
    
    # Run type checking
    print("🔍 Running type checking...")
    try:
        run_command("hatch run lint:typing", cwd=repo_root)
    except subprocess.CalledProcessError as e:
        print(f"❌ Type checking failed: {e}")
        sys.exit(1)
    
    # Build the package
    print("📦 Building package...")
    try:
        run_command("hatch build", cwd=repo_root)
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        sys.exit(1)
    
    # List built files
    print("📋 Built files:")
    for file in dist_dir.iterdir():
        print(f"  - {file.name}")
    
    print("✅ Build completed successfully!")


if __name__ == "__main__":
    main()