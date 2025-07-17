# Build and Release Guide

This document describes the build and release process for the Opero project.

## Prerequisites

- Python 3.10+
- [Hatch](https://hatch.pypa.io/) for project management
- Git for version control

## Quick Start

```bash
# Set up development environment
make setup

# Run all checks
make check

# Build package
make build

# Create a patch release
make release VERSION=patch
```

## Development Workflow

### 1. Environment Setup

```bash
# Install hatch if not already installed
pip install hatch

# Set up development environment
make setup

# Activate development environment
hatch shell

# Install pre-commit hooks
make install-hooks
```

### 2. Development Commands

```bash
# Run tests
make test

# Run tests with coverage
make test-cov

# Run linting and formatting
make lint
make format

# Run type checking
make typecheck

# Run all checks together
make check

# Run benchmarks
make benchmark
```

### 3. Using Scripts Directly

The `scripts/` directory contains Python scripts for various tasks:

```bash
# Development utilities
python scripts/dev.py setup     # Set up development environment
python scripts/dev.py lint      # Run linting
python scripts/dev.py test      # Run tests
python scripts/dev.py check     # Run all checks
python scripts/dev.py clean     # Clean build artifacts

# Build package
python scripts/build.py

# Run tests with coverage
python scripts/test.py

# Create a release
python scripts/release.py [patch|minor|major]
```

## Git-Tag-Based Versioning

The project uses [hatch-vcs](https://github.com/ofek/hatch-vcs) for automatic versioning based on git tags.

### How it works:

1. **Version Source**: The version is automatically derived from git tags
2. **Version Format**: Tags should follow semantic versioning (e.g., `v1.2.3`)
3. **Development Versions**: Between releases, versions include commit info (e.g., `1.2.3.dev1+g1234567`)

### Current version:

```bash
# Check current version
python -c "import opero; print(opero.__version__)"

# Or using hatch
hatch version
```

## Release Process

### Automatic Release (Recommended)

Use the release script for automated releases:

```bash
# Create a patch release (1.0.0 -> 1.0.1)
python scripts/release.py patch

# Create a minor release (1.0.1 -> 1.1.0)  
python scripts/release.py minor

# Create a major release (1.1.0 -> 2.0.0)
python scripts/release.py major
```

The script will:
1. ✅ Check that working directory is clean
2. 🔨 Run build process (linting, tests, build)
3. 📝 Update CHANGELOG.md
4. 🏷️ Create git tag
5. 🚀 Push to origin
6. 🎉 Trigger GitHub Actions for PyPI release

### Manual Release

If you need to create a release manually:

```bash
# 1. Ensure everything is ready
make check
make build

# 2. Update CHANGELOG.md manually
# Add your changes under a new version section

# 3. Commit changes
git add CHANGELOG.md
git commit -m "docs: update changelog for v1.2.3"

# 4. Create and push tag
git tag v1.2.3
git push origin main
git push origin v1.2.3
```

## CI/CD Pipeline

### GitHub Actions Workflows

The project uses GitHub Actions for continuous integration and deployment:

#### 1. `push.yml` - Continuous Integration
- **Triggers**: Push to main, pull requests
- **Jobs**: 
  - Code quality checks (ruff)
  - Tests on multiple Python versions
  - Build distribution files

#### 2. `release.yml` - Release Pipeline
- **Triggers**: Git tags matching `v*`
- **Jobs**:
  - Multi-platform testing (Linux, Windows, macOS)
  - Build standalone binaries
  - Publish to PyPI
  - Create GitHub release with artifacts

### Artifacts

Each release produces:
- **Python Package**: Published to PyPI
- **Source Distribution**: `.tar.gz` file
- **Wheel Distribution**: `.whl` file
- **Standalone Binaries**: 
  - `opero-linux-x86_64`
  - `opero-windows-x86_64.exe`
  - `opero-macos-x86_64`

## Testing

### Test Suite Structure

```
tests/
├── test_core.py         # Core functionality tests
├── test_decorators.py   # Decorator interface tests
├── test_integration.py  # Integration tests
├── test_edge_cases.py   # Edge cases and error handling
├── test_benchmark.py    # Performance benchmarks
└── test_package.py      # Package-level tests
```

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
hatch run test:test tests/test_core.py

# Run benchmarks
make benchmark

# Run tests in parallel
hatch run test:test -n auto
```

### Test Coverage

The project aims for >90% test coverage. Coverage reports are generated in multiple formats:
- Terminal output
- XML report (`coverage.xml`)
- HTML report (`htmlcov/`)

## Building

### Local Build

```bash
# Build using make
make build

# Build using script
python scripts/build.py

# Build using hatch directly
hatch build
```

### Build Artifacts

After building, you'll find:
- `dist/opero-*.tar.gz` - Source distribution
- `dist/opero-*.whl` - Wheel distribution

### Build Requirements

The build process requires:
- `hatchling` - Build backend
- `hatch-vcs` - Version control integration
- `ruff` - Linting and formatting
- `mypy` - Type checking

## Troubleshooting

### Common Issues

1. **Version not updating**
   ```bash
   # Ensure you have git tags
   git tag --list
   
   # Check hatch-vcs configuration
   hatch version
   ```

2. **Tests failing**
   ```bash
   # Clean and reinstall
   make clean
   make dev-install
   make test
   ```

3. **Linting errors**
   ```bash
   # Auto-fix formatting
   make format
   
   # Check remaining issues
   make lint
   ```

4. **Build failures**
   ```bash
   # Clean previous builds
   make clean
   
   # Rebuild
   make build
   ```

### Getting Help

- Check existing [GitHub Issues](https://github.com/twardoch/opero/issues)
- Review the [main README](README.md)
- Examine the [CHANGELOG](CHANGELOG.md)

## Environment Variables

Some behaviors can be controlled with environment variables:

```bash
# Skip time-consuming tests
export OPERO_SKIP_SLOW_TESTS=1

# Verbose test output
export OPERO_VERBOSE_TESTS=1

# Custom test timeout
export OPERO_TEST_TIMEOUT=60
```

## Development Best Practices

1. **Always run checks before committing**:
   ```bash
   make check
   ```

2. **Use pre-commit hooks**:
   ```bash
   make install-hooks
   ```

3. **Write tests for new features**:
   - Add integration tests for new decorators
   - Include edge cases and error conditions
   - Add benchmarks for performance-critical code

4. **Follow semantic versioning**:
   - Patch: Bug fixes
   - Minor: New features, backward compatible
   - Major: Breaking changes

5. **Update documentation**:
   - Update README for new features
   - Update CHANGELOG for releases
   - Add docstrings for new functions