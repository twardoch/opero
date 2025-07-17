#!/usr/bin/env python3
"""
Development script for the opero package.
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
    """Main development function."""
    repo_root = Path(__file__).parent.parent
    print(f"Repository root: {repo_root}")
    
    if len(sys.argv) < 2:
        print("Usage: python dev.py <command>")
        print("Commands:")
        print("  setup    - Set up development environment")
        print("  lint     - Run linting and formatting")
        print("  test     - Run tests")
        print("  check    - Run all checks (lint + test)")
        print("  clean    - Clean build artifacts")
        print("  install  - Install package in development mode")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "setup":
        print("🔧 Setting up development environment...")
        try:
            run_command("hatch --version")
        except subprocess.CalledProcessError:
            print("❌ Hatch is not installed. Please install it with: pip install hatch")
            sys.exit(1)
        
        print("✅ Development environment is ready!")
        print("Available commands:")
        print("  hatch shell          - Activate development environment")
        print("  hatch run test:test  - Run tests")
        print("  hatch run lint:all   - Run linting and type checking")
    
    elif command == "lint":
        print("🔍 Running linting and formatting...")
        try:
            run_command("hatch run lint:fmt", cwd=repo_root)
            run_command("hatch run lint:typing", cwd=repo_root)
        except subprocess.CalledProcessError as e:
            print(f"❌ Linting failed: {e}")
            sys.exit(1)
        print("✅ Linting completed!")
    
    elif command == "test":
        print("🧪 Running tests...")
        try:
            run_command("hatch run test:test-cov", cwd=repo_root)
        except subprocess.CalledProcessError as e:
            print(f"❌ Tests failed: {e}")
            sys.exit(1)
        print("✅ Tests completed!")
    
    elif command == "check":
        print("🔍 Running all checks...")
        try:
            run_command("hatch run lint:all", cwd=repo_root)
            run_command("hatch run test:test-cov", cwd=repo_root)
        except subprocess.CalledProcessError as e:
            print(f"❌ Checks failed: {e}")
            sys.exit(1)
        print("✅ All checks passed!")
    
    elif command == "clean":
        print("🧹 Cleaning build artifacts...")
        import shutil
        
        paths_to_clean = [
            repo_root / "dist",
            repo_root / "build",
            repo_root / "src" / "opero.egg-info",
            repo_root / "__pycache__",
            repo_root / ".pytest_cache",
            repo_root / ".coverage",
            repo_root / "coverage.xml",
            repo_root / "htmlcov",
        ]
        
        for path in paths_to_clean:
            if path.exists():
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                print(f"Removed: {path}")
        
        # Clean __pycache__ directories recursively
        for pycache in repo_root.rglob("__pycache__"):
            if pycache.is_dir():
                shutil.rmtree(pycache)
                print(f"Removed: {pycache}")
        
        print("✅ Cleanup completed!")
    
    elif command == "install":
        print("📦 Installing package in development mode...")
        try:
            run_command("pip install -e .", cwd=repo_root)
        except subprocess.CalledProcessError as e:
            print(f"❌ Installation failed: {e}")
            sys.exit(1)
        print("✅ Package installed in development mode!")
    
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()