"""
FastAPI main application for MCP Open Client.
"""

import io
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from ..exceptions import MCPError
from .endpoints.chat import router as chat_router
from .endpoints.conversations import router as conversations_router
from .endpoints.providers import router as providers_router
from .endpoints.registry import router as registry_router
from .endpoints.servers import get_server_manager, router
from .endpoints.sse import router as sse_router
from .endpoints.terminal import router as terminal_router

# Configure UTF-8 encoding for stdout/stderr to handle Unicode characters (emojis, arrows, etc.)
# This fixes 'charmap' codec errors on Windows when printing Unicode characters
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NoCacheMiddleware(BaseHTTPMiddleware):
    """
    Middleware to disable caching for static files during development.

    Adds Cache-Control headers to prevent browser caching of JS/CSS files.
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Disable caching for static files (JS, CSS, etc.)
        if request.url.path.startswith("/ui/"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events, including cleanup of MCP servers.
    """
    # Startup
    logger.info("MCP Open Client API starting up...")

    # The application is ready to receive requests
    yield

    # Shutdown - clean up all running MCP servers
    logger.info("MCP Open Client API shutting down...")
    server_manager = get_server_manager()
    try:
        await server_manager.shutdown_all()
        logger.info("All MCP servers have been shut down")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

    logger.info("MCP Open Client API shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="MCP Open Client API",
    description="API for managing Model Context Protocol (MCP) servers with STDIO transport",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add no-cache middleware for development (prevents browser caching of static files)
app.add_middleware(NoCacheMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, configure specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)
app.include_router(providers_router)
app.include_router(chat_router)
app.include_router(registry_router)
app.include_router(conversations_router)
app.include_router(sse_router)
app.include_router(terminal_router)

# Mount static files for UI
ui_path = Path(__file__).parent.parent.parent / "ui"
if ui_path.exists():
    app.mount("/ui", StaticFiles(directory=str(ui_path), html=True), name="ui")

# Mount MCP server using fastapi-mcp
try:
    from fastapi_mcp import FastApiMCP

    logger.info("Initializing fastapi-mcp integration...")
    mcp = FastApiMCP(app, name="MCP Open Client API")
    mcp.mount_http()  # Mounts at /mcp by default
    logger.info("MCP server mounted at /mcp endpoint")
except Exception as e:
    logger.warning(f"Failed to mount MCP server: {e}")
    logger.warning("MCP tools will not be available via HTTP transport")


@app.exception_handler(MCPError)
async def mcp_error_handler(request, exc: MCPError):
    """Handle MCP-specific errors."""
    return JSONResponse(
        status_code=400,
        content={"success": False, "error": str(exc), "type": "MCPError"},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "type": "InternalServerError",
        },
    )


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "MCP Open Client API",
        "version": "0.1.0",
        "description": "API for managing Model Context Protocol (MCP) servers with STDIO transport",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "mcp_servers": "/servers",
            "create_server": "POST /servers",
            "list_servers": "GET /servers",
            "start_server": "POST /servers/{id}/start",
            "stop_server": "POST /servers/{id}/stop",
            "get_tools": "GET /servers/{id}/tools",
            "remove_server": "DELETE /servers/{id}",
            "ai_providers": "/providers",
            "create_provider": "POST /providers",
            "list_providers": "GET /providers",
            "get_provider": "GET /providers/{id}",
            "update_provider": "PUT /providers/{id}",
            "delete_provider": "DELETE /providers/{id}",
            "list_models": "GET /providers/{id}/models",
            "add_model": "POST /providers/{id}/models",
            "update_model": "PUT /providers/{id}/models/{model_name}",
            "delete_model": "DELETE /providers/{id}/models/{model_name}",
            "test_provider": "POST /providers/{id}/test",
            "test_model": "POST /providers/{id}/models/{model_name}/test",
            "openai_chat": "/v1/chat/completions",
            "stream_chat": "/v1/chat/stream",
            "list_models": "/v1/models",
            "list_tools": "/v1/tools",
            "registry_search": "GET /registry/search",
            "registry_list": "GET /registry/servers",
            "registry_get_server": "GET /registry/servers/{name}",
            "registry_categories": "GET /registry/categories",
            "registry_health": "GET /registry/health",
            "conversations": "/conversations",
            "create_conversation": "POST /conversations",
            "list_conversations": "GET /conversations",
            "get_conversation": "GET /conversations/{id}",
            "update_conversation": "PUT /conversations/{id}",
            "delete_conversation": "DELETE /conversations/{id}",
            "add_message": "POST /conversations/{id}/messages",
            "get_messages": "GET /conversations/{id}/messages",
            "add_context": "POST /conversations/{id}/context",
            "get_context": "GET /conversations/{id}/context",
            "enable_tool": "POST /conversations/{id}/tools",
            "get_enabled_tools": "GET /conversations/{id}/tools",
            "get_available_tools": "GET /conversations/{id}/tools/available",
            "search_conversations": "GET /conversations/search",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    server_manager = get_server_manager()
    servers = server_manager.get_all_servers()

    running_count = sum(1 for s in servers if s.status.value == "running")
    configured_count = sum(1 for s in servers if s.status.value == "configured")
    error_count = sum(1 for s in servers if s.status.value == "error")

    # Get provider statistics
    from .endpoints.providers import provider_manager

    providers_response = provider_manager.get_all_providers()
    providers = providers_response.providers

    enabled_count = sum(1 for p in providers if p.enabled)
    disabled_count = sum(1 for p in providers if not p.enabled)

    return {
        "status": "healthy",
        "mcp_servers": {
            "total": len(servers),
            "running": running_count,
            "configured": configured_count,
            "error": error_count,
        },
        "ai_providers": {
            "total": len(providers),
            "enabled": enabled_count,
            "disabled": disabled_count,
            "default": providers_response.default_provider,
        },
    }


def start_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = False):
    """
    Start the FastAPI server.

    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Enable auto-reload for development
    """
    import uvicorn

    uvicorn.run(
        "mcp_open_client.api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":
    start_server(reload=True)
