"""CLI entry point.

    python -m mcp_server --demo            # bundled sample data, offline
    python -m mcp_server                   # live JSON-RPC backend (BACKEND_URL)
    python -m mcp_server --allow-write     # disable the read-only allowlist

The server speaks the Model Context Protocol over stdio (the default transport),
ready to be registered with an MCP client such as Claude Desktop.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

from mcp_server import __version__
from mcp_server.config import build_settings
from mcp_server.server import create_server


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="mcp-erp-server",
        description="MCP server exposing an ERP / JSON-RPC backend as read-only tools.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        default=None,
        help="Serve the bundled sample dataset with no network access.",
    )
    parser.add_argument(
        "--backend-url",
        dest="backend_url",
        default=None,
        help="JSON-RPC endpoint to use in live mode (overrides BACKEND_URL).",
    )

    readonly_group = parser.add_mutually_exclusive_group()
    readonly_group.add_argument(
        "--readonly",
        dest="readonly",
        action="store_true",
        default=None,
        help="Enforce the read-only allowlist (default).",
    )
    readonly_group.add_argument(
        "--allow-write",
        dest="readonly",
        action="store_false",
        default=None,
        help="Disable the read-only allowlist (reserved for future write tools).",
    )

    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Build and run the server. Returns a process exit code."""
    args = _parse_args(argv)

    cli_overrides: dict[str, Any] = {
        "demo": args.demo,
        "backend_url": args.backend_url,
        "readonly": args.readonly,
    }
    settings = build_settings(cli_overrides)

    server = create_server(settings)
    # FastMCP.run() blocks, serving over stdio until the client disconnects.
    server.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
