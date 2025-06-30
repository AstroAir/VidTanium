# Contributing to VidTanium

Thank you for your interest in contributing to VidTanium! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Contributing Process](#contributing-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Issue Reporting](#issue-reporting)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)

## Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please be respectful and professional in all interactions.

### Our Standards

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- Basic knowledge of Python and Qt/PySide6
- Familiarity with async/await programming

### Setting Up Development Environment

1. **Fork and clone the repository**

   ```bash
   git clone https://github.com/yourusername/VidTanium.git
   cd VidTanium
   ```

2. **Set up Python environment**

   ```bash
   # Using uv (recommended)
   uv sync --dev

   # Or using pip
   pip install -e ".[dev]"
   ```

3. **Install pre-commit hooks**

   ```bash
   pre-commit install
   ```

4. **Verify setup**

   ```bash
   python main.py --debug
   pytest tests/
   ```

## Development Environment

### Required Tools

- **Python 3.11+**: Core language
- **uv**: Dependency management (preferred) or pip
- **pytest**: Testing framework
- **black**: Code formatting
- **flake8**: Linting
- **mypy**: Type checking
- **pre-commit**: Git hooks

### Optional Tools

- **Qt Designer**: UI design
- **FFmpeg**: Media processing testing
- **Docker**: Containerized testing

### Environment Variables

Create a `.env` file for development:

```bash
# Development settings
DEBUG=true
LOG_LEVEL=DEBUG

# API Keys (if using AI features)
ANTHROPIC_API_KEY=your_key_here
PERPLEXITY_API_KEY=your_key_here
```

## Contributing Process

### Types of Contributions

We welcome various types of contributions:

- **Bug fixes**: Resolve existing issues
- **Feature additions**: New functionality
- **Performance improvements**: Optimization work
- **Documentation**: Improve docs and examples
- **Testing**: Add or improve tests
- **UI/UX improvements**: Interface enhancements

### Workflow

1. **Check existing issues** - Look for related work
2. **Create/claim an issue** - Discuss your proposal
3. **Fork and branch** - Create a feature branch
4. **Develop and test** - Implement your changes
5. **Submit PR** - Create a pull request
6. **Review process** - Address feedback
7. **Merge** - Changes integrated into main

## Coding Standards

### Python Style

We follow PEP 8 with some modifications:

```python
# Good examples
class DownloadManager:
    """Manages video download operations."""
    
    def __init__(self, max_concurrent: int = 5) -> None:
        self._max_concurrent = max_concurrent
        self._active_tasks: list[DownloadTask] = []
    
    async def download_video(self, url: str) -> DownloadResult:
        """Download video from URL."""
        task = await self._create_task(url)
        return await self._execute_task(task)
```

### Code Organization

- **Modules**: Keep modules focused and cohesive
- **Classes**: Single responsibility principle
- **Functions**: Pure functions when possible
- **Imports**: Absolute imports, group by type
- **Type hints**: Use throughout for better IDE support

### Documentation Style

```python
def process_m3u8_playlist(url: str, encryption_key: str = None) -> PlaylistInfo:
    """Process M3U8 playlist and extract video segments.
    
    Args:
        url: The M3U8 playlist URL
        encryption_key: Optional AES encryption key
        
    Returns:
        PlaylistInfo: Parsed playlist information
        
    Raises:
        PlaylistError: When playlist cannot be parsed
        NetworkError: When URL is unreachable
        
    Example:
        >>> info = process_m3u8_playlist("https://example.com/playlist.m3u8")
        >>> print(f"Found {len(info.segments)} segments")
    """
```

## Testing Guidelines

### Test Structure

```bash
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── e2e/           # End-to-end tests
├── fixtures/      # Test data
└── conftest.py    # Pytest configuration
```

### Writing Tests

```python
import pytest
from unittest.mock import Mock, patch

from src.core.downloader import DownloadManager

class TestDownloadManager:
    """Test suite for DownloadManager."""
    
    @pytest.fixture
    def download_manager(self):
        """Create DownloadManager instance for testing."""
        return DownloadManager(max_concurrent=2)
    
    async def test_create_task_success(self, download_manager):
        """Test successful task creation."""
        url = "https://example.com/video.m3u8"
        task = await download_manager.create_task(url)
        
        assert task.url == url
        assert task.status == TaskStatus.PENDING
    
    @patch('src.core.downloader.requests.get')
    async def test_download_with_network_error(self, mock_get, download_manager):
        """Test download handling with network errors."""
        mock_get.side_effect = ConnectionError("Network error")
        
        with pytest.raises(NetworkError):
            await download_manager.download_video("https://example.com/bad.m3u8")
```

### Test Coverage

- Maintain >90% test coverage
- Test both success and failure scenarios
- Include edge cases and error conditions
- Mock external dependencies

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/core/test_downloader.py

# Run tests matching pattern
pytest -k "test_download"

# Run tests with verbose output
pytest -v -s
```

## Documentation

### Types of Documentation

1. **Code documentation**: Docstrings and comments
2. **API documentation**: Generated from docstrings
3. **User guides**: Installation and usage instructions
4. **Developer guides**: Architecture and contribution info

### Documentation Standards

- Clear, concise writing
- Include examples where helpful
- Keep documentation up-to-date with code
- Use proper markdown formatting

### Building Documentation

```bash
# Generate API docs
pdoc src/ -o docs/api/

# Lint documentation
markdownlint *.md docs/*.md
```

## Issue Reporting

### Bug Reports

Include the following information:

- **Environment**: OS, Python version, VidTanium version
- **Steps to reproduce**: Detailed reproduction steps
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Error messages**: Full error traces
- **Screenshots**: If UI-related

### Feature Requests

Describe:

- **Problem**: What problem does this solve?
- **Solution**: Proposed implementation approach
- **Alternatives**: Other solutions considered
- **Use cases**: Real-world usage scenarios

## Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] Changes are focused and atomic
- [ ] Commit messages are clear

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Performance improvement
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes
```

### Review Process

1. **Automated checks**: CI/CD pipeline must pass
2. **Code review**: At least one maintainer approval
3. **Testing**: Verify functionality works as expected
4. **Documentation**: Ensure docs are updated
5. **Integration**: Merge when all requirements met

## Release Process

### Version Numbering

We use [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes

### Release Steps

1. **Update version** in `pyproject.toml`
2. **Update CHANGELOG.md** with new version
3. **Create release branch** from main
4. **Run full test suite** and fix any issues
5. **Create Git tag** with version number
6. **Build distribution packages**
7. **Deploy to package repositories**
8. **Update documentation** sites
9. **Announce release** in appropriate channels

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Pull Requests**: Code contributions
- **Wiki**: Community documentation

### Getting Help

- Check existing documentation
- Search closed issues
- Ask in GitHub Discussions
- Contact maintainers directly for sensitive issues

---

Thank you for contributing to VidTanium! Your efforts help make this project better for everyone.
