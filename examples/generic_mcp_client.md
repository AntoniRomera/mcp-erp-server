# Registering mcp-erp-server with a generic MCP client

This server speaks the [Model Context Protocol](https://modelcontextprotocol.io)
over **stdio** (the default transport). Any MCP-compatible client can launch it
as a subprocess and talk to it over stdin/stdout.

## Launch command

```bash
# Demo mode (bundled sample data, no backend, fully offline)
python -m mcp_server --demo

# Live mode (JSON-RPC backend)
BACKEND_URL=http://localhost:8069 READONLY=true python -m mcp_server
```

## Generic stdio config (JSON)

Most clients accept a server entry shaped like this:

```json
{
  "mcpServers": {
    "erp-demo": {
      "command": "python",
      "args": ["-m", "mcp_server", "--demo"],
      "cwd": "/absolute/path/to/mcp-erp-server"
    }
  }
}
```

For a live backend, drop `--demo` and pass env vars:

```json
{
  "mcpServers": {
    "erp": {
      "command": "python",
      "args": ["-m", "mcp_server"],
      "cwd": "/absolute/path/to/mcp-erp-server",
      "env": {
        "BACKEND_URL": "http://localhost:8069",
        "READONLY": "true"
      }
    }
  }
}
```

## Tools exposed

| Tool | Description |
|------|-------------|
| `list_invoices` | List invoices, optionally filtered by `partner_id` and `state` (`draft`/`posted`/`paid`). |
| `get_partner` | Fetch a single partner by `partner_id`. |
| `search_products` | Search products by `query` (name/SKU substring) and/or `category`. |

All three are **read-only** and gated by an allowlist (see `mcp_server/security.py`).

## Tips

- Prefer an absolute path or a virtualenv-resolved interpreter for `command`
  (e.g. `/abs/path/.venv/bin/python`) so the client can find the dependencies.
- Alternatively `pip install .` and use the `mcp-erp-server` console script as
  the `command` with `["--demo"]` as `args`.
