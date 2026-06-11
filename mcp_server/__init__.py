"""mcp-erp-server: a Model Context Protocol server exposing an ERP / JSON-RPC
backend to AI agents as typed, read-only tools.

Public surface:
    __version__   - package version string.
    create_server - build a configured FastMCP server (see server.py).
"""

from __future__ import annotations

__version__ = "0.1.0"

from mcp_server.server import create_server

__all__ = ["__version__", "create_server"]
