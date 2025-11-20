# 🚀 Quick Start Guide

## Local Installation & Testing

### 1. Install in Development Mode

```bash
# Navigate to project directory
cd mcp-terminal

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

This installs the package in development mode, so changes to the code are immediately reflected.

### 2. Run the Server

```bash
# Start on default port (8777)
mcp-terminal

# Or with custom options
mcp-terminal --port 9000 --reload
```

You should see:
```
============================================================
🖥️  MCP Terminal Server
============================================================
Version:    0.1.0
Host:       127.0.0.1
Port:       8777
Log Level:  info
Reload:     False
============================================================

📡 Server starting at http://127.0.0.1:8777
📚 API Docs:     http://127.0.0.1:8777/docs
🔧 MCP Endpoint: http://127.0.0.1:8777/mcp

Press CTRL+C to stop the server
```

### 3. Test the API

Open your browser and go to:
- **API Docs**: http://localhost:8777/docs
- **Try the interactive API documentation**

Or use curl:

```bash
# Create a terminal
curl -X POST http://localhost:8777/terminals \
  -H "Content-Type: application/json" \
  -d '{"rows": 24, "cols": 80}'

# Save the terminal_id from response, then send a command
curl -X POST http://localhost:8777/terminals/{terminal_id}/input \
  -H "Content-Type: application/json" \
  -d '{"data": "echo Hello from MCP Terminal\n"}'

# Get the snapshot
curl http://localhost:8777/terminals/{terminal_id}/snapshot

# List all terminals
curl http://localhost:8777/terminals

# Close the terminal
curl -X DELETE http://localhost:8777/terminals/{terminal_id}
```

### 4. Test with Python

```python
import asyncio
from mcp_terminal import TerminalManager

async def test():
    manager = TerminalManager()

    # Create terminal
    terminal_id = await manager.create(rows=24, cols=80)
    print(f"Created terminal: {terminal_id}")

    # Send command
    await manager.send_input(terminal_id, "echo Hello World\n")

    # Wait a bit for output
    await asyncio.sleep(0.5)

    # Get snapshot
    snapshot = await manager.get_snapshot(terminal_id)
    print("Display:")
    print(snapshot["display"])

    # Close
    await manager.close(terminal_id)

asyncio.run(test())
```

## Building the Package

### Build

```bash
# Install build tools
pip install build

# Build the package
python -m build
```

This creates:
- `dist/mcp_terminal-0.1.0.tar.gz` - Source distribution
- `dist/mcp_terminal-0.1.0-py3-none-any.whl` - Wheel

### Test the Built Package

```bash
# Create a clean virtual environment
python -m venv test_env
source test_env/bin/activate  # Windows: test_env\Scripts\activate

# Install the wheel
pip install dist/mcp_terminal-0.1.0-py3-none-any.whl

# Test it
mcp-terminal --version
mcp-terminal
```

## Publishing to PyPI

See [PUBLISHING.md](PUBLISHING.md) for detailed instructions on publishing to PyPI.

Quick version:

```bash
# Install twine
pip install twine

# Test the package
twine check dist/*

# Upload to TestPyPI first (recommended)
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

## Troubleshooting

### Import Errors

If you get import errors, make sure you're in the right directory and have installed the package:

```bash
pip install -e .
```

### Port Already in Use

If port 8777 is already in use:

```bash
mcp-terminal --port 8888
```

### Terminal Not Working on Windows

Make sure you have the latest version of terminado:

```bash
pip install --upgrade terminado
```

## Next Steps

1. ✅ Test locally with `pip install -e .`
2. ✅ Run the server with `mcp-terminal`
3. ✅ Test all endpoints in the API docs
4. ✅ Build the package with `python -m build`
5. ✅ Test on TestPyPI
6. ✅ Publish to PyPI

## Configuration

Before publishing, update these files:

1. **pyproject.toml** - Add your name, email, GitHub URL
2. **src/mcp_terminal/__init__.py** - Update author info
3. **README.md** - Replace placeholder URLs with your actual repository

## Support

- **Documentation**: See [README.md](README.md)
- **Publishing**: See [PUBLISHING.md](PUBLISHING.md)
- **Issues**: Open an issue on GitHub
