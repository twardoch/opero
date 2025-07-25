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

Opero has optional dependencies that enable additional features:

### Enhanced Multiprocessing

For better serialization support (handles more Python object types):

```bash
pip install opero[pathos]
```

This adds [pathos](https://github.com/uqfoundation/pathos) which provides:
- Enhanced pickling capabilities via `dill`
- Better support for lambda functions and closures
- Improved handling of complex objects in multiprocessing

### Asynchronous Multiprocessing

For running async functions in separate processes:

```bash
pip install opero[aiomultiprocess]
```

This enables the `async_process` mode in `@opmap` for CPU-intensive async operations.

### All Optional Dependencies

To install all optional features:

```bash
pip install opero[all]
```

## Development Installation

For contributing to Opero or running from source:

```bash
# Clone the repository
git clone https://github.com/twardoch/opero.git
cd opero

# Install with development dependencies
pip install -e ".[dev,test]"

# Or using Hatch (recommended)
pip install hatch
hatch shell
```

## Verify Installation

After installation, verify Opero is working:

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

These are always installed:

- **tenacity** (≥8.0.0): Retry logic foundation
- **asynciolimiter** (≥1.0.0): Async-compatible rate limiting
- **twat-cache** (≥2.3.0): Flexible caching backend
- **twat-mp** (≥2.6.0): Multiprocessing abstraction

### Optional Dependencies

Installed based on your chosen extras:

- **pathos** (≥0.3.0): Enhanced multiprocessing
- **aiomultiprocess** (≥0.9.0): Async multiprocessing

## Platform Support

Opero is tested on:
- Linux (Ubuntu 20.04+)
- macOS (11+)
- Windows (10+)

With Python versions:
- Python 3.10
- Python 3.11
- Python 3.12
- PyPy 3.10

## Troubleshooting

### Import Errors

If you encounter import errors after installation:

```bash
# Ensure pip is up to date
pip install --upgrade pip

# Reinstall with verbose output
pip install --force-reinstall -v opero
```

### Permission Errors

On Unix-like systems, you might need to use user installation:

```bash
pip install --user opero
```

Or use a virtual environment (recommended):

```bash
python -m venv opero-env
source opero-env/bin/activate  # On Windows: opero-env\Scripts\activate
pip install opero
```

### Cache Backend Issues

If you encounter cache-related errors, ensure the `klepto` package is available:

```bash
pip install klepto
```

## Next Steps

- Continue to [Quick Start](quickstart.md) to see Opero in action
- Read the [Configuration Guide](configuration.md) for customization options
- Explore the [User Guide](../guide/basic-usage.md) for detailed examples