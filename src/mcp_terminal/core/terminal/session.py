"""
Terminal session management using terminado for cross-platform PTY support.
"""

import logging
import os
import uuid
from datetime import datetime
from typing import Optional

from terminado import NamedTermManager

logger = logging.getLogger(__name__)


class TerminalSession:
    """
    Represents a single terminal session with PTY support.

    Uses terminado for cross-platform compatibility (Windows/Linux/macOS).
    Handles encoding in UTF-8 for special characters.
    """

    def __init__(
        self,
        rows: int = 24,
        cols: int = 80,
        shell_command: Optional[list] = None,
    ):
        """
        Initialize a new terminal session.

        Args:
            rows: Number of rows (height) of the terminal
            cols: Number of columns (width) of the terminal
            shell_command: Custom shell command (defaults to system shell)
        """
        self.id = str(uuid.uuid4())
        self.rows = rows
        self.cols = cols
        self.created_at = datetime.utcnow()
        self.is_alive = False

        # Terminal manager for PTY
        self.term_manager = NamedTermManager(
            shell_command=shell_command or self._get_default_shell(),
            max_terminals=1,
        )

        # Terminal process
        self.terminal = None

        # Output buffer
        self._output_buffer = []

        logger.info(f"Terminal session created: {self.id}")

    def _get_default_shell(self) -> list:
        """
        Get default shell command for the current OS.

        Returns:
            Shell command as list
        """
        if os.name == "nt":  # Windows
            return ["cmd.exe"]
        else:  # Unix/Linux/macOS
            return [os.environ.get("SHELL", "/bin/bash")]

    async def start(self):
        """Start the terminal session."""
        if self.is_alive:
            logger.warning(f"Terminal {self.id} already started")
            return

        try:
            # Create new terminal
            self.terminal = self.term_manager.new_terminal()
            self.terminal.ptyproc.setwinsize(self.rows, self.cols)
            self.is_alive = True

            logger.info(f"Terminal {self.id} started")
        except Exception as e:
            logger.error(f"Failed to start terminal {self.id}: {e}")
            raise

    async def write(self, data: str):
        """
        Write data to the terminal.

        Args:
            data: String data to write (commands, keystrokes, etc.)
        """
        if not self.is_alive or not self.terminal:
            raise RuntimeError(f"Terminal {self.id} is not running")

        try:
            import asyncio

            # Decode escape sequences (e.g., \x1b for ESC, \x03 for Ctrl+C)
            # This allows sending control characters from the API
            try:
                data = data.encode().decode('unicode-escape')
            except:
                # If decoding fails, use original data
                pass

            # Convert line endings for Windows compatibility
            # Windows cmd.exe expects \r\n (CRLF) for proper command execution
            if os.name == "nt":  # Windows
                # Replace \n with \r\n for proper command execution
                data = data.replace("\n", "\r\n")

            # Run blocking write in executor with 5 second timeout
            # terminado expects string, not bytes
            loop = asyncio.get_event_loop()
            await asyncio.wait_for(
                loop.run_in_executor(
                    None, lambda: self.terminal.ptyproc.write(data)
                ),
                timeout=5.0,
            )
        except asyncio.TimeoutError:
            logger.error(f"Timeout writing to terminal {self.id}")
            raise RuntimeError(f"Timeout writing to terminal {self.id}")
        except Exception as e:
            logger.error(f"Failed to write to terminal {self.id}: {e}")
            raise

    async def read(self, timeout: float = 0.1) -> str:
        """
        Read available output from the terminal.

        Args:
            timeout: Timeout in seconds

        Returns:
            Available output as UTF-8 string
        """
        if not self.is_alive or not self.terminal:
            raise RuntimeError(f"Terminal {self.id} is not running")

        try:
            import asyncio
            import os
            import select

            # Small delay to let data accumulate
            await asyncio.sleep(timeout)

            # Check if data is available to read (non-blocking)
            try:
                loop = asyncio.get_event_loop()

                # Use select to check if data is available
                fd = self.terminal.ptyproc.fd
                if os.name == 'nt':  # Windows
                    # On Windows, just try to read
                    try:
                        output = await loop.run_in_executor(
                            None, lambda: os.read(fd, 4096)
                        )
                        if output:
                            return output.decode("utf-8", errors="replace")
                    except:
                        pass
                else:  # Unix/Linux/macOS
                    # Use select to check if data is available
                    readable, _, _ = select.select([fd], [], [], 0)
                    if readable:
                        output = await loop.run_in_executor(
                            None, lambda: os.read(fd, 4096)
                        )
                        if output:
                            return output.decode("utf-8", errors="replace")

            except (OSError, IOError) as e:
                # No data available or error reading
                logger.debug(f"No data available or error: {e}")
                pass

            return ""
        except Exception as e:
            logger.error(f"Failed to read from terminal {self.id}: {e}")
            return ""

    async def resize(self, rows: int, cols: int):
        """
        Resize the terminal.

        Args:
            rows: New number of rows
            cols: New number of columns
        """
        if not self.is_alive or not self.terminal:
            raise RuntimeError(f"Terminal {self.id} is not running")

        try:
            self.rows = rows
            self.cols = cols
            self.terminal.ptyproc.setwinsize(rows, cols)
            logger.info(f"Terminal {self.id} resized to {rows}x{cols}")
        except Exception as e:
            logger.error(f"Failed to resize terminal {self.id}: {e}")
            raise

    async def close(self):
        """Close the terminal session and cleanup resources."""
        if not self.is_alive:
            logger.warning(f"Terminal {self.id} already closed")
            return

        try:
            if self.terminal:
                self.terminal.kill()

            self.is_alive = False
            logger.info(f"Terminal {self.id} closed")
        except Exception as e:
            logger.error(f"Failed to close terminal {self.id}: {e}")
            raise
