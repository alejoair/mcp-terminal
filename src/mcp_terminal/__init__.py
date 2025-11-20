"""
MCP Terminal - Interactive terminal sessions via MCP protocol.

A Model Context Protocol (MCP) server that provides cross-platform
terminal sessions with PTY support for Windows, Linux, and macOS.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .core.terminal import TerminalManager, TerminalSession

__all__ = ["TerminalManager", "TerminalSession", "__version__"]
