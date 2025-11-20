# 🖥️ MCP Terminal Server

[![PyPI version](https://badge.fury.io/py/mcp-terminal.svg)](https://badge.fury.io/py/mcp-terminal)
[![Python Versions](https://img.shields.io/pypi/pyversions/mcp-terminal.svg)](https://pypi.org/project/mcp-terminal/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Interactive terminal sessions via Model Context Protocol (MCP)**

MCP Terminal Server provides cross-platform PTY (pseudo-terminal) support for Windows, Linux, and macOS, exposing terminal sessions through both REST API and MCP protocol. Perfect for AI assistants, remote terminal access, and terminal automation.

## ✨ Features

- **🌍 Cross-platform**: Works on Windows (cmd.exe/PowerShell), Linux, and macOS
- **🔄 Real PTY**: Supports interactive commands (vim, nano, htop, etc.)
- **👁️ Visual Snapshots**: Captures what a human would see on the terminal screen
- **🔤 UTF-8 Support**: Handles special characters and emojis correctly
- **🚀 MCP Protocol**: Auto-exposes all endpoints as MCP tools via fastapi-mcp
- **📡 REST API**: Full HTTP/REST API with FastAPI
- **🎯 Multiple Sessions**: Manage multiple terminal sessions simultaneously

## 📦 Installation

### From PyPI

```bash
pip install mcp-terminal
```

### From Source

```bash
git clone https://github.com/alejoair/mcp-terminal
cd mcp-terminal
pip install -e .
```

## 🚀 Quick Start

### Start the Server

```bash
# Start on default port (8777)
mcp-terminal

# Start on custom port
mcp-terminal --port 9000

# Development mode with auto-reload
mcp-terminal --reload

# Custom host and port
mcp-terminal --host 0.0.0.0 --port 8888
```

### Access the Server

Once running, you can access:

- **API Documentation**: http://localhost:8777/docs
- **MCP Endpoint**: http://localhost:8777/mcp
- **Health Check**: http://localhost:8777/health

## 📖 Usage

### REST API

#### Create a Terminal

```bash
curl -X POST http://localhost:8777/terminals \
  -H "Content-Type: application/json" \
  -d '{"rows": 24, "cols": 80}'
```

Response:
```json
{
  "success": true,
  "terminal_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Terminal created successfully"
}
```

#### Send Commands

```bash
curl -X POST http://localhost:8777/terminals/{terminal_id}/input \
  -H "Content-Type: application/json" \
  -d '{"data": "echo Hello World\n"}'
```

#### Get Visual Snapshot

```bash
curl http://localhost:8777/terminals/{terminal_id}/snapshot
```

Response:
```json
{
  "terminal_id": "550e8400-e29b-41d4-a716-446655440000",
  "display": "C:\\Users\\...\nHello World\nC:\\Users\\...> ",
  "lines": ["C:\\Users\\...", "Hello World", "C:\\Users\\...> "],
  "cursor": {"row": 2, "col": 15},
  "size": {"rows": 24, "cols": 80},
  "is_alive": true,
  "created_at": "2024-01-01T00:00:00"
}
```

#### List Terminals

```bash
curl http://localhost:8777/terminals
```

#### Resize Terminal

```bash
curl -X PUT http://localhost:8777/terminals/{terminal_id}/resize \
  -H "Content-Type: application/json" \
  -d '{"rows": 30, "cols": 100}'
```

#### Close Terminal

```bash
curl -X DELETE http://localhost:8777/terminals/{terminal_id}
```

### MCP Tools

When using with MCP clients (like Claude Desktop), the following tools are automatically available:

- `create_terminal_terminals__post` - Create new terminal
- `list_terminals_terminals__get` - List active terminals
- `get_terminal_snapshot_terminals__terminal_id__snapshot_get` - Get visual snapshot
- `send_terminal_input_terminals__terminal_id__input_post` - Send commands
- `resize_terminal_terminals__terminal_id__resize_put` - Resize terminal
- `close_terminal_terminals__terminal_id__delete` - Close terminal

### Python API

```python
from mcp_terminal import TerminalManager

# Create manager
manager = TerminalManager()

# Create terminal
terminal_id = await manager.create(rows=24, cols=80)

# Send input
await manager.send_input(terminal_id, "echo Hello\n")

# Get snapshot
snapshot = await manager.get_snapshot(terminal_id)
print(snapshot["display"])

# Close terminal
await manager.close(terminal_id)
```

## 🏗️ Architecture

```
src/mcp_terminal/
├── __init__.py          # Package initialization
├── __main__.py          # CLI entry point
├── server.py            # FastAPI application with MCP integration
├── core/
│   └── terminal/
│       ├── session.py   # TerminalSession - PTY management
│       ├── buffer.py    # TerminalBuffer - Visual screen capture
│       └── manager.py   # TerminalManager - Multi-session coordinator
└── models/
    └── terminal.py      # Pydantic models for API
```

## 🔧 Configuration

### Command Line Options

```
--host HOST          Host to bind to (default: 127.0.0.1)
--port PORT          Port to bind to (default: 8777)
--reload             Enable auto-reload for development
--log-level LEVEL    Set log level (debug, info, warning, error, critical)
--version            Show version and exit
```

### Environment Variables

You can also configure via environment variables:

```bash
export MCP_TERMINAL_HOST=0.0.0.0
export MCP_TERMINAL_PORT=9000
export MCP_TERMINAL_LOG_LEVEL=debug
```

## 🧪 Testing

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=mcp_terminal
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Uses [terminado](https://github.com/jupyter/terminado) for cross-platform PTY support
- Uses [pyte](https://github.com/selectel/pyte) for terminal emulation
- MCP integration via [fastapi-mcp](https://github.com/mcp/fastapi-mcp)

## 📚 Resources

- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [terminado Documentation](https://terminado.readthedocs.io/)

## 🐛 Bug Reports

If you find a bug, please open an issue on [GitHub](https://github.com/alejoair/mcp-terminal/issues).

## 💬 Support

For questions and support, please use [GitHub Discussions](https://github.com/alejoair/mcp-terminal/discussions).

---

Made with ❤️ by the MCP Terminal team
