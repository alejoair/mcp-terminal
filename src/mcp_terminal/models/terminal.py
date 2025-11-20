"""
Pydantic models for terminal API endpoints.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TerminalCreate(BaseModel):
    """Request model for creating a new terminal."""

    rows: int = Field(default=24, ge=1, le=200, description="Terminal height in rows")
    cols: int = Field(
        default=80, ge=1, le=500, description="Terminal width in columns"
    )
    shell_command: Optional[List[str]] = Field(
        default=None, description="Custom shell command"
    )


class CursorPosition(BaseModel):
    """Cursor position information."""

    row: int = Field(description="Cursor row (zero-indexed)")
    col: int = Field(description="Cursor column (zero-indexed)")


class TerminalSize(BaseModel):
    """Terminal size information."""

    rows: int = Field(description="Terminal height")
    cols: int = Field(description="Terminal width")


class TerminalSnapshot(BaseModel):
    """Terminal visual snapshot."""

    terminal_id: str = Field(description="Terminal session ID")
    display: str = Field(description="Current terminal display as text")
    lines: List[str] = Field(description="Display lines as list")
    cursor: CursorPosition = Field(description="Cursor position")
    size: TerminalSize = Field(description="Terminal size")
    is_alive: bool = Field(description="Whether terminal is running")
    created_at: str = Field(description="Terminal creation timestamp")


class TerminalResponse(BaseModel):
    """Response model for terminal operations."""

    success: bool = Field(description="Operation success status")
    terminal_id: str = Field(description="Terminal session ID")
    message: Optional[str] = Field(default=None, description="Response message")


class TerminalInfo(BaseModel):
    """Terminal session information."""

    id: str = Field(description="Terminal session ID")
    rows: int = Field(description="Terminal height")
    cols: int = Field(description="Terminal width")
    is_alive: bool = Field(description="Whether terminal is running")
    created_at: str = Field(description="Creation timestamp")


class TerminalListResponse(BaseModel):
    """Response model for listing terminals."""

    success: bool = Field(description="Operation success status")
    terminals: List[TerminalInfo] = Field(description="List of active terminals")
    count: int = Field(description="Number of active terminals")


class TerminalInput(BaseModel):
    """Request model for sending input to terminal."""

    data: str = Field(description="Input data to send to terminal")


class TerminalResize(BaseModel):
    """Request model for resizing terminal."""

    rows: int = Field(ge=1, le=200, description="New terminal height")
    cols: int = Field(ge=1, le=500, description="New terminal width")
