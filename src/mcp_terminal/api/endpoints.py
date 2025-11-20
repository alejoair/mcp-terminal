"""
Terminal HTTP endpoints.

Provides REST API for managing terminal sessions.
"""

import asyncio
import logging
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect

from ..models import (
    TerminalCreate,
    TerminalInput,
    TerminalListResponse,
    TerminalResize,
    TerminalResponse,
    TerminalSnapshot,
)
from .dependencies import TerminalManagerDep, get_terminal_manager

logger = logging.getLogger(__name__)

# Create router for terminal endpoints
router = APIRouter(prefix="/terminals", tags=["terminals"])


@router.post(
    "/",
    response_model=TerminalResponse,
    status_code=201,
    operation_id="create_terminal",
    summary="Create new terminal session",
)
async def create_terminal(
    request: TerminalCreate,
    manager: TerminalManagerDep,
):
    """
    Create a new terminal session.

    Args:
        request: Terminal creation parameters (rows, cols, shell_command)
        manager: Terminal manager dependency

    Returns:
        Terminal creation response with terminal ID
    """
    try:
        terminal_id = await manager.create(
            rows=request.rows,
            cols=request.cols,
            shell_command=request.shell_command,
        )

        return TerminalResponse(
            success=True,
            terminal_id=terminal_id,
            message="Terminal created successfully",
        )
    except Exception as e:
        logger.error(f"Error creating terminal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/",
    response_model=TerminalListResponse,
    operation_id="list_terminals",
    summary="List all terminals",
)
async def list_terminals(manager: TerminalManagerDep):
    """
    List all active terminal sessions.

    Args:
        manager: Terminal manager dependency

    Returns:
        List of active terminals with their info
    """
    try:
        terminals = await manager.list_terminals()
        return TerminalListResponse(
            success=True, terminals=terminals, count=len(terminals)
        )
    except Exception as e:
        logger.error(f"Error listing terminals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{terminal_id}/snapshot",
    response_model=TerminalSnapshot,
    operation_id="get_terminal_snapshot",
    summary="Get terminal visual snapshot",
)
async def get_terminal_snapshot(
    terminal_id: str,
    manager: TerminalManagerDep,
    view_mode: Literal["full", "last_line", "last_n_lines", "cursor_area"] = Query(
        default="full",
        description="View mode: 'full' (entire screen), 'last_line' (only last line), 'last_n_lines' (last N lines), 'cursor_area' (lines around cursor)",
    ),
    n_lines: int = Query(
        default=10,
        ge=1,
        le=200,
        description="Number of lines for 'last_n_lines' mode",
    ),
    context_lines: int = Query(
        default=3,
        ge=1,
        le=20,
        description="Context lines before/after cursor for 'cursor_area' mode",
    ),
):
    """
    Get visual snapshot of terminal.

    Shows what a human would see on the terminal screen.
    Supports different view modes to reduce context for LLMs.

    Args:
        terminal_id: Terminal session ID
        manager: Terminal manager dependency
        view_mode: View mode to use (full, last_line, last_n_lines, cursor_area)
        n_lines: Number of lines for last_n_lines mode
        context_lines: Context lines for cursor_area mode

    Returns:
        Terminal snapshot with display, cursor, and metadata
    """
    try:
        # Add 5 second timeout
        snapshot = await asyncio.wait_for(
            manager.get_snapshot(terminal_id, view_mode, n_lines, context_lines),
            timeout=5.0,
        )
        return TerminalSnapshot(**snapshot)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Request timeout")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting snapshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{terminal_id}/input",
    response_model=TerminalResponse,
    operation_id="send_terminal_input",
    summary="Send input to terminal",
)
async def send_terminal_input(
    terminal_id: str,
    request: TerminalInput,
    manager: TerminalManagerDep,
):
    """
    Send input to terminal session.

    Use this to send commands, keystrokes, or any input to the terminal.

    IMPORTANT: No automatic newline conversion is performed. You must send
    the exact characters needed for your shell/application.

    Special characters:
    - Use \\r\\n for Windows shell commands (cmd.exe, PowerShell)
    - Use \\n for Unix shells and text editors (vim, nano, multiline text)
    - Use \\x1b for ESC key (exit insert mode in vim, etc.)
    - Use \\x03 for Ctrl+C (interrupt process)
    - Use \\x04 for Ctrl+D (EOF/logout)
    - Other control characters: \\x01-\\x1F

    Examples:
    - Windows cmd.exe: "dir\\r\\n"
    - Windows PowerShell: "Get-ChildItem\\r\\n"
    - Unix bash: "ls\\n"
    - Vim multiline text: "line1\\nline2\\nline3"
    - Exit vim insert mode: "\\x1b"
    - Vim save and quit: "\\x1b:wq\\n"
    - Interrupt process: "\\x03"

    Args:
        terminal_id: Terminal session ID
        request: Input data to send
        manager: Terminal manager dependency

    Returns:
        Operation response
    """
    try:
        # Add 5 second timeout
        await asyncio.wait_for(
            manager.send_input(terminal_id, request.data), timeout=5.0
        )
        return TerminalResponse(
            success=True, terminal_id=terminal_id, message="Input sent successfully"
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Request timeout")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error sending input: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/{terminal_id}/resize",
    response_model=TerminalResponse,
    operation_id="resize_terminal",
    summary="Resize terminal window",
)
async def resize_terminal(
    terminal_id: str,
    request: TerminalResize,
    manager: TerminalManagerDep,
):
    """
    Resize terminal session.

    Args:
        terminal_id: Terminal session ID
        request: New terminal size (rows, cols)
        manager: Terminal manager dependency

    Returns:
        Operation response
    """
    try:
        # Add 5 second timeout
        await asyncio.wait_for(
            manager.resize(terminal_id, request.rows, request.cols), timeout=5.0
        )
        return TerminalResponse(
            success=True, terminal_id=terminal_id, message="Terminal resized"
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Request timeout")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error resizing terminal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/{terminal_id}",
    response_model=TerminalResponse,
    operation_id="close_terminal",
    summary="Close and cleanup terminal",
)
async def close_terminal(terminal_id: str, manager: TerminalManagerDep):
    """
    Close terminal session.

    Terminates the terminal session and cleans up resources.

    Args:
        terminal_id: Terminal session ID
        manager: Terminal manager dependency

    Returns:
        Operation response
    """
    try:
        # Add 5 second timeout
        await asyncio.wait_for(manager.close(terminal_id), timeout=5.0)
        return TerminalResponse(
            success=True, terminal_id=terminal_id, message="Terminal closed"
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Request timeout")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error closing terminal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/{terminal_id}/ws")
async def terminal_websocket(websocket: WebSocket, terminal_id: str):
    """
    WebSocket endpoint for real-time terminal I/O.

    Handles bidirectional communication:
    - Receives output from PTY and sends to client
    - Receives input from client and sends to PTY
    - Updates snapshot buffer automatically

    Args:
        websocket: WebSocket connection
        terminal_id: Terminal session ID
    """
    manager = get_terminal_manager()
    session = await manager.get(terminal_id)

    if not session:
        await websocket.close(code=1008, reason="Terminal not found")
        return

    await websocket.accept()
    logger.info(f"WebSocket connected for terminal {terminal_id}")

    # Create tasks for bidirectional communication
    async def read_from_pty():
        """Read from PTY and send to WebSocket client."""
        import os

        try:
            fd = session.terminal.ptyproc.fd
            while session.is_alive:
                try:
                    # Read from PTY (non-blocking)
                    loop = asyncio.get_event_loop()
                    output = await loop.run_in_executor(
                        None, lambda: os.read(fd, 4096)
                    )

                    if output:
                        # Update snapshot buffer
                        manager.update_snapshot(terminal_id, output)

                        # Send to WebSocket client
                        await websocket.send_bytes(output)

                except OSError:
                    await asyncio.sleep(0.01)
                except Exception as e:
                    logger.error(f"Error reading from PTY: {e}")
                    break

                await asyncio.sleep(0.01)
        except Exception as e:
            logger.error(f"PTY read task error: {e}")

    async def write_to_pty():
        """Receive from WebSocket client and write to PTY."""
        try:
            while True:
                try:
                    # Receive from WebSocket
                    data = await websocket.receive_text()

                    # Write to PTY
                    await session.write(data)

                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"Error writing to PTY: {e}")
                    break
        except Exception as e:
            logger.error(f"PTY write task error: {e}")

    # Run both tasks concurrently
    read_task = asyncio.create_task(read_from_pty())
    write_task = asyncio.create_task(write_to_pty())

    try:
        # Wait for either task to complete
        done, pending = await asyncio.wait(
            [read_task, write_task], return_when=asyncio.FIRST_COMPLETED
        )

        # Cancel remaining tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass
        logger.info(f"WebSocket disconnected for terminal {terminal_id}")
