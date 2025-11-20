"""
Application lifespan management.

Handles startup and shutdown events for the FastAPI application.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .dependencies import get_terminal_manager

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events, including cleanup of terminals.
    """
    # Startup
    logger.info("MCP Terminal Server starting up...")
    yield

    # Shutdown - clean up all running terminals
    logger.info("MCP Terminal Server shutting down...")
    manager = get_terminal_manager()
    try:
        await manager.close_all()
        logger.info("All terminals have been closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

    logger.info("MCP Terminal Server shutdown complete")
