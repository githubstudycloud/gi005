# Voice Clone TTS Tests

This directory contains the test suite for Voice Clone TTS.

## Test Structure

```
tests/
├── conftest.py          # Pytest configuration and fixtures
├── test_base.py         # Tests for base classes (VoiceEmbedding, VoiceClonerBase)
├── test_xtts.py         # Tests for XTTS engine
├── test_server.py       # Tests for HTTP server
├── test_client.py       # Tests for HTTP client
├── test_v3_gateway.py   # Tests for v3 Gateway (microservices)
└── test_v3_worker.py    # Tests for v3 Worker (microservices)
```

## Running Tests

### Install pytest

```bash
pip install pytest pytest-cov
```

### Run all tests

```bash
# From project root
pytest

# With verbose output
pytest -v

# With coverage report
pytest --cov=voice-clone-tts/production
```

### Run specific test files

```bash
# Run base tests only
pytest tests/test_base.py

# Run XTTS tests only
pytest tests/test_xtts.py
```

### Run by markers

```bash
# Skip slow tests (model loading)
pytest -m "not slow"

# Skip integration tests
pytest -m "not integration"

# Run only unit tests
pytest -m "not slow and not integration"
```

## Test Categories

### Unit Tests (Default)
- Fast tests that don't require model loading
- Test imports, class instantiation, method signatures
- Run on every commit

### Slow Tests (`@pytest.mark.slow`)
- Require model loading (~30s-2min)
- Test actual synthesis functionality
- Run before releases

### Integration Tests (`@pytest.mark.integration`)
- Require running server/services
- Test HTTP endpoints and client/server communication
- Run in CI/CD with service containers

## Writing New Tests

### Test Structure

```python
import pytest

class TestFeatureName:
    """Tests for FeatureName."""

    def test_basic_functionality(self):
        """Test basic behavior."""
        # Arrange
        ...
        # Act
        result = ...
        # Assert
        assert result == expected

    @pytest.mark.slow
    def test_with_model(self, loaded_xtts_cloner):
        """Test with loaded model (slow)."""
        ...

    @pytest.mark.integration
    def test_with_server(self, test_client):
        """Test with running server."""
        ...
```

### Using Fixtures

Common fixtures from `conftest.py`:

| Fixture | Scope | Description |
|---------|-------|-------------|
| `project_root` | session | Project root directory |
| `production_path` | session | Production code directory |
| `test_audio_path` | session | Test audio directory |
| `sample_audio` | session | Sample audio file path |
| `voices_dir` | session | Voices storage directory |
| `temp_output_dir` | function | Temporary output directory |
| `xtts_cloner` | module | XTTS cloner (not loaded) |
| `loaded_xtts_cloner` | module | XTTS cloner with model |

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt pytest
      - run: pytest -m "not slow and not integration"

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt pytest
      # Download model files...
      - run: pytest -m "slow or integration"
```

## Troubleshooting

### Tests fail to import

Ensure you're running from project root:
```bash
cd voice-clone-tts
pytest
```

### Model not found

Run slow tests only after model setup:
```bash
# First setup models
cd tts_model && cat xtts_v2.tar.part_* | tar -xvf -

# Then run slow tests
pytest -m slow
```

### Server not running for integration tests

Start server before running integration tests:
```bash
# Terminal 1: Start server
python main.py serve --engine xtts --port 8000

# Terminal 2: Run tests
pytest -m integration
```
