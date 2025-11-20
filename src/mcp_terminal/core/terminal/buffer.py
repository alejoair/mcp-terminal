"""
Terminal buffer management using pyte for visual screen capture.
"""

import logging
from typing import Dict, List, Tuple

import pyte

logger = logging.getLogger(__name__)


class TerminalBuffer:
    """
    Manages terminal screen buffer and visual output capture.

    Uses pyte to emulate a terminal screen and process ANSI/VT100 sequences.
    Provides snapshot of what a human would see in the terminal.
    """

    def __init__(self, rows: int = 24, cols: int = 80):
        """
        Initialize terminal buffer.

        Args:
            rows: Number of rows (height)
            cols: Number of columns (width)
        """
        self.rows = rows
        self.cols = cols

        # Create pyte screen
        self.screen = pyte.Screen(cols, rows)
        self.stream = pyte.ByteStream(self.screen)

        logger.debug(f"Terminal buffer created: {rows}x{cols}")

    def feed(self, data: bytes):
        """
        Feed data to the terminal buffer.

        Processes ANSI escape sequences and updates screen buffer.

        Args:
            data: Raw bytes from terminal output
        """
        try:
            self.stream.feed(data)
        except Exception as e:
            logger.error(f"Error feeding data to buffer: {e}")

    def get_display(self) -> str:
        """
        Get current terminal display as plain text.

        Returns what a human would see on screen.

        Returns:
            Terminal display as multi-line string
        """
        try:
            lines = []
            for row_idx in range(self.rows):
                line = self.screen.display[row_idx]
                lines.append(line)

            return "\n".join(lines)
        except Exception as e:
            logger.error(f"Error getting display: {e}")
            return ""

    def get_display_lines(self) -> List[str]:
        """
        Get current terminal display as list of lines.

        Returns:
            List of strings, one per row
        """
        try:
            return [self.screen.display[i] for i in range(self.rows)]
        except Exception as e:
            logger.error(f"Error getting display lines: {e}")
            return []

    def get_cursor_position(self) -> Tuple[int, int]:
        """
        Get current cursor position.

        Returns:
            Tuple of (row, col) - zero-indexed
        """
        return (self.screen.cursor.y, self.screen.cursor.x)

    def get_cursor_info(self) -> Dict[str, int]:
        """
        Get detailed cursor information.

        Returns:
            Dict with cursor details
        """
        return {
            "row": self.screen.cursor.y,
            "col": self.screen.cursor.x,
            "visible": not self.screen.cursor.hidden,
        }

    def get_snapshot(self) -> Dict[str, any]:
        """
        Get complete snapshot of terminal state.

        Returns:
            Dict containing display, cursor position, and metadata
        """
        cursor_row, cursor_col = self.get_cursor_position()

        return {
            "display": self.get_display(),
            "lines": self.get_display_lines(),
            "cursor": {"row": cursor_row, "col": cursor_col},
            "size": {"rows": self.rows, "cols": self.cols},
        }

    def resize(self, rows: int, cols: int):
        """
        Resize the terminal buffer.

        Args:
            rows: New number of rows
            cols: New number of columns
        """
        try:
            self.rows = rows
            self.cols = cols
            self.screen.resize(rows, cols)
            logger.debug(f"Buffer resized to {rows}x{cols}")
        except Exception as e:
            logger.error(f"Error resizing buffer: {e}")
            raise

    def clear(self):
        """Clear the terminal buffer."""
        try:
            self.screen.reset()
        except Exception as e:
            logger.error(f"Error clearing buffer: {e}")

    def get_line(self, row: int) -> str:
        """
        Get specific line from display.

        Args:
            row: Row index (zero-indexed)

        Returns:
            Line content as string
        """
        if 0 <= row < self.rows:
            return self.screen.display[row]
        return ""

    def get_last_lines(self, n: int) -> List[str]:
        """
        Get last N lines from display.

        Args:
            n: Number of lines to retrieve from bottom

        Returns:
            List of last N lines
        """
        if n <= 0:
            return []
        if n >= self.rows:
            return self.get_display_lines()

        start_row = max(0, self.rows - n)
        return [self.screen.display[i] for i in range(start_row, self.rows)]

    def get_last_line(self) -> str:
        """
        Get the last line from display.

        Returns:
            Last line content as string
        """
        return self.screen.display[self.rows - 1] if self.rows > 0 else ""

    def get_cursor_area(self, context_lines: int = 3) -> Dict[str, any]:
        """
        Get lines around the cursor position.

        Args:
            context_lines: Number of lines before and after cursor

        Returns:
            Dict with lines, cursor info, and range
        """
        cursor_row, cursor_col = self.get_cursor_position()

        start_row = max(0, cursor_row - context_lines)
        end_row = min(self.rows, cursor_row + context_lines + 1)

        lines = [self.screen.display[i] for i in range(start_row, end_row)]

        return {
            "lines": lines,
            "cursor": {"row": cursor_row, "col": cursor_col},
            "range": {"start_row": start_row, "end_row": end_row},
            "total_lines": len(lines),
        }

    def get_snapshot_with_mode(
        self, view_mode: str = "full", n_lines: int = 10, context_lines: int = 3
    ) -> Dict[str, any]:
        """
        Get snapshot with specific view mode.

        Args:
            view_mode: View mode - "full", "last_line", "last_n_lines", "cursor_area"
            n_lines: Number of lines for "last_n_lines" mode
            context_lines: Context lines for "cursor_area" mode

        Returns:
            Dict containing display data based on view mode
        """
        cursor_row, cursor_col = self.get_cursor_position()

        if view_mode == "last_line":
            lines = [self.get_last_line()]
            display = lines[0]
            range_info = {"start_row": self.rows - 1, "end_row": self.rows}

        elif view_mode == "last_n_lines":
            lines = self.get_last_lines(n_lines)
            display = "\n".join(lines)
            start_row = max(0, self.rows - n_lines)
            range_info = {"start_row": start_row, "end_row": self.rows}

        elif view_mode == "cursor_area":
            cursor_data = self.get_cursor_area(context_lines)
            lines = cursor_data["lines"]
            display = "\n".join(lines)
            range_info = cursor_data["range"]

        else:  # "full" or default
            lines = self.get_display_lines()
            display = self.get_display()
            range_info = {"start_row": 0, "end_row": self.rows}

        return {
            "display": display,
            "lines": lines,
            "cursor": {"row": cursor_row, "col": cursor_col},
            "size": {"rows": self.rows, "cols": self.cols},
            "view_mode": view_mode,
            "range": range_info,
        }
