# Installation

Get started with Opero in minutes using pip.

## Requirements

- **Python**: 3.8 or higher  
- **Operating System**: Linux, macOS, or Windows  
- **Dependencies**: Automatically handled by pip  

## Basic Installation

Install Opero with pip:

```bash
pip install opero
```

This installs the core Opero library with all essential features:

- `@opero` decorator for single function resilience  
- `@opmap` decorator for parallel processing  
- Basic retry, fallback, cache, and rate limiting  
- Thread and process-based parallelization  

## Optional Dependencies

Opero supports optional dependencies to extend functionality.

### Enhanced Multiprocessing with Pathos

For advanced multiprocessing that handles complex objects:

```bash
pip install opero[pathos]
```

**Benefits:**
- Serialize closures, lambdas, and class methods  
- Handle nested functions and complex data structures  
- More robust process-based parallelization  

**Use this when:** Standard multiprocessing fails to pickle your objects.

### Async Multiprocessing

To run async functions in separate processes:

```bash
pip install opero[aiomultiprocess]
```

**Benefits:**
- Run async functions in parallel processes  
- Combine async I/O with CPU-bound parallelization  
- Useful for mixed workloads  

**Use this when:** You're dealing with CPU-intensive async tasks or need process isolation for async code.

### All Features

Install everything at once:

```bash
pip install opero[all]
```

Includes all optional dependencies for full functionality.

## Installation Options

### Development Installation

For contributors or those wanting the latest development version:

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

Opero's core dependencies (installed automatically):

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
# Confirm correct environment
which python
pip list | grep opero

# Reinstall if needed
pip uninstall opero
pip install opero
```

**Pickling errors with multiprocessing:**
```bash
# Install pathos for better serialization
pip install opero[pathos]
```

**Permission errors during install:**
```bash
# Try user-local install or use a virtual environment
pip install --user opero
```

### Platform-Specific Notes

**Windows:**
- Some features may require Visual C++ Build Tools  
- WSL recommended for best compatibility  

**macOS:**
- Xcode Command Line Tools may be required  
- Install with: `xcode-select --install`  

**Linux:**
- Usually works out of the box  
- May need build tools: `sudo apt-get install build-essential`  

## Next Steps

Installation complete!

Now you can:

1. **[Quick Start](quickstart.md)** – Write your first resilient function  
2. **[Configuration](configuration.md)** – Learn essential configuration options  
3. **[Basic Usage](../guide/basic-usage.md)** – Explore core concepts  

## Version Compatibility

| Opero Version | Python Version | Status |
|---------------|----------------|--------|
| 1.x | 3.8+ | ✅ Supported |
| 0.x | 3.8+ | ⚠️ Legacy |

## Getting Help

If something goes wrong:

1. Check [GitHub Issues](https://github.com/twardoch/opero/issues)  
2. Review the [troubleshooting guide](../api/utils.md#troubleshooting)  
3. Start a [discussion](https://github.com/twardoch/opero/discussions)