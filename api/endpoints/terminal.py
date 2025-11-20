"""
Terminal API endpoints for interactive terminal sessions.
"""

import asyncio
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

try:
    from ...core.terminal import TerminalManager
except ImportError:
    try:
        from mcp_terminal.core.terminal import TerminalManager
    except ImportError:
        # Fallback for older structure
        from core.terminal import TerminalManager

from ..models.terminal import (
    TerminalCreate,
    TerminalInput,
    TerminalListResponse,
    TerminalResize,
    TerminalResponse,
    TerminalSnapshot,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/terminals", tags=["terminals"])

# Singleton terminal manager
_terminal_manager: TerminalManager = None


def get_terminal_manager() -> TerminalManager:
    """
    Get or create terminal manager instance.

    Returns:
        TerminalManager singleton
    """
    global _terminal_manager
    if _terminal_manager is None:
        _terminal_manager = TerminalManager()
    return _terminal_manager


TerminalManagerDep = Annotated[TerminalManager, Depends(get_terminal_manager)]


@router.post("/", response_model=TerminalResponse, status_code=201)
async def create_terminal(
    request: TerminalCreate,
    manager: TerminalManagerDep,
):
    """
    Create a new terminal session.

    Args:
        request: Terminal creation parameters
        manager: Terminal manager dependency

    Returns:
        Terminal creation response
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
        List of active terminals
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

    Args:
        terminal_id: Terminal session ID
        manager: Terminal manager dependency

    Returns:
        Terminal snapshot with display and cursor info
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

    Args:
        terminal_id: Terminal session ID
        request: Input data
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
        request: New size
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
