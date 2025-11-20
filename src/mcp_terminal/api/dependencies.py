"""
Dependencies for FastAPI endpoints.

Provides singleton instances and dependency injection.
"""

import logging
from typing import Annotated

from fastapi import Depends

from ..core.terminal import TerminalManager

logger = logging.getLogger(__name__)

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


# Type alias for dependency injection
TerminalManagerDep = Annotated[TerminalManager, Depends(get_terminal_manager)]
