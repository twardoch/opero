# Installation

Get started with Opero in minutes with a simple pip install.

## Requirements

- **Python**: 3.8 or higher
- **Operating System**: Linux, macOS, or Windows  
- **Dependencies**: Automatically handled by pip

## Basic Installation

Install Opero using pip:

```bash
pip install opero
```

This installs the core Opero library with all essential features:

- `@opero` decorator for single function resilience
- `@opmap` decorator for parallel processing  
- Basic retry, fallback, cache, and rate limiting
- Thread and process-based parallelization

## Optional Dependencies

Opero offers optional dependencies to unlock additional capabilities:

### Enhanced Multiprocessing with Pathos

For advanced multiprocessing that can handle more complex objects:

```bash
pip install opero[pathos]
```

**Benefits:**
- Pickle more complex objects (closures, lambdas, class methods)
- Better support for nested functions and complex data structures
- More robust process-based parallelization

**When to use:** Choose this when you need to process complex objects or encounter pickling errors with standard multiprocessing.

### Async Multiprocessing

For running async functions in separate processes:

```bash
pip install opero[aiomultiprocess]
```

**Benefits:**
- Run async functions in parallel processes
- Combine the benefits of async I/O with process-based CPU parallelization
- Best of both worlds for mixed workloads

**When to use:** Ideal for CPU-intensive async functions or when you need process isolation for async operations.

### All Features

Install everything:

```bash
pip install opero[all]
```

This includes all optional dependencies for maximum functionality.

## Installation Options

### Development Installation

If you're contributing to Opero or want the latest development version:

```bash
git clone https://github.com/twardoch/opero.git
cd opero
pip install -e ".[all]"
```

### Specific Versions

Install a specific version:

```bash
pip install opero==1.0.0
```

### Virtual Environments

We recommend using virtual environments:

```bash
# Using venv
python -m venv opero-env
source opero-env/bin/activate  # On Windows: opero-env\Scripts\activate
pip install opero[all]

# Using conda
conda create -n opero-env python=3.11
conda activate opero-env
pip install opero[all]
```

## Verification

Verify your installation:

```python
import opero
print(f"Opero version: {opero.__version__}")

# Test basic functionality
from opero import opero

@opero(retries=1)
def test_function():
    return "Opero is working!"

result = test_function()
print(result)  # Should print: Opero is working!
```

## Dependency Overview

Opero's core dependencies (automatically installed):

| Package | Purpose | 
|---------|---------|
| `twat-cache` | Caching backend |
| `twat-mp` | Parallel processing engine |
| `tenacity` | Retry mechanisms |
| `asynciolimiter` | Rate limiting |

Optional dependencies:

| Package | Feature | Install Command |
|---------|---------|----------------|
| `pathos` | Enhanced multiprocessing | `pip install opero[pathos]` |
| `aiomultiprocess` | Async multiprocessing | `pip install opero[aiomultiprocess]` |

## Troubleshooting

### Common Issues

**ImportError after installation:**
```bash
# Make sure you're in the right environment
which python
pip list | grep opero

# Reinstall if needed
pip uninstall opero
pip install opero
```

**Pickling errors with multiprocessing:**
```bash
# Install pathos for better object serialization
pip install opero[pathos]
```

**Permission errors on installation:**
```bash
# Use --user flag or virtual environment
pip install --user opero
```

### Platform-Specific Notes

**Windows:**
- Some features may require Visual C++ Build Tools
- Use Windows Subsystem for Linux (WSL) for best compatibility

**macOS:**
- Xcode Command Line Tools may be required
- Install with: `xcode-select --install`

**Linux:**
- Usually works out of the box
- May need build essentials: `sudo apt-get install build-essential`

## Next Steps

✅ **Installation complete!** 

Now you're ready to:

1. **[Quick Start](quickstart.md)** - Write your first resilient function
2. **[Configuration](configuration.md)** - Learn essential configuration options  
3. **[Basic Usage](../guide/basic-usage.md)** - Explore core concepts

## Version Compatibility

| Opero Version | Python Version | Status |
|---------------|----------------|---------|
| 1.x | 3.8+ | ✅ Supported |
| 0.x | 3.8+ | ⚠️ Legacy |

## Getting Help

If you encounter issues:

1. Check our [GitHub Issues](https://github.com/twardoch/opero/issues)
2. Review the [troubleshooting guide](../api/utils.md#troubleshooting)
3. Start a [discussion](https://github.com/twardoch/opero/discussions)