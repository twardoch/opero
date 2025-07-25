# Contributing to Opero

Thank you for your interest in contributing to Opero! This guide will help you get started with contributing to the project.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- GitHub account
- Basic knowledge of Python async/await and decorators

### Development Setup

1. **Fork and Clone**

   ```bash
   # Fork the repository on GitHub, then:
   git clone https://github.com/YOUR_USERNAME/opero.git
   cd opero
   ```

2. **Install Hatch**

   We use [Hatch](https://hatch.pypa.io/) for project management:

   ```bash
   pip install hatch
   ```

3. **Set Up Development Environment**

   ```bash
   # Create and activate development environment
   hatch shell
   
   # This installs Opero in editable mode with all dependencies
   ```

4. **Install Pre-commit Hooks**

   ```bash
   pre-commit install
   ```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Your Changes

Follow the coding standards and ensure your changes include:
- Implementation code
- Tests for new functionality
- Documentation updates
- Type hints

### 3. Run Tests

```bash
# Run all tests
hatch run test

# Run tests with coverage
hatch run test-cov

# Run specific test file
hatch run pytest tests/test_decorators.py

# Run tests in parallel
hatch run pytest -n auto
```

### 4. Check Code Quality

```bash
# Run all linting and formatting
hatch run lint:all

# Format code
hatch run lint:fmt

# Type checking
hatch run lint:typing
```

### 5. Update Documentation

If your changes affect the public API:
1. Update docstrings
2. Update relevant documentation in `src_docs/`
3. Build docs locally to verify:
   ```bash
   mkdocs serve
   # View at http://localhost:8000
   ```

### 6. Commit Your Changes

```bash
# Stage your changes
git add .

# Commit with descriptive message
git commit -m "feat: add support for custom retry predicates"
```

Follow conventional commit format:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions or changes
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `chore:` Maintenance tasks

### 7. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Coding Standards

### Code Style

We use Ruff for linting and formatting:

```python
# Good: Clear, typed, documented
from typing import Optional

def process_data(
    data: dict[str, Any],
    timeout: Optional[float] = None
) -> dict[str, Any]:
    """
    Process data with optional timeout.
    
    Args:
        data: Input data dictionary
        timeout: Optional timeout in seconds
        
    Returns:
        Processed data dictionary
        
    Raises:
        ValueError: If data is invalid
    """
    if not data:
        raise ValueError("Data cannot be empty")
    
    return transform(data, timeout=timeout)
```

### Type Hints

Always use type hints:

```python
from typing import TypeVar, Callable, Any, Optional

T = TypeVar('T')

def retry_operation(
    func: Callable[..., T],
    retries: int = 3,
    delay: float = 1.0
) -> T:
    """Retry an operation with delay."""
    ...
```

### Async Support

Ensure compatibility with both sync and async:

```python
import asyncio
from typing import Union, Awaitable

def ensure_awaitable(
    value: Union[T, Awaitable[T]]
) -> Awaitable[T]:
    """Ensure a value is awaitable."""
    if asyncio.iscoroutine(value):
        return value
    return asyncio.create_task(asyncio.coroutine(lambda: value)())
```

### Error Handling

Use custom exceptions for clarity:

```python
class OperoConfigError(OperoError):
    """Raised when configuration is invalid."""
    
    def __init__(self, param: str, value: Any, reason: str):
        super().__init__(
            f"Invalid {param}={value}: {reason}"
        )
        self.param = param
        self.value = value
        self.reason = reason
```

## Testing Guidelines

### Test Structure

```python
import pytest
from unittest.mock import Mock, patch

class TestOperoDecorator:
    """Test suite for @opero decorator."""
    
    def test_basic_retry(self):
        """Test basic retry functionality."""
        mock_func = Mock(side_effect=[Exception("fail"), "success"])
        
        @opero(retries=2)
        def test_func():
            return mock_func()
        
        result = test_func()
        assert result == "success"
        assert mock_func.call_count == 2
    
    @pytest.mark.asyncio
    async def test_async_function(self):
        """Test async function support."""
        @opero(cache=True)
        async def async_func(x):
            await asyncio.sleep(0.01)
            return x * 2
        
        result = await async_func(5)
        assert result == 10
```

### Test Coverage

Aim for high test coverage:
- Unit tests for all public functions
- Integration tests for decorator combinations
- Edge cases and error conditions
- Performance benchmarks for critical paths

### Fixtures

Use fixtures for common test data:

```python
@pytest.fixture
def mock_api_client():
    """Mock API client for testing."""
    client = Mock()
    client.get.return_value = {"status": "ok"}
    return client

@pytest.fixture
def sample_data():
    """Sample data for tests."""
    return [
        {"id": 1, "name": "Test 1"},
        {"id": 2, "name": "Test 2"},
    ]
```

## Documentation

### Docstring Format

Use Google-style docstrings:

```python
def complex_function(
    param1: str,
    param2: Optional[int] = None,
    **kwargs: Any
) -> dict[str, Any]:
    """
    One-line summary of function purpose.
    
    Detailed description of what the function does, including any
    important behavior or side effects.
    
    Args:
        param1: Description of param1
        param2: Description of param2. Defaults to None.
        **kwargs: Additional keyword arguments passed to underlying
            implementation. Supports:
            - option1 (bool): Description of option1
            - option2 (str): Description of option2
    
    Returns:
        Description of return value structure.
        
    Raises:
        ValueError: When param1 is empty
        TypeError: When param2 is not an integer
        
    Examples:
        Basic usage:
        ```python
        result = complex_function("test", param2=42)
        print(result)  # {"status": "ok", "value": 42}
        ```
        
        With additional options:
        ```python
        result = complex_function(
            "test",
            param2=10,
            option1=True,
            option2="advanced"
        )
        ```
        
    Note:
        This function is thread-safe but not process-safe.
        
    See Also:
        simple_function: For basic use cases
        async_function: For async version
    """
```

### API Documentation

When adding new features:
1. Update relevant `.md` files in `src_docs/`
2. Add examples to docstrings
3. Update the API reference
4. Add to changelog

## Pull Request Process

### Before Submitting

- [ ] All tests pass (`hatch run test`)
- [ ] Code is formatted (`hatch run lint:fmt`)
- [ ] Type checking passes (`hatch run lint:typing`)
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated
- [ ] Commit messages follow conventional format

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] My code follows the project style guidelines
- [ ] I have performed a self-review
- [ ] I have added tests covering my changes
- [ ] All new and existing tests pass
- [ ] I have updated documentation
```

### Review Process

1. Automated checks must pass
2. At least one maintainer review required
3. All feedback addressed
4. Final approval from maintainer
5. Squash and merge

## Release Process

Releases are automated via GitHub Actions:

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create and push tag: `git tag v0.3.0`
4. Push tags: `git push --tags`
5. GitHub Action builds and publishes to PyPI

## Getting Help

- **Discord**: Join our Discord server (link in README)
- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and ideas
- **Email**: adam+github@twardoch.com

## Code of Conduct

Please note that this project is released with a Contributor Code of Conduct. By participating in this project you agree to abide by its terms.

## Recognition

Contributors are recognized in:
- CHANGELOG.md for specific contributions
- GitHub contributors page
- Special thanks in release notes

Thank you for contributing to Opero! 🎉