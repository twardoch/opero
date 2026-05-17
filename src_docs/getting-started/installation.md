# Installation

## Requirements

- Python 3.10 or higher
- pip package manager

## Basic Installation

Install Opero using pip:

```bash
pip install opero
```

This installs the core package with all essential features:
- Retry mechanisms with exponential backoff
- Parameter-based fallbacks
- Rate limiting
- Caching (memory backend)
- Basic parallel processing

## Optional Dependencies

Opero supports additional features through optional dependencies:

### Enhanced Multiprocessing

For better serialization support:

```bash
pip install opero[pathos]
```

Adds [pathos](https://github.com/uqfoundation/pathos) which provides:
- Enhanced pickling via `dill`
- Support for lambda functions and closures
- Improved handling of complex objects in multiprocessing

### Asynchronous Multiprocessing

For running async functions in separate processes:

```bash
pip install opero[aiomultiprocess]
```

Enables the `async_process` mode in `@opmap` for CPU-intensive async operations.

### All Optional Dependencies

To install everything:

```bash
pip install opero[all]
```

## Development Installation

For contributing or running from source:

```bash
# Clone the repository
git clone https://github.com/twardoch/opero.git
cd opero

# Install with development dependencies
pip install -e ".[dev,test]"

# Or using Hatch (preferred)
pip install hatch
hatch shell
```

## Verify Installation

Test that Opero works:

```python
import opero
print(opero.__version__)

# Test basic functionality
from opero import opero as opero_decorator

@opero_decorator(retries=2)
def test_function():
    return "Opero is working!"

print(test_function())
```

## Dependencies Overview

### Core Dependencies

Always installed:

- **tenacity** (≥8.0.0): Retry logic
- **asynciolimiter** (≥1.0.0): Async rate limiting
- **twat-cache** (≥2.3.0): Caching backend
- **twat-mp** (≥2.6.0): Multiprocessing wrapper

### Optional Dependencies

Installed with extras:

- **pathos** (≥0.3.0): Enhanced multiprocessing
- **aiomultiprocess** (≥0.9.0): Async multiprocessing

## Platform Support

Opero is tested on:
- Linux (Ubuntu 20.04+)
- macOS (11+)
- Windows (10+)

With Python versions:
- 3.10, 3.11, 3.12
- PyPy 3.10

## Troubleshooting

### Import Errors

If imports fail after installation:

```bash
# Update pip
pip install --upgrade pip

# Force reinstall
pip install --force-reinstall -v opero
```

### Permission Errors

On Unix-like systems, try user installation:

```bash
pip install --user opero
```

Or use a virtual environment (better idea):

```bash
python -m venv opero-env
source opero-env/bin/activate  # Windows: opero-env\Scripts\activate
pip install opero
```

### Cache Backend Issues

If caching breaks, install `klepto`:

```bash
pip install klepto
```

## Next Steps

- [Quick Start](quickstart.md) – see Opero in action
- [Configuration Guide](configuration.md) – customize behavior
- [User Guide](../guide/basic-usage.md) – detailed examples