# Contributing to Terminal Coding Agent

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

This project follows a code of conduct to ensure a welcoming environment for all contributors. Please be respectful and considerate in all interactions.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/terminal-coding-agent.git
   cd terminal-coding-agent
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/terminal-coding-agent.git
   ```

## Development Setup

1. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

4. **Install development tools**:
   ```bash
   pip install black flake8 mypy pytest pytest-cov pytest-asyncio
   ```

## Project Structure

```
terminal-coding-agent/
├── src/                      # Source code
│   ├── agent.py             # Core agent orchestrator
│   ├── cli.py               # CLI interface
│   ├── llm_provider.py      # LLM API wrapper
│   ├── config.py            # Configuration management
│   ├── tools/               # Tool implementations
│   ├── execution/           # Sandboxed execution
│   └── utils/               # Utility modules
├── tests/                   # Test files
├── config.yaml             # Configuration
└── README.md               # Documentation
```

## How to Contribute

### Reporting Bugs

1. **Check existing issues** to avoid duplicates
2. **Create a new issue** with:
   - Clear, descriptive title
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version)
   - Error messages and logs

### Suggesting Features

1. **Open an issue** with the `enhancement` label
2. **Describe the feature**:
   - Use case and motivation
   - Proposed implementation (if applicable)
   - Potential challenges

### Contributing Code

1. **Pick an issue** or create one
2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** following coding standards
4. **Write tests** for new functionality
5. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add feature description"
   ```
6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Create a Pull Request**

## Coding Standards

### Python Style Guide

- Follow **PEP 8** conventions
- Use **type hints** for function signatures
- Write **docstrings** for all public functions and classes
- Keep functions **small and focused**
- Maximum line length: **127 characters**

### Code Formatting

We use automated tools for consistent formatting:

```bash
# Format code with black
black .

# Sort imports with isort
isort .

# Check style with flake8
flake8 .

# Type check with mypy
mypy src/
```

### Docstring Format

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description of function.
    
    Longer description if needed, explaining what the function does,
    any important details, and usage examples.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When invalid input is provided
        
    Example:
        >>> function_name("test", 42)
        True
    """
    pass
```

### Commit Message Format

Follow conventional commits:

```
<type>: <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat: add code execution sandbox

fix: resolve race condition in tool execution

docs: update README with new examples
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_agent.py

# Run specific test
pytest tests/test_agent.py::test_function_name
```

### Writing Tests

1. **Test file naming**: `test_<module_name>.py`
2. **Test function naming**: `test_<function_name>_<scenario>`
3. **Use fixtures** for common setup
4. **Mock external dependencies** (API calls, file I/O)

Example test:

```python
import pytest
from src.agent import CodingAgent
from src.config import Config

@pytest.fixture
def agent():
    """Create agent instance for testing."""
    config = Config("test_config.yaml")
    return CodingAgent(config)

def test_process_message_success(agent):
    """Test successful message processing."""
    response = await agent.process_message("Create a test file")
    assert "created" in response.lower()
    assert agent.iteration_count > 0

def test_process_message_error_handling(agent):
    """Test error handling in message processing."""
    with pytest.raises(ValueError):
        await agent.process_message("")
```

### Test Coverage

- Aim for **>80% code coverage**
- All new features must include tests
- Bug fixes should include regression tests

## Pull Request Process

### Before Submitting

1. **Update your branch** with latest upstream:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run all checks**:
   ```bash
   # Format code
   black .
   isort .
   
   # Run linters
   flake8 .
   mypy src/
   
   # Run tests
   pytest --cov=src
   ```

3. **Update documentation** if needed

### PR Template

When creating a PR, include:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests added/updated
- [ ] All tests passing
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added and passing
- [ ] Dependent changes merged

## Related Issues
Fixes #(issue number)

## Screenshots (if applicable)
Add screenshots for UI changes
```

### Review Process

1. **Automated checks** must pass (CI/CD)
2. **At least one approval** required
3. **Address review comments** promptly
4. **Squash commits** if requested
5. **Maintainer will merge** when approved

### After Merge

1. **Delete your branch**:
   ```bash
   git branch -d feature/your-feature-name
   git push origin --delete feature/your-feature-name
   ```

2. **Update your fork**:
   ```bash
   git checkout main
   git pull upstream main
   git push origin main
   ```

## Development Workflow

### Adding a New Tool

1. **Create tool file** in `src/tools/`:
   ```python
   from src.tools.base import BaseTool
   
   class MyNewTool(BaseTool):
       name = "my_new_tool"
       description = "Description of what the tool does"
       
       def get_schema(self):
           return {
               "type": "object",
               "properties": {
                   "param": {"type": "string", "description": "Parameter description"}
               },
               "required": ["param"]
           }
       
       async def execute(self, **kwargs):
           # Implementation
           return {"success": True, "result": "..."}
   ```

2. **Register tool** in `src/tools/__init__.py`
3. **Write tests** in `tests/test_tools.py`
4. **Update documentation** in README.md

### Debugging Tips

1. **Enable debug logging**:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Use the Python debugger**:
   ```python
   import pdb; pdb.set_trace()
   ```

3. **Test in isolation**:
   ```bash
   python -m src.tools.my_tool
   ```

4. **Check logs**:
   ```bash
   tail -f agent.log
   ```

## Release Process

Maintainers follow these steps for releases:

1. **Update version** in `setup.py`
2. **Update CHANGELOG.md**
3. **Create release branch**: `release/v0.2.0`
4. **Tag the release**: `git tag v0.2.0`
5. **Push to GitHub**: `git push --tags`
6. **Create GitHub release** with notes
7. **Publish to PyPI** (if applicable)

## Getting Help

- **Join discussions** on GitHub Discussions
- **Ask questions** in issues with `question` label
- **Check documentation** in the wiki
- **Contact maintainers** for sensitive issues

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in significant features

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

Thank you for contributing to Terminal Coding Agent! 🚀