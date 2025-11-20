# 📦 Publishing to PyPI

This guide explains how to publish `mcp-terminal` to PyPI.

## Prerequisites

1. **PyPI Account**: Create accounts on both:
   - [TestPyPI](https://test.pypi.org/account/register/) (for testing)
   - [PyPI](https://pypi.org/account/register/) (for production)

2. **API Tokens**: Generate API tokens for both accounts:
   - TestPyPI: https://test.pypi.org/manage/account/token/
   - PyPI: https://pypi.org/manage/account/token/

3. **Install build tools**:
   ```bash
   pip install --upgrade build twine
   ```

## Step-by-Step Publishing

### 1. Update Version

Edit `pyproject.toml` and `src/mcp_terminal/__init__.py` to update the version:

```toml
# pyproject.toml
[project]
version = "0.1.0"  # Update this
```

```python
# src/mcp_terminal/__init__.py
__version__ = "0.1.0"  # Update this
```

### 2. Update Metadata

Edit `pyproject.toml` to add your information:

```toml
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]

[project.urls]
Homepage = "https://github.com/yourusername/mcp-terminal"
Repository = "https://github.com/yourusername/mcp-terminal"
Issues = "https://github.com/yourusername/mcp-terminal/issues"
```

### 3. Clean Previous Builds

```bash
# Remove old build artifacts
rm -rf dist/ build/ *.egg-info src/*.egg-info
```

### 4. Build the Package

```bash
# Build source distribution and wheel
python -m build
```

This creates files in `dist/`:
- `mcp_terminal-0.1.0.tar.gz` (source distribution)
- `mcp_terminal-0.1.0-py3-none-any.whl` (wheel)

### 5. Check the Package

```bash
# Validate the package
twine check dist/*
```

Should output:
```
Checking dist/mcp_terminal-0.1.0-py3-none-any.whl: PASSED
Checking dist/mcp_terminal-0.1.0.tar.gz: PASSED
```

### 6. Test on TestPyPI (Recommended)

```bash
# Upload to TestPyPI first
twine upload --repository testpypi dist/*
```

Enter your TestPyPI API token when prompted.

Test the installation:
```bash
# Create a test environment
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ mcp-terminal

# Test it
mcp-terminal --version
mcp-terminal --help
```

### 7. Publish to PyPI

Once tested, publish to the real PyPI:

```bash
# Upload to PyPI
twine upload dist/*
```

Enter your PyPI API token when prompted.

### 8. Verify Installation

```bash
# Create a fresh environment
python -m venv verify_env
source verify_env/bin/activate  # On Windows: verify_env\Scripts\activate

# Install from PyPI
pip install mcp-terminal

# Test it
mcp-terminal --version
mcp-terminal
```

## Configure ~/.pypirc (Optional)

To avoid entering tokens each time, create `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR-API-TOKEN-HERE

[testpypi]
username = __token__
password = pypi-YOUR-TESTPYPI-TOKEN-HERE
repository = https://test.pypi.org/legacy/
```

Then you can upload with:
```bash
twine upload --repository testpypi dist/*
twine upload dist/*
```

## Automating with GitHub Actions (Optional)

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install build twine

      - name: Build package
        run: python -m build

      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

Add your PyPI API token as a GitHub secret named `PYPI_API_TOKEN`.

## Version Bumping

For semantic versioning:
- **Patch** (0.1.0 → 0.1.1): Bug fixes
- **Minor** (0.1.0 → 0.2.0): New features, backward compatible
- **Major** (0.1.0 → 1.0.0): Breaking changes

## Troubleshooting

### Error: "File already exists"

You can't re-upload the same version. Bump the version number and rebuild.

### Error: "Invalid distribution"

Check your `pyproject.toml` syntax and ensure all required fields are present.

### Error: "Package name already taken"

If `mcp-terminal` is taken, choose a different name in `pyproject.toml`.

## Resources

- [Python Packaging Guide](https://packaging.python.org/)
- [PyPI Help](https://pypi.org/help/)
- [Twine Documentation](https://twine.readthedocs.io/)
