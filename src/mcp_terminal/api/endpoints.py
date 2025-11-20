"""
Terminal HTTP endpoints.

Provides REST API for managing terminal sessions.
"""

import asyncio
import logging

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

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


@router.post("/", response_model=TerminalResponse, status_code=201)
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


@router.get("/", response_model=TerminalListResponse)
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


@router.get("/{terminal_id}/snapshot", response_model=TerminalSnapshot)
async def get_terminal_snapshot(terminal_id: str, manager: TerminalManagerDep):
    """
    Get visual snapshot of terminal.

    Shows what a human would see on the terminal screen.

    Args:
        terminal_id: Terminal session ID
        manager: Terminal manager dependency

    Returns:
        Terminal snapshot with display, cursor, and metadata
    """
    try:
        # Add 5 second timeout
        snapshot = await asyncio.wait_for(
            manager.get_snapshot(terminal_id), timeout=5.0
        )
        return TerminalSnapshot(**snapshot)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Request timeout")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting snapshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{terminal_id}/input", response_model=TerminalResponse)
async def send_terminal_input(
    terminal_id: str,
    request: TerminalInput,
    manager: TerminalManagerDep,
):
    """
    Send input to terminal session.

    Use this to send commands, keystrokes, or any input to the terminal.

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


@router.put("/{terminal_id}/resize", response_model=TerminalResponse)
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


@router.delete("/{terminal_id}", response_model=TerminalResponse)
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
