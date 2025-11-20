"""
Terminal manager for handling multiple terminal sessions.
"""

import asyncio
import logging
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
        self._output_tasks: Dict[str, asyncio.Task] = {}

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

        # Store
        self.sessions[session.id] = session
        self.buffers[session.id] = buffer

        # Start output monitoring task
        task = asyncio.create_task(self._monitor_output(session.id))
        self._output_tasks[session.id] = task

        logger.info(f"Terminal created: {session.id}")
        return session.id

    async def _monitor_output(self, terminal_id: str):
        """
        Monitor terminal output and feed to buffer.

        Args:
            terminal_id: Terminal session ID
        """
        session = self.sessions.get(terminal_id)
        buffer = self.buffers.get(terminal_id)

        if not session or not buffer:
            return

        while session.is_alive:
            try:
                # Read from terminal
                output = await session.read(timeout=0.1)

                # Feed to buffer
                if output:
                    buffer.feed(output.encode("utf-8"))

                # Small sleep to prevent tight loop
                await asyncio.sleep(0.05)
            except Exception as e:
                logger.error(f"Error monitoring terminal {terminal_id}: {e}")
                break

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

    async def get_snapshot(self, terminal_id: str) -> Dict:
        """
        Get visual snapshot of terminal.

        Args:
            terminal_id: Terminal ID

        Returns:
            Snapshot dict with display, cursor, etc.
        """
        buffer = self.buffers.get(terminal_id)
        session = self.sessions.get(terminal_id)

        if not buffer or not session:
            raise ValueError(f"Terminal not found: {terminal_id}")

        snapshot = buffer.get_snapshot()
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

        # Cancel output monitoring task
        task = self._output_tasks.get(terminal_id)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Close session
        await session.close()

        # Cleanup
        del self.sessions[terminal_id]
        del self.buffers[terminal_id]
        if terminal_id in self._output_tasks:
            del self._output_tasks[terminal_id]

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
