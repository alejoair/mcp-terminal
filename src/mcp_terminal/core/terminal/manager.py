"""
Terminal manager for handling multiple terminal sessions.
"""

import asyncio
import logging
from collections import deque
from typing import Dict, List, Optional

from .buffer import TerminalBuffer
from .session import TerminalSession

logger = logging.getLogger(__name__)


class TerminalManager:
    """
    Manages multiple terminal sessions.

    Coordinates TerminalSession and TerminalBuffer for each terminal.
    """

    def __init__(self):
        """Initialize the terminal manager."""
        self.sessions: Dict[str, TerminalSession] = {}
        self.buffers: Dict[str, TerminalBuffer] = {}
        # Circular buffer of last 5 snapshots per terminal
        self.snapshot_buffers: Dict[str, deque] = {}

        logger.info("Terminal manager initialized")

    async def create(
        self,
        rows: int = 24,
        cols: int = 80,
        shell_command: Optional[list] = None,
    ) -> str:
        """
        Create a new terminal session.

        Args:
            rows: Terminal height
            cols: Terminal width
            shell_command: Custom shell command

        Returns:
            Terminal ID
        """
        # Create session
        session = TerminalSession(rows, cols, shell_command)
        await session.start()

        # Create buffer
        buffer = TerminalBuffer(rows, cols)

        # Create snapshot buffer (circular, max 5)
        snapshot_buffer = deque(maxlen=5)

        # Store
        self.sessions[session.id] = session
        self.buffers[session.id] = buffer
        self.snapshot_buffers[session.id] = snapshot_buffer

        # Start internal output reader task
        task = asyncio.create_task(self._internal_output_reader(session.id))
        if not hasattr(self, '_reader_tasks'):
            self._reader_tasks = {}
        self._reader_tasks[session.id] = task

        logger.info(f"Terminal created: {session.id}")
        return session.id

    async def _internal_output_reader(self, terminal_id: str):
        """
        Internal output reader task.

        Automatically reads from PTY and updates snapshot buffer.

        Args:
            terminal_id: Terminal session ID
        """
        session = self.sessions.get(terminal_id)
        if not session:
            return

        logger.info(f"Internal output reader started for terminal {terminal_id}")

        try:
            while session.is_alive:
                try:
                    # Use terminado's read() method with timeout
                    loop = asyncio.get_event_loop()

                    def read_pty():
                        try:
                            # Read with short timeout (1 second)
                            return session.terminal.ptyproc.read()
                        except:
                            return b''

                    output = await loop.run_in_executor(None, read_pty)

                    if output:
                        # Decode if string, encode if needed
                        if isinstance(output, str):
                            output = output.encode('utf-8', errors='replace')

                        # Update snapshot buffer
                        self.update_snapshot(terminal_id, output)

                except Exception as e:
                    logger.debug(f"Read cycle: {e}")
                    pass

                # Small sleep to prevent tight loop
                await asyncio.sleep(0.05)
        except Exception as e:
            logger.error(f"Internal output reader error: {e}")
        finally:
            logger.info(f"Internal output reader stopped for terminal {terminal_id}")

    def update_snapshot(self, terminal_id: str, output: bytes):
        """
        Update terminal buffer with output and cache snapshot.

        Called by internal reader or WebSocket handler when new output arrives.

        Args:
            terminal_id: Terminal session ID
            output: Raw output bytes from terminal
        """
        buffer = self.buffers.get(terminal_id)
        snapshot_buffer = self.snapshot_buffers.get(terminal_id)

        if not buffer or snapshot_buffer is None:
            logger.warning(f"Buffer not found for terminal {terminal_id}")
            return

        # Feed output to buffer
        buffer.feed(output)

        # Generate and cache snapshot
        snapshot = buffer.get_snapshot()
        snapshot_buffer.append(snapshot)

        logger.debug(f"Snapshot updated for terminal {terminal_id}")

    async def get(self, terminal_id: str) -> Optional[TerminalSession]:
        """
        Get terminal session by ID.

        Args:
            terminal_id: Terminal ID

        Returns:
            TerminalSession or None
        """
        return self.sessions.get(terminal_id)

    async def send_input(self, terminal_id: str, data: str):
        """
        Send input to a terminal.

        Args:
            terminal_id: Terminal ID
            data: Input data to send
        """
        session = self.sessions.get(terminal_id)
        if not session:
            raise ValueError(f"Terminal not found: {terminal_id}")

        await session.write(data)

    async def get_snapshot(
        self,
        terminal_id: str,
        view_mode: str = "full",
        n_lines: int = 10,
        context_lines: int = 3,
    ) -> Dict:
        """
        Get cached visual snapshot of terminal with optional view mode.

        Returns the most recent snapshot from the buffer (updated via WebSocket).

        Args:
            terminal_id: Terminal ID
            view_mode: View mode - "full", "last_line", "last_n_lines", "cursor_area"
            n_lines: Number of lines for "last_n_lines" mode
            context_lines: Context lines for "cursor_area" mode

        Returns:
            Snapshot dict with display, cursor, etc.
        """
        session = self.sessions.get(terminal_id)
        buffer = self.buffers.get(terminal_id)

        if not session or not buffer:
            raise ValueError(f"Terminal not found: {terminal_id}")

        # Get snapshot with specified view mode
        if view_mode != "full":
            # Use buffer's view mode method for filtered views
            snapshot = buffer.get_snapshot_with_mode(view_mode, n_lines, context_lines)
        else:
            # Use cached snapshot for full view
            snapshot_buffer = self.snapshot_buffers.get(terminal_id)
            if snapshot_buffer:
                snapshot = dict(snapshot_buffer[-1])  # Copy last snapshot
            else:
                # No snapshots yet, get from buffer directly
                snapshot = buffer.get_snapshot()

        # Add metadata
        snapshot["terminal_id"] = terminal_id
        snapshot["is_alive"] = session.is_alive
        snapshot["created_at"] = session.created_at.isoformat()

        return snapshot

    async def resize(self, terminal_id: str, rows: int, cols: int):
        """
        Resize a terminal.

        Args:
            terminal_id: Terminal ID
            rows: New height
            cols: New width
        """
        session = self.sessions.get(terminal_id)
        buffer = self.buffers.get(terminal_id)

        if not session or not buffer:
            raise ValueError(f"Terminal not found: {terminal_id}")

        await session.resize(rows, cols)
        buffer.resize(rows, cols)

    async def close(self, terminal_id: str):
        """
        Close a terminal session.

        Args:
            terminal_id: Terminal ID
        """
        session = self.sessions.get(terminal_id)
        if not session:
            raise ValueError(f"Terminal not found: {terminal_id}")

        # Cancel internal reader task
        if hasattr(self, '_reader_tasks') and terminal_id in self._reader_tasks:
            task = self._reader_tasks[terminal_id]
            task.cancel()
            try:
                await asyncio.wait_for(task, timeout=1.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
            del self._reader_tasks[terminal_id]

        # Close session
        await session.close()

        # Cleanup
        del self.sessions[terminal_id]
        del self.buffers[terminal_id]
        if terminal_id in self.snapshot_buffers:
            del self.snapshot_buffers[terminal_id]

        logger.info(f"Terminal closed: {terminal_id}")

    async def list_terminals(self) -> List[Dict]:
        """
        List all active terminals.

        Returns:
            List of terminal info dicts
        """
        terminals = []
        for terminal_id, session in self.sessions.items():
            terminals.append(
                {
                    "id": terminal_id,
                    "rows": session.rows,
                    "cols": session.cols,
                    "is_alive": session.is_alive,
                    "created_at": session.created_at.isoformat(),
                }
            )
        return terminals

    async def close_all(self):
        """Close all terminal sessions."""
        terminal_ids = list(self.sessions.keys())
        for terminal_id in terminal_ids:
            try:
                await self.close(terminal_id)
            except Exception as e:
                logger.error(f"Error closing terminal {terminal_id}: {e}")
