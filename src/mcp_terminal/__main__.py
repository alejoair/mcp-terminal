"""
MCP Terminal Server - Main entry point.

Run the server with:
    python -m mcp_terminal
    or
    mcp-terminal
"""

import argparse
import io
import logging
import sys

import uvicorn

# Configure UTF-8 encoding for stdout/stderr on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def main():
    """Main entry point for the MCP Terminal Server."""
    parser = argparse.ArgumentParser(
        description="MCP Terminal Server - Interactive terminal sessions via MCP protocol",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start server on default port (8777)
  mcp-terminal

  # Start server on custom port
  mcp-terminal --port 9000

  # Start with auto-reload for development
  mcp-terminal --reload

  # Custom host and port
  mcp-terminal --host 0.0.0.0 --port 8888

Documentation: https://github.com/yourusername/mcp-terminal
        """,
    )

    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8777,
        help="Port to bind to (default: 8777)",
    )

    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default="info",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Log level (default: info)",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = getattr(logging, args.log_level.upper())
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger = logging.getLogger(__name__)

    # Print startup banner
    print("=" * 60)
    print("🖥️  MCP Terminal Server")
    print("=" * 60)
    print(f"Version:    0.1.0")
    print(f"Host:       {args.host}")
    print(f"Port:       {args.port}")
    print(f"Log Level:  {args.log_level}")
    print(f"Reload:     {args.reload}")
    print("=" * 60)
    print(f"\n📡 Server starting at http://{args.host}:{args.port}")
    print(f"📚 API Docs:     http://{args.host}:{args.port}/docs")
    print(f"🔧 MCP Endpoint: http://{args.host}:{args.port}/mcp")
    print("\nPress CTRL+C to stop the server\n")

    try:
        # Start uvicorn server
        uvicorn.run(
            "mcp_terminal.server:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=args.log_level,
            access_log=True,
        )
    except KeyboardInterrupt:
        logger.info("\n👋 Shutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Server failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
