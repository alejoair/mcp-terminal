"""
MCP Terminal Server - FastAPI application with MCP integration.

This server provides interactive terminal sessions via HTTP/REST and MCP protocol.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.endpoints import router
from .api.lifespan import lifespan

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="MCP Terminal Server",
    description="Interactive terminal sessions via Model Context Protocol (MCP)",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include router
app.include_router(router)

# Mount MCP server using fastapi-mcp
try:
    from fastapi_mcp import FastApiMCP

    logger.info("Initializing fastapi-mcp integration...")
    mcp = FastApiMCP(app, name="MCP Terminal Server")
    mcp.mount_http()  # Mounts at /mcp by default
    logger.info("✓ MCP server mounted at /mcp endpoint")
except ImportError:
    logger.warning("fastapi-mcp not installed. MCP tools will not be available.")
    logger.warning("Install with: pip install fastapi-mcp")
except Exception as e:
    logger.warning(f"Failed to mount MCP server: {e}")
    logger.warning("MCP tools will not be available via HTTP transport")
