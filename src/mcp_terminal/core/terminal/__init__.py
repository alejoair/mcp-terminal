"""
Terminal module for managing interactive terminal sessions.

Provides cross-platform PTY support and visual screen capture.
"""

from .buffer import TerminalBuffer
from .manager import TerminalManager
from .session import TerminalSession

__all__ = ["TerminalManager", "TerminalSession", "TerminalBuffer"]
