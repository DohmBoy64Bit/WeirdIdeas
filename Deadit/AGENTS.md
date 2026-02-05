# AGENTS.md

## Build, Lint, and Test Commands

### Setup
```bash
# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running Tests
```bash
# Run all tests
pytest

# Run a single test file
pytest tests/test_file.py

# Run a specific test
pytest tests/test_file.py::test_function_name

# Run with coverage
pytest --cov=src

# Run with verbose output
pytest -v
```

### Linting and Formatting
```bash
# Run linter
flake8 src/

# Format code with black
black src/

# Check format with isort
isort src/
```

## Code Style Guidelines

### Imports
- Sort imports alphabetically with standard library, third-party, and local imports separated
- Use relative imports for local modules
- Import full module names for clarity

### Formatting
- Follow PEP 8 style guide
- 88 character line width
- 4 spaces for indentation
- Use double quotes for strings
- Include type hints for all functions and methods

### Naming Conventions
- Use snake_case for functions and variables
- Use PascalCase for classes
- Use UPPER_CASE for constants
- Avoid single character variable names except for loop counters

### Error Handling
- Use specific exception types instead of bare `except:`
- Log errors appropriately with context
- Propagate exceptions instead of suppressing them
- Validate input parameters early

### Types and Annotations
- Include type hints for all function parameters and return values
- Use `Optional` for nullable types
- Use `Union` for multiple possible types
- Annotate class attributes

### Documentation
- Document all public functions with docstrings
- Use Google-style docstrings
- Include parameter descriptions and return values
- Document exceptional behavior

### Testing
- Write unit tests for all business logic
- Test edge cases and error conditions
- Use pytest fixtures for test setup
- Maintain test coverage above 80%

### Architecture
- Follow separation of concerns
- Keep functions small and focused (single responsibility)
- Avoid code duplication (DRY)
- Use composition over inheritance
- Keep modules focused on single responsibilities

### Security Rules
- Validate all user inputs
- Sanitize output before displaying
- Follow the project's quality gate and safety rules
- No hard-coded secrets in source code

This file follows the OPENCODE_RULES.md guidelines for deterministic style enforcement and project conventions.

## Additional Guidelines

When in doubt about any aspect of the project's implementation, always consult the OPENCODE_RULES.md file first. This ensures compliance with all project conventions and maintains consistency across the codebase.