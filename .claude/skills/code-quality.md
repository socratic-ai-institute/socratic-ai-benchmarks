# Code Quality Skill

## Description
Maintain high code quality with automated testing, linting, and security checks.

## When to Use
- Before committing code
- During code review
- When adding new features
- When refactoring

## Quick Commands

### Format Code
```bash
cd /home/user/socratic-ai-benchmarks
make format
```

### Run All Linters
```bash
make lint
```

### Security Audit
```bash
make check-security
```

### Full Audit
```bash
make audit
```

## Code Standards

### Python Style
- **Formatter**: Black (line length: 100)
- **Import Sorting**: isort (Black-compatible profile)
- **Linters**: ruff, flake8, pylint, mypy
- **Type Hints**: Required for public functions

### Security
- **Tool**: Bandit
- **Config**: `.bandit.yml`
- **Focus**: SQL injection, shell injection, pickle usage, weak crypto

### Testing
- **Framework**: pytest
- **Coverage Target**: >80% for core library
- **Test Organization**:
  - `tests/unit/` - Fast, mocked tests
  - `tests/integration/` - AWS integration tests
- **Markers**: `@pytest.mark.unit`, `@pytest.mark.integration`

## Pre-commit Hooks

### Setup
```bash
make install-dev  # Installs pre-commit hooks
```

### Manual Run
```bash
make pre-commit
```

### What Gets Checked
1. Trailing whitespace
2. End of file newlines
3. YAML/JSON syntax
4. Large files (>1MB)
5. Merge conflicts
6. Private keys
7. Python formatting (Black)
8. Import sorting (isort)
9. Linting (ruff)
10. Security (Bandit)
11. Type checking (mypy) - optional
12. Unit tests

## Testing Best Practices

### Writing Tests
```python
# Good: Descriptive name, clear assertion
def test_socratic_question_detection():
    """Test that open-ended questions are detected correctly."""
    response = "What assumptions are you making?"
    scores = compute_heuristic_scores(response)
    assert scores["is_open_ended"] is True

# Bad: Unclear name, complex setup
def test_1():
    r = "What?"
    s = compute_heuristic_scores(r)
    assert s["is_open_ended"]
```

### Test Organization
```python
class TestHeuristicScores:
    """Tests for heuristic scoring functions."""

    def test_good_socratic_question(self):
        """Test scoring of a good Socratic question."""
        # Arrange
        response = "What assumptions are you making?"

        # Act
        scores = compute_heuristic_scores(response)

        # Assert
        assert scores["has_question"] is True
        assert scores["is_open_ended"] is True
```

### Fixtures
```python
# Use conftest.py for shared fixtures
@pytest.fixture
def sample_dialogue_turn():
    """Sample dialogue turn for testing."""
    return {
        "turn_index": 0,
        "student": "What is leadership?",
        "ai": "What do you think makes a good leader?",
        "input_tokens": 100,
        "output_tokens": 50
    }

# Use in tests
def test_turn_processing(sample_dialogue_turn):
    result = process_turn(sample_dialogue_turn)
    assert result is not None
```

## Common Issues

### Linter Conflicts
- Black and flake8 may disagree on line length
- Use `--ignore=E203,W503` for flake8
- Configure in `pytest.ini` or `setup.cfg`

### Type Errors
- Add `# type: ignore` only when necessary
- Prefer fixing the actual type issue
- Use `typing.Any` sparingly

### Test Failures
- Check if fixtures are set up correctly
- Verify mocks return expected data
- Review test isolation (no shared state)

## Coverage Reports

### Generate Report
```bash
make test-cov
```

### View Report
```bash
# Terminal
cat serverless/htmlcov/index.html

# Browser (serve locally)
cd serverless/htmlcov && python3 -m http.server 8001
# Visit http://localhost:8001
```

### Interpreting Coverage
- **Green**: >80% coverage (good)
- **Yellow**: 60-80% coverage (acceptable)
- **Red**: <60% coverage (needs improvement)

## Related Commands
- `make test` - Run tests
- `make lint` - Run linters
- `make format` - Format code
- `make audit` - Full audit (lint + security + tests)
- `make pre-commit` - Run pre-commit hooks
